"""Explicit maintenance of disposable test data with a matching exported snapshot."""

import hashlib
import json
import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, text

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    Allocation,
    AllocationAdjustment,
    AllocationRound,
    AllocationRun,
    AuditEvent,
    LoginSession,
    PreferenceItem,
    PreferenceSubmission,
    RoundStaff,
    Sextet,
    SextetMember,
    StaffReservation,
    User,
)

GUARDED = (
    "audit_events",
    "allocation_adjustments",
    "allocations",
    "allocation_runs",
    "preference_items",
    "sextet_members",
    "sextets",
    "round_staff",
    "allocation_rounds",
)


def qa_user(user):
    return user.role == "STUDENT" and bool(
        re.fullmatch(r"qa-aluno-\d{2,3}@(if-arbitra\.invalid|example\.org)", user.login.casefold())
    )


def encode(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def export_rows(db, model, condition=None, exclude=()):
    query = select(model)
    if condition is not None:
        query = query.where(condition)
    rows = [
        {c.name: getattr(row, c.name) for c in model.__table__.columns if c.name not in exclude}
        for row in db.scalars(query)
    ]
    return sorted(
        json.loads(json.dumps(rows, default=encode)), key=lambda r: json.dumps(r, sort_keys=True)
    )


def preview_cleanup(db):
    if db.scalar(
        select(AuditEvent.id)
        .where(AuditEvent.payload["action"].astext == "TEST_DATA_CLEANED")
        .limit(1)
    ):
        raise DomainError(
            "CLEANUP_ALREADY_COMPLETED", "A limpeza inicial de testes já foi concluída.", 409
        )
    rounds = list(db.scalars(select(AllocationRound)))
    if any(r.status != "ARCHIVED" for r in rounds):
        raise DomainError(
            "CLEANUP_ROUND_ACTIVE", "Arquive todas as rodadas antes desta limpeza de testes.", 409
        )
    round_ids = [r.id for r in rounds]
    qa_ids = [u.id for u in db.scalars(select(User)) if qa_user(u)]
    group_ids = list(db.scalars(select(Sextet.id).where(Sextet.round_id.in_(round_ids))))
    snapshot = {
        "users": export_rows(db, User, User.id.in_(qa_ids), exclude=("password_hash",)),
        "rounds": export_rows(db, AllocationRound, AllocationRound.id.in_(round_ids)),
        "round_staff": export_rows(db, RoundStaff, RoundStaff.round_id.in_(round_ids)),
        "groups": export_rows(db, Sextet, Sextet.round_id.in_(round_ids)),
        "members": export_rows(db, SextetMember, SextetMember.sextet_id.in_(group_ids)),
        "submissions": export_rows(
            db, PreferenceSubmission, PreferenceSubmission.round_id.in_(round_ids)
        ),
        "preferences": export_rows(db, PreferenceItem, PreferenceItem.round_id.in_(round_ids)),
        "runs": export_rows(db, AllocationRun, AllocationRun.round_id.in_(round_ids)),
        "allocations": export_rows(db, Allocation, Allocation.round_id.in_(round_ids)),
        "adjustments": export_rows(
            db, AllocationAdjustment, AllocationAdjustment.round_id.in_(round_ids)
        ),
        "audit": export_rows(db, AuditEvent),
        "qa_reservations": export_rows(
            db, StaffReservation, StaffReservation.captain_id.in_(qa_ids)
        ),
    }
    fingerprint = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "fingerprint": fingerprint,
        "counts": {k: len(v) for k, v in snapshot.items()},
        "snapshot": snapshot,
    }


def cleanup(db, request, fingerprint):
    # Exclusive transactional locks prevent concurrent writes and preserve FK checks.
    tables = ", ".join(
        (*GUARDED, "preference_submissions", "users", "login_sessions", "staff_reservations")
    )
    db.execute(text(f"LOCK TABLE {tables} IN ACCESS EXCLUSIVE MODE"))
    preview = preview_cleanup(db)
    if preview["fingerprint"] != fingerprint:
        raise DomainError(
            "CLEANUP_CONFLICT", "Os dados mudaram. Exporte uma nova cópia antes de limpar.", 409
        )
    round_ids = [UUID(r["id"]) for r in preview["snapshot"]["rounds"]]
    qa_ids = [UUID(u["id"]) for u in preview["snapshot"]["users"]]
    group_ids = [UUID(g["id"]) for g in preview["snapshot"]["groups"]]
    # DDL is transactional: a failure rolls back both data and trigger changes.
    for table in GUARDED:
        db.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
    db.execute(delete(AuditEvent))
    for model in (
        AllocationAdjustment,
        Allocation,
        AllocationRun,
        PreferenceItem,
        PreferenceSubmission,
    ):
        db.execute(delete(model).where(model.round_id.in_(round_ids)))
    db.execute(delete(SextetMember).where(SextetMember.sextet_id.in_(group_ids)))
    db.execute(delete(Sextet).where(Sextet.round_id.in_(round_ids)))
    db.execute(delete(RoundStaff).where(RoundStaff.round_id.in_(round_ids)))
    db.execute(delete(AllocationRound).where(AllocationRound.id.in_(round_ids)))
    db.execute(delete(StaffReservation).where(StaffReservation.captain_id.in_(qa_ids)))
    db.execute(delete(LoginSession).where(LoginSession.user_id.in_(qa_ids)))
    db.execute(delete(User).where(User.id.in_(qa_ids)))
    for table in GUARDED:
        db.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))
    record(
        db,
        request,
        Event.ADMIN,
        payload={
            "action": "TEST_DATA_CLEANED",
            "counts": preview["counts"],
            "backup_fingerprint": fingerprint,
        },
        entity_type="MAINTENANCE",
    )
    return {"deleted": preview["counts"], "audit_remaining": 1}
