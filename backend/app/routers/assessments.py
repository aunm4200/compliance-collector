"""Assessment orchestration endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..auth import Principal, get_principal, require_global_admin
from ..config import Settings, get_settings
from ..jobs import run_assessment
from ..models import Assessment, AssessmentCreate, AssessmentList, RunStatus
from ..storage import EvidenceStorage, build_storage

router = APIRouter(prefix="/assessments", tags=["assessments"])


def get_storage(settings: Settings = Depends(get_settings)) -> EvidenceStorage:
    return build_storage(settings.storage_backend, settings.storage_local_path)


@router.post("", response_model=Assessment, status_code=status.HTTP_202_ACCEPTED)
async def create_assessment(
    body: AssessmentCreate,
    background: BackgroundTasks,
    principal: Principal = Depends(require_global_admin),
    settings: Settings = Depends(get_settings),
    storage: EvidenceStorage = Depends(get_storage),
) -> Assessment:
    """Queue a new assessment run."""
    now = datetime.now(UTC)
    assessment = Assessment(
        id=uuid.uuid4().hex,
        tenant_id=principal.tenant_id,
        initiated_by_oid=principal.object_id,
        initiated_by_name=principal.name,
        label=body.label,
        frameworks=body.frameworks,
        status=RunStatus.QUEUED,
        created_at=now,
        updated_at=now,
    )
    storage.save_assessment(assessment)

    if settings.enable_background_jobs:
        background.add_task(run_assessment, assessment, settings, storage)

    return assessment


@router.get("", response_model=AssessmentList)
def list_assessments(
    principal: Principal = Depends(get_principal),
    storage: EvidenceStorage = Depends(get_storage),
) -> AssessmentList:
    items = storage.list_assessments(principal.tenant_id)
    return AssessmentList(items=items, total=len(items))


@router.get("/{assessment_id}", response_model=Assessment)
def get_assessment(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    storage: EvidenceStorage = Depends(get_storage),
) -> Assessment:
    assessment = storage.load_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if assessment.tenant_id != principal.tenant_id:
        # Tenant isolation — never leak assessments across tenants.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return assessment
