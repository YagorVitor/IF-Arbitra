from fastapi import APIRouter

from app.api.routes import (
    allocation,
    audit,
    auth,
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
    router.include_router(routes.router)
