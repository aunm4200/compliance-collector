"""Command-line interface for compliance-collector."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from compliance_collector import __version__
from compliance_collector.auth import build_graph_client
from compliance_collector.collectors.conditional_access import ConditionalAccessCollector
from compliance_collector.collectors.mfa_registration import MfaRegistrationCollector
from compliance_collector.manifest import build_manifest, write_manifest
from compliance_collector.report import render_report

app = typer.Typer(
    name="compliance-collector",
    help="Open-source compliance evidence auto-collector for Microsoft 365 and Azure.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show the installed version."""
    console.print(f"compliance-collector v{__version__}")


@app.command()
def collect(
    tenant_id: str = typer.Option(..., "--tenant-id", "-t", help="Entra tenant ID (GUID)."),
    client_id: str = typer.Option(..., "--client-id", "-c", help="App registration client ID."),
    cert_path: Path = typer.Option(..., "--cert-path", "-k", help="Path to PEM certificate file."),
    output: Path = typer.Option(Path("./evidence"), "--output", "-o", help="Output directory."),
    skip_report: bool = typer.Option(False, "--skip-report", help="Skip HTML report generation."),
) -> None:
    """Collect evidence from a Microsoft 365 tenant."""
    if not cert_path.exists():
        console.print(f"[red]ERROR[/red] Certificate not found: {cert_path}")
        raise typer.Exit(code=1)

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold cyan]compliance-collector v{__version__}[/bold cyan]")
    console.print(f"Tenant: {tenant_id}")
    console.print(f"Output: {run_dir}\n")

    client = build_graph_client(tenant_id, client_id, cert_path)

    collectors = [
        ConditionalAccessCollector(client),
        MfaRegistrationCollector(client),
    ]

    results_table = Table(title="Collection Results")
    results_table.add_column("Collector", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Items")

    collector_versions: dict[str, str] = {}

    for c in collectors:
        try:
            count = asyncio.run(c.run(run_dir))
            results_table.add_row(c.name, "OK", str(count))
            collector_versions[c.name] = c.version
        except Exception as exc:
            results_table.add_row(c.name, f"FAIL: {exc}", "-")

    console.print(results_table)

    manifest = build_manifest(run_dir, tenant_id, run_id, collector_versions)
    manifest_path = write_manifest(manifest, run_dir)
    console.print(f"\n[bold green]✓[/bold green] Manifest written: {manifest_path}")
    console.print(f"[bold green]✓[/bold green] {manifest['file_count']} evidence files collected.")

    if not skip_report:
        report_path = render_report(run_dir, tenant_id, run_id, manifest)
        console.print(f"[bold green]✓[/bold green] HTML report: {report_path}")
