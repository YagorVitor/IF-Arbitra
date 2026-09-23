from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError
from starlette.exceptions import HTTPException

from app.core.audit import Event, independent
from app.core.errors import DomainError


def error(request, code, message, status):
    return JSONResponse(
        {"code": code, "message": message, "request_id": request.state.request_id},
        status_code=status,
    )


def domain_error(request, exc):
    if request.method != "GET":
        independent(request, Event.REJECTED, payload={"code": exc.code, "path": request.url.path})
    return error(request, exc.code, exc.message, exc.status)


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


def operational_error(request, exc):
    return error(request, "SERVICE_BUSY", "O serviço está ocupado. Aguarde e tente novamente.", 503)


def http_error(request, exc):
    response = error(
        request,
        "NOT_FOUND"
        if exc.status_code == 404
        else "METHOD_NOT_ALLOWED"
        if exc.status_code == 405
        else "HTTP_ERROR",
        "Recurso não encontrado." if exc.status_code == 404 else "Operação HTTP não permitida.",
        exc.status_code,
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


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


def register_exception_handlers(app):
    for exception, handler in (
        (DomainError, domain_error),
        (IntegrityError, integrity_error),
        (OperationalError, operational_error),
        (TimeoutError, operational_error),
        (HTTPException, http_error),
        (RequestValidationError, validation_error),
    ):
        app.add_exception_handler(exception, handler)
