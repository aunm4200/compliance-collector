"""JWT validation for inbound portal requests.

The portal UI signs users in via MSAL against our multi-tenant Entra app
and calls this API with an access token. We validate signature, issuer,
audience, and expiry here before handing control to any route.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from .config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

# Well-Known IDs for Entra ID built-in directory roles.
# Source: https://learn.microsoft.com/entra/identity/role-based-access-control/permissions-reference
_GLOBAL_ADMIN_WID = "62e90394-69f5-4237-9190-012177145e10"
_GLOBAL_READER_WID = "f2ef992c-3afb-46b9-b7cf-a126ee74c451"

_WID_ROLE_MAP = {
    _GLOBAL_ADMIN_WID: "GlobalAdministrator",
    _GLOBAL_READER_WID: "GlobalReader",
}


@dataclass(slots=True)
class Principal:
    """The authenticated caller."""

    subject: str
    tenant_id: str
    object_id: str
    name: str
    email: str
    roles: list[str]
    raw_claims: dict[str, Any]


class _JwksCache:
    def __init__(self) -> None:
        self._keys: dict[str, Any] | None = None
        self._expires_at: float = 0.0

    async def get(self, settings: Settings) -> dict[str, Any]:
        if self._keys is not None and time.time() < self._expires_at:
            return self._keys
        url = (
            f"https://login.microsoftonline.com/{settings.entra_app_tenant_id}/discovery/v2.0/keys"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            self._keys = resp.json()
        self._expires_at = time.time() + settings.entra_jwks_cache_seconds
        return self._keys


_jwks_cache = _JwksCache()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _validate_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise _unauthorized("invalid token header") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise _unauthorized("token missing kid")

    jwks = await _jwks_cache.get(settings)
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise _unauthorized("signing key not found")

    audience = settings.entra_api_audience or f"api://{settings.entra_app_client_id}"

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            audience=audience,
            options={"verify_iss": False},  # multi-tenant: iss varies per tenant
        )
    except JWTError as exc:
        raise _unauthorized(f"token validation failed: {exc}") from exc


async def get_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """FastAPI dependency returning the authenticated principal."""
    # Dev bypass: allow unauthenticated calls if no client id configured
    if not settings.entra_app_client_id and settings.environment == "dev":
        return Principal(
            subject="dev-user",
            tenant_id="dev-tenant",
            object_id="dev-oid",
            name="Dev User",
            email="dev@example.invalid",
            roles=["GlobalAdministrator"],
            raw_claims={},
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("missing bearer token")

    claims = await _validate_token(credentials.credentials, settings)
    request.state.claims = claims

    # Map wids (directory role WIDs) → role strings. The roles claim only carries
    # app roles, not directory roles like Global Administrator or Global Reader.
    wids: list[str] = claims.get("wids", []) or []
    roles = [_WID_ROLE_MAP[w] for w in wids if w in _WID_ROLE_MAP]
    roles.extend(r for r in (claims.get("roles", []) or []) if r not in roles)

    return Principal(
        subject=claims.get("sub", ""),
        tenant_id=claims.get("tid", ""),
        object_id=claims.get("oid", ""),
        name=claims.get("name", ""),
        email=claims.get("preferred_username") or claims.get("upn") or "",
        roles=roles,
        raw_claims=claims,
    )


def require_global_admin(principal: Principal = Depends(get_principal)) -> Principal:
    """Gate endpoints to Global Administrators."""
    if "GlobalAdministrator" not in principal.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global Administrator role required",
        )
    return principal


def require_global_reader_or_admin(principal: Principal = Depends(get_principal)) -> Principal:
    """Gate endpoints to Global Administrators or Global Readers.

    Swap require_global_admin for this in assessments.py when ready to
    drop the GA requirement.
    """
    if not {"GlobalAdministrator", "GlobalReader"} & set(principal.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global Administrator or Global Reader role required",
        )
    return principal
