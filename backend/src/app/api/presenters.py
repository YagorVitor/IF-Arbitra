from sqlalchemy import func, select

from app.db.models import (
    InstitutionalStaff,
    PreferenceItem,
    PreferenceSubmission,
    RoundStaff,
    Sextet,
    SextetMember,
    User,
)
from app.db.session import database_now


def round_views(db, rounds):
    ids = [r.id for r in rounds]
    staff_by_round = {id_: [] for id_ in ids}
    for staff, association in db.execute(
        select(InstitutionalStaff, RoundStaff)
        .join(RoundStaff)
        .where(RoundStaff.round_id.in_(ids))
        .order_by(RoundStaff.order)
    ):
        staff_by_round[association.round_id].append((staff, association.order))
    counts = dict(
        db.execute(
            select(Sextet.round_id, func.count())
            .where(Sextet.round_id.in_(ids))
            .group_by(Sextet.round_id)
        ).all()
    )
    submissions = dict(
        db.execute(
            select(PreferenceSubmission.round_id, func.count())
            .where(PreferenceSubmission.round_id.in_(ids))
            .group_by(PreferenceSubmission.round_id)
        ).all()
    )
    now = database_now(db)
    return [
        _round_data(r, staff_by_round[r.id], counts.get(r.id, 0), submissions.get(r.id, 0), now)
        for r in rounds
    ]


def round_view(db, r):
    return round_views(db, [r])[0]


def _round_data(r, staff, count, preferences, now):
    return {
        "id": r.id,
        "name": r.name,
        "status": r.status,
        **{
            k: getattr(r, k)
            for k in [
                "registration_opens_at",
                "registration_closes_at",
                "preferences_open_at",
                "preferences_close_at",
            ]
        },
        "server_now": now,
        "registration_open": r.status == "OPEN"
        and r.registration_opens_at <= now < r.registration_closes_at,
        "preferences_open": r.status == "OPEN"
        and r.preferences_open_at <= now < r.preferences_close_at,
        "can_process": r.status == "OPEN" and now >= r.preferences_close_at,
        "staff": [{"id": s.id, "name": s.name, "order": order} for s, order in staff],
        "registered": count,
        "with_preferences": preferences,
        "repechage": count - preferences,
        "capacity": len(staff),
        "shortfall": max(0, count - len(staff)),
    }


def sextet_view(db, sextet):
    members = db.execute(
        select(SextetMember.slot, User.id, User.name)
        .join(User)
        .where(SextetMember.sextet_id == sextet.id)
        .order_by(SextetMember.slot)
    ).all()
    submission = db.get(PreferenceSubmission, sextet.id)
    ranking = list(
        db.scalars(
            select(PreferenceItem.staff_id)
            .where(PreferenceItem.sextet_id == sextet.id)
            .order_by(PreferenceItem.position)
        )
    )
    return {
        "id": sextet.id,
        "name": sextet.name,
        "member_count": sextet.member_count,
        "round_id": sextet.round_id,
        "leader_id": sextet.created_by,
        "registration_completed_at": sextet.registration_completed_at,
        "priority_sequence": sextet.priority_sequence,
        "members": [{"slot": slot, "id": id_, "name": name} for slot, id_, name in members],
        "preferences": ranking,
        "preference_version": submission.version if submission else 0,
        "preferences_submitted_at": submission.submitted_at if submission else None,
    }
