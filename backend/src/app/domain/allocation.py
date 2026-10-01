from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candidate:
    id: str
    registered_at: datetime
    sequence: int
    preferences: tuple[str, ...]


def allocate(candidates: list[Candidate], staff_order: list[str]) -> list[dict]:
    """Serial priority. Repechage uses the frozen round order, never name or set iteration."""
    if len(set(staff_order)) != len(staff_order):
        raise ValueError("Duplicate eligible staff")
    eligible = set(staff_order)
    if len({c.id for c in candidates}) != len(candidates):
        raise ValueError("Candidate IDs must be unique")
    priority = sorted(candidates, key=lambda c: (c.registered_at, c.sequence))
    if len({c.sequence for c in candidates}) != len(candidates):
        raise ValueError("Priority sequence must be unique")
    for c in candidates:
        if c.preferences and (
            set(c.preferences) != eligible or len(c.preferences) != len(eligible)
        ):
            raise ValueError("Incomplete preference snapshot")
    main = [c for c in priority if c.preferences]
    repechage = [c for c in priority if not c.preferences]
    used: dict[str, str] = {}
    result = []
    for order, c in enumerate(main + repechage, 1):
        ranking = list(c.preferences) if c.preferences else staff_order
        chosen = next((s for s in ranking if s not in used), None)
        unavailable = [
            {"staff_id": s, "sextet_id": used[s]}
            for s in ranking[: ranking.index(chosen) if chosen else len(ranking)]
            if s in used
        ]
        result.append(
            {
                "sextet_id": c.id,
                "staff_id": chosen,
                "kind": "MAIN" if c.preferences else "REPECHAGE",
                "status": "ALLOCATED" if chosen else "UNALLOCATED",
                "preference_position": ranking.index(chosen) + 1
                if chosen and c.preferences
                else None,
                "trace": {
                    "processing_order": order,
                    "registration_completed_at": c.registered_at.isoformat(),
                    "priority_sequence": c.sequence,
                    "ranking": list(c.preferences),
                    "fallback_order": staff_order if not c.preferences else [],
                    "unavailable": unavailable,
                    "chosen": chosen,
                    "reason": "FIRST_AVAILABLE" if chosen else "CAPACITY_EXHAUSTED",
                },
            }
        )
        if chosen:
            used[chosen] = c.id
    return result


