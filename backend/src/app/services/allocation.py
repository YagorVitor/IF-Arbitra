import hashlib
import json
from uuid import UUID

from sqlalchemy import select

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    Allocation,
    AllocationRun,
    InstitutionalStaff,
    PreferenceItem,
    Sextet,
)
from app.db.session import database_now
from app.domain.allocation import Candidate, allocate
from app.services.rounds import eligible_staff, locked_round


def process_allocation(db, request, round_id, user):
    round_ = locked_round(db, round_id)
    previous = db.scalar(
        select(AllocationRun).where(
            AllocationRun.round_id == round_id, AllocationRun.status == "COMPLETED"
        )
    )
    if previous:
        return previous
    if round_.status != "OPEN" or database_now(db) < round_.preferences_close_at:
        raise DomainError(
            "ALLOCATION_NOT_READY", "A alocação só pode ser executada após o prazo de preferências."
        )
    groups = list(
        db.scalars(
            select(Sextet)
            .where(Sextet.round_id == round_id)
            .order_by(Sextet.registration_completed_at, Sextet.priority_sequence)
        )
    )
    staff = eligible_staff(db, round_id)
    items = db.execute(
        select(PreferenceItem.sextet_id, PreferenceItem.staff_id)
        .where(PreferenceItem.round_id == round_id)
        .order_by(PreferenceItem.sextet_id, PreferenceItem.position)
    ).all()
    rankings = {}
    for g, s in items:
        rankings.setdefault(g, []).append(str(s))
    candidates = [
        Candidate(
            str(g.id),
            g.registration_completed_at,
            g.priority_sequence,
            tuple(rankings.get(g.id, [])),
        )
        for g in groups
    ]
    names = {
        str(s.id): s.name
        for s in db.scalars(select(InstitutionalStaff).where(InstitutionalStaff.id.in_(staff)))
    }
    snapshot = {
        "round_id": str(round_id),
        "staff_order": [str(s) for s in staff],
        "staff_names": names,
        "groups": [
            {
                "id": c.id,
                "member_count": g.member_count,
                "registered_at": c.registered_at.isoformat(),
                "sequence": c.sequence,
                "preferences": list(c.preferences),
            }
            for c, g in zip(candidates, groups, strict=True)
        ],
    }
    run = AllocationRun(
        round_id=round_id,
        status="PROCESSING",
        executed_by=user.id,
        snapshot=snapshot,
        input_fingerprint=hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    )
    db.add(run)
    db.flush()
    record(
        db,
        request,
        Event.ALLOCATION_STARTED,
        run.id,
        {"fingerprint": run.input_fingerprint},
        entity_type="ALLOCATION_RUN",
    )
    for result in allocate(candidates, [str(s) for s in staff]):
        db.add(
            Allocation(
                run_id=run.id,
                round_id=round_id,
                sextet_id=UUID(result["sextet_id"]),
                staff_id=UUID(result["staff_id"]) if result["staff_id"] else None,
                kind=result["kind"],
                status=result["status"],
                preference_position=result["preference_position"],
                trace=result["trace"],
            )
        )
        record(
            db,
            request,
            Event.GROUP_PROCESSED,
            result["sextet_id"],
            payload={"run_id": str(run.id), **result},
            entity_type="SEXTET",
        )
    run.status, run.finished_at = "COMPLETED", database_now(db)
    round_.status = "PROCESSED"
    record(
        db,
        request,
        Event.ALLOCATION_FINISHED,
        run.id,
        {"round_id": str(round_id), "groups": len(groups)},
        entity_type="ALLOCATION_RUN",
    )
    return run
