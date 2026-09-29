from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.schemas.rounds import RoundInput


def round_payload():
    now = datetime.now(UTC)
    return {
        "name": "Rodada de trios",
        "registration_opens_at": now,
        "registration_closes_at": now + timedelta(hours=1),
        "preferences_open_at": now,
        "preferences_close_at": now + timedelta(hours=2),
        "staff_ids": [uuid4()],
    }


def test_new_rounds_use_trios_by_default():
    assert RoundInput(**round_payload()).formation_mode == "TRIOS"


def test_removed_formation_mode_cannot_be_submitted():
    with pytest.raises(ValidationError) as rejected:
        RoundInput(**round_payload(), formation_mode="SEXTET")
    assert rejected.value.errors()[0]["loc"] == ("formation_mode",)
