"""One release step: migrate, seed, and apply least-privilege runtime grants."""

import os

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.db import engine
from app.seed import seed


def main():
    role = os.environ["RUNTIME_DATABASE_ROLE"]
    with engine.connect() as db:
        owner = db.scalar(text("SELECT current_user"))
        privileged = db.scalar(
            text(
                "SELECT rolsuper OR rolcreaterole OR rolcreatedb FROM pg_roles WHERE rolname=:role"
            ),
            {"role": role},
        )
        if owner == role or privileged is None or privileged:
            raise RuntimeError(
                "Runtime role must exist, differ from schema owner, and have no administrative privileges"
            )
    command.upgrade(Config("alembic.ini"), "head")
    seed()
    quoted = engine.dialect.identifier_preparer.quote(role)
    with engine.begin() as db:
        for sql in [
            f"GRANT USAGE ON SCHEMA public TO {quoted}",
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {quoted}",
            f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {quoted}",
            f"REVOKE UPDATE, DELETE, TRUNCATE ON audit_events, sextets, allocations FROM {quoted}",
            f"REVOKE INSERT, UPDATE, DELETE ON alembic_version FROM {quoted}",
            f"REVOKE TRUNCATE ON ALL TABLES IN SCHEMA public FROM {quoted}",
            f"REVOKE CREATE ON SCHEMA public FROM {quoted}",
        ]:
            db.execute(text(sql))


if __name__ == "__main__":
    main()
