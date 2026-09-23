"""Stable seed IDs are explicitly assigned once; names can subsequently be corrected."""

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.db import SessionFactory
from app.models import InstitutionalStaff

STAFF = [
    ("b3601f91-e41f-46d8-bc43-000000000001", "Anderson Aparecido Lima da Silva"),
    ("b3601f91-e41f-46d8-bc43-000000000002", "Carolina Valério Barra Rocha"),
    ("b3601f91-e41f-46d8-bc43-000000000003", "Denise Elaine Emidio"),
    ("b3601f91-e41f-46d8-bc43-000000000004", "Dione Cabral"),
    ("b3601f91-e41f-46d8-bc43-000000000005", "Jorge Henrique de Oliveira Silva"),
    ("b3601f91-e41f-46d8-bc43-000000000006", "Junior Fernandes Marques"),
    ("b3601f91-e41f-46d8-bc43-000000000007", "Jurandyr Carneiro Nobre de Lacerda Neto"),
    ("b3601f91-e41f-46d8-bc43-000000000008", "Marta Kawamura Gonçalves"),
    ("b3601f91-e41f-46d8-bc43-000000000009", "Mauro de Lucca"),
    ("b3601f91-e41f-46d8-bc43-00000000000a", "Natalia Maria Casagrande"),
    ("b3601f91-e41f-46d8-bc43-00000000000b", "Raphael Carlini Zambon"),
    ("b3601f91-e41f-46d8-bc43-00000000000c", "Renata Maria Porto Vanni"),
    ("b3601f91-e41f-46d8-bc43-00000000000d", "Rita de Cássia Cunha Ferreira"),
    ("b3601f91-e41f-46d8-bc43-00000000000e", "Rosana Núbia Sorbille"),
]


def seed():
    with SessionFactory.begin() as db:
        for id_, name in STAFF:
            db.execute(
                insert(InstitutionalStaff)
                .values(id=UUID(id_), name=name, active=True)
                .on_conflict_do_nothing(index_elements=["id"])
            )


if __name__ == "__main__":
    seed()
    print(
        "Seed concluído: 14 identidades institucionais verificadas; correções existentes preservadas."
    )