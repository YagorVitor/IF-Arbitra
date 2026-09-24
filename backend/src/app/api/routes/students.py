from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, select

from app.api.dependencies import admin, current_user
from app.api.schemas.users import (
    AdminStudentOut,
    CredentialDispatchOut,
    StudentSearchOut,
    UserInput,
    UserOut,
)
from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    LoginSession,
    SextetMember,
    User,
)
from app.db.session import SessionFactory, database_now
from app.services.credential_dispatch import dispatch_credentials

router = APIRouter()


@router.get("/admin/students", response_model=list[AdminStudentOut], tags=["Administração"])
def admin_students(include_removed: bool = False, user=Depends(admin)):
    with SessionFactory() as db:
        query = select(User).where(User.role == "STUDENT")
        if not include_removed:
            query = query.where(User.removed_at.is_(None))
        rows = db.scalars(query.order_by(User.name, User.id)).all()
        return [
            {
                "id": student.id,
                "name": student.name,
                "login": student.login,
                "email": student.email,
                "active": student.active,
                "removed_at": student.removed_at,
                "credentials_issued": student.password_hash is not None,
            }
            for student in rows
        ]


@router.get("/students", response_model=list[StudentSearchOut], tags=["Alunos"])
def students(q: str = Query(min_length=2, max_length=100), user=Depends(current_user)):
    with SessionFactory() as db:
        term = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = (
            db.execute(
                select(
                    User.id,
                    User.name,
                    User.login,
                    select(SextetMember.user_id)
                    .where(SextetMember.user_id == User.id, SextetMember.active)
                    .exists()
                    .label("occupied"),
                )
                .where(
                    User.active,
                    User.role == "STUDENT",
                    (User.name.ilike(f"%{term}%") | User.login.ilike(f"%{term}%")),
                )
                .order_by(User.name, User.id)
                .limit(20)
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]


@router.post("/admin/students", response_model=UserOut, status_code=201, tags=["Administração"])
def create_student(data: UserInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        address = str(data.email).casefold()
        existing = db.scalar(select(User).where(User.email == address).with_for_update())
        if existing:
            if existing.role != "STUDENT" or existing.removed_at is None:
                raise DomainError("EMAIL_ALREADY_EXISTS", "Este e-mail já está cadastrado.", 409)
            previous = {"name": existing.name, "removed_at": existing.removed_at.isoformat()}
            existing.name = data.name
            existing.login = address
            existing.active = False
            existing.password_hash = None
            existing.email_verified_at = None
            existing.removed_at = None
            db.execute(delete(LoginSession).where(LoginSession.user_id == existing.id))
            record(
                db,
                request,
                Event.ADMIN,
                existing.id,
                {"action": "STUDENT_RESTORED"},
                before=previous,
                after={"name": existing.name, "login": existing.login},
                entity_type="USER",
            )
            return existing
        student = User(
            name=data.name,
            login=address,
            email=address,
            password_hash=None,
            active=False,
        )
        db.add(student)
        db.flush()
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_CREATED"},
            after={"name": student.name, "login": student.login},
            entity_type="USER",
        )
        return student


@router.delete("/admin/students/{student_id}", status_code=204, tags=["Administração"])
def remove_student(student_id: UUID, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User).where(User.id == student_id, User.role == "STUDENT").with_for_update()
        )
        if not student or student.removed_at is not None:
            raise DomainError("STUDENT_NOT_FOUND", "Aluno não encontrado.", 404)
        membership = db.scalar(
            select(SextetMember)
            .where(SextetMember.user_id == student.id, SextetMember.active)
            .limit(1)
        )
        if membership:
            raise DomainError(
                "STUDENT_IN_SEXTET",
                "Arquive a rodada do aluno antes de removê-lo.",
                409,
            )
        before = {"active": student.active, "removed_at": None}
        student.active = False
        student.removed_at = database_now(db)
        db.execute(delete(LoginSession).where(LoginSession.user_id == student.id))
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_REMOVED"},
            before=before,
            after={"active": False, "removed_at": student.removed_at.isoformat()},
            entity_type="USER",
        )


@router.post(
    "/admin/students/dispatch-credentials",
    response_model=CredentialDispatchOut,
    tags=["Administração"],
)
def dispatch_student_credentials(request: Request, user=Depends(admin)):
    return dispatch_credentials(request)
