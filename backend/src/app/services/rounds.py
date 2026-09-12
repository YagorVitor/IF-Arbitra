from sqlalchemy import delete, select, update

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    AllocationRound,
    InstitutionalStaff,
    RoundStaff,
    Sextet,
    SextetMember,
)
from app.db.session import database_now


def locked_round(db, round_id):
    # Every critical writer takes this database row lock, including round administration.
    # PostgreSQL coordinates multiple processes; no process-local lock is relied on.
    round_ = db.scalar(
        select(AllocationRound).where(AllocationRound.id == round_id).with_for_update()
    )
    if not round_:
        raise DomainError("ROUND_NOT_FOUND", "Rodada não encontrada.", 404)
    return round_


def eligible_staff(db, round_id):
    return list(
        db.scalars(
            select(RoundStaff.staff_id)
            .where(RoundStaff.round_id == round_id)
            .order_by(RoundStaff.order)
        )
    )


def assert_window(db, round_, kind):
    now = database_now(db)
    opens = round_.preferences_open_at if kind == "preferences" else round_.registration_opens_at
    closes = round_.preferences_close_at if kind == "preferences" else round_.registration_closes_at
    if round_.status != "OPEN" or not opens <= now < closes:
        code = "PREFERENCE_WINDOW_CLOSED" if kind == "preferences" else "REGISTRATION_WINDOW_CLOSED"
        raise DomainError(
            code,
            "O período de envio de preferências está fechado."
            if kind == "preferences"
            else "O período de confirmação de sextetos está fechado.",
        )
    return now


def set_round_staff(db, r, ids):
    found = list(
        db.scalars(
            select(InstitutionalStaff.id)
            .where(InstitutionalStaff.id.in_(ids), InstitutionalStaff.active)
            .order_by(InstitutionalStaff.id)
            .with_for_update()
        )
    )
    if set(found) != set(ids):
        raise DomainError(
            "STAFF_NOT_ELIGIBLE", "Selecione apenas servidores ativos existentes.", 422
        )
    db.execute(delete(RoundStaff).where(RoundStaff.round_id == r.id))
    db.add_all([RoundStaff(round_id=r.id, staff_id=s, order=i) for i, s in enumerate(ids)])


def create_round(db, request, data):
    r = AllocationRound(**data.model_dump(exclude={"staff_ids"}))
    db.add(r)
    db.flush()
    set_round_staff(db, r, data.staff_ids)
    record(
        db,
        request,
        Event.ADMIN,
        r.id,
        {"action": "ROUND_CREATED"},
        after=data.model_dump(mode="json"),
        entity_type="ALLOCATION_ROUND",
    )
    db.flush()
    return r


def edit_round(db, request, round_id, data):
    r = locked_round(db, round_id)
    if r.status != "DRAFT":
        raise DomainError(
            "ROUND_FROZEN", "Os prazos e os servidores são fixados ao abrir a rodada."
        )
    before = {k: str(getattr(r, k)) for k in data.model_dump(exclude={"staff_ids"})}
    before["staff_ids"] = [str(s) for s in eligible_staff(db, r.id)]
    for k, v in data.model_dump(exclude={"staff_ids"}).items():
        setattr(r, k, v)
    set_round_staff(db, r, data.staff_ids)
    record(
        db,
        request,
        Event.ADMIN,
        r.id,
        {"action": "ROUND_UPDATED"},
        before=before,
        after=data.model_dump(mode="json"),
        entity_type="ALLOCATION_ROUND",
    )
    db.flush()
    return r


def transition(db, request, round_id, data):
    allowed = {
        "open": ("DRAFT", "OPEN"),
        "publish": ("PROCESSED", "PUBLISHED"),
        "archive": ("PUBLISHED", "ARCHIVED"),
    }
    r = locked_round(db, round_id)
    before, after = allowed[data.action]
    if r.status == after:
        return r
    if r.status != before:
        raise DomainError(
            "INVALID_ROUND_TRANSITION", "Esta ação não é permitida no estado atual da rodada."
        )
    if data.action == "open" and database_now(db) >= r.preferences_close_at:
        raise DomainError("ROUND_EXPIRED", "Defina prazos futuros antes de abrir a rodada.")
    if data.action == "open":
        ids = eligible_staff(db, r.id)
        active = list(
            db.scalars(
                select(InstitutionalStaff.id)
                .where(InstitutionalStaff.id.in_(ids), InstitutionalStaff.active)
                .order_by(InstitutionalStaff.id)
                .with_for_update()
            )
        )
        if not ids or set(ids) != set(active):
            raise DomainError(
                "STAFF_NOT_ELIGIBLE",
                "Revise os servidores elegíveis antes de abrir a rodada.",
                422,
            )
    r.status = after
    db.flush()
    if data.action == "archive":
        db.execute(
            update(SextetMember)
            .where(SextetMember.sextet_id.in_(select(Sextet.id).where(Sextet.round_id == round_id)))
            .values(active=False)
        )
    record(
        db,
        request,
        Event.ADMIN,
        r.id,
        {"action": data.action},
        before={"status": before},
        after={"status": after},
        entity_type="ALLOCATION_ROUND",
    )
    return r
