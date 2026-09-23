from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.presenters import sextet_view
from app.api.schemas.sextets import SextetInput, SextetOut, SextetSummaryOut
from app.core.audit import Event, independent
from app.db.models import (
    Sextet,
    SextetMember,
)
from app.db.session import SessionFactory
from app.services.sextets import owned_sextet, register_sextet

router = APIRouter()


@router.get("/rounds/{round_id}/my-sextet", response_model=SextetOut | None, tags=["Sextetos"])
def my_sextet(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        s = db.scalar(
            select(Sextet)
            .join(SextetMember)
            .where(Sextet.round_id == round_id, SextetMember.user_id == user.id)
        )
        return sextet_view(db, s) if s else None


@router.post(
    "/rounds/{round_id}/sextets", response_model=SextetOut, status_code=201, tags=["Sextetos"]
)
def confirm_sextet(round_id: UUID, data: SextetInput, request: Request, user=Depends(current_user)):
    independent(request, Event.SEXTET_ATTEMPT, round_id, entity_type="ALLOCATION_ROUND")
    with SessionFactory.begin() as db:
        s = register_sextet(db, request, round_id, user, data)
        return sextet_view(db, s)


@router.get(
    "/admin/rounds/{round_id}/sextets",
    response_model=list[SextetSummaryOut],
    tags=["Administração"],
)
def admin_sextets(round_id: UUID, user=Depends(admin)):
    with SessionFactory() as db:
        # Bounded institutional dataset; the admin list avoids fetching each composition/ranking.
        return [
            {
                "id": s.id,
                "name": s.name,
                "member_count": s.member_count,
                "registration_completed_at": s.registration_completed_at,
                "priority_sequence": s.priority_sequence,
            }
            for s in db.scalars(
                select(Sextet)
                .where(Sextet.round_id == round_id)
                .order_by(Sextet.registration_completed_at, Sextet.priority_sequence)
                .limit(500)
            )
        ]


@router.get("/sextets/{sextet_id}", response_model=SextetOut, tags=["Sextetos"])
def get_sextet(sextet_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        return sextet_view(db, owned_sextet(db, sextet_id, user))
