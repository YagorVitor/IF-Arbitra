"""Idempotently load the initial roster without undoing administrator changes."""

import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.dialects.postgresql import insert

from app.db.models import InstitutionalStaff, User
from app.db.session import SessionFactory


def load_roster() -> dict:
    path = os.environ.get("IF_ARBITRA_ROSTER_PATH")
    raw = os.environ.get("IF_ARBITRA_ROSTER_JSON")
    if bool(path) == bool(raw):
        raise RuntimeError(
            "Configure exatamente uma fonte: IF_ARBITRA_ROSTER_PATH ou IF_ARBITRA_ROSTER_JSON"
        )
    roster = json.loads(Path(path).read_text(encoding="utf-8") if path else raw)
    if (
        not isinstance(roster, dict)
        or not isinstance(roster.get("staff"), list)
        or not isinstance(roster.get("students"), list)
    ):
        raise ValueError("Cadastro inicial inválido")
    return roster


def seed(roster: dict | None = None):
    roster = roster if roster is not None else load_roster()
    with SessionFactory.begin() as db:
        for row in roster["staff"]:
            statement = insert(InstitutionalStaff).values(
                id=UUID(row["id"]), name=row["name"], email=row["email"], active=True
            )
            db.execute(
                statement.on_conflict_do_update(
                    index_elements=["id"],
                    set_={"email": statement.excluded.email},
                    where=InstitutionalStaff.email.is_(None),
                )
            )
        for row in roster["students"]:
            name, email = row["name"], row["email"]
            db.execute(
                insert(User)
                .values(
                    id=uuid5(NAMESPACE_URL, f"if-arbitra:student:{email}"),
                    name=name,
                    login=email,
                    email=email,
                    role="STUDENT",
                    password_hash=None,
                    active=False,
                )
                .on_conflict_do_nothing(index_elements=["email"])
            )


if __name__ == "__main__":
    roster = load_roster()
    seed(roster)
    print(
        f"Seed concluído: {len(roster['students'])} alunos e {len(roster['staff'])} servidores iniciais."
    )
