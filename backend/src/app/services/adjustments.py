from collections import Counter
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import select

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import Allocation, AllocationAdjustment, Sextet
from app.services.rounds import eligible_staff, locked_round


def latest_adjustments(db, round_ids):
    return {
        row.round_id: row
        for row in db.scalars(
            select(AllocationAdjustment)
            .where(AllocationAdjustment.round_id.in_(round_ids))
            .order_by(AllocationAdjustment.round_id, AllocationAdjustment.revision.desc())
            .distinct(AllocationAdjustment.round_id)
        )
    }


def effective_allocations(db, round_ids, adjustments=None):
    adjustments = latest_adjustments(db, round_ids) if adjustments is None else adjustments
    rows = []
    for allocation in db.scalars(select(Allocation).where(Allocation.round_id.in_(round_ids))):
        values = {
            column.name: getattr(allocation, column.name) for column in Allocation.__table__.columns
        }
        values["manually_adjusted"] = False
        adjustment = adjustments.get(allocation.round_id)
        if adjustment:
            assignment = adjustment.assignments[str(allocation.id)]
            staff_id = UUID(assignment["staff_id"]) if assignment["staff_id"] else None
            changed = staff_id != allocation.staff_id
            ranking = allocation.trace.get("ranking", [])
            values.update(
                staff_id=staff_id,
                staff_slot=assignment["staff_slot"],
                status="ALLOCATED" if staff_id else "UNALLOCATED",
                preference_position=ranking.index(str(staff_id)) + 1
                if str(staff_id) in ranking
                else None,
                manually_adjusted=changed,
                trace={
                    **allocation.trace,
                    "chosen": str(staff_id) if staff_id else None,
                    "reason": "ADMIN_ADJUSTED" if changed else allocation.trace["reason"],
                },
            )
        rows.append(SimpleNamespace(**values))
    # Pairing reflects the current assignment, including administrative singletons.
    by_staff = {}
    for row in rows:
        if row.staff_id:
            by_staff.setdefault((row.round_id, row.staff_id), []).append(row)
    for row in rows:
        partners = [
            other for other in by_staff.get((row.round_id, row.staff_id), []) if other.id != row.id
        ]
        row.trace = {**row.trace, "paired_with": str(partners[0].sextet_id) if partners else None}
    return rows


def adjust_allocation(db, request, round_id, data, user):
    round_ = locked_round(db, round_id)
    if round_.status not in {"PROCESSED", "PUBLISHED"}:
        raise DomainError(
            "ADJUSTMENT_NOT_ALLOWED", "Ajuste uma rodada processada ou publicada.", 409
        )
    latest = latest_adjustments(db, [round_id]).get(round_id)
    revision = latest.revision if latest else 0
    if data.expected_revision != revision:
        raise DomainError(
            "ADJUSTMENT_CONFLICT",
            "Outra pessoa ajustou esta rodada. Recarregue os resultados.",
            409,
        )
    allocations = effective_allocations(db, [round_id])
    ids = {a.id for a in allocations}
    assignments = {item.allocation_id: item.staff_id for item in data.assignments}
    if len(assignments) != len(data.assignments) or set(assignments) != ids or not ids:
        raise DomainError(
            "INVALID_ASSIGNMENTS", "Informe cada trio desta rodada uma única vez.", 422
        )
    eligible = set(eligible_staff(db, round_id))
    if any(staff_id and staff_id not in eligible for staff_id in assignments.values()):
        raise DomainError("STAFF_NOT_ELIGIBLE", "Selecione um servidor elegível desta rodada.", 422)
    capacity = 2 if round_.formation_mode == "TRIOS" else 1
    if any(count > capacity for count in Counter(s for s in assignments.values() if s).values()):
        raise DomainError(
            "STAFF_CAPACITY_EXCEEDED",
            f"O servidor admite no máximo {capacity} grupo(s) nesta rodada.",
            409,
        )
    if all(assignments[a.id] == a.staff_id for a in allocations):
        raise DomainError("NO_ADJUSTMENT", "Altere pelo menos uma atribuição antes de salvar.", 422)
    priority = list(
        db.scalars(
            select(Sextet.id)
            .where(Sextet.round_id == round_id)
            .order_by(Sextet.registration_completed_at, Sextet.priority_sequence)
        )
    )
    positions = {id_: position for position, id_ in enumerate(priority)}
    used = Counter()
    snapshot = {}
    for allocation in sorted(allocations, key=lambda a: positions[a.sextet_id]):
        staff_id = assignments[allocation.id]
        if staff_id:
            used[staff_id] += 1
        snapshot[str(allocation.id)] = {
            "staff_id": str(staff_id) if staff_id else None,
            "staff_slot": used[staff_id] if staff_id else 1,
        }
    adjustment = AllocationAdjustment(
        round_id=round_id,
        revision=revision + 1,
        assignments=snapshot,
        reason=data.reason,
        executed_by=user.id,
    )
    db.add(adjustment)
    db.flush()
    record(
        db,
        request,
        Event.ADMIN,
        adjustment.id,
        {"action": "ALLOCATION_ADJUSTED", "round_id": str(round_id), "reason": data.reason},
        before={str(a.id): str(a.staff_id) if a.staff_id else None for a in allocations},
        after=snapshot,
        entity_type="ALLOCATION_ADJUSTMENT",
    )
    return {"revision": adjustment.revision}
