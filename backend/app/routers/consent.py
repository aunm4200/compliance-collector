"""Admin consent flow endpoints.

The portal UI calls ``GET /consent/url`` to obtain the Microsoft
identity-platform admin-consent URL for the signed-in user's tenant,
and ``POST /consent/callback`` once the admin-consent redirect returns.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import Principal, get_principal, require_global_admin
from ..config import Settings, get_settings
from ..models import ConsentInitResponse, ConsentRecord

router = APIRouter(prefix="/consent", tags=["consent"])

# In-memory state store. Production deployments replace this with
# Cosmos DB or Table Storage keyed by ``state``.
_state_store: dict[str, dict] = {}
_consent_records: dict[str, ConsentRecord] = {}


@router.get("/url", response_model=ConsentInitResponse)
def get_consent_url(
    redirect_uri: str = Query(..., description="UI callback URL registered in Entra."),
    principal: Principal = Depends(require_global_admin),
    settings: Settings = Depends(get_settings),
) -> ConsentInitResponse:
    """Return the admin-consent URL for the caller's tenant."""
    if not settings.entra_app_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="entra_app_client_id is not configured",
        )

    state = secrets.token_urlsafe(24)
    _state_store[state] = {
        "tenant_id": principal.tenant_id,
        "object_id": principal.object_id,
        "created_at": datetime.now(UTC).isoformat(),
    }

    params = {
        "client_id": settings.entra_app_client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    consent_url = (
        f"https://login.microsoftonline.com/{principal.tenant_id}/adminconsent?" + urlencode(params)
    )
    return ConsentInitResponse(consent_url=consent_url, state=state)


@router.post("/callback", response_model=ConsentRecord)
def consent_callback(
    tenant: str = Query(..., description="Tenant ID returned by Entra."),
    state: str = Query(...),
    admin_consent: bool = Query(True),
    principal: Principal = Depends(require_global_admin),
) -> ConsentRecord:
    """Record the result of the admin-consent redirect."""
    pending = _state_store.pop(state, None)
    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="unknown or expired state"
        )
    if pending["tenant_id"] != tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant mismatch")

    record = ConsentRecord(
        tenant_id=tenant,
        consent_granted_at=datetime.now(UTC) if admin_consent else None,
        granted_by_oid=principal.object_id,
        granted_by_name=principal.name,
        scopes=[
            "Policy.Read.All",
            "Directory.Read.All",
            "AuditLog.Read.All",
            "Reports.Read.All",
            "RoleManagement.Read.Directory",
        ],
        status="granted" if admin_consent else "pending",
    )
    _consent_records[tenant] = record
    return record


@router.get("/status", response_model=ConsentRecord)
def consent_status(
    principal: Principal = Depends(get_principal),
) -> ConsentRecord:
    """Return the stored consent record for the caller's tenant."""
    record = _consent_records.get(principal.tenant_id)
    if record is None:
        return ConsentRecord(tenant_id=principal.tenant_id, status="pending")
    return record
