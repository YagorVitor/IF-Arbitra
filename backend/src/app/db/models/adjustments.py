import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class AllocationAdjustment(Base):
    """Append-only revisions; the automatic allocation remains reproducible."""

    __tablename__ = "allocation_adjustments"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allocation_rounds.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    assignments: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(String(1000))
    executed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("round_id", "revision"),)
