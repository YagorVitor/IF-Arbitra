import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

priority_sequence = Sequence("priority_sequence")


class Sextet(Base):
    __tablename__ = "sextets"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allocation_rounds.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(80))
    member_count: Mapped[int] = mapped_column(Integer, default=6)
    registration_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    priority_sequence: Mapped[int] = mapped_column(
        BigInteger, priority_sequence, server_default=priority_sequence.next_value(), unique=True
    )
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID)
    __table_args__ = (
        CheckConstraint("member_count BETWEEN 3 AND 6", name="ck_sextets_member_count"),
        UniqueConstraint("id", "round_id"),
        UniqueConstraint("created_by", "idempotency_key"),
        Index("ix_sextet_priority", "round_id", "registration_completed_at", "priority_sequence"),
    )


class SextetMember(Base):
    __tablename__ = "sextet_members"
    sextet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sextets.id"), primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint("slot BETWEEN 0 AND 5"),
        UniqueConstraint("sextet_id", "user_id"),
        Index("uq_student_active_sextet", "user_id", unique=True, postgresql_where=text("active")),
    )
