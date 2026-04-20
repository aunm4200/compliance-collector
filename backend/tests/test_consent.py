"""Tests for the consent flow."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings, get_settings


def test_consent_url_requires_client_id(client: TestClient) -> None:
    # dev_settings has no entra_app_client_id → endpoint should 500
    r = client.get("/consent/url", params={"redirect_uri": "http://localhost:3000/cb"})
    assert r.status_code == 500


def test_consent_url_returns_link(client: TestClient, dev_settings: Settings) -> None:
    dev_settings.entra_app_client_id = "00000000-0000-0000-0000-000000000000"
    client.app.dependency_overrides[get_settings] = lambda: dev_settings

    r = client.get("/consent/url", params={"redirect_uri": "http://localhost:3000/cb"})
    assert r.status_code == 200
    body = r.json()
    assert "adminconsent" in body["consent_url"]
    assert body["state"]


def test_consent_status_defaults_to_pending(client: TestClient) -> None:
    r = client.get("/consent/status")
    assert r.status_code == 200
    body = r.json()
    assert body["tenant_id"] == "tenant-1"
    assert body["status"] == "pending"
