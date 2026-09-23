from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.schemas.staff import StaffInput, StaffOut
from app.core.audit import Event, record
from app.core.errors import DomainError
from app.db.models import (
    InstitutionalStaff,
)
from app.db.session import SessionFactory, database_now

router = APIRouter()


@router.get("/staff", response_model=list[StaffOut], tags=["Servidores institucionais"])
def staff(user=Depends(current_user)):
    with SessionFactory() as db:
        return [
            {"id": s.id, "name": s.name, "active": s.active}
            for s in db.scalars(
                select(InstitutionalStaff).order_by(InstitutionalStaff.name, InstitutionalStaff.id)
            )
        ]


@router.post("/admin/staff", response_model=StaffOut, status_code=201, tags=["Administração"])
def create_staff(data: StaffInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = InstitutionalStaff(**data.model_dump())
        db.add(s)
        db.flush()
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_CREATED"},
            after=data.model_dump(),
            entity_type="INSTITUTIONAL_STAFF",
        )
        return {"id": s.id, **data.model_dump()}


@router.put("/admin/staff/{staff_id}", response_model=StaffOut, tags=["Administração"])
def update_staff(staff_id: UUID, data: StaffInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = db.scalar(
            select(InstitutionalStaff).where(InstitutionalStaff.id == staff_id).with_for_update()
        )
        if not s:
            raise DomainError("STAFF_NOT_FOUND", "Servidor não encontrado.", 404)
        before = {"name": s.name, "active": s.active}
        s.name, s.active, s.updated_at = data.name, data.active, database_now(db)
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_UPDATED"},
            before=before,
            after=data.model_dump(),
            entity_type="INSTITUTIONAL_STAFF",
        )
        return {"id": s.id, **data.model_dump()}
