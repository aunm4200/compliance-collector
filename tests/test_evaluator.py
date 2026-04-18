"""Tests for the control evaluator."""

from __future__ import annotations

import json
from pathlib import Path

from compliance_collector.config import Control, ControlEvidence
from compliance_collector.evaluator import (
    FAIL,
    NOT_APPLICABLE,
    PASS,
    _compare_pct,
    evaluate_control,
)


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_compare_pct_operators() -> None:
    assert _compare_pct(100, ">= 95") is True
    assert _compare_pct(90, ">= 95") is False
    assert _compare_pct(3, "<= 4") is True
    assert _compare_pct(5, "<= 4") is False
    assert _compare_pct(100, "== 100") is True


def test_ca_mfa_all_users_pass(tmp_path: Path) -> None:
    _write(
        tmp_path / "conditional_access_policies.json",
        {
            "value": [
                {
                    "displayName": "Require MFA for All",
                    "state": "enabled",
                    "conditions": {
                        "users": {"includeUsers": ["All"]},
                        "applications": {"includeApplications": ["All"]},
                    },
                    "grantControls": {"builtInControls": ["mfa"]},
                }
            ]
        },
    )
    control = Control(
        control_id="TEST-1",
        framework="TEST",
        title="MFA for All",
        evidence=[ControlEvidence(collector="conditional_access_policies")],
        pass_criteria={"ca_policy_enforces_mfa_for_all_users": True},
    )
    result = evaluate_control(control, tmp_path)
    assert result["status"] == PASS


def test_ca_mfa_all_users_fail_when_disabled(tmp_path: Path) -> None:
    _write(
        tmp_path / "conditional_access_policies.json",
        {
            "value": [
                {
                    "displayName": "Require MFA for All",
                    "state": "disabled",
                    "conditions": {
                        "users": {"includeUsers": ["All"]},
                        "applications": {"includeApplications": ["All"]},
                    },
                    "grantControls": {"builtInControls": ["mfa"]},
                }
            ]
        },
    )
    control = Control(
        control_id="TEST-2",
        framework="TEST",
        title="MFA for All",
        evidence=[ControlEvidence(collector="conditional_access_policies")],
        pass_criteria={"ca_policy_enforces_mfa_for_all_users": True},
    )
    result = evaluate_control(control, tmp_path)
    assert result["status"] == FAIL


def test_not_applicable_when_evidence_missing(tmp_path: Path) -> None:
    control = Control(
        control_id="TEST-3",
        framework="TEST",
        title="MFA coverage",
        evidence=[ControlEvidence(collector="mfa_registration_report")],
        pass_criteria={"mfa_registered_pct": ">= 95"},
    )
    result = evaluate_control(control, tmp_path)
    assert result["status"] == NOT_APPLICABLE


def test_admin_mfa_coverage_threshold(tmp_path: Path) -> None:
    _write(
        tmp_path / "mfa_registration_report.json",
        {
            "value": [],
            "summary": {"admin_mfa_coverage_pct": 100.0},
        },
    )
    control = Control(
        control_id="TEST-4",
        framework="TEST",
        title="Admin MFA",
        evidence=[ControlEvidence(collector="mfa_registration_report")],
        pass_criteria={"admin_mfa_coverage_pct": ">= 100"},
    )
    assert evaluate_control(control, tmp_path)["status"] == PASS


def test_global_admin_count_within_limits(tmp_path: Path) -> None:
    _write(
        tmp_path / "privileged_role_assignments.json",
        {
            "value": [],
            "summary": {"global_admin_count": 3},
        },
    )
    control = Control(
        control_id="TEST-5",
        framework="TEST",
        title="GA count",
        evidence=[ControlEvidence(collector="privileged_role_assignments")],
        pass_criteria={"global_admin_count_within_limits": "<= 4"},
    )
    assert evaluate_control(control, tmp_path)["status"] == PASS
