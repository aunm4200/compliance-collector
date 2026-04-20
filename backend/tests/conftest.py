"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import Principal, get_principal, require_global_admin
from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def dev_settings(tmp_path: Path) -> Settings:
    """Settings suitable for unit tests (no Entra, local storage)."""
    return Settings(
        environment="dev",
        entra_app_client_id="",  # triggers dev auth bypass
        storage_backend="local",
        storage_local_path=str(tmp_path / "evidence"),
        enable_background_jobs=False,
    )


@pytest.fixture
def admin_principal() -> Principal:
    return Principal(
        subject="sub-1",
        tenant_id="tenant-1",
        object_id="oid-1",
        name="Test Admin",
        email="admin@example.invalid",
        roles=["GlobalAdministrator"],
        raw_claims={},
    )


@pytest.fixture
def client(dev_settings: Settings, admin_principal: Principal) -> Generator[TestClient, None, None]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: dev_settings
    app.dependency_overrides[get_principal] = lambda: admin_principal
    app.dependency_overrides[require_global_admin] = lambda: admin_principal
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
