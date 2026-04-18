"""Tests for report generation."""

from __future__ import annotations

import json
from pathlib import Path

from compliance_collector.manifest import build_manifest
from compliance_collector.report import render_report


def test_render_report_produces_html(tmp_path: Path) -> None:
    # Seed evidence dir with a plausible collector output
    (tmp_path / "conditional_access_policies.json").write_text(
        json.dumps({"value": [{"id": "a", "displayName": "Require MFA"}], "collected_count": 1})
    )
    manifest = build_manifest(tmp_path, "tenant-x", "run-1", {"conditional_access_policies": "0.1.0"})

    report = render_report(tmp_path, "tenant-x", "run-1", manifest)

    assert report.exists()
    html = report.read_text(encoding="utf-8")
    assert "Compliance Evidence Report" in html
    assert "tenant-x" in html
    assert "conditional_access_policies" in html


def test_render_report_includes_control_coverage(tmp_path: Path) -> None:
    (tmp_path / "conditional_access_policies.json").write_text(
        json.dumps({"value": [], "collected_count": 0})
    )
    manifest = build_manifest(tmp_path, "t", "r", {})
    report = render_report(tmp_path, "t", "r", manifest)
    html = report.read_text(encoding="utf-8")
    # At least one CIS control should appear in the rendered page
    assert "CIS-" in html
    assert "Control Coverage" in html
