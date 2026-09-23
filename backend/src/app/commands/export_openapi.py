"""Generate the frontend contract without opening a database connection."""

import argparse
import json
from pathlib import Path

from app.core.paths import backend_root
from app.main import app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, help="Destino opcional do arquivo OpenAPI")
    args = parser.parse_args()
    destination = args.output or backend_root().parent / "docs" / "openapi.json"
    content = json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            parser.exit(1, "Contrato desatualizado: execute app.commands.export_openapi.\n")
        print("Contrato OpenAPI atualizado.")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        print("docs/openapi.json gerado.")


if __name__ == "__main__":
    main()
