"""Evidence storage abstraction.

v0.4 ships with a ``LocalStorage`` implementation for development and
container-local deployments. A ``BlobStorage`` backend (Azure Blob
Storage + managed identity) is planned for v0.5.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Assessment


class EvidenceStorage(ABC):
    """Persists assessments, evidence files, and reports."""

    @abstractmethod
    def run_dir(self, assessment: Assessment) -> Path: ...

    @abstractmethod
    def save_assessment(self, assessment: Assessment) -> None: ...

    @abstractmethod
    def load_assessment(self, assessment_id: str) -> Assessment | None: ...

    @abstractmethod
    def list_assessments(self, tenant_id: str) -> list[Assessment]: ...

    @abstractmethod
    def save_json(self, assessment: Assessment, filename: str, payload: dict[str, Any]) -> Path: ...


class LocalStorage(EvidenceStorage):
    """Filesystem-backed storage suitable for dev + single-tenant docker."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # --- helpers ---
    def _tenant_dir(self, tenant_id: str) -> Path:
        tdir = self.root / tenant_id
        tdir.mkdir(parents=True, exist_ok=True)
        return tdir

    def run_dir(self, assessment: Assessment) -> Path:
        rdir = self._tenant_dir(assessment.tenant_id) / assessment.id
        rdir.mkdir(parents=True, exist_ok=True)
        return rdir

    # --- assessments ---
    def save_assessment(self, assessment: Assessment) -> None:
        assessment.updated_at = datetime.now(UTC)
        path = self.run_dir(assessment) / "assessment.json"
        path.write_text(assessment.model_dump_json(indent=2), encoding="utf-8")

    def load_assessment(self, assessment_id: str) -> Assessment | None:
        for tenant_dir in self.root.iterdir():
            if not tenant_dir.is_dir():
                continue
            candidate = tenant_dir / assessment_id / "assessment.json"
            if candidate.exists():
                return Assessment.model_validate_json(candidate.read_text(encoding="utf-8"))
        return None

    def list_assessments(self, tenant_id: str) -> list[Assessment]:
        tdir = self._tenant_dir(tenant_id)
        items: list[Assessment] = []
        for run_dir in sorted(tdir.iterdir(), reverse=True):
            f = run_dir / "assessment.json"
            if f.exists():
                items.append(Assessment.model_validate_json(f.read_text(encoding="utf-8")))
        return items

    # --- evidence ---
    def save_json(self, assessment: Assessment, filename: str, payload: dict[str, Any]) -> Path:
        path = self.run_dir(assessment) / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


def build_storage(backend: str, local_path: str) -> EvidenceStorage:
    """Factory for the configured storage backend."""
    if backend == "local":
        return LocalStorage(local_path)
    msg = f"Storage backend not yet implemented: {backend!r}"
    raise NotImplementedError(msg)
