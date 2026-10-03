from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.dependencies import admin
from app.api.schemas.reservations import ReservationInput, ReservationOut
from app.core.errors import DomainError
from app.db.models import InstitutionalStaff, StaffReservation, User
from app.db.session import SessionFactory, database_now

router = APIRouter()


@router.get("/admin/reservations", response_model=list[ReservationOut], tags=["Administração"])
def reservations(user=Depends(admin)):
    with SessionFactory() as db:
        return [
            {
                "captain_id": row.captain_id,
                "captain_name": captain.name,
                "staff_id": row.staff_id,
                "staff_name": staff.name,
                "reason": row.reason,
                "updated_at": row.updated_at,
                "enabled": captain.is_captain and captain.removed_at is None and staff.active,
            }
            for row, captain, staff in db.execute(
                select(StaffReservation, User, InstitutionalStaff)
                .join(User, User.id == StaffReservation.captain_id)
                .join(InstitutionalStaff, InstitutionalStaff.id == StaffReservation.staff_id)
                .order_by(User.name)
            )
        ]


@router.put("/admin/students/{captain_id}/reservation", status_code=204, tags=["Administração"])
def set_reservation(captain_id: UUID, data: ReservationInput, user=Depends(admin)):
    with SessionFactory.begin() as db:
        # Serialize concurrent assignments to the same staff before checking the unique constraint.
        if data.staff_id:
            staff = db.scalar(
                select(InstitutionalStaff)
                .where(InstitutionalStaff.id == data.staff_id)
                .with_for_update()
            )
            if not staff or not staff.active:
                raise DomainError("STAFF_NOT_FOUND", "Selecione um servidor ativo.", 422)
        captain = db.scalar(select(User).where(User.id == captain_id).with_for_update())
        if not captain or captain.role != "STUDENT":
            raise DomainError("STUDENT_NOT_FOUND", "Aluno não encontrado.", 404)
        if data.staff_id and (not captain.is_captain or captain.removed_at is not None):
            raise DomainError("CAPTAIN_REQUIRED", "Selecione um capitão cadastrado.", 422)
        row = db.get(StaffReservation, captain_id)
        if data.staff_id:
            conflict = db.scalar(
                select(StaffReservation).where(
                    StaffReservation.staff_id == data.staff_id,
                    StaffReservation.captain_id != captain_id,
                )
            )
            if conflict:
                raise DomainError(
                    "RESERVATION_CONFLICT", "Este servidor já tem uma reserva administrativa.", 409
                )
            if row is None:
                row = StaffReservation(captain_id=captain_id)
                db.add(row)
            row.staff_id, row.reason, row.updated_by = data.staff_id, data.reason.strip(), user.id
            row.updated_at = database_now(db)
        elif row:
            db.delete(row)
