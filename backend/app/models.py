"""Pydantic API models for the backend."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    """Lifecycle states for an assessment run."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class Framework(StrEnum):
    """Supported compliance frameworks."""

    CIS_M365 = "cis-m365"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST_CSF = "nist-csf"
    HIPAA = "hipaa"


class AssessmentCreate(BaseModel):
    """Request body to start a new assessment."""

    frameworks: list[Framework] = Field(
        ..., min_length=1, description="Frameworks to evaluate against."
    )
    label: str | None = Field(default=None, max_length=200)


class Assessment(BaseModel):
    """An assessment run."""

    id: str
    tenant_id: str
    initiated_by_oid: str
    initiated_by_name: str
    label: str | None = None
    frameworks: list[Framework]
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    evidence_file_count: int = 0
    error_message: str | None = None


class AssessmentList(BaseModel):
    items: list[Assessment]
    total: int


class ControlFinding(BaseModel):
    """Per-control pass/fail result embedded in a report summary."""

    control_id: str
    framework: str
    title: str
    status: Literal["pass", "fail", "not_applicable", "error"]
    reasons: list[str] = Field(default_factory=list)


class ReportSummary(BaseModel):
    """High-level summary for a completed assessment."""

    assessment_id: str
    tenant_id: str
    generated_at: datetime
    totals: dict[str, int]  # {"pass": n, "fail": n, "na": n, "error": n}
    per_framework: dict[str, dict[str, int]]
    findings: list[ControlFinding]
    html_report_url: str | None = None
    manifest_url: str | None = None


class ConsentRecord(BaseModel):
    """Tracks admin consent state for a customer tenant."""

    tenant_id: str
    consent_granted_at: datetime | None = None
    granted_by_oid: str | None = None
    granted_by_name: str | None = None
    scopes: list[str] = Field(default_factory=list)
    status: Literal["pending", "granted", "revoked"] = "pending"


class ConsentInitResponse(BaseModel):
    """Response for ``GET /consent/url``."""

    consent_url: str
    state: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
