"""Administrator-triggered delivery of equal-length student credentials."""

import secrets
import smtplib
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.message import EmailMessage
from uuid import uuid4

from sqlalchemy import func, select

from app.core.audit import Event, independent, record
from app.core.config import settings
from app.core.errors import DomainError
from app.core.security import hasher
from app.db.models import User
from app.db.session import SessionFactory

PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PASSWORD_LENGTH = 8
MAX_DELIVERY_WORKERS = 4


def new_password() -> str:
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(PASSWORD_LENGTH))


def _send_credentials(email: str, password: str):
    config = settings()
    message = EmailMessage()
    message["From"] = config.smtp_from
    message["To"] = email
    message["Subject"] = "IF-Arbitra: suas credenciais de acesso"
    message.set_content(
        "Suas credenciais para o IF-Arbitra:\n\n"
        f"Usuário: {email}\n"
        f"Senha: {password}\n\n"
        "Aguarde a abertura da rodada pela administração para participar."
    )
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=5) as smtp:
            if config.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if config.smtp_username:
                smtp.login(config.smtp_username, config.smtp_password or "")
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise DomainError("EMAIL_UNAVAILABLE", "Falha no envio das credenciais.", 503) from exc


def _deliver_one(request, user_id, dispatch_id) -> str:
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User)
            .where(
                User.id == user_id,
                User.role == "STUDENT",
                User.active.is_(False),
                User.password_hash.is_(None),
                User.email.is_not(None),
                User.removed_at.is_(None),
            )
            .with_for_update(skip_locked=True)
        )
        if student is None:
            return "skipped"
        address = student.email.casefold()
        conflict = db.scalar(select(User.id).where(User.login == address, User.id != user_id))
        if conflict:
            raise DomainError("LOGIN_ALREADY_EXISTS", "O e-mail conflita com outro login.", 409)
        password = new_password()
        student.login = address
        student.password_hash = hasher.hash(password)
        db.flush()  # Resolve uniqueness errors before sending an email.
        _send_credentials(address, password)
        student.active = True
        record(
            db,
            request,
            Event.CREDENTIAL_DISPATCHED,
            student.id,
            {"dispatch_id": str(dispatch_id), "password_length": PASSWORD_LENGTH},
            entity_type="USER",
        )
    return "sent"


def dispatch_credentials(request) -> dict:
    if not settings().smtp_host or not settings().smtp_from:
        raise DomainError("EMAIL_UNAVAILABLE", "Configure SMTP antes do disparo.", 503)
    dispatch_id = uuid4()
    with SessionFactory.begin() as db:
        recipients = db.execute(
            select(User.id, User.email)
            .where(
                User.role == "STUDENT",
                User.active.is_(False),
                User.password_hash.is_(None),
                User.email.is_not(None),
                User.removed_at.is_(None),
            )
            .order_by(User.id)
        ).all()
        record(
            db,
            request,
            Event.CREDENTIAL_DISPATCH_STARTED,
            dispatch_id,
            {"eligible": len(recipients), "password_length": PASSWORD_LENGTH},
            entity_type="CREDENTIAL_DISPATCH",
        )
    sent = 0
    failed = []
    with ThreadPoolExecutor(max_workers=MAX_DELIVERY_WORKERS) as pool:
        future_to_recipient = {
            pool.submit(_deliver_one, request, user_id, dispatch_id): (user_id, address)
            for user_id, address in recipients
        }
        for future in as_completed(future_to_recipient):
            user_id, address = future_to_recipient[future]
            try:
                sent += future.result() == "sent"
            except Exception as exc:
                code = exc.code if isinstance(exc, DomainError) else "DISPATCH_FAILED"
                failed.append({"email": address, "code": code})
                independent(
                    request,
                    Event.CREDENTIAL_DELIVERY_FAILED,
                    user_id,
                    {"dispatch_id": str(dispatch_id), "code": code},
                    entity_type="USER",
                )
    with SessionFactory.begin() as db:
        pending_remaining = db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.role == "STUDENT",
                User.active.is_(False),
                User.password_hash.is_(None),
                User.email.is_not(None),
                User.removed_at.is_(None),
            )
        )
        record(
            db,
            request,
            Event.CREDENTIAL_DISPATCH_FINISHED,
            dispatch_id,
            {"sent": sent, "failed": len(failed), "pending_remaining": pending_remaining},
            entity_type="CREDENTIAL_DISPATCH",
        )
    return {
        "dispatch_id": dispatch_id,
        "eligible": len(recipients),
        "sent": sent,
        "failed": sorted(failed, key=lambda item: item["email"]),
        "pending_remaining": pending_remaining,
    }
