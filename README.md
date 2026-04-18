# compliance-collector

**Open-source compliance evidence auto-collector for Microsoft 365 and Azure.**

From zero to SOC 2 / ISO 27001 / CIS M365 evidence pack in 10 minutes — no licenses, no SaaS, no vendor lock-in.

---

## What it does

Connects to your Microsoft 365 tenant via read-only Graph API permissions, collects the configuration artifacts auditors actually ask for (Conditional Access policies, MFA coverage, admin activity, sharing settings, DLP rules, etc.), maps each artifact to control IDs across multiple compliance frameworks, and produces a timestamped, tamper-evident evidence pack.

**Supported frameworks (initial):**
- SOC 2 (Trust Services Criteria)
- ISO/IEC 27001:2022
- CIS Microsoft 365 Foundations Benchmark v3
- *Planned:* NIST CSF 2.0, HIPAA Security Rule, Essential 8

## Why

Audit prep for M365 tenants today means weeks of manual screenshots and PowerShell exports. Microsoft's Secure Score and Compliance Manager are good but licensed (E5/Purview), score-focused (not evidence-focused), and don't produce the packs auditors ingest. This tool closes that gap with open source.

## Status

Alpha — expect breaking changes. See [roadmap](#roadmap).

## Quickstart

```bash
# 1. Install
pipx install compliance-collector

# 2. Register an Entra app (see docs/setup.md)

# 3. Run your first collection
compliance-collector collect \
  --tenant-id <your-tenant-id> \
  --client-id <app-client-id> \
  --cert-path ./auth.pem \
  --output ./evidence

# 4. Open the report
open evidence/<timestamp>/report.html
```

## Roadmap

- **v0.1 (MVP):** Conditional Access + identity collectors, CIS M365 mapping, HTML report
- **v0.2:** SOC 2 + ISO 27001 mappings, 15+ collectors
- **v0.3:** Scheduled runs, drift detection
- **v1.0:** Multi-tenant, signed manifests, PDF export
- **v2.0:** Web UI, plugin system

## Contributing

Issues, PRs, and new framework mappings welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
