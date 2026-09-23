from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.dependencies import admin, current_user
from app.api.presenters import round_view, round_views
from app.api.schemas.rounds import RoundInput, RoundOut, TransitionInput
from app.core.errors import DomainError
from app.db.models import (
    AllocationRound,
)
from app.db.session import SessionFactory
from app.services import rounds as round_service

router = APIRouter()


@router.get("/rounds", response_model=list[RoundOut], tags=["Rodadas"])
def rounds(user=Depends(current_user)):
    with SessionFactory() as db:
        stmt = select(AllocationRound).order_by(AllocationRound.created_at.desc()).limit(100)
        if user.role != "ADMIN":
            stmt = stmt.where(AllocationRound.status != "DRAFT")
        return round_views(db, list(db.scalars(stmt)))


@router.get("/rounds/{round_id}", response_model=RoundOut, tags=["Rodadas"])
def get_round(round_id: UUID, user=Depends(current_user)):
    with SessionFactory() as db:
        r = db.get(AllocationRound, round_id)
        if not r or (r.status == "DRAFT" and user.role != "ADMIN"):
            raise DomainError("ROUND_NOT_FOUND", "Rodada não encontrada.", 404)
        return round_view(db, r)


@router.post("/admin/rounds", response_model=RoundOut, status_code=201, tags=["Administração"])
def create_round(data: RoundInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        return round_view(db, round_service.create_round(db, request, data))


@router.put("/admin/rounds/{round_id}", response_model=RoundOut, tags=["Administração"])
def edit_round(round_id: UUID, data: RoundInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        return round_view(db, round_service.edit_round(db, request, round_id, data))


@router.post("/admin/rounds/{round_id}/transition", response_model=RoundOut, tags=["Administração"])
def transition(round_id: UUID, data: TransitionInput, request: Request, user=Depends(admin)):
    with SessionFactory.begin() as db:
        return round_view(db, round_service.transition(db, request, round_id, data))
