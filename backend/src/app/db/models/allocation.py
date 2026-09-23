import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class AllocationRun(Base):
    __tablename__ = "allocation_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allocation_rounds.id"), index=True)
    status: Mapped[str] = mapped_column(String(24))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    algorithm_version: Mapped[str] = mapped_column(String(32), default="serial-priority-v1")
    input_fingerprint: Mapped[str | None] = mapped_column(String(64))
    snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("id", "round_id"),
        CheckConstraint("status IN ('PROCESSING','COMPLETED','FAILED')"),
        Index(
            "uq_official_run",
            "round_id",
            unique=True,
            postgresql_where=text("status IN ('PROCESSING','COMPLETED')"),
        ),
    )


class Allocation(Base):
    __tablename__ = "allocations"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID)
    round_id: Mapped[uuid.UUID] = mapped_column(UUID)
    sextet_id: Mapped[uuid.UUID] = mapped_column(UUID)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUID)
    preference_position: Mapped[int | None] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24))
    trace: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = (
        ForeignKeyConstraint(
            ["run_id", "round_id"], ["allocation_runs.id", "allocation_runs.round_id"]
        ),
        ForeignKeyConstraint(["sextet_id", "round_id"], ["sextets.id", "sextets.round_id"]),
        ForeignKeyConstraint(
            ["round_id", "staff_id"], ["round_staff.round_id", "round_staff.staff_id"]
        ),
        UniqueConstraint("round_id", "sextet_id"),
        UniqueConstraint("round_id", "staff_id"),
        CheckConstraint("kind IN ('MAIN','REPECHAGE')"),
        CheckConstraint(
            "(status = 'ALLOCATED' AND staff_id IS NOT NULL) OR "
            "(status = 'UNALLOCATED' AND staff_id IS NULL)"
        ),
    )
