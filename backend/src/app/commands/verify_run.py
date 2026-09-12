"""Read-only replay of an official execution for an institutional audit."""

import argparse
import hashlib
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.db.models import Allocation, AllocationRun
from app.db.session import SessionFactory
from app.domain.allocation import Candidate, allocate


def verify(db, run_id: UUID) -> int:
    run = db.get(AllocationRun, run_id)
    if run is None or run.status != "COMPLETED":
        raise ValueError("Informe uma execução concluída existente.")
    if run.algorithm_version != "serial-priority-v1":
        raise ValueError("Versão do algoritmo não suportada por este verificador.")
    snapshot = run.snapshot
    fingerprint = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if fingerprint != run.input_fingerprint or snapshot.get("round_id") != str(run.round_id):
        raise ValueError("O snapshot diverge da impressão digital ou da rodada registrada.")
    candidates = [
        Candidate(
            g["id"],
            datetime.fromisoformat(g["registered_at"]),
            g["sequence"],
            tuple(g["preferences"]),
        )
        for g in snapshot["groups"]
    ]
    expected = allocate(candidates, snapshot["staff_order"])
    persisted = {
        str(a.sextet_id): {
            "sextet_id": str(a.sextet_id),
            "staff_id": str(a.staff_id) if a.staff_id else None,
            "kind": a.kind,
            "status": a.status,
            "preference_position": a.preference_position,
            "trace": a.trace,
        }
        for a in db.scalars(select(Allocation).where(Allocation.run_id == run.id))
    }
    if persisted != {r["sextet_id"]: r for r in expected}:
        raise ValueError("As alocações persistidas divergem da reprodução do algoritmo.")
    return len(expected)


def main():
    parser = argparse.ArgumentParser(description="Reproduzir uma execução sem modificar o banco")
    parser.add_argument("run_id", type=UUID)
    args = parser.parse_args()
    try:
        with SessionFactory() as db:
            count = verify(db, args.run_id)
    except (ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Verificação recusada: {exc}\n")
    print(f"Execução verificada: fingerprint, {count} alocações e trilhas consistentes.")


if __name__ == "__main__":
    main()
