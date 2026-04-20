"""Build a Microsoft Graph credential for a customer tenant.

Three modes are supported:

* ``mi_fic`` — production. Uses a user-assigned Managed Identity as the
  federated identity credential (FIC) assertion source against our
  multi-tenant Entra app registration. No secrets, no certificates.
* ``secret`` — dev/local only. Uses a client secret stored in settings.
* ``cert`` — backwards compatibility with the v0.3 CLI certificate flow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from azure.identity import (
    CertificateCredential,
    ClientAssertionCredential,
    ClientSecretCredential,
    ManagedIdentityCredential,
)

from .config import Settings


class TokenCredentialLike(Protocol):
    """Minimal protocol matching azure.identity credentials."""

    def get_token(self, *scopes: str) -> object: ...


def _mi_fic_credential(settings: Settings, customer_tenant_id: str) -> ClientAssertionCredential:
    """Build a federated-identity credential.

    The user-assigned managed identity attached to our backend mints tokens
    for ``api://AzureADTokenExchange``. Those tokens are then presented as
    client assertions against our multi-tenant Entra app, which is
    authorized in the customer tenant via admin consent.
    """
    mi = ManagedIdentityCredential(client_id=settings.graph_managed_identity_client_id or None)

    def _assertion() -> str:
        token = mi.get_token(settings.graph_fic_audience)
        return token.token

    return ClientAssertionCredential(
        tenant_id=customer_tenant_id,
        client_id=settings.entra_app_client_id,
        func=_assertion,
    )


def _secret_credential(settings: Settings, customer_tenant_id: str) -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=customer_tenant_id,
        client_id=settings.entra_app_client_id,
        client_secret=settings.graph_client_secret,
    )


def _cert_credential(settings: Settings, customer_tenant_id: str) -> CertificateCredential:
    return CertificateCredential(
        tenant_id=customer_tenant_id,
        client_id=settings.entra_app_client_id,
        certificate_path=str(Path(settings.graph_cert_path)),
    )


def build_customer_credential(settings: Settings, customer_tenant_id: str) -> TokenCredentialLike:
    """Return an appropriate Graph credential for ``customer_tenant_id``."""
    mode = settings.graph_auth_mode
    if mode == "mi_fic":
        return _mi_fic_credential(settings, customer_tenant_id)
    if mode == "secret":
        return _secret_credential(settings, customer_tenant_id)
    if mode == "cert":
        return _cert_credential(settings, customer_tenant_id)
    msg = f"Unknown graph_auth_mode: {mode!r}"
    raise ValueError(msg)
