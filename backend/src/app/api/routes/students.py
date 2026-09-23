from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.schemas.users import StudentSearchOut, UserInput, UserOut
from app.core.audit import Event, record
from app.core.security import hasher
from app.db.models import (
    SextetMember,
    User,
)
from app.db.session import SessionFactory

router = APIRouter()


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
        student = User(
            name=data.name, login=data.login.casefold(), password_hash=hasher.hash(data.password)
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
