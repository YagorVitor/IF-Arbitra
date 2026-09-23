from alembic.script import ScriptDirectory
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.migrations import migration_config
from app.db.session import engine

router = APIRouter()


@router.get("/health", tags=["Operação"])
def health():
    return {"status": "alive"}


@router.get("/ready", tags=["Operação"])
def ready():
    try:
        config = migration_config()
        expected = set(ScriptDirectory.from_config(config).get_heads())
        with engine.connect() as conn:
            versions = set(conn.scalars(text("SELECT version_num FROM alembic_version")))
        if not expected or versions != expected:
            return JSONResponse({"status": "not_ready"}, status_code=503)
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
