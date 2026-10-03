from fastapi import APIRouter

from app.api.routes import (
    allocation,
    audit,
    auth,
    maintenance,
    preferences,
    reservations,
    rounds,
    sextets,
    staff,
    students,
)

router = APIRouter()
for routes in (
    auth,
    students,
    staff,
    rounds,
    sextets,
    preferences,
    allocation,
    audit,
    reservations,
):
    # Maintenance endpoints use the same administrator authorization boundary.
    router.include_router(routes.router)
router.include_router(maintenance.router)
