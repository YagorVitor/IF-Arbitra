from datetime import UTC, datetime

from app.domain.allocation import Candidate, allocate_groups


def test_every_first_choice_precedes_second_choice_with_temporal_ties():
    now = datetime.now(UTC)
    candidates = [
        Candidate("early", now, 1, ("A", "B", "C")),
        Candidate("same", now, 2, ("A", "B", "C")),
        Candidate("later", now, 3, ("B", "A", "C")),
    ]
    rows = {row["sextet_id"]: row for row in allocate_groups(candidates, ["A", "B", "C"])}
    assert rows["early"]["staff_id"] == "A"
    assert rows["later"]["staff_id"] == "B"
    assert rows["same"]["staff_id"] == "C"
    assert rows["same"]["preference_position"] == 3


def test_unranked_group_uses_remaining_server_and_overflow_is_pending():
    now = datetime.now(UTC)
    rows = allocate_groups(
        [Candidate(str(i), now, i, () if i > 1 else ("A", "B")) for i in range(1, 4)], ["A", "B"]
    )
    assert [r["staff_id"] for r in rows] == ["A", "B", None]
    assert rows[1]["kind"] == "REPECHAGE"
    assert rows[2]["trace"]["reason"] == "CAPACITY_EXHAUSTED"
