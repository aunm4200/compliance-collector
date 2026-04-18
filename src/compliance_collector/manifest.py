"""Evidence manifest generation with SHA-256 hashing.

Every evidence collection run produces a manifest.json listing every file,
its SHA-256 hash, size, and collection timestamp. This gives auditors a
tamper-evident record: any file modification invalidates the hash.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file, streaming to handle large files."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    evidence_dir: Path,
    tenant_id: str,
    run_id: str,
    collector_versions: dict[str, str],
) -> dict[str, Any]:
    """Walk the evidence directory and build a manifest dict.

    Args:
        evidence_dir: The run-specific evidence directory.
        tenant_id: The tenant whose config was collected.
        run_id: A unique ID for this run (usually an ISO timestamp).
        collector_versions: Map of collector name -> version used.
    """
    files: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rel = path.relative_to(evidence_dir)
            files.append(
                {
                    "path": str(rel).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )

    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "tenant_id": tenant_id,
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "collector_versions": collector_versions,
        "file_count": len(files),
        "files": files,
    }


def write_manifest(manifest: dict[str, Any], evidence_dir: Path) -> Path:
    """Write the manifest as pretty JSON."""
    manifest_path = evidence_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path
