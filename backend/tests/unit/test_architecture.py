"""Keep dependency direction explicit as the backend grows."""

import ast

import pytest

from app.core.paths import backend_root


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [
        ("domain", ("fastapi", "sqlalchemy", "app.api", "app.db", "app.services", "app.core")),
        ("services", ("fastapi", "app.api")),
        ("core", ("app.api", "app.services")),
        ("db", ("app.api", "app.services")),
    ],
)
def test_dependency_direction(layer, forbidden):
    violations = []
    for path in (backend_root() / "src/app" / layer).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            modules = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            for module in modules:
                if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden):
                    violations.append(f"{path.name}:{node.lineno}: {module}")
    assert not violations, violations


def test_migration_assets_are_independent_of_working_directory(tmp_path, monkeypatch):
    from alembic.script import ScriptDirectory

    from app.db.migrations import migration_config

    monkeypatch.chdir(tmp_path)
    assert ScriptDirectory.from_config(migration_config()).get_current_head() == "0004_run_history"


def test_explicit_backend_directory_is_validated(tmp_path, monkeypatch):
    monkeypatch.setenv("IF_ARBITRA_BACKEND_DIR", str(tmp_path))
    with pytest.raises(RuntimeError, match="config/alembic.ini"):
        backend_root()
