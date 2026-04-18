"""Microsoft Graph authentication.

Uses app-only authentication with a certificate. We deliberately avoid client
secrets because certificates are the Microsoft-recommended path for unattended
automation and are easier to rotate safely.
"""

from __future__ import annotations

from pathlib import Path

from azure.identity import CertificateCredential
from msgraph import GraphServiceClient


def build_graph_client(
    tenant_id: str,
    client_id: str,
    cert_path: Path,
) -> GraphServiceClient:
    """Build an authenticated Graph client using certificate credentials.

    Args:
        tenant_id: The Entra tenant ID (GUID).
        client_id: The app registration client ID.
        cert_path: Path to a PEM file containing both the private key and cert.

    Returns:
        An authenticated GraphServiceClient ready to make calls.
    """
    if not cert_path.exists():
        raise FileNotFoundError(f"Certificate not found: {cert_path}")

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_path=str(cert_path),
    )

    # Scopes use the /.default pattern for app-only flows — actual scopes are
    # defined on the app registration, not requested at runtime.
    scopes = ["https://graph.microsoft.com/.default"]

    return GraphServiceClient(credentials=credential, scopes=scopes)
