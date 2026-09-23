from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete

from app.api.dependencies import current_user
from app.api.schemas.users import LoginInput, UserOut
from app.core.audit import Event, record
from app.core.config import settings
from app.core.security import COOKIE, digest
from app.db.models import LoginSession, User
from app.db.session import SessionFactory
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=UserOut)
def login(data: LoginInput, request: Request, response: Response):
    user, token = authenticate(request, data.login, data.password)
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings().cookie_secure,
        samesite=settings().cookie_samesite,
        max_age=settings().session_hours * 3600,
    )
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, user: User = Depends(current_user)):
    with SessionFactory.begin() as db:
        db.execute(
            delete(LoginSession).where(
                LoginSession.token_hash == digest(request.cookies.get(COOKIE, ""))
            )
        )
        record(db, request, Event.LOGOUT, user.id, entity_type="USER")
    response.delete_cookie(
        COOKIE, secure=settings().cookie_secure, samesite=settings().cookie_samesite
    )
