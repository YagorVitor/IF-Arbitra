import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.audit import Event, independent, record
from app.config import settings
from app.db import SessionFactory, database_now
from app.errors import DomainError
from app.models import LoginSession, LoginThrottle, User
from app.schemas import LoginInput, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
dummy_hash = hasher.hash(secrets.token_urlsafe(32))
COOKIE = "if_arbitra_session"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def current_user(request: Request) -> User:
    token = request.cookies.get(COOKIE, "")
    with SessionFactory() as db:
        user = db.scalar(
            select(User)
            .join(LoginSession)
            .where(
                LoginSession.token_hash == digest(token),
                LoginSession.expires_at > database_now(db),
                User.active,
            )
        )
        if not user:
            raise DomainError("AUTH_REQUIRED", "Entre para acessar o processo.", 401)
        request.state.actor_id = user.id
        return user


def admin(user: User = Depends(current_user)) -> User:
    if user.role != "ADMIN":
        raise DomainError("ADMIN_REQUIRED", "Esta ação é exclusiva da administração.", 403)
    return user


def throttle(request: Request, login: str):
    # Persistent counters coordinate all workers. IP and login each have independent limits.
    ip = request.client.host if request.client else "unknown"
    denied = False
    with SessionFactory.begin() as db:
        now = database_now(db)
        db.execute(delete(LoginThrottle).where(LoginThrottle.expires_at < now))
        for key, limit in sorted([(digest("ip:" + ip), 300), (digest("login:" + login), 10)]):
            db.execute(
                insert(LoginThrottle)
                .values(key=key, count=0, expires_at=now + timedelta(minutes=15))
                .on_conflict_do_nothing()
            )
            counter = db.scalar(
                select(LoginThrottle).where(LoginThrottle.key == key).with_for_update()
            )
            counter.count += 1
            denied |= counter.count > limit
    if denied:
        independent(request, Event.LOGIN_FAILED, payload={"reason": "RATE_LIMITED"})
        raise DomainError("RATE_LIMITED", "Muitas tentativas. Aguarde 15 minutos.", 429)


@router.post("/login", response_model=UserOut)
def login(data: LoginInput, request: Request, response: Response):
    identifier = data.login.casefold()
    throttle(request, identifier)
    with SessionFactory.begin() as db:
        # Serialize password verification with operator password resets/session revocation.
        user = db.scalar(
            select(User).where(User.login == identifier, User.active).with_for_update()
        )
        try:
            hasher.verify(user.password_hash if user else dummy_hash, data.password)
            valid = user is not None
        except VerificationError:
            valid = False
        if not valid:
            independent(request, Event.LOGIN_FAILED)
            raise DomainError("INVALID_CREDENTIALS", "Identificador ou senha incorretos.", 401)
        request.state.actor_id = user.id
        if hasher.check_needs_rehash(user.password_hash):
            user.password_hash = hasher.hash(data.password)
        now = database_now(db)
        db.execute(delete(LoginSession).where(LoginSession.expires_at < now))
        token = secrets.token_urlsafe(48)
        db.add(
            LoginSession(
                token_hash=digest(token),
                user_id=user.id,
                expires_at=now + timedelta(hours=settings().session_hours),
            )
        )
        record(db, request, Event.LOGIN_SUCCESS, user.id, entity_type="USER")
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
