from collections import Counter

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
from app.services.adjustments import effective_allocations


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
    sizes = Counter()
    for rid, size, count in db.execute(
        select(Sextet.round_id, Sextet.member_count, func.count())
        .where(Sextet.round_id.in_(ids))
        .group_by(Sextet.round_id, Sextet.member_count)
    ):
        sizes[(rid, size)] = count
    submissions = dict(
        db.execute(
            select(PreferenceSubmission.round_id, func.count())
            .where(PreferenceSubmission.round_id.in_(ids))
            .group_by(PreferenceSubmission.round_id)
        ).all()
    )
    pending = Counter(
        a.round_id for a in effective_allocations(db, ids) if a.status == "UNALLOCATED"
    )
    now = database_now(db)
    return [
        _round_data(
            r,
            staff_by_round[r.id],
            counts.get(r.id, 0),
            submissions.get(r.id, 0),
            pending.get(r.id, 0),
            now,
            sum(sizes[(r.id, size)] for size in (5, 6)),
            sizes[(r.id, 7)],
        )
        for r in rounds
    ]


def round_view(db, r):
    return round_views(db, [r])[0]


def _round_data(r, staff, count, preferences, pending, now, six, seven):
    return {
        "id": r.id,
        "name": r.name,
        "status": r.status,
        "formation_mode": r.formation_mode,
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
        "capacity": len(staff) * (2 if r.formation_mode == "TRIOS" else 1),
        "shortfall": max(0, count - len(staff) * (2 if r.formation_mode == "TRIOS" else 1)),
        "pending": pending,
        "registered_six": six,
        "registered_seven": seven,
        "limit_six": 3 if r.formation_mode == "GROUPS" else None,
        "limit_seven": 8 if r.formation_mode == "GROUPS" else None,
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
