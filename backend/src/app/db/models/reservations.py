from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class StaffReservation(Base):
    __tablename__ = "staff_reservations"
    captain_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("institutional_staff.id"), unique=True)
    reason: Mapped[str] = mapped_column(String(1000))
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
