import json
import logging
import time
import uuid

from fastapi import Request
from sqlalchemy.exc import OperationalError, TimeoutError
from starlette.concurrency import run_in_threadpool

from app.api.errors import error
from app.core.audit import Event, independent
from app.core.config import settings

logger = logging.getLogger("if_arbitra")


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
            # Count received bytes as well: chunked requests can omit Content-Length.
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 65536:
                    break
                chunks.append(chunk)
            if size > 65536:
                response = error(
                    request, "PAYLOAD_TOO_LARGE", "A solicitação excede o tamanho permitido.", 413
                )
            else:
                # Starlette's cached request replays this bounded body to the downstream app.
                request._body = b"".join(chunks)
                response = await call_next(request)
        except (OperationalError, TimeoutError):
            response = error(
                request, "SERVICE_BUSY", "O serviço está ocupado. Aguarde e tente novamente.", 503
            )
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
    if response.status_code in {400, 413} or (
        response.status_code == 403 and request.headers.get("origin") != settings().frontend_url
    ):
        try:
            await run_in_threadpool(
                independent,
                request,
                Event.REJECTED,
                payload={"status": response.status_code, "path": request.url.path},
            )
        except (OperationalError, TimeoutError):
            logger.error(
                json.dumps(
                    {"request_id": request.state.request_id, "error_type": "AuditUnavailable"}
                )
            )
    response.headers.update(
        {
            "X-Request-ID": request.state.request_id,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin",
            "Cache-Control": "no-store",
        }
    )
    # Early middleware errors must remain readable by the authorized frontend too.
    if request.headers.get("origin") == settings().frontend_url:
        response.headers["Access-Control-Allow-Origin"] = settings().frontend_url
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
        if "origin" not in response.headers.get("Vary", "").lower():
            response.headers.add_vary_header("Origin")
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
