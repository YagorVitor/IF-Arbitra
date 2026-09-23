import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class AllocationRound(Base):
    __tablename__ = "allocation_rounds"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="DRAFT")
    registration_opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    preferences_open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    preferences_close_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','OPEN','PROCESSED','PUBLISHED','ARCHIVED')"),
        CheckConstraint("registration_opens_at < registration_closes_at"),
        CheckConstraint("preferences_open_at < preferences_close_at"),
        CheckConstraint("registration_closes_at <= preferences_close_at"),
    )


class RoundStaff(Base):
    __tablename__ = "round_staff"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("allocation_rounds.id"), primary_key=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutional_staff.id"), primary_key=True
    )
    order: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("round_id", "order"), CheckConstraint('"order" >= 0'))
