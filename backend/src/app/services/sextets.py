from sqlalchemy import select

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    Sextet,
    SextetMember,
    User,
)
from app.services.rounds import assert_window, locked_round


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
            select(User)
            .where(User.id.in_(data.members), User.active, User.role == "STUDENT")
            .order_by(User.id)
            .with_for_update()
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
