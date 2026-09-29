from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.schemas.allocation import AllocationRunDetailOut, AllocationRunSummaryOut, ResultsOut
from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    Allocation,
    AllocationRound,
    AllocationRun,
    InstitutionalStaff,
    Sextet,
    SextetMember,
    User,
)
from app.db.session import SessionFactory, database_now
from app.services.allocation import process_allocation

router = APIRouter()


@router.post(
    "/admin/rounds/{round_id}/allocate",
    response_model=AllocationRunSummaryOut,
    tags=["Alocação"],
)
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
                record(
                    db,
                    request,
                    Event.ALLOCATION_FAILED,
                    run.id,
                    {"round_id": str(round_id)},
                    entity_type="ALLOCATION_RUN",
                )
        raise


@router.get("/rounds/{round_id}/results", response_model=ResultsOut, tags=["Alocação"])
def results(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        r = db.get(AllocationRound, round_id)
        if not r or (r.status == "DRAFT" and user.role != "ADMIN"):
            raise DomainError("ROUND_NOT_FOUND", "Rodada não encontrada.", 404)
        if user.role != "ADMIN" and r.status not in {"PUBLISHED", "ARCHIVED"}:
            return {"published": False, "allocations": []}
        round_allocations = list(
            db.scalars(select(Allocation).where(Allocation.round_id == round_id))
        )
        by_staff = {}
        for allocation in round_allocations:
            if allocation.staff_id:
                by_staff.setdefault(allocation.staff_id, []).append(allocation)
        trio_ids = {a.sextet_id for a in round_allocations}
        trio_names = (
            dict(db.execute(select(Sextet.id, Sextet.name).where(Sextet.id.in_(trio_ids))).all())
            if trio_ids
            else {}
        )
        members_by_trio = {id_: [] for id_ in trio_ids}
        if trio_ids:
            for trio_id, slot, member_id, name in db.execute(
                select(SextetMember.sextet_id, SextetMember.slot, User.id, User.name)
                .join(User, SextetMember.user_id == User.id)
                .where(SextetMember.sextet_id.in_(trio_ids))
                .order_by(SextetMember.sextet_id, SextetMember.slot)
            ):
                members_by_trio[trio_id].append({"slot": slot, "id": member_id, "name": name})
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
                    "staff_slot": a.staff_slot,
                    "partner_trio": next(
                        (
                            {
                                "id": partner.sextet_id,
                                "name": trio_names[partner.sextet_id],
                                "members": members_by_trio[partner.sextet_id],
                            }
                            for partner in by_staff.get(a.staff_id, [])
                            if partner.sextet_id != a.sextet_id
                        ),
                        None,
                    )
                    if r.formation_mode == "TRIOS" and a.staff_id
                    else None,
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


@router.get("/admin/runs/{run_id}", response_model=AllocationRunDetailOut, tags=["Auditoria"])
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
