"""Tests for the assessments router."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_list_assessment(client: TestClient) -> None:
    resp = client.post(
        "/assessments",
        json={"frameworks": ["cis-m365", "soc2"], "label": "Quarterly review"},
    )
    assert resp.status_code == 202, resp.text
    created = resp.json()
    assert created["status"] == "queued"
    assert created["tenant_id"] == "tenant-1"
    assert created["label"] == "Quarterly review"
    assert set(created["frameworks"]) == {"cis-m365", "soc2"}

    # List now contains the new assessment
    listing = client.get("/assessments").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == created["id"]

    # Fetch by id
    fetched = client.get(f"/assessments/{created['id']}").json()
    assert fetched["id"] == created["id"]


def test_get_missing_assessment_returns_404(client: TestClient) -> None:
    r = client.get("/assessments/does-not-exist")
    assert r.status_code == 404


def test_create_requires_frameworks(client: TestClient) -> None:
    r = client.post("/assessments", json={"frameworks": []})
    assert r.status_code == 422


def test_report_summary_409_when_not_completed(client: TestClient) -> None:
    created = client.post("/assessments", json={"frameworks": ["cis-m365"]}).json()
    r = client.get(f"/assessments/{created['id']}/report/summary")
    # Background jobs disabled in tests → status stays 'queued'
    assert r.status_code == 409
