from sqlalchemy import delete, select

from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    PreferenceItem,
    PreferenceSubmission,
)
from app.services.rounds import assert_window, eligible_staff, locked_round
from app.services.sextets import owned_sextet


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
