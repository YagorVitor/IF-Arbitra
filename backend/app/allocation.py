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
