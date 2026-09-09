from datetime import UTC, datetime, timedelta
from itertools import permutations

import pytest

from app.allocation import Candidate, allocate

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def c(id_, priority, preferences=()):
    return Candidate(id_, NOW, priority, tuple(preferences))


def test_required_example():
    groups = [c("1", 1, "ABC"), c("2", 2, "ACB"), c("3", 3, "BAC")]
    assert [r["staff_id"] for r in allocate(groups, list("ABC"))] == list("ACB")


def test_serial_priority_differs_from_parallel_first_choices():
    groups = [c("1", 1, "ABC"), c("2", 2, "ABC"), c("3", 3, "BAC")]
    result = allocate(groups, list("ABC"))
    assert [r["staff_id"] for r in result] == list("ABC")
    assert result[1]["trace"]["unavailable"] == [{"staff_id": "A", "sextet_id": "1"}]


def test_repechage_after_ranked_and_capacity():
    result = allocate(
        [c("no-ranking", 1), c("ranked", 2, "AB"), c("extra", 3), c("last", 4)], list("AB")
    )
    assert [r["sextet_id"] for r in result] == ["ranked", "no-ranking", "extra", "last"]
    assert [r["staff_id"] for r in result] == ["A", "B", None, None]
    assert result[2]["status"] == "UNALLOCATED"


def test_timestamp_precedes_tiebreaker():
    older = Candidate("older", NOW - timedelta(microseconds=1), 99, tuple("AB"))
    assert allocate([c("newer", 1, "BA"), older], list("AB"))[0]["sextet_id"] == "older"


def test_determinism_independent_input_order():
    groups = [c("1", 1, "ABC"), c("2", 2, "ABC"), c("3", 3)]
    expected = allocate(groups, list("ABC"))
    for ordering in permutations(groups):
        assert allocate(list(ordering), list("ABC")) == expected


@pytest.mark.parametrize("ranking", ["AA", "A", "ABD", "ABCA"])
def test_invalid_snapshot_rejected(ranking):
    with pytest.raises(ValueError):
        allocate([c("1", 1, ranking)], list("ABC"))
