import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app import api, auth
from app.audit import Event, independent
from app.config import settings
from app.db import engine
from app.errors import DomainError
from app.schemas import ErrorOut

logger = logging.getLogger("if_arbitra")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    yield
    engine.dispose()


app = FastAPI(
    title="IF-Arbitra",
    version="1.0.0",
    lifespan=lifespan,
    responses={code: {"model": ErrorOut} for code in [401, 403, 404, 409, 422, 429, 503]},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings().frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Request-ID"],
)


def error(request, code, message, status):
    return JSONResponse(
        {"code": code, "message": message, "request_id": request.state.request_id},
        status_code=status,
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    started = time.perf_counter()
    length = request.headers.get("content-length", "0")
    # Exact Origin verification protects cookie sessions, including login CSRF and cross-site POSTs.
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.headers.get("origin") != settings().frontend_url
    ):
        response = error(request, "ORIGIN_REJECTED", "Origem da solicitação não autorizada.", 403)
    elif not length.isascii() or not length.isdecimal() or len(length) > 12:
        response = error(request, "INVALID_INPUT", "Tamanho da solicitação inválido.", 400)
    elif int(length) > 65536:
        response = error(
            request, "PAYLOAD_TOO_LARGE", "A solicitação excede o tamanho permitido.", 413
        )
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            # Exception type is diagnostic; SQL parameters and credential bodies are never logged.
            logger.error(
                json.dumps(
                    {"request_id": request.state.request_id, "error_type": type(exc).__name__}
                )
            )
            response = error(
                request,
                "INTERNAL_ERROR",
                "Não foi possível concluir a operação. Informe o código de atendimento à administração.",
                500,
            )
    response.headers.update(
        {
            "X-Request-ID": request.state.request_id,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin",
            "Cache-Control": "no-store",
        }
    )
    logger.info(
        json.dumps(
            {
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        )
    )
    return response


@app.exception_handler(DomainError)
def domain_error(request, exc):
    if request.method != "GET":
        independent(request, Event.REJECTED, payload={"code": exc.code, "path": request.url.path})
    return error(request, exc.code, exc.message, exc.status)


@app.exception_handler(IntegrityError)
def integrity_error(request, exc):
    constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "")
    if constraint == "uq_student_active_sextet":
        code, message = (
            "STUDENT_ALREADY_IN_SEXTET",
            "Este aluno já pertence a outro sexteto. Revise a composição.",
        )
    elif constraint == "users_login_key":
        code, message = "LOGIN_ALREADY_EXISTS", "Este identificador já está cadastrado."
    else:
        code, message = (
            "INTEGRITY_CONFLICT",
            "Os dados conflitam com o estado atual do processo. Recarregue e confira a operação.",
        )
    independent(request, Event.REJECTED, payload={"code": code, "path": request.url.path})
    return error(request, code, message, 409)


@app.exception_handler(OperationalError)
def operational_error(request, exc):
    return error(request, "SERVICE_BUSY", "O serviço está ocupado. Aguarde e tente novamente.", 503)


@app.exception_handler(RequestValidationError)
def validation_error(request, exc):
    # Do not echo Pydantic inputs: login/student payloads contain passwords.
    if request.method != "GET":
        independent(
            request, Event.REJECTED, payload={"code": "INVALID_INPUT", "path": request.url.path}
        )
    return error(
        request,
        "INVALID_INPUT",
        "Confira os campos, a quantidade de integrantes e as datas informadas.",
        422,
    )


@app.get("/health", tags=["Operação"])
def health():
    return {"status": "alive"}


@app.get("/ready", tags=["Operação"])
def ready():
    try:
        with engine.connect() as conn:
            version = conn.scalar(text("SELECT version_num FROM alembic_version"))
        if version != "0003_audit_context":
            return JSONResponse({"status": "not_ready"}, status_code=503)
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}


app.include_router(auth.router, prefix="/api")
app.include_router(api.router, prefix="/api")
