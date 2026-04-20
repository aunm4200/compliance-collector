"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from . import __version__
from .config import get_settings
from .routers import assessments, auth_router, consent, health, reports


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=level.upper())
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


def create_app() -> FastAPI:
    """Build and configure the FastAPI app."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    app = FastAPI(
        title="Compliance Collector API",
        description="Backend for the compliance-collector web portal.",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log = structlog.get_logger()
        log.exception("unhandled_error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    app.include_router(health.router)
    app.include_router(auth_router.router)
    app.include_router(consent.router)
    app.include_router(assessments.router)
    app.include_router(reports.router)

    return app


app = create_app()