def allocate_trios(candidates: list[Candidate], staff_order: list[str]) -> list[dict]:
    """Pair trios by preference pass, then registration time, with one pair per staff."""
    if len(set(staff_order)) != len(staff_order):
        raise ValueError("Duplicate eligible staff")
    if len({c.id for c in candidates}) != len(candidates):
        raise ValueError("Candidate IDs must be unique")
    if len({c.sequence for c in candidates}) != len(candidates):
        raise ValueError("Priority sequence must be unique")
    eligible = set(staff_order)
    for candidate in candidates:
        if candidate.preferences and (
            len(candidate.preferences) != len(staff_order) or set(candidate.preferences) != eligible
        ):
            raise ValueError("Incomplete preference snapshot")

    priority = sorted(candidates, key=lambda c: (c.registered_at, c.sequence))
    remaining = {c.id: c for c in priority}
    available = set(staff_order)
    pairs: list[tuple[str, Candidate, Candidate, int | None]] = []

    # At each preference position, fill complete sextets only. A trio that did
    # not find a partner stays in the pool for its next preference.
    for preference_pass in range(len(staff_order)):
        while True:
            proposals = []
            for staff_index, staff_id in enumerate(staff_order):
                if staff_id not in available:
                    continue
                interested = sorted(
                    (
                        c
                        for c in remaining.values()
                        if c.preferences and c.preferences.index(staff_id) <= preference_pass
                    ),
                    key=lambda c: (c.preferences.index(staff_id), c.registered_at, c.sequence),
                )
                if len(interested) < 2:
                    continue
                first, second = interested[:2]
                proposals.append(
                    (
                        max(first.preferences.index(staff_id), second.preferences.index(staff_id)),
                        first.registered_at,
                        first.sequence,
                        second.registered_at,
                        second.sequence,
                        staff_index,
                        staff_id,
                        first,
                        second,
                    )
                )
            if not proposals:
                break
            *_, staff_id, first, second = min(proposals)
            pairs.append((staff_id, first, second, preference_pass + 1))
            available.remove(staff_id)
            del remaining[first.id]
            del remaining[second.id]

    # Ranked trios take precedence over trios without a submitted list. A
    # complete pair in repescagem uses the first still available preference.
    fallback = sorted(
        remaining.values(),
        key=lambda c: (not bool(c.preferences), c.registered_at, c.sequence),
    )
    while len(fallback) >= 2 and available:
        first, second = fallback[:2]
        ranking = first.preferences or second.preferences or tuple(staff_order)
        staff_id = next(staff for staff in ranking if staff in available)
        pairs.append((staff_id, first, second, None))
        available.remove(staff_id)
        del remaining[first.id]
        del remaining[second.id]
        fallback = fallback[2:]

    result = []
    for staff_id, first, second, preference_pass in pairs:
        for slot, (candidate, partner) in enumerate(((first, second), (second, first)), 1):
            result.append(
                {
                    "sextet_id": candidate.id,
                    "staff_id": staff_id,
                    "staff_slot": slot,
                    "kind": "MAIN" if candidate.preferences else "REPECHAGE",
                    "status": "ALLOCATED",
                    "preference_position": candidate.preferences.index(staff_id) + 1
                    if candidate.preferences
                    else None,
                    "trace": {
                        "processing_order": len(result) + 1,
                        "registration_completed_at": candidate.registered_at.isoformat(),
                        "priority_sequence": candidate.sequence,
                        "ranking": list(candidate.preferences),
                        "fallback_order": staff_order if not candidate.preferences else [],
                        "unavailable": [],
                        "chosen": staff_id,
                        "reason": "PREFERENCE_PAIR" if preference_pass else "FALLBACK_PAIR",
                        "preference_pass": preference_pass,
                        "paired_with": partner.id,
                    },
                }
            )
    for candidate in priority:
        if candidate.id not in remaining:
            continue
        result.append(
            {
                "sextet_id": candidate.id,
                "staff_id": None,
                "staff_slot": 1,
                "kind": "MAIN" if candidate.preferences else "REPECHAGE",
                "status": "UNALLOCATED",
                "preference_position": None,
                "trace": {
                    "processing_order": len(result) + 1,
                    "registration_completed_at": candidate.registered_at.isoformat(),
                    "priority_sequence": candidate.sequence,
                    "ranking": list(candidate.preferences),
                    "fallback_order": staff_order if not candidate.preferences else [],
                    "unavailable": [],
                    "chosen": None,
                    "reason": "AWAITING_PAIR" if available else "CAPACITY_EXHAUSTED",
                    "preference_pass": None,
                    "paired_with": None,
                },
            }
        )
    return result


def allocate_groups(candidates: list[Candidate], staff_order: list[str]) -> list[dict]:
    """One group per server: all first choices, then second choices, temporal ties."""
    allocate(candidates, staff_order)  # Validate the complete frozen input.
    priority = sorted(candidates, key=lambda c: (c.registered_at, c.sequence))
    chosen = {}
    used = {}
    ordered = []
    for position in range(len(staff_order)):
        for candidate in priority:
            if candidate.id in chosen or not candidate.preferences:
                continue
            staff_id = candidate.preferences[position]
            if staff_id not in used:
                chosen[candidate.id] = (staff_id, position + 1)
                used[staff_id] = candidate.id
                ordered.append(candidate)
    for candidate in priority:
        if candidate.preferences or candidate.id in chosen:
            continue
        staff_id = next((s for s in staff_order if s not in used), None)
        if staff_id:
            chosen[candidate.id] = (staff_id, None)
            used[staff_id] = candidate.id
            ordered.append(candidate)
    ordered.extend(c for c in priority if c.id not in chosen)
    return [
        {
            "sextet_id": c.id,
            "staff_id": chosen.get(c.id, (None, None))[0],
            "staff_slot": 1,
            "kind": "MAIN" if c.preferences else "REPECHAGE",
            "status": "ALLOCATED" if c.id in chosen else "UNALLOCATED",
            "preference_position": chosen.get(c.id, (None, None))[1],
            "trace": {
                "processing_order": i,
                "registration_completed_at": c.registered_at.isoformat(),
                "priority_sequence": c.sequence,
                "ranking": list(c.preferences),
                "fallback_order": staff_order if not c.preferences else [],
                "unavailable": [],
                "chosen": chosen.get(c.id, (None, None))[0],
                "reason": "PREFERENCE_PASS"
                if c.id in chosen and c.preferences
                else "FALLBACK"
                if c.id in chosen
                else "CAPACITY_EXHAUSTED",
            },
        }
        for i, c in enumerate(ordered, 1)
    ]
