"""HTML report generation from collected evidence.

Produces a single-file report.html per run with:
- Collection metadata (tenant, run id, timestamp)
- Per-collector summary
- Per-framework control coverage
- Manifest integrity block with SHA-256 hashes
- Links to each evidence JSON file
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from compliance_collector.config import Control, load_controls

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_CONTROLS_DIR = Path(__file__).parent / "controls"


def _load_summaries(evidence_dir: Path) -> dict[str, dict[str, Any]]:
    """Read each collector's JSON file and extract summary + item count."""
    summaries: dict[str, dict[str, Any]] = {}
    for json_file in sorted(evidence_dir.glob("*.json")):
        if json_file.name == "manifest.json":
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries[json_file.stem] = {
            "file": json_file.name,
            "count": data.get("collected_count") or len(data.get("value", []) or []),
            "summary": data.get("summary", {}),
        }
    return summaries


def _group_controls_by_framework(controls: list[Control]) -> dict[str, list[Control]]:
    grouped: dict[str, list[Control]] = {}
    for c in controls:
        grouped.setdefault(c.framework, []).append(c)
    return grouped


def _controls_with_evidence(
    controls: list[Control],
    collector_names: set[str],
) -> list[dict[str, Any]]:
    """For each control, mark which evidence is available in this run."""
    results = []
    for c in controls:
        required = [e.collector for e in c.evidence]
        available = [r for r in required if r in collector_names]
        missing = [r for r in required if r not in collector_names]
        results.append({
            "control_id": c.control_id,
            "framework": c.framework,
            "title": c.title,
            "description": c.description,
            "required_collectors": required,
            "available_collectors": available,
            "missing_collectors": missing,
            "has_all_evidence": len(missing) == 0,
        })
    return results


def render_report(
    evidence_dir: Path,
    tenant_id: str,
    run_id: str,
    manifest: dict[str, Any],
) -> Path:
    """Render an HTML report for this evidence run.

    Returns the path to the generated report.html.
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")

    summaries = _load_summaries(evidence_dir)
    collector_names = set(summaries.keys())

    controls = load_controls(_CONTROLS_DIR)
    control_rows = _controls_with_evidence(controls, collector_names)
    frameworks = _group_controls_by_framework(controls)

    framework_coverage = {
        fw: {
            "total": len(fw_controls),
            "covered": sum(
                1 for row in control_rows
                if row["framework"] == fw and row["has_all_evidence"]
            ),
        }
        for fw, fw_controls in frameworks.items()
    }

    rendered = template.render(
        tenant_id=tenant_id,
        run_id=run_id,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        manifest=manifest,
        summaries=summaries,
        control_rows=control_rows,
        framework_coverage=framework_coverage,
    )

    report_path = evidence_dir / "report.html"
    report_path.write_text(rendered, encoding="utf-8")
    return report_path
