"""Routes that expose information about the current principal."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import Principal, get_principal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def get_me(principal: Principal = Depends(get_principal)) -> dict:
    """Return a sanitized view of the current user."""
    return {
        "subject": principal.subject,
        "tenant_id": principal.tenant_id,
        "object_id": principal.object_id,
        "name": principal.name,
        "email": principal.email,
        "roles": principal.roles,
    }
