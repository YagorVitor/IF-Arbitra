import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, select

from app.api.dependencies import admin, current_user
from app.api.schemas.users import (
    AdminStudentOut,
    CaptainInput,
    CredentialDispatchOut,
    StudentAccessOut,
    StudentProfileInput,
    StudentSearchOut,
    UserInput,
    UserOut,
)
from app.core.audit import Event, record
from app.core.errors import DomainError
from app.core.security import hasher
from app.db.models import (
    LoginSession,
    SextetMember,
    User,
)
from app.db.session import SessionFactory, database_now
from app.services.credential_dispatch import dispatch_credentials, send_test_email

router = APIRouter()


@router.post("/admin/email/test", tags=["Administração"])
def test_email(request: Request, user=Depends(admin)) -> dict[str, str | bool]:
    return send_test_email(request, user)


@router.post("/admin/students/{student_id}/restore", response_model=UserOut, tags=["Administração"])
def restore_student(student_id: UUID, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User).where(User.id == student_id, User.role == "STUDENT").with_for_update()
        )
        if not student or student.removed_at is None:
            raise DomainError("STUDENT_NOT_REMOVED", "Selecione um aluno removido existente.", 409)
        student.removed_at = None
        student.active = False
        student.password_hash = None
        student.email_verified_at = None
        db.execute(delete(LoginSession).where(LoginSession.user_id == student.id))
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_RESTORED"},
            after={"active": False, "removed_at": None},
            entity_type="USER",
        )
        return student


@router.post(
    "/admin/students/{student_id}/access", response_model=StudentAccessOut, tags=["Administração"]
)
def issue_student_access(student_id: UUID, request: Request, user=Depends(admin)):
    """Explicit manual delivery: returned once, never persisted or audited in plaintext."""
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User).where(User.id == student_id, User.role == "STUDENT").with_for_update()
        )
        if not student or student.removed_at is not None:
            raise DomainError(
                "STUDENT_NOT_FOUND", "Aluno não encontrado. Restaure o cadastro antes.", 404
            )
        if not student.is_captain:
            raise DomainError(
                "CAPTAIN_REQUIRED", "Somente capitães recebem credenciais de acesso.", 403
            )
        password = secrets.token_urlsafe(16)
        student.password_hash = hasher.hash(password)
        student.active = True
        db.execute(delete(LoginSession).where(LoginSession.user_id == student.id))
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_ACCESS_ISSUED_MANUALLY"},
            after={"active": True},
            entity_type="USER",
        )
        return {"login": student.login, "password": password}


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
                "is_captain": student.is_captain,
                "phone": student.phone,
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
                    User.removed_at.is_(None),
                    User.is_captain.is_(False),
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
            existing.is_captain = data.is_captain
            existing.phone = data.phone
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
            is_captain=data.is_captain,
            phone=data.phone,
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
            after={"name": student.name, "login": student.login, "is_captain": student.is_captain},
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


@router.put("/admin/students/{student_id}/captain", response_model=UserOut, tags=["Administração"])
def set_captain(student_id: UUID, data: CaptainInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User).where(User.id == student_id, User.role == "STUDENT").with_for_update()
        )
        if not student or student.removed_at is not None:
            raise DomainError("STUDENT_NOT_FOUND", "Aluno não encontrado.", 404)
        if student.is_captain == data.is_captain:
            return student
        membership = db.scalar(
            select(SextetMember)
            .where(SextetMember.user_id == student.id, SextetMember.active)
            .limit(1)
        )
        if membership:
            raise DomainError(
                "STUDENT_IN_SEXTET",
                "Arquive a rodada antes de alterar a função de um integrante.",
                409,
            )
        before = {"is_captain": student.is_captain}
        student.is_captain = data.is_captain
        student.active = False
        student.password_hash = None
        db.execute(delete(LoginSession).where(LoginSession.user_id == student.id))
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "CAPTAIN_CHANGED"},
            before=before,
            after={"is_captain": student.is_captain},
            entity_type="USER",
        )
        return student


@router.put("/admin/students/{student_id}/profile", response_model=UserOut, tags=["Administração"])
def update_student_profile(
    student_id: UUID, data: StudentProfileInput, request: Request, user=Depends(admin)
):
    with SessionFactory.begin() as db:
        student = db.scalar(
            select(User).where(User.id == student_id, User.role == "STUDENT").with_for_update()
        )
        if not student or student.removed_at is not None:
            raise DomainError("STUDENT_NOT_FOUND", "Aluno não encontrado.", 404)
        before = {"name": student.name}
        phone_changed = student.phone != data.phone
        student.name = data.name
        student.phone = data.phone
        record(
            db,
            request,
            Event.ADMIN,
            student.id,
            {"action": "STUDENT_PROFILE_UPDATED", "phone_changed": phone_changed},
            before=before,
            after={"name": student.name},
            entity_type="USER",
        )
        return student
