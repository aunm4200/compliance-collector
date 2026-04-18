"""HTML report generation from collected evidence.

Produces a single-file report.html per run with:
- Collection metadata
- Per-collector summary
- Per-framework control coverage
- Evaluation results (PASS/FAIL/N/A per control)
- Manifest integrity block with SHA-256 hashes
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from compliance_collector.config import Control, load_controls
from compliance_collector.evaluator import evaluate_controls

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_CONTROLS_DIR = Path(__file__).parent / "controls"


def _load_summaries(evidence_dir: Path) -> dict[str, dict[str, Any]]:
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


def _group_by_framework(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item["framework"], []).append(item)
    return grouped


def render_report(
    evidence_dir: Path,
    tenant_id: str,
    run_id: str,
    manifest: dict[str, Any],
) -> Path:
    """Render an HTML report for this evidence run."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")

    summaries = _load_summaries(evidence_dir)

    controls: list[Control] = load_controls(_CONTROLS_DIR)
    evaluations = evaluate_controls(controls, evidence_dir)

    # Per-framework pass/fail counts for header cards
    framework_stats: dict[str, dict[str, int]] = {}
    for e in evaluations:
        fw = framework_stats.setdefault(e["framework"], {"pass": 0, "fail": 0, "na": 0, "total": 0})
        fw["total"] += 1
        if e["status"] == "pass":
            fw["pass"] += 1
        elif e["status"] == "fail":
            fw["fail"] += 1
        else:
            fw["na"] += 1

    evaluations_by_framework = _group_by_framework(evaluations)

    rendered = template.render(
        tenant_id=tenant_id,
        run_id=run_id,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        manifest=manifest,
        summaries=summaries,
        evaluations_by_framework=evaluations_by_framework,
        framework_stats=framework_stats,
    )

    report_path = evidence_dir / "report.html"
    report_path.write_text(rendered, encoding="utf-8")
    return report_path
