"""Report retrieval endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from compliance_collector.config import Control, load_controls
from compliance_collector.evaluator import evaluate_controls
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..auth import Principal, get_principal
from ..config import Settings, get_settings
from ..models import ControlFinding, ReportSummary, RunStatus
from ..storage import EvidenceStorage, build_storage

router = APIRouter(prefix="/assessments/{assessment_id}/report", tags=["reports"])


def _resolve_controls_dir() -> Path:
    """Find the bundled controls directory, whether installed or in-tree."""
    import compliance_collector as _cc

    pkg_dir = Path(_cc.__file__).parent / "controls"
    if pkg_dir.exists():
        return pkg_dir
    repo_dir = Path(__file__).resolve().parents[3] / "src" / "compliance_collector" / "controls"
    return repo_dir


_CONTROLS_DIR = _resolve_controls_dir()


def get_storage(settings: Settings = Depends(get_settings)) -> EvidenceStorage:
    return build_storage(settings.storage_backend, settings.storage_local_path)


def _filter_controls(controls: list[Control], frameworks: list[str]) -> list[Control]:
    wanted = {f.lower() for f in frameworks}
    return [c for c in controls if c.framework.lower() in wanted]


_STATUS_MAP = {"pass": "pass", "fail": "fail", "not_applicable": "na"}


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

    evidence_dir = storage.run_dir(assessment)
    all_controls = load_controls(_CONTROLS_DIR)
    controls = _filter_controls(all_controls, [f.value for f in assessment.frameworks])
    evaluations = evaluate_controls(controls, evidence_dir)

    totals = {"pass": 0, "fail": 0, "na": 0, "error": 0}
    per_framework: dict[str, dict[str, int]] = {}
    findings: list[ControlFinding] = []

    for e in evaluations:
        bucket = _STATUS_MAP.get(e["status"], "error")
        totals[bucket] += 1

        fw = per_framework.setdefault(e["framework"], {"pass": 0, "fail": 0, "na": 0, "error": 0})
        fw[bucket] += 1

        finding_status = (
            e["status"] if e["status"] in {"pass", "fail", "not_applicable"} else "error"
        )
        findings.append(
            ControlFinding(
                control_id=e["control_id"],
                framework=e["framework"],
                title=e["title"],
                status=finding_status,  # type: ignore[arg-type]
                reasons=[r["reason"] for r in e.get("rule_results", [])],
            )
        )

    return ReportSummary(
        assessment_id=assessment.id,
        tenant_id=assessment.tenant_id,
        generated_at=assessment.completed_at or datetime.now(UTC),
        totals=totals,
        per_framework=per_framework,
        findings=findings,
        html_report_url=f"/assessments/{assessment.id}/report/html",
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
