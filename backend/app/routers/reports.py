"""Report retrieval endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..auth import Principal, get_principal
from ..config import Settings, get_settings
from ..models import ReportSummary, RunStatus
from ..storage import EvidenceStorage, build_storage

router = APIRouter(prefix="/assessments/{assessment_id}/report", tags=["reports"])


def get_storage(settings: Settings = Depends(get_settings)) -> EvidenceStorage:
    return build_storage(settings.storage_backend, settings.storage_local_path)


@router.get("/summary", response_model=ReportSummary)
def report_summary(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    storage: EvidenceStorage = Depends(get_storage),
) -> ReportSummary:
    assessment = storage.load_assessment(assessment_id)
    if assessment is None or assessment.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if assessment.status != RunStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"assessment is {assessment.status}",
        )

    # Minimal stub — the evaluator integration lands in v0.5.
    return ReportSummary(
        assessment_id=assessment.id,
        tenant_id=assessment.tenant_id,
        generated_at=assessment.completed_at or datetime.now(UTC),
        totals={"pass": 0, "fail": 0, "na": 0, "error": 0},
        per_framework={},
        findings=[],
    )


@router.get("/html")
def report_html(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    storage: EvidenceStorage = Depends(get_storage),
) -> FileResponse:
    assessment = storage.load_assessment(assessment_id)
    if assessment is None or assessment.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    html_path = storage.run_dir(assessment) / "report.html"
    if not html_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="report not yet generated"
        )
    return FileResponse(html_path, media_type="text/html")
