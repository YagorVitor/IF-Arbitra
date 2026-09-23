from fastapi import Depends, Request
from sqlalchemy import select

from app.core.errors import DomainError
from app.core.security import COOKIE, digest
from app.db.models import LoginSession, User
from app.db.session import SessionFactory, database_now


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
