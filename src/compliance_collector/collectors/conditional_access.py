"""Collect all Conditional Access policies from the tenant.

Evidence captured:
- Every CA policy: conditions, grant controls, session controls, state
- Supports: SOC 2 CC6.1, ISO 27001 A.9.4, CIS M365 1.1.x, NIST CSF PR.AC-1

Requires Graph permission: Policy.Read.All
"""

from __future__ import annotations

from typing import Any

from compliance_collector.collectors.base import BaseCollector


class ConditionalAccessCollector(BaseCollector):
    name = "conditional_access_policies"
    version = "0.1.0"

    async def collect(self) -> dict[str, Any]:
        """Fetch all Conditional Access policies from the tenant."""
        response = await self.client.identity.conditional_access.policies.get()

        if response is None or response.value is None:
            return {"value": [], "collected_count": 0}

        # Serialize each policy to a plain dict. The Graph SDK returns typed
        # objects; we call their backing store to get a JSON-friendly form.
        policies = []
        for policy in response.value:
            # Each Graph object has a backing_store that holds raw values
            policies.append({
                "id": policy.id,
                "displayName": policy.display_name,
                "state": policy.state.value if policy.state else None,
                "createdDateTime": str(policy.created_date_time) if policy.created_date_time else None,
                "modifiedDateTime": str(policy.modified_date_time) if policy.modified_date_time else None,
                "conditions": self._serialize(policy.conditions),
                "grantControls": self._serialize(policy.grant_controls),
                "sessionControls": self._serialize(policy.session_controls),
            })

        return {
            "value": policies,
            "collected_count": len(policies),
        }

    @staticmethod
    def _serialize(obj: Any) -> Any:
        """Best-effort serialization of Graph SDK objects to dicts."""
        if obj is None:
            return None
        if hasattr(obj, "__dict__"):
            return {
                k: ConditionalAccessCollector._serialize(v)
                for k, v in obj.__dict__.items()
                if not k.startswith("_") and v is not None
            }
        if isinstance(obj, list):
            return [ConditionalAccessCollector._serialize(i) for i in obj]
        if hasattr(obj, "value") and hasattr(obj, "name"):  # enum
            return obj.value
        return obj
