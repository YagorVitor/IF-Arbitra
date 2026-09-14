"""Popula uma instalação local com dados realistas para validar o frontend.

Execução:
    python -m app.seed

O seed é idempotente: usa IDs e logins estáveis, não remove registros existentes e
preserva nomes de servidores já corrigidos manualmente. As credenciais impressas ao
final são destinadas somente ao ambiente local de desenvolvimento.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.auth import digest, hasher
from app.db import SessionFactory
from app.models import (
    Allocation,
    AllocationRound,
    AllocationRun,
    AuditEvent,
    InstitutionalStaff,
    LoginSession,
    PreferenceItem,
    PreferenceSubmission,
    RoundStaff,
    Sextet,
    SextetMember,
    User,
)

PASSWORD = "testing-password-2026"
ADMIN_ID = UUID("10000000-0000-4000-8000-000000000001")

# IDs estáveis permitem que o frontend seja configurado com links/bookmarks fixos.
STAFF = [
    ("b3601f91-e41f-46d8-bc43-000000000001", "Prof. José da Silva"),
    ("b3601f91-e41f-46d8-bc43-000000000002", "Prof. Ana Martins"),
    ("b3601f91-e41f-46d8-bc43-000000000003", "Prof. Carlos Pereira"),
    ("b3601f91-e41f-46d8-bc43-000000000004", "Prof. Juliana Souza"),
    ("b3601f91-e41f-46d8-bc43-000000000005", "Prof. Ricardo Almeida"),
    ("b3601f91-e41f-46d8-bc43-000000000006", "Prof. Fernanda Costa"),
    ("b3601f91-e41f-46d8-bc43-000000000007", "Prof. Marcos Oliveira"),
    ("b3601f91-e41f-46d8-bc43-000000000008", "Prof. Daniela Ribeiro"),
    ("b3601f91-e41f-46d8-bc43-000000000009", "Prof. Eduardo Santos"),
    ("b3601f91-e41f-46d8-bc43-00000000000a", "Prof. Patrícia Gomes"),
    ("b3601f91-e41f-46d8-bc43-00000000000b", "Prof. Bruno Carvalho"),
    ("b3601f91-e41f-46d8-bc43-00000000000c", "Prof. Camila Ferreira"),
    ("b3601f91-e41f-46d8-bc43-00000000000d", "Prof. Lucas Mendes"),
    ("b3601f91-e41f-46d8-bc43-00000000000e", "Prof. Beatriz Lima"),
]

# O primeiro grupo usa o identificador exibido na imagem de referência.
STUDENT_NAMES = [
    "Yagor Vitor Silva dos Santos",
    "Mariana Alves Oliveira",
    "João Pedro Ferreira",
    "Larissa Costa Mendes",
    "Gabriel Henrique Souza",
    "Beatriz Rodrigues Lima",
    "Lucas Martins Carvalho",
    "Ana Clara Pereira",
    "Rafael Gomes da Silva",
    "Isabela Fernandes Rocha",
    "Matheus Almeida Santos",
    "Julia Vitória Barbosa",
    "Enzo Gabriel Moreira",
    "Letícia Cristina Dias",
    "Pedro Henrique Nunes",
    "Sofia Martins Ribeiro",
    "Miguel Araújo Costa",
    "Manuela Castro Oliveira",
    "Davi Lucas Cardoso",
    "Helena Mendes Alves",
    "Arthur Vinícius Ramos",
    "Laura Beatriz Teixeira",
    "Bernardo Freitas Souza",
    "Alice Vitória Martins",
    "Gustavo Lima Pereira",
    "Valentina Duarte Silva",
    "Heitor César Gomes",
    "Cecília Andrade Santos",
    "Samuel Correia Alves",
    "Lorena Maria Costa",
    "Theo Barbosa Ferreira",
    "Maria Eduarda Nascimento",
    "Nicolas Vieira Lima",
    "Heloísa Moraes Silva",
    "Pietro Carvalho Mendes",
    "Clara Beatriz Rocha",
    "Breno Matos Oliveira",
    "Luísa Helena Souza",
    "Ian Gabriel Santos",
    "Emanuelly Freire Costa",
    "Vicente Alves Pereira",
    "Melissa Ribeiro Gomes",
    "Caleb Martins Silva",
    "Lívia Araújo Ferreira",
    "Noah Henrique Lima",
    "Esther Campos Souza",
    "Anthony Rodrigues Costa",
    "Maitê Fernandes Alves",
    "Caio Augusto Martins",
    "Elisa Moura Fernandes",
    "Henrique Tavares Lima",
    "Nicole Vitória Souza",
    "Otávio César Ribeiro",
    "Yasmin Oliveira Santos",
    "Leandro Pires Carvalho",
    "Rebeca Cristina Alves",
    "Murilo Nascimento Costa",
    "Agatha Beatriz Gomes",
    "Vitor Hugo Teixeira",
    "Eloá Martins Pereira",
    "Joaquim Duarte Silva",
    "Rafaela Mendes Rocha",
    "Augusto Freitas Lima",
    "Sarah Vitória Campos",
    "André Luiz Barbosa",
    "Bianca Araújo Santos",
    "Tomás Henrique Souza",
    "Nina Carvalho Ferreira",
    "Diego Matheus Oliveira",
    "Ayla Fernandes Costa",
    "Cauã Gabriel Ribeiro",
    "Mirella Alves Mendes",
]

ROUND_ID = UUID("20000000-0000-4000-8000-000000000001")
OPEN_ROUND_ID = UUID("20000000-0000-4000-8000-000000000002")
SEXTET_IDS = [UUID(f"30000000-0000-4000-8000-{i:012d}") for i in range(1, 9)]


def get_or_create_user(db, *, user_id, name, login, role="STUDENT"):
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            name=name,
            login=login,
            role=role,
            password_hash=hasher.hash(PASSWORD),
            active=True,
        )
        db.add(user)
        db.flush()
    return user


def ensure_staff(db):
    result = []
    for id_, name in STAFF:
        staff = db.get(InstitutionalStaff, UUID(id_))
        if staff is None:
            staff = InstitutionalStaff(id=UUID(id_), name=name, active=True)
            db.add(staff)
            db.flush()
        result.append(staff)
    return result


def ensure_round(db, *, round_id, name, status, now, staff, open_window=False):
    round_ = db.get(AllocationRound, round_id)
    if round_ is None:
        if open_window:
            registration_close = now + timedelta(days=7)
            preferences_close = now + timedelta(days=14)
        else:
            registration_close = now - timedelta(days=20)
            preferences_close = now - timedelta(days=10)
        round_ = AllocationRound(
            id=round_id,
            name=name,
            # O trigger freeze_round_staff exige que os servidores sejam
            # associados enquanto a rodada ainda está em DRAFT.
            status="DRAFT",
            registration_opens_at=now - timedelta(days=30),
            registration_closes_at=registration_close,
            preferences_open_at=now - timedelta(days=25),
            preferences_close_at=preferences_close,
        )
        db.add(round_)
        db.flush()
    for position, person in enumerate(staff):
        if db.scalar(
            select(RoundStaff).where(
                RoundStaff.round_id == round_.id, RoundStaff.staff_id == person.id
            )
        ) is None:
            db.add(RoundStaff(round_id=round_.id, staff_id=person.id, order=position))
    db.flush()
    if round_.status == "DRAFT" and status != "DRAFT":
        round_.status = status
        db.flush()
    return round_


def ensure_audit(db, event_type, entity_id, actor_id, payload):
    exists = db.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == event_type,
            AuditEvent.entity_id == str(entity_id),
            AuditEvent.payload["seed"].astext == "frontend-demo",
        )
    )
    if exists is None:
        db.add(
            AuditEvent(
                event_type=event_type,
                actor_user_id=actor_id,
                entity_id=str(entity_id),
                request_id=str(uuid4()),
                payload={"seed": "frontend-demo", **payload},
            )
        )


def seed():
    now = datetime.now(UTC).replace(microsecond=0)
    with SessionFactory.begin() as db:
        staff = ensure_staff(db)
        admin = get_or_create_user(
            db,
            user_id=ADMIN_ID,
            name="Administrador IF-Arbitra",
            login="admin",
            role="ADMIN",
        )
        students = [
            get_or_create_user(
                db,
                user_id=UUID(f"40000000-0000-4000-8000-{i:012d}"),
                name=name,
                login="aq" + str(30214015 + i),
            )
            for i, name in enumerate(STUDENT_NAMES, 1)
        ]

        published = ensure_round(
            db,
            round_id=ROUND_ID,
            name="Rodada 2026/2",
            # A rodada precisa passar por OPEN para aceitar sextetos e preferências.
            # Ao final do seed ela avança por PROCESSED até PUBLISHED.
            status="OPEN",
            now=now,
            staff=staff,
        )
        open_round = ensure_round(
            db,
            round_id=OPEN_ROUND_ID,
            name="Rodada 2026/3 · inscrições abertas",
            status="OPEN",
            now=now,
            staff=staff,
            open_window=True,
        )

        # Oito sextetos e 48 alunos reproduzem o cenário de resultados da referência.
        for group_index, sextet_id in enumerate(SEXTET_IDS):
            members = students[group_index * 6 : group_index * 6 + 6]
            sextet = db.get(Sextet, sextet_id)
            if sextet is None:
                sextet = Sextet(
                    id=sextet_id,
                    round_id=published.id,
                    created_by=members[0].id,
                    name=f"Sexteto {group_index + 1:02d}",
                    registration_completed_at=now - timedelta(days=18, minutes=group_index),
                    idempotency_key=UUID(f"50000000-0000-4000-8000-{group_index + 1:012d}"),
                )
                db.add(sextet)
                db.flush()
            for slot, student in enumerate(members):
                if db.scalar(
                    select(SextetMember).where(
                        SextetMember.sextet_id == sextet.id,
                        SextetMember.slot == slot,
                    )
                ) is None:
                    db.add(
                        SextetMember(
                            sextet_id=sextet.id, slot=slot, user_id=student.id, active=True
                        )
                    )
            submission = db.get(PreferenceSubmission, sextet.id)
            if submission is None:
                submission = PreferenceSubmission(
                    sextet_id=sextet.id,
                    round_id=published.id,
                    version=1,
                    submitted_at=now - timedelta(days=12, minutes=group_index),
                )
                db.add(submission)
                db.flush()
                # Rotações produzem posições diferentes no resultado administrativo.
                ranking = staff[group_index % len(staff) :] + staff[: group_index % len(staff)]
                db.add_all(
                    [
                        PreferenceItem(
                            sextet_id=sextet.id,
                            position=position,
                            round_id=published.id,
                            staff_id=person.id,
                        )
                        for position, person in enumerate(ranking, 1)
                    ]
                )
        db.flush()

        run = db.scalar(
            select(AllocationRun).where(
                AllocationRun.round_id == published.id, AllocationRun.status == "COMPLETED"
            )
        )
        if run is None:
            run = AllocationRun(
                id=UUID("60000000-0000-4000-8000-000000000001"),
                round_id=published.id,
                status="COMPLETED",
                started_at=now - timedelta(days=10, hours=2),
                finished_at=now - timedelta(days=10, hours=1),
                executed_by=admin.id,
                algorithm_version="serial-priority-v1",
                input_fingerprint="frontend-demo-seed",
                snapshot={
                    "seed": "frontend-demo",
                    "round_id": str(published.id),
                    "staff_order": [str(person.id) for person in staff],
                    "groups": [str(sextet_id) for sextet_id in SEXTET_IDS],
                },
            )
            db.add(run)
            db.flush()
            for group_index, sextet_id in enumerate(SEXTET_IDS):
                assigned = staff[group_index]
                db.add(
                    Allocation(
                        run_id=run.id,
                        round_id=published.id,
                        sextet_id=sextet_id,
                        staff_id=assigned.id,
                        preference_position=(group_index % len(staff)) + 1,
                        kind="MAIN",
                        status="ALLOCATED",
                        trace={
                            "processing_order": group_index + 1,
                            "chosen": str(assigned.id),
                            "reason": "FIRST_AVAILABLE",
                            "seed": "frontend-demo",
                        },
                    )
                )

        if published.status == "OPEN":
            published.status = "PROCESSED"
            db.flush()
            published.status = "PUBLISHED"
            db.flush()

        ensure_audit(db, "ROUND_CREATED", published.id, admin.id, {"name": published.name})
        ensure_audit(db, "ALLOCATION_COMPLETED", run.id, admin.id, {"groups": 8})
        ensure_audit(db, "ROUND_PUBLISHED", published.id, admin.id, {"status": "PUBLISHED"})
        ensure_audit(db, "ROUND_OPENED", open_round.id, admin.id, {"status": "OPEN"})

        # Uma sessão previsível facilita testes manuais por clientes que não fazem login.
        for user in [admin, *students]:
            token = digest(str(user.id))
            if db.get(LoginSession, token) is None:
                db.add(
                    LoginSession(
                        token_hash=token,
                        user_id=user.id,
                        expires_at=now + timedelta(days=30),
                    )
                )

    return {
        "admin_login": "admin",
        "student_login": students[0].login,
        "password": PASSWORD,
        "published_round_id": str(ROUND_ID),
        "open_round_id": str(OPEN_ROUND_ID),
        "students": len(students),
        "staff": len(staff),
        "sextets": len(SEXTET_IDS),
    }


if __name__ == "__main__":
    summary = seed()
    print("Seed de demonstração concluído.")
    for key, value in summary.items():
        print(f"{key}: {value}")
