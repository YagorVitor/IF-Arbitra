from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.schemas.staff import StaffCreateInput, StaffOut, StaffUpdateInput
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
            {"id": s.id, "name": s.name, "email": s.email, "active": s.active}
            for s in db.scalars(
                select(InstitutionalStaff).order_by(InstitutionalStaff.name, InstitutionalStaff.id)
            )
        ]


@router.post("/admin/staff", response_model=StaffOut, status_code=201, tags=["Administração"])
def create_staff(data: StaffCreateInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        address = str(data.email).casefold()
        existing = db.scalar(
            select(InstitutionalStaff).where(InstitutionalStaff.email == address).with_for_update()
        )
        if existing:
            if existing.active:
                raise DomainError(
                    "STAFF_EMAIL_ALREADY_EXISTS", "Este e-mail já está cadastrado.", 409
                )
            previous = {"name": existing.name, "active": False}
            existing.name = data.name
            existing.active = True
            existing.updated_at = database_now(db)
            record(
                db,
                request,
                Event.ADMIN,
                existing.id,
                {"action": "STAFF_RESTORED"},
                before=previous,
                after={"name": existing.name, "email": address, "active": True},
                entity_type="INSTITUTIONAL_STAFF",
            )
            return {"id": existing.id, "name": existing.name, "email": address, "active": True}
        s = InstitutionalStaff(name=data.name, email=address, active=True)
        db.add(s)
        db.flush()
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_CREATED"},
            after={"name": s.name, "email": s.email, "active": s.active},
            entity_type="INSTITUTIONAL_STAFF",
        )
        return {"id": s.id, "name": s.name, "email": s.email, "active": s.active}


@router.put("/admin/staff/{staff_id}", response_model=StaffOut, tags=["Administração"])
def update_staff(staff_id: UUID, data: StaffUpdateInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = db.scalar(
            select(InstitutionalStaff).where(InstitutionalStaff.id == staff_id).with_for_update()
        )
        if not s:
            raise DomainError("STAFF_NOT_FOUND", "Servidor não encontrado.", 404)
        before = {"name": s.name, "email": s.email, "active": s.active}
        s.name, s.active, s.updated_at = data.name, data.active, database_now(db)
        if data.email is not None:
            s.email = str(data.email).casefold()
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_UPDATED"},
            before=before,
            after={"name": s.name, "email": s.email, "active": s.active},
            entity_type="INSTITUTIONAL_STAFF",
        )
        return {"id": s.id, "name": s.name, "email": s.email, "active": s.active}


@router.delete("/admin/staff/{staff_id}", status_code=204, tags=["Administração"])
def remove_staff(staff_id: UUID, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        s = db.scalar(
            select(InstitutionalStaff).where(InstitutionalStaff.id == staff_id).with_for_update()
        )
        if not s:
            raise DomainError("STAFF_NOT_FOUND", "Servidor não encontrado.", 404)
        if not s.active:
            return
        s.active = False
        s.updated_at = database_now(db)
        record(
            db,
            request,
            Event.ADMIN,
            s.id,
            {"action": "STAFF_REMOVED"},
            before={"active": True},
            after={"active": False},
            entity_type="INSTITUTIONAL_STAFF",
        )
