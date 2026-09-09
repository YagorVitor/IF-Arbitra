import hashlib
import json
from uuid import UUID

from sqlalchemy import delete, select

from app.allocation import Candidate, allocate
from app.audit import Event, record
from app.db import database_now
from app.errors import DomainError
from app.models import (
    Allocation,
    AllocationRound,
    AllocationRun,
    InstitutionalStaff,
    PreferenceItem,
    PreferenceSubmission,
    RoundStaff,
    Sextet,
    SextetMember,
    User,
)


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


def register_sextet(db, request, round_id, user, data):
    round_ = locked_round(db, round_id)
    prior = db.scalar(
        select(Sextet).where(
            Sextet.created_by == user.id, Sextet.idempotency_key == data.idempotency_key
        )
    )
    if prior:
        members = list(
            db.scalars(
                select(SextetMember.user_id)
                .where(SextetMember.sextet_id == prior.id)
                .order_by(SextetMember.slot)
            )
        )
        if prior.round_id != round_id or members != data.members or prior.name != data.name:
            raise DomainError(
                "IDEMPOTENCY_CONFLICT", "Esta confirmação já foi usada com outros dados."
            )
        return prior
    assert_window(db, round_, "registration")
    if user.role != "STUDENT" or data.members[0] != user.id:
        raise DomainError(
            "NOT_SEXTET_LEADER", "O líder do Trio A deve ser o aluno autenticado.", 403
        )
    if len(set(data.members)) != 6:
        raise DomainError("DUPLICATE_MEMBER", "Selecione seis alunos diferentes.", 422)
    students = list(
        db.scalars(
            select(User).where(User.id.in_(data.members), User.active, User.role == "STUDENT")
        )
    )
    if len(students) != 6:
        raise DomainError(
            "INVALID_SEXTET_COMPOSITION", "Todos os seis integrantes devem ser alunos ativos.", 422
        )
    sextet = Sextet(
        round_id=round_id, created_by=user.id, name=data.name, idempotency_key=data.idempotency_key
    )
    db.add(sextet)
    db.flush()
    db.add_all(
        [
            SextetMember(sextet_id=sextet.id, slot=i, user_id=member)
            for i, member in enumerate(data.members)
        ]
    )
    db.flush()  # Partial unique index rejects overlapping memberships, even across different rounds.
    record(
        db,
        request,
        Event.SEXTET_CREATED,
        sextet.id,
        after={
            "members": [str(m) for m in data.members],
            "registration_completed_at": sextet.registration_completed_at.isoformat(),
            "priority_sequence": sextet.priority_sequence,
            "round_id": str(round_id),
        },
        entity_type="SEXTET",
    )
    return sextet


def owned_sextet(db, sextet_id, user, leader=False):
    sextet = db.get(Sextet, sextet_id)
    if not sextet:
        raise DomainError("SEXTET_NOT_FOUND", "Sexteto não encontrado.", 404)
    member = db.scalar(
        select(SextetMember).where(
            SextetMember.sextet_id == sextet.id, SextetMember.user_id == user.id
        )
    )
    if leader and sextet.created_by != user.id:
        raise DomainError(
            "NOT_SEXTET_LEADER", "Somente o líder do Trio A pode enviar preferências.", 403
        )
    if not leader and not member and user.role != "ADMIN":
        raise DomainError("SEXTET_NOT_FOUND", "Sexteto não encontrado.", 404)
    return sextet


def save_preferences(db, request, sextet_id, user, data):
    sextet = owned_sextet(db, sextet_id, user, leader=True)
    round_ = locked_round(db, sextet.round_id)
    now = assert_window(db, round_, "preferences")
    eligible = eligible_staff(db, round_.id)
    if len(data.staff_ids) != len(eligible) or set(data.staff_ids) != set(eligible):
        raise DomainError(
            "INVALID_PREFERENCE_RANKING",
            "A lista precisa conter todos os servidores elegíveis, uma única vez.",
            422,
        )
    submission = db.get(PreferenceSubmission, sextet_id)
    current = list(
        db.scalars(
            select(PreferenceItem.staff_id)
            .where(PreferenceItem.sextet_id == sextet_id)
            .order_by(PreferenceItem.position)
        )
    )
    version = submission.version if submission else 0
    # An exact retry of the last accepted version is safe; a stale different draft is rejected.
    if data.expected_version != version:
        if submission and data.expected_version == version - 1 and current == data.staff_ids:
            return submission
        raise DomainError(
            "PREFERENCE_VERSION_CONFLICT",
            "As preferências foram alteradas em outra aba. Recarregue antes de salvar.",
        )
    if not submission:
        submission = PreferenceSubmission(
            sextet_id=sextet_id, round_id=round_.id, version=1, submitted_at=now
        )
        db.add(submission)
    else:
        submission.version += 1
        submission.submitted_at = now
        db.execute(delete(PreferenceItem).where(PreferenceItem.sextet_id == sextet_id))
    db.flush()
    db.add_all(
        [
            PreferenceItem(sextet_id=sextet_id, round_id=round_.id, position=i, staff_id=s)
            for i, s in enumerate(data.staff_ids, 1)
        ]
    )
    record(
        db,
        request,
        Event.PREFERENCE_UPDATED if version else Event.PREFERENCE_SUBMITTED,
        sextet_id,
        before={"ranking": [str(s) for s in current], "version": version},
        after={"ranking": [str(s) for s in data.staff_ids], "version": submission.version},
        entity_type="SEXTET",
    )
    return submission


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
                "registered_at": c.registered_at.isoformat(),
                "sequence": c.sequence,
                "preferences": list(c.preferences),
            }
            for c in candidates
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
