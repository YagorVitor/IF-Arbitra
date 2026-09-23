import secrets
from datetime import timedelta

from argon2.exceptions import VerificationError
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert

from app.core.audit import Event, independent, record
from app.core.config import settings
from app.core.errors import DomainError
from app.core.security import digest, dummy_hash, hasher
from app.db.models import LoginSession, LoginThrottle, User
from app.db.session import SessionFactory, database_now


def throttle(request, login: str):
    # Persistent counters coordinate all workers. IP and login each have independent limits.
    ip = request.client.host if request.client else "unknown"
    denied = False
    with SessionFactory.begin() as db:
        now = database_now(db)
        for key, limit in sorted([(digest("ip:" + ip), 300), (digest("login:" + login), 10)]):
            expired = LoginThrottle.expires_at <= now
            count = db.scalar(
                insert(LoginThrottle)
                .values(key=key, count=1, expires_at=now + timedelta(minutes=15))
                .on_conflict_do_update(
                    index_elements=[LoginThrottle.key],
                    set_={
                        "count": case((expired, 1), else_=LoginThrottle.count + 1),
                        "expires_at": case(
                            (expired, now + timedelta(minutes=15)), else_=LoginThrottle.expires_at
                        ),
                    },
                )
                .returning(LoginThrottle.count)
            )
            denied |= count > limit
    if denied:
        independent(request, Event.LOGIN_FAILED, payload={"reason": "RATE_LIMITED"})
        raise DomainError("RATE_LIMITED", "Muitas tentativas. Aguarde 15 minutos.", 429)


def authenticate(request, login, password):
    identifier = login.casefold()
    throttle(request, identifier)
    try:
        with SessionFactory.begin() as db:
            # Serialize password verification with operator password resets/session revocation.
            user = db.scalar(
                select(User).where(User.login == identifier, User.active).with_for_update()
            )
            try:
                hasher.verify(user.password_hash if user else dummy_hash, password)
                valid = user is not None
            except VerificationError:
                valid = False
            if not valid:
                raise DomainError("INVALID_CREDENTIALS", "Identificador ou senha incorretos.", 401)
            request.state.actor_id = user.id
            if hasher.check_needs_rehash(user.password_hash):
                user.password_hash = hasher.hash(password)
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
    except DomainError as exc:
        if exc.code == "INVALID_CREDENTIALS":
            # Release the login transaction before opening an independent audit transaction.
            independent(request, Event.LOGIN_FAILED)
        raise
    return user, token
