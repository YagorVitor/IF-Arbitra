from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, select, update

from app.audit import Event, independent, record
from app.auth import admin, current_user, hasher
from app.db import SessionFactory, database_now
from app.errors import DomainError
from app.models import (
    Allocation,
    AllocationRound,
    AllocationRun,
    AuditEvent,
    InstitutionalStaff,
    RoundStaff,
    Sextet,
    SextetMember,
    User,
)
from app.responses import PreferenceOut, RoundOut, SextetOut, StaffOut
from app.schemas import (
    PreferencesInput,
    RoundInput,
    SextetInput,
    StaffInput,
    TransitionInput,
    UserInput,
    UserOut,
)
from app.services import (
    locked_round,
    owned_sextet,
    process_allocation,
    register_sextet,
    save_preferences,
)
from app.views import round_view, round_views, sextet_view

router = APIRouter()


@router.get("/students", tags=["Alunos"])
def students(q: str = Query(min_length=2, max_length=100), user=Depends(current_user)):
    with SessionFactory() as db:
        term = q.replace("%", "\\%").replace("_", "\\_")
        rows = (
            db.execute(
                select(
                    User.id,
                    User.name,
                    User.login,
                    select(SextetMember.user_id)
                    .where(SextetMember.user_id == User.id, SextetMember.active)
                    .exists()
                    .label("occupied"),
                )
                .where(
                    User.active,
                    User.role == "STUDENT",
                    (User.name.ilike(f"%{term}%") | User.login.ilike(f"%{term}%")),
                )
                .order_by(User.name, User.id)
                .limit(20)
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]


@router.post("/admin/students", response_model=UserOut, status_code=201, tags=["Administração"])
def create_student(data: UserInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        student = User(
            name=data.name, login=data.login.casefold(), password_hash=hasher.hash(data.password)
        )
        db.add(student)
        db.flush()
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_CREATED"},
            after={"name": student.name, "login": student.login},
        )
        return student


@router.get("/staff", response_model=list[StaffOut], tags=["Servidores institucionais"])
def staff(user=Depends(current_user)):
    with SessionFactory() as db:
        return [
            {"id": s.id, "name": s.name, "active": s.active}
            for s in db.scalars(
                select(InstitutionalStaff).order_by(InstitutionalStaff.name, InstitutionalStaff.id)
            )
        ]


@router.post("/admin/staff", status_code=201, tags=["Administração"])
def create_staff(data: StaffInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = InstitutionalStaff(**data.model_dump())
        db.add(s)
        db.flush()
        record(db, request, Event.ADMIN, s.id, {"action": "STAFF_CREATED"}, after=data.model_dump())
        return {"id": s.id, **data.model_dump()}


@router.put("/admin/staff/{staff_id}", tags=["Administração"])
def update_staff(staff_id: UUID, data: StaffInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = db.scalar(
            select(InstitutionalStaff).where(InstitutionalStaff.id == staff_id).with_for_update()
        )
        if not s:
            raise DomainError("STAFF_NOT_FOUND", "Servidor não encontrado.", 404)
        before = {"name": s.name, "active": s.active}
        s.name, s.active, s.updated_at = data.name, data.active, database_now(db)
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_UPDATED"},
            before=before,
            after=data.model_dump(),
        )
        return {"id": s.id, **data.model_dump()}


@router.get("/rounds", response_model=list[RoundOut], tags=["Rodadas"])
def rounds(user=Depends(current_user)):
    with SessionFactory() as db:
        stmt = select(AllocationRound).order_by(AllocationRound.created_at.desc()).limit(100)
        if user.role != "ADMIN":
            stmt = stmt.where(AllocationRound.status != "DRAFT")
        return round_views(db, list(db.scalars(stmt)))


@router.get("/rounds/{round_id}", response_model=RoundOut, tags=["Rodadas"])
def get_round(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        r = db.get(AllocationRound, round_id)
        if not r or (r.status == "DRAFT" and user.role != "ADMIN"):
            raise DomainError("ROUND_NOT_FOUND", "Rodada não encontrada.", 404)
        return round_view(db, r)


def set_round_staff(db, r, ids):
    found = list(
        db.scalars(
            select(InstitutionalStaff.id).where(
                InstitutionalStaff.id.in_(ids), InstitutionalStaff.active
            )
        )
    )
    if set(found) != set(ids):
        raise DomainError(
            "STAFF_NOT_ELIGIBLE", "Selecione apenas servidores ativos existentes.", 422
        )
    db.execute(delete(RoundStaff).where(RoundStaff.round_id == r.id))
    db.add_all([RoundStaff(round_id=r.id, staff_id=s, order=i) for i, s in enumerate(ids)])


@router.post("/admin/rounds", status_code=201, tags=["Administração"])
def create_round(data: RoundInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
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
        )
        db.flush()
        return round_view(db, r)


@router.put("/admin/rounds/{round_id}", tags=["Administração"])
def edit_round(round_id: UUID, data: RoundInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        r = locked_round(db, round_id)
        if r.status != "DRAFT":
            raise DomainError(
                "ROUND_FROZEN", "Os prazos e os servidores são fixados ao abrir a rodada."
            )
        before = {k: str(getattr(r, k)) for k in data.model_dump(exclude={"staff_ids"})}
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
        )
        db.flush()
        return round_view(db, r)


@router.post("/admin/rounds/{round_id}/transition", tags=["Administração"])
def transition(round_id: UUID, data: TransitionInput, request: Request, user=Depends(admin)):
    allowed = {
        "open": ("DRAFT", "OPEN"),
        "publish": ("PROCESSED", "PUBLISHED"),
        "archive": ("PUBLISHED", "ARCHIVED"),
    }
    with SessionFactory.begin() as db:
        r = locked_round(db, round_id)
        before, after = allowed[data.action]
        if r.status == after:
            return round_view(db, r)
        if r.status != before:
            raise DomainError(
                "INVALID_ROUND_TRANSITION", "Esta ação não é permitida no estado atual da rodada."
            )
        if data.action == "open" and database_now(db) >= r.preferences_close_at:
            raise DomainError("ROUND_EXPIRED", "Defina prazos futuros antes de abrir a rodada.")
        r.status = after
        db.flush()
        if data.action == "archive":
            db.execute(
                update(SextetMember)
                .where(
                    SextetMember.sextet_id.in_(select(Sextet.id).where(Sextet.round_id == round_id))
                )
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
        )
        return round_view(db, r)


@router.get("/rounds/{round_id}/my-sextet", response_model=SextetOut | None, tags=["Sextetos"])
def my_sextet(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        s = db.scalar(
            select(Sextet)
            .join(SextetMember)
            .where(Sextet.round_id == round_id, SextetMember.user_id == user.id)
        )
        return sextet_view(db, s) if s else None


@router.post(
    "/rounds/{round_id}/sextets", response_model=SextetOut, status_code=201, tags=["Sextetos"]
)
def confirm_sextet(round_id: UUID, data: SextetInput, request: Request, user=Depends(current_user)):
    independent(request, Event.SEXTET_ATTEMPT, round_id)
    with SessionFactory.begin() as db:
        s = register_sextet(db, request, round_id, user, data)
        return sextet_view(db, s)


@router.put("/sextets/{sextet_id}/preferences", response_model=PreferenceOut, tags=["Preferências"])
def preferences(
    sextet_id: UUID, data: PreferencesInput, request: Request, user=Depends(current_user)
):
    independent(request, Event.PREFERENCE_ATTEMPT, sextet_id)
    with SessionFactory.begin() as db:
        submission = save_preferences(db, request, sextet_id, user, data)
        return {"version": submission.version, "submitted_at": submission.submitted_at}


@router.get("/admin/rounds/{round_id}/sextets", tags=["Administração"])
def admin_sextets(round_id: UUID, user=Depends(admin)):
    with SessionFactory() as db:
        # Bounded institutional dataset; the admin list avoids fetching each composition/ranking.
        return [
            {
                "id": s.id,
                "name": s.name,
                "registration_completed_at": s.registration_completed_at,
                "priority_sequence": s.priority_sequence,
            }
            for s in db.scalars(
                select(Sextet)
                .where(Sextet.round_id == round_id)
                .order_by(Sextet.registration_completed_at, Sextet.priority_sequence)
                .limit(500)
            )
        ]


@router.get("/sextets/{sextet_id}", response_model=SextetOut, tags=["Sextetos"])
def get_sextet(sextet_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        return sextet_view(db, owned_sextet(db, sextet_id, user))


@router.post("/admin/rounds/{round_id}/allocate", tags=["Alocação"])
def process(round_id: UUID, request: Request, user=Depends(admin)):
    try:
        with SessionFactory.begin() as db:
            run = process_allocation(db, request, round_id, user)
            return {"id": run.id, "status": run.status, "input_fingerprint": run.input_fingerprint}
    except DomainError:
        raise
    except Exception:
        # Official changes rolled back. Persist a failed attempt separately, permitting a retry.
        with SessionFactory.begin() as db:
            if db.get(AllocationRound, round_id):
                run = AllocationRun(
                    round_id=round_id,
                    executed_by=user.id,
                    status="FAILED",
                    finished_at=database_now(db),
                )
                db.add(run)
                db.flush()
                record(db, request, Event.ALLOCATION_FAILED, run.id, {"round_id": str(round_id)})
        raise


@router.get("/rounds/{round_id}/results", tags=["Alocação"])
def results(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        r = db.get(AllocationRound, round_id)
        if not r:
            raise DomainError("ROUND_NOT_FOUND", "Rodada não encontrada.", 404)
        if user.role != "ADMIN" and r.status not in {"PUBLISHED", "ARCHIVED"}:
            return {"published": False, "allocations": []}
        stmt = (
            select(Allocation, Sextet.name, InstitutionalStaff.name)
            .select_from(Allocation)
            .join(Sextet, Allocation.sextet_id == Sextet.id)
            .outerjoin(InstitutionalStaff, Allocation.staff_id == InstitutionalStaff.id)
        )
        stmt = stmt.where(Allocation.round_id == round_id)
        if user.role != "ADMIN":
            stmt = stmt.where(
                Allocation.sextet_id.in_(
                    select(SextetMember.sextet_id).where(SextetMember.user_id == user.id)
                )
            )
        rows = db.execute(
            stmt.order_by(Sextet.registration_completed_at, Sextet.priority_sequence)
        ).all()
        return {
            "published": r.status in {"PUBLISHED", "ARCHIVED"},
            "allocations": [
                {
                    "id": a.id,
                    "sextet_id": a.sextet_id,
                    "sextet_name": name,
                    "staff_name": staff_name,
                    "staff_id": a.staff_id,
                    "run_id": a.run_id,
                    "status": a.status,
                    "kind": a.kind,
                    "preference_position": a.preference_position,
                    "trace": a.trace
                    if user.role == "ADMIN"
                    else {k: v for k, v in a.trace.items() if k != "unavailable"},
                }
                for a, name, staff_name in rows
            ],
        }


@router.get("/admin/runs/{run_id}", tags=["Auditoria"])
def run_detail(run_id: UUID, user=Depends(admin)):
    with SessionFactory() as db:
        run = db.get(AllocationRun, run_id)
        if not run:
            raise DomainError("RUN_NOT_FOUND", "Execução não encontrada.", 404)
        return {
            "id": run.id,
            "status": run.status,
            "algorithm_version": run.algorithm_version,
            "input_fingerprint": run.input_fingerprint,
            "snapshot": run.snapshot,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
        }


@router.get("/admin/audit", tags=["Auditoria"])
def audit_events(
    event: str | None = Query(None, max_length=80),
    entity: str | None = Query(None, max_length=80),
    actor: UUID | None = None,
    request_id: UUID | None = None,
    before_id: int | None = Query(None, gt=0),
    since: str | None = Query(None, max_length=40),
    until: str | None = Query(None, max_length=40),
    user=Depends(admin),
):
    from datetime import datetime

    stmt = select(AuditEvent, User.name).outerjoin(User, AuditEvent.actor_user_id == User.id)
    for column, value in [
        (AuditEvent.event_type, event),
        (AuditEvent.entity_id, entity),
        (AuditEvent.actor_user_id, actor),
        (AuditEvent.request_id, str(request_id) if request_id else None),
    ]:
        if value:
            stmt = stmt.where(column == value)
    try:
        if since:
            stmt = stmt.where(AuditEvent.occurred_at >= datetime.fromisoformat(since))
        if until:
            stmt = stmt.where(AuditEvent.occurred_at <= datetime.fromisoformat(until))
    except ValueError:
        raise DomainError("INVALID_DATE", "Informe datas válidas para a consulta.", 422) from None
    if before_id:
        stmt = stmt.where(AuditEvent.id < before_id)
    with SessionFactory() as db:
        rows = db.execute(stmt.order_by(AuditEvent.id.desc()).limit(51)).all()
        return {
            "next_cursor": rows[49][0].id if len(rows) > 50 else None,
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "occurred_at": e.occurred_at,
                    "actor_name": name,
                    "actor_user_id": e.actor_user_id,
                    "entity_id": e.entity_id,
                    "request_id": e.request_id,
                    "payload": e.payload,
                    "previous_state": e.previous_state,
                    "resulting_state": e.resulting_state,
                }
                for e, name in rows[:50]
            ],
        }
