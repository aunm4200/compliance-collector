"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Backend settings.

    Loaded from environment variables (and an optional ``.env`` file in dev).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Service metadata ---
    service_name: str = "compliance-collector-backend"
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # --- Entra / auth (inbound: validating JWTs from the portal UI) ---
    entra_app_client_id: str = ""
    entra_app_tenant_id: str = "common"  # "common" = multi-tenant
    entra_api_audience: str = ""  # Usually api://<client_id>
    entra_jwks_cache_seconds: int = 3600

    # --- Graph auth (outbound: calling Microsoft Graph on behalf of customer tenants) ---
    graph_auth_mode: Literal["mi_fic", "secret", "cert"] = "mi_fic"
    graph_managed_identity_client_id: str = ""  # User-assigned MI client ID
    graph_fic_audience: str = "api://AzureADTokenExchange"
    graph_client_secret: str = ""  # dev only
    graph_cert_path: str = ""  # backwards-compat path

    # --- Storage ---
    storage_backend: Literal["local", "blob"] = "local"
    storage_local_path: str = "./evidence_store"
    storage_blob_account_url: str = ""
    storage_blob_container: str = "evidence"

    # --- Feature flags ---
    enable_background_jobs: bool = True

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_cors_allow_origins(cls, value: Any) -> list[str]:
        """Accept JSON arrays, comma-separated strings, or a single origin."""
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ALLOW_ORIGINS JSON value must be an array")
                return [str(origin).strip() for origin in parsed if str(origin).strip()]

            return [origin.strip() for origin in raw.split(",") if origin.strip()]

        return value


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()
