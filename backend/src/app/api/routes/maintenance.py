from fastapi import APIRouter, Depends, Request
from pydantic import Field

from app.api.dependencies import admin
from app.api.schemas.common import Input
from app.core.errors import DomainError
from app.db.session import SessionFactory
from app.services.test_cleanup import cleanup, preview_cleanup

router = APIRouter()


class CleanupInput(Input):
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirm_test_data: bool


@router.get("/admin/maintenance/test-data", tags=["Administração"])
def preview(user=Depends(admin)) -> dict:
    with SessionFactory() as db:
        return preview_cleanup(db)


@router.post("/admin/maintenance/test-data/cleanup", tags=["Administração"])
def execute(data: CleanupInput, request: Request, user=Depends(admin)) -> dict:
    if not data.confirm_test_data:
        raise DomainError(
            "CLEANUP_CONFIRMATION_REQUIRED", "Confirme que os dados são descartáveis de teste.", 422
        )
    with SessionFactory.begin() as db:
        return cleanup(db, request, data.fingerprint)
