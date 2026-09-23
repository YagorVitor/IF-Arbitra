"""Resolve repository assets for editable installs and the container layout."""

import os
from pathlib import Path


def backend_root() -> Path:
    configured = os.environ.get("IF_ARBITRA_BACKEND_DIR")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if not (candidate / "config/alembic.ini").is_file():
            raise RuntimeError("IF_ARBITRA_BACKEND_DIR não contém config/alembic.ini")
        return candidate
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "config/alembic.ini").is_file():
            return candidate
    raise RuntimeError("Configure IF_ARBITRA_BACKEND_DIR com a pasta de implantação do backend")
