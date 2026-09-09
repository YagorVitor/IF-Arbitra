import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    login: Mapped[str] = mapped_column(String(160), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="STUDENT")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("role IN ('ADMIN','STUDENT')"),)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class InstitutionalStaff(Base):
    __tablename__ = "institutional_staff"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


priority_sequence = Sequence("priority_sequence")


class Sextet(Base):
    __tablename__ = "sextets"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allocation_rounds.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(80))
    registration_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    priority_sequence: Mapped[int] = mapped_column(
        BigInteger, priority_sequence, server_default=priority_sequence.next_value(), unique=True
    )
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID)
    __table_args__ = (
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


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), index=True)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    previous_state: Mapped[dict | None] = mapped_column(JSONB)
    resulting_state: Mapped[dict | None] = mapped_column(JSONB)
