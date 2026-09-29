from datetime import UTC, datetime, timedelta
from itertools import permutations

import pytest

from app.domain.allocation import Candidate, allocate_trios

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def trio(name, sequence, ranking="ABC"):
    return Candidate(name, NOW + timedelta(seconds=sequence), sequence, tuple(ranking))


def assignments(result):
    return {entry["sextet_id"]: entry for entry in result}


def test_first_two_trios_for_each_first_choice_form_a_sextet():
    candidates = [
        trio("a1", 1),
        trio("b1", 2, "BAC"),
        trio("a2", 3),
        trio("b2", 4, "BAC"),
        trio("a3", 5),
        trio("a4", 6),
    ]
    result = assignments(allocate_trios(candidates, list("ABC")))
    assert [
        (result[id_]["staff_id"], result[id_]["staff_slot"])
        for id_ in ("a1", "a2", "b1", "b2", "a3", "a4")
    ] == [("A", 1), ("A", 2), ("B", 1), ("B", 2), ("C", 1), ("C", 2)]
    assert result["a1"]["trace"]["paired_with"] == "a2"
    assert result["a3"]["preference_position"] == 3


def test_unmatched_first_choice_waits_for_second_preference():
    candidates = [trio("first", 1, "AB"), trio("second", 2, "BA")]
    result = assignments(allocate_trios(candidates, list("AB")))
    assert result["first"]["staff_id"] == result["second"]["staff_id"] == "A"
    assert result["second"]["preference_position"] == 2


def test_odd_trio_waits_for_administrator_instead_of_forming_partial_group():
    result = assignments(allocate_trios([trio("a", 1), trio("b", 2), trio("c", 3)], list("ABC")))
    assert result["c"]["status"] == "UNALLOCATED"
    assert result["c"]["trace"]["reason"] == "AWAITING_PAIR"
    assert result["c"]["staff_id"] is None


def test_ranked_trio_can_pair_with_unranked_trio_in_repechage():
    result = assignments(allocate_trios([trio("ranked", 1), trio("unranked", 2, "")], list("ABC")))
    assert result["ranked"]["staff_id"] == result["unranked"]["staff_id"] == "A"
    assert result["unranked"]["kind"] == "REPECHAGE"


def test_capacity_and_input_order_are_deterministic():
    candidates = [trio(str(i), i, "AB") for i in range(1, 6)]
    expected = allocate_trios(candidates, list("AB"))
    assert sum(item["status"] == "ALLOCATED" for item in expected) == 4
    assert expected[-1]["trace"]["reason"] == "CAPACITY_EXHAUSTED"
    for ordering in permutations(candidates):
        assert allocate_trios(list(ordering), list("AB")) == expected


@pytest.mark.parametrize("ranking", ["AA", "A", "ABD"])
def test_incomplete_or_duplicate_ranking_is_rejected(ranking):
    with pytest.raises(ValueError):
        allocate_trios([trio("a", 1, ranking)], list("AB"))
