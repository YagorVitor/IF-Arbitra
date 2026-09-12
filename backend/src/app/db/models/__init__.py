"""Register all mapped entities against one SQLAlchemy metadata registry."""

from app.db.models.allocation import Allocation, AllocationRun
from app.db.models.audit import AuditEvent
from app.db.models.base import Base
from app.db.models.preferences import PreferenceItem, PreferenceSubmission
from app.db.models.rounds import AllocationRound, RoundStaff
from app.db.models.sextets import Sextet, SextetMember
from app.db.models.staff import InstitutionalStaff
from app.db.models.users import LoginSession, LoginThrottle, User

__all__ = [
    "Base",
    "User",
    "LoginSession",
    "LoginThrottle",
    "InstitutionalStaff",
    "AllocationRound",
    "RoundStaff",
    "Sextet",
    "SextetMember",
    "PreferenceSubmission",
    "PreferenceItem",
    "AllocationRun",
    "Allocation",
    "AuditEvent",
]
