"""One configuration source shared by deploy, readiness and integration tests."""

from alembic.config import Config

from app.core.paths import backend_root


def migration_config() -> Config:
    return Config(str(backend_root() / "config/alembic.ini"))
