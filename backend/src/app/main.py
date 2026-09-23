"""Compose the HTTP application; business rules live in their own modules."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.middleware import request_context
from app.api.router import router
from app.api.routes.health import router as health_router
from app.api.schemas.common import ErrorOut
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    yield
    engine.dispose()


def create_app():
    app = FastAPI(
        title="IF-Arbitra",
        version="1.0.0",
        lifespan=lifespan,
        responses={
            code: {"model": ErrorOut}
            for code in [400, 401, 403, 404, 405, 409, 413, 422, 429, 500, 503]
        },
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings().frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    app.middleware("http")(request_context)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(router, prefix="/api")
    return app


app = create_app()
