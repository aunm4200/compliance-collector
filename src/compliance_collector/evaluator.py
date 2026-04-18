"""Control evaluation engine.

Reads `pass_criteria` from each control and runs named rule functions against
the collected evidence. Produces PASS / FAIL / NOT_APPLICABLE per control.

Rules are registered with the @rule decorator. To add a new control check,
just write a function decorated with @rule("criterion_name") — no framework
changes needed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from compliance_collector.config import Control

RuleFn = Callable[[Path, Any], tuple[str, str]]
RULES: dict[str, RuleFn] = {}

PASS = "pass"
FAIL = "fail"
NOT_APPLICABLE = "not_applicable"
ERROR = "error"


def rule(name: str) -> Callable[[RuleFn], RuleFn]:
    """Register a function as an evaluation rule for a pass_criteria key."""

    def decorator(fn: RuleFn) -> RuleFn:
        RULES[name] = fn
        return fn

    return decorator


def _load(evidence_dir: Path, filename: str) -> dict[str, Any] | None:
    path = evidence_dir / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _compare_pct(actual: float, expected: str) -> bool:
    """Compare a percentage against an expression like '>= 100' or '> 90'."""
    m = re.match(r"\s*(>=|<=|==|>|<)\s*(\d+(?:\.\d+)?)\s*$", expected)
    if not m:
        return False
    op, val = m.group(1), float(m.group(2))
    return {
        ">=": actual >= val,
        "<=": actual <= val,
        "==": actual == val,
        ">": actual > val,
        "<": actual < val,
    }[op]


# -------- Rule implementations --------


@rule("ca_policy_enforces_mfa_for_all_users")
def _ca_mfa_all_users(evidence_dir: Path, _expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "conditional_access_policies.json")
    if data is None:
        return NOT_APPLICABLE, "Conditional Access evidence not available."
    for p in data.get("value", []):
        if p.get("state") != "enabled":
            continue
        users = (p.get("conditions") or {}).get("users") or {}
        apps = (p.get("conditions") or {}).get("applications") or {}
        grant = p.get("grantControls") or {}
        if (
            "All" in (users.get("includeUsers") or [])
            and "All" in (apps.get("includeApplications") or [])
            and "mfa" in (grant.get("builtInControls") or [])
        ):
            return PASS, f"Policy '{p.get('displayName')}' enforces MFA for all users & apps."
    return FAIL, "No enabled CA policy enforces MFA for all users across all apps."


@rule("ca_policy_enforces_mfa_for_admins")
def _ca_mfa_admins(evidence_dir: Path, _expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "conditional_access_policies.json")
    if data is None:
        return NOT_APPLICABLE, "Conditional Access evidence not available."
    for p in data.get("value", []):
        if p.get("state") != "enabled":
            continue
        users = (p.get("conditions") or {}).get("users") or {}
        grant = p.get("grantControls") or {}
        if (users.get("includeRoles") or []) and "mfa" in (grant.get("builtInControls") or []):
            return PASS, f"Policy '{p.get('displayName')}' requires MFA for admin roles."
    return FAIL, "No enabled CA policy enforces MFA for directory roles."


@rule("ca_policy_enforces_sign_in_frequency")
def _ca_sign_in_freq(evidence_dir: Path, _expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "conditional_access_policies.json")
    if data is None:
        return NOT_APPLICABLE, "Conditional Access evidence not available."
    for p in data.get("value", []):
        if p.get("state") != "enabled":
            continue
        session = p.get("sessionControls") or {}
        if session.get("signInFrequency") or {}:
            return PASS, f"Policy '{p.get('displayName')}' configures sign-in frequency."
    return FAIL, "No enabled CA policy configures sign-in frequency."


@rule("admin_mfa_coverage_pct")
def _admin_mfa_coverage(evidence_dir: Path, expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "mfa_registration_report.json")
    if data is None:
        return NOT_APPLICABLE, "MFA registration evidence not available."
    summary = data.get("summary") or {}
    actual = summary.get("admin_mfa_coverage_pct")
    if actual is None:
        return NOT_APPLICABLE, "Admin MFA coverage not in summary."
    if _compare_pct(actual, str(expected)):
        return PASS, f"Admin MFA coverage {actual}% satisfies '{expected}'."
    return FAIL, f"Admin MFA coverage {actual}% does not satisfy '{expected}'."


@rule("mfa_registered_pct")
def _mfa_coverage(evidence_dir: Path, expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "mfa_registration_report.json")
    if data is None:
        return NOT_APPLICABLE, "MFA registration evidence not available."
    summary = data.get("summary") or {}
    actual = summary.get("mfa_registered_pct")
    if actual is None:
        return NOT_APPLICABLE, "MFA coverage not in summary."
    if _compare_pct(actual, str(expected)):
        return PASS, f"MFA coverage {actual}% satisfies '{expected}'."
    return FAIL, f"MFA coverage {actual}% does not satisfy '{expected}'."


@rule("global_admin_count_within_limits")
def _ga_count(evidence_dir: Path, expected: Any) -> tuple[str, str]:
    data = _load(evidence_dir, "privileged_role_assignments.json")
    if data is None:
        return NOT_APPLICABLE, "Privileged roles evidence not available."
    summary = data.get("summary") or {}
    actual = summary.get("global_admin_count", 0)
    if _compare_pct(actual, str(expected)):
        return PASS, f"Global admin count {actual} satisfies '{expected}'."
    return FAIL, f"Global admin count {actual} does not satisfy '{expected}' (CIS recommends 2–4)."


# -------- Evaluator --------


def evaluate_control(control: Control, evidence_dir: Path) -> dict[str, Any]:
    """Run all rules in a control's pass_criteria and aggregate the status."""
    rule_results = []
    for criterion, expected in (control.pass_criteria or {}).items():
        fn = RULES.get(criterion)
        if fn is None:
            rule_results.append(
                {
                    "criterion": criterion,
                    "status": NOT_APPLICABLE,
                    "reason": f"No rule implemented for '{criterion}'.",
                }
            )
            continue
        try:
            status, reason = fn(evidence_dir, expected)
        except Exception as exc:
            status, reason = ERROR, f"Rule raised: {exc}"
        rule_results.append({"criterion": criterion, "status": status, "reason": reason})

    # Aggregate: any FAIL/ERROR => FAIL; any PASS (and no failures) => PASS; else NOT_APPLICABLE
    statuses = {r["status"] for r in rule_results}
    if FAIL in statuses or ERROR in statuses:
        overall = FAIL
    elif PASS in statuses:
        overall = PASS
    else:
        overall = NOT_APPLICABLE

    return {
        "control_id": control.control_id,
        "framework": control.framework,
        "title": control.title,
        "status": overall,
        "rule_results": rule_results,
    }


def evaluate_controls(controls: list[Control], evidence_dir: Path) -> list[dict[str, Any]]:
    """Evaluate a list of controls against collected evidence."""
    return [evaluate_control(c, evidence_dir) for c in controls]
