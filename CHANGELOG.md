# Changelog

## [0.2.0] - Unreleased

### Added
- **HTML report** — per-run `report.html` with summary cards, collection results, control coverage, and manifest integrity. Auditor-friendly, single-file, no external dependencies.
- **MFA Registration collector** — pulls the per-user authentication methods registration report with aggregate summary (MFA coverage %, admin MFA coverage %).
- **Expanded CIS M365 control registry** — now 8 controls mapped (up from 4), including SSPR, sign-in frequency, third-party consent, and password policy.
- Tests for report generation.

### Changed
- `collect` command now generates an HTML report by default. Pass `--skip-report` to disable.

## [0.1.0] - Initial release

- First working Conditional Access policy collector
- SHA-256 manifest generation
- CIS M365 control registry (4 controls)
- CLI with Typer + Rich
- Cert-based Graph auth
