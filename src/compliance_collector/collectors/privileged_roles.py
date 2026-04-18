"""Collect all active privileged role assignments.

Evidence captured:
- Every active directory role and its member users/principals
- Summary counts per role (critical for SOC 2 CC6.2 / CC6.3)

Supports: SOC 2 CC6.2, CC6.3; ISO 27001 A.9.2.3; CIS M365 1.1.1; NIST CSF PR.AC-4

Requires Graph permission: RoleManagement.Read.Directory
"""

from __future__ import annotations

from typing import Any

from compliance_collector.collectors.base import BaseCollector

# Built-in role template IDs that CIS/SOC 2 auditors always ask about.
PRIVILEGED_ROLE_NAMES = {
    "Global Administrator",
    "Privileged Role Administrator",
    "Privileged Authentication Administrator",
    "User Administrator",
    "Exchange Administrator",
    "SharePoint Administrator",
    "Intune Administrator",
    "Conditional Access Administrator",
    "Security Administrator",
    "Application Administrator",
    "Cloud Application Administrator",
    "Billing Administrator",
    "Helpdesk Administrator",
}


class PrivilegedRolesCollector(BaseCollector):
    name = "privileged_role_assignments"
    version = "0.1.0"

    async def collect(self) -> dict[str, Any]:
        """Fetch directory role assignments with member details."""
        roles_resp = await self.client.directory_roles.get()
        if roles_resp is None or roles_resp.value is None:
            return {"value": [], "collected_count": 0, "summary": {}}

        assignments: list[dict[str, Any]] = []
        for role in roles_resp.value:
            members_resp = await self.client.directory_roles.by_directory_role_id(
                role.id
            ).members.get()
            members = []
            if members_resp and members_resp.value:
                for m in members_resp.value:
                    members.append(
                        {
                            "id": getattr(m, "id", None),
                            "displayName": getattr(m, "display_name", None),
                            "userPrincipalName": getattr(m, "user_principal_name", None),
                            "type": type(m).__name__,
                        }
                    )
            assignments.append(
                {
                    "roleId": role.id,
                    "displayName": role.display_name,
                    "description": role.description,
                    "roleTemplateId": role.role_template_id,
                    "memberCount": len(members),
                    "members": members,
                }
            )

        # Summary for the auditor at a glance
        by_role = {a["displayName"]: a["memberCount"] for a in assignments}
        global_admin_count = by_role.get("Global Administrator", 0)
        privileged_total = sum(
            count for name, count in by_role.items() if name in PRIVILEGED_ROLE_NAMES
        )

        summary = {
            "total_roles_with_members": len(assignments),
            "global_admin_count": global_admin_count,
            "privileged_assignment_count": privileged_total,
            "members_per_role": by_role,
        }

        return {
            "value": assignments,
            "collected_count": len(assignments),
            "summary": summary,
        }
