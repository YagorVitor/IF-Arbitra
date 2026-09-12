import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class PreferenceSubmission(Base):
    __tablename__ = "preference_submissions"
    sextet_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    round_id: Mapped[uuid.UUID] = mapped_column(UUID)
    version: Mapped[int] = mapped_column(Integer, default=1)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["sextet_id", "round_id"], ["sextets.id", "sextets.round_id"]),
        UniqueConstraint("sextet_id", "round_id"),
        CheckConstraint("version > 0"),
    )


class PreferenceItem(Base):
    __tablename__ = "preference_items"
    sextet_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[uuid.UUID] = mapped_column(UUID)
    staff_id: Mapped[uuid.UUID] = mapped_column(UUID)
    __table_args__ = (
        ForeignKeyConstraint(
            ["sextet_id", "round_id"],
            ["preference_submissions.sextet_id", "preference_submissions.round_id"],
        ),
        ForeignKeyConstraint(
            ["round_id", "staff_id"], ["round_staff.round_id", "round_staff.staff_id"]
        ),
        UniqueConstraint("sextet_id", "staff_id"),
        CheckConstraint("position > 0"),
    )
