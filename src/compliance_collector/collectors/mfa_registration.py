"""Collect the MFA/authentication methods registration report.

Evidence captured:
- Per-user registration state for strong authentication methods
- Default MFA method, registered methods, and whether MFA-capable

Supports: SOC 2 CC6.1, ISO 27001 A.9.4.2, CIS M365 1.1.3, NIST CSF PR.AC-7

Requires Graph permission: AuditLog.Read.All + UserAuthenticationMethod.Read.All
(Reports.Read.All also works for the reports beta endpoint.)
"""

from __future__ import annotations

from typing import Any

from compliance_collector.collectors.base import BaseCollector


class MfaRegistrationCollector(BaseCollector):
    name = "mfa_registration_report"
    version = "0.1.0"

    async def collect(self) -> dict[str, Any]:
        """Fetch the per-user MFA registration report.

        Uses Graph's userRegistrationDetails endpoint which returns one row
        per user showing registered methods and MFA capability.
        """
        response = await self.client.reports.authentication_methods.user_registration_details.get()

        if response is None or response.value is None:
            return {"value": [], "collected_count": 0, "summary": {}}

        users: list[dict[str, Any]] = []
        for u in response.value:
            users.append({
                "id": u.id,
                "userPrincipalName": u.user_principal_name,
                "userDisplayName": u.user_display_name,
                "isAdmin": u.is_admin,
                "isMfaCapable": u.is_mfa_capable,
                "isMfaRegistered": u.is_mfa_registered,
                "isPasswordlessCapable": u.is_passwordless_capable,
                "defaultMfaMethod": u.default_mfa_method.value if u.default_mfa_method else None,
                "methodsRegistered": [m for m in (u.methods_registered or [])],
                "lastUpdatedDateTime": str(u.last_updated_date_time) if u.last_updated_date_time else None,
            })

        # Compute a small summary for quick auditor consumption
        total = len(users)
        mfa_registered = sum(1 for u in users if u["isMfaRegistered"])
        admins = [u for u in users if u["isAdmin"]]
        admin_mfa_registered = sum(1 for u in admins if u["isMfaRegistered"])

        summary = {
            "total_users": total,
            "mfa_registered_users": mfa_registered,
            "mfa_registered_pct": round(100 * mfa_registered / total, 2) if total else 0,
            "total_admins": len(admins),
            "admin_mfa_registered": admin_mfa_registered,
            "admin_mfa_coverage_pct": round(100 * admin_mfa_registered / len(admins), 2) if admins else 0,
        }

        return {
            "value": users,
            "collected_count": total,
            "summary": summary,
        }
