# Changelog

## [0.3.0] - Unreleased

### Added
- **Control evaluator** — rule-based pass/fail engine. Each `pass_criteria` key maps to a Python rule function; results aggregate to PASS / FAIL / NOT_APPLICABLE per control.
- **Privileged Roles collector** — pulls every active directory role and its members, with summary counts (Global Admins, privileged assignments). Supports SOC 2 CC6.2/CC6.3.
- **SOC 2 control registry** — 6 Trust Services Criteria mapped to existing evidence (CC6.1, CC6.2, CC6.3, CC6.6, CC6.7, CC7.2). Demonstrates "collect once, map many."
- **Enhanced HTML report** — per-framework pass/fail tables with rule-level reasons for each finding.
- Tests for evaluator and each rule implementation.

### Changed
- Report now shows per-framework coverage cards (pass / fail / n/a counts) instead of "evidence collected" status.
- `collect` command runs the evaluator automatically after collection; results embedded in the HTML report.

### Graph Permissions (new)
- `RoleManagement.Read.Directory` (required for privileged roles collector)

## [0.2.0]

### Added
- HTML report with summary cards and control coverage
- MFA Registration collector
- Expanded CIS M365 control registry (4 → 8)

### Changed
- `collect` generates HTML report by default

## [0.1.0] - Initial release
- Conditional Access policy collector
- SHA-256 manifest
- CIS M365 registry (4 controls)
- Typer + Rich CLI
- Cert-based Graph auth
