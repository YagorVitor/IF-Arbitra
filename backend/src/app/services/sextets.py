from sqlalchemy import func, select

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
            "NOT_SEXTET_LEADER", "O primeiro integrante deve ser o aluno autenticado.", 403
        )
    if len(set(data.members)) != len(data.members):
        raise DomainError("DUPLICATE_MEMBER", "Selecione alunos diferentes.", 422)
    if round_.formation_mode == "TRIOS" and len(data.members) != 3:
        raise DomainError(
            "INVALID_TRIO_COMPOSITION", "O trio deve ter exatamente três alunos.", 422
        )
    if round_.formation_mode == "GROUPS":
        if len(data.members) not in {6, 7}:
            raise DomainError(
                "INVALID_GROUP_COMPOSITION",
                "Informe seis integrantes obrigatórios, incluindo o capitão, e um sétimo opcional.",
                422,
            )
        count = db.scalar(
            select(func.count())
            .select_from(Sextet)
            .where(Sextet.round_id == round_id, Sextet.member_count == len(data.members))
        )
        limit = 3 if len(data.members) == 6 else 8
        if count >= limit:
            raise DomainError(
                "GROUP_SIZE_LIMIT_REACHED",
                f"Esta rodada já tem {limit} grupos com {len(data.members)} integrantes.",
                409,
            )
    elif round_.formation_mode == "SEXTET" and len(data.members) > 6:
        raise DomainError(
            "INVALID_SEXTET_COMPOSITION",
            "A composição desta rodada histórica admite até seis alunos.",
            422,
        )
    students = list(
        db.scalars(
            select(User)
            .where(
                User.id.in_(data.members),
                User.active,
                User.removed_at.is_(None),
                User.role == "STUDENT",
            )
            .order_by(User.id)
            .with_for_update()
        )
    )
    if len(students) != len(data.members):
        raise DomainError(
            "INVALID_SEXTET_COMPOSITION", "Todos os integrantes devem ser alunos ativos.", 422
        )
    sextet = Sextet(
        round_id=round_id,
        created_by=user.id,
        name=data.name,
        member_count=len(data.members),
        idempotency_key=data.idempotency_key,
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
            "member_count": len(data.members),
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
        raise DomainError("SEXTET_NOT_FOUND", "Grupo não encontrado.", 404)
    member = db.scalar(
        select(SextetMember).where(
            SextetMember.sextet_id == sextet.id, SextetMember.user_id == user.id
        )
    )
    if leader and sextet.created_by != user.id:
        raise DomainError(
            "NOT_SEXTET_LEADER", "Somente o capitão do grupo pode enviar preferências.", 403
        )
    if not leader and not member and user.role != "ADMIN":
        raise DomainError("SEXTET_NOT_FOUND", "Grupo não encontrado.", 404)
    return sextet
