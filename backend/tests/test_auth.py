"""Tests for the auth router and principal handling."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_me_returns_principal(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Test Admin"
    assert body["tenant_id"] == "tenant-1"
    assert "GlobalAdministrator" in body["roles"]
