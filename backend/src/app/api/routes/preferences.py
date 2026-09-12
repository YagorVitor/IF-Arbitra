from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import current_user
from app.api.schemas.preferences import PreferenceOut, PreferencesInput
from app.core.audit import Event, independent
from app.db.session import SessionFactory
from app.services.preferences import save_preferences

router = APIRouter()


@router.put("/sextets/{sextet_id}/preferences", response_model=PreferenceOut, tags=["Preferências"])
def preferences(
    sextet_id: UUID, data: PreferencesInput, request: Request, user=Depends(current_user)
):
    independent(request, Event.PREFERENCE_ATTEMPT, sextet_id, entity_type="SEXTET")
    with SessionFactory.begin() as db:
        submission = save_preferences(db, request, sextet_id, user, data)
        return {"version": submission.version, "submitted_at": submission.submitted_at}
