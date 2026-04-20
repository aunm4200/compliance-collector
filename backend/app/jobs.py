"""Background job runner for assessment executions.

Wraps the existing ``compliance_collector`` library: builds a Graph
client via ``graph_auth.build_customer_credential`` and invokes each
collector, streaming results into the configured storage backend.

v0.4 uses FastAPI ``BackgroundTasks`` for in-process execution. v0.5
will replace this with an Azure Queue-triggered worker.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime

import structlog
from compliance_collector.collectors.conditional_access import ConditionalAccessCollector
from compliance_collector.collectors.mfa_registration import MfaRegistrationCollector
from compliance_collector.collectors.privileged_roles import PrivilegedRolesCollector
from compliance_collector.report import render_report
from msgraph import GraphServiceClient

from .config import Settings
from .graph_auth import build_customer_credential
from .models import Assessment, RunStatus
from .storage import EvidenceStorage

log = structlog.get_logger()


def _build_graph_client(settings: Settings, tenant_id: str) -> GraphServiceClient:
    credential = build_customer_credential(settings, tenant_id)
    return GraphServiceClient(
        credentials=credential,
        scopes=["https://graph.microsoft.com/.default"],
    )


async def run_assessment(
    assessment: Assessment,
    settings: Settings,
    storage: EvidenceStorage,
) -> None:
    """Execute the collectors for an assessment and persist results."""
    log.info("assessment.start", assessment_id=assessment.id, tenant_id=assessment.tenant_id)
    assessment.status = RunStatus.RUNNING
    assessment.started_at = datetime.now(UTC)
    storage.save_assessment(assessment)

    run_dir = storage.run_dir(assessment)
    file_count = 0

    try:
        client = _build_graph_client(settings, assessment.tenant_id)
        collectors = [
            ConditionalAccessCollector(client),
            MfaRegistrationCollector(client),
            PrivilegedRolesCollector(client),
        ]
        for collector in collectors:
            try:
                await collector.run(run_dir)
                file_count += 1
                log.info(
                    "collector.ok",
                    assessment_id=assessment.id,
                    collector=collector.name,
                )
            except Exception as exc:
                log.warning(
                    "collector.fail",
                    assessment_id=assessment.id,
                    collector=collector.name,
                    error=str(exc),
                )

        assessment.evidence_file_count = file_count

        # Render HTML report (best-effort — lack of evidence shouldn't fail the run)
        with contextlib.suppress(Exception):
            render_report(
                evidence_dir=run_dir,
                tenant_id=assessment.tenant_id,
                run_id=assessment.id,
                manifest={"frameworks": [f.value for f in assessment.frameworks]},
            )

        assessment.status = RunStatus.SUCCEEDED
    except Exception as exc:
        log.exception("assessment.failed", assessment_id=assessment.id)
        assessment.status = RunStatus.FAILED
        assessment.error_message = str(exc)
    finally:
        assessment.completed_at = datetime.now(UTC)
        storage.save_assessment(assessment)
        log.info("assessment.end", assessment_id=assessment.id, status=assessment.status)
