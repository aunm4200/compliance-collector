"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import __version__
from ..config import Settings, get_settings
from ..models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
def healthz(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
        environment=settings.environment,
    )


@router.get("/readyz", response_model=HealthResponse)
def readyz(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Readiness probe."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
        environment=settings.environment,
    )
