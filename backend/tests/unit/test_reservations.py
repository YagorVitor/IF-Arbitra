from datetime import UTC, datetime

import pytest

from app.domain.allocation import Candidate, allocate_groups


def test_reservation_precedes_first_choices_without_changing_rankings():
    now = datetime.now(UTC)
    candidates = [
        Candidate("early", now, 1, ("A", "B", "C")),
        Candidate("reserved", now, 3, ("C", "B", "A")),
        Candidate("second", now, 2, ("A", "B", "C")),
    ]
    result = {
        row["sextet_id"]: row
        for row in allocate_groups(candidates, ["A", "B", "C"], {"reserved": "A"})
    }
    assert result["reserved"]["staff_id"] == "A"
    assert result["reserved"]["trace"]["reason"] == "ADMIN_RESERVED"
    assert result["reserved"]["preference_position"] is None
    assert result["reserved"]["trace"]["ranking"] == ["C", "B", "A"]
    assert result["early"]["staff_id"] == "B"
    assert result["second"]["staff_id"] == "C"


def test_reserved_group_without_preferences_is_allocated():
    result = allocate_groups([Candidate("group", datetime.now(UTC), 1, ())], ["A"], {"group": "A"})
    assert result[0]["status"] == "ALLOCATED"
    assert result[0]["trace"]["reason"] == "ADMIN_RESERVED"


@pytest.mark.parametrize(
    "reservations", [{"missing": "A"}, {"one": "missing"}, {"one": "A", "two": "A"}]
)
def test_invalid_reservations_rejected(reservations):
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        allocate_groups(
            [Candidate("one", now, 1, ()), Candidate("two", now, 2, ())], ["A", "B"], reservations
        )
