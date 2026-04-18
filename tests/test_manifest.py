"""Tests for manifest generation."""

from __future__ import annotations

import json
from pathlib import Path

from compliance_collector.manifest import build_manifest, sha256_file, write_manifest


def test_sha256_file(tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello world")
    # SHA-256 of "hello world" is a well-known constant
    assert sha256_file(f) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_build_manifest_empty_dir(tmp_path: Path) -> None:
    m = build_manifest(tmp_path, "tenant-abc", "run-1", {})
    assert m["tenant_id"] == "tenant-abc"
    assert m["run_id"] == "run-1"
    assert m["file_count"] == 0
    assert m["files"] == []


def test_build_manifest_with_files(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text('{"x": 1}')
    (tmp_path / "b.json").write_text('{"y": 2}')

    m = build_manifest(tmp_path, "t", "r", {"collector-a": "0.1.0"})
    assert m["file_count"] == 2
    assert m["collector_versions"] == {"collector-a": "0.1.0"}
    paths = {f["path"] for f in m["files"]}
    assert paths == {"a.json", "b.json"}
    for f in m["files"]:
        assert len(f["sha256"]) == 64


def test_write_manifest_roundtrip(tmp_path: Path) -> None:
    (tmp_path / "evidence.json").write_text("{}")
    m = build_manifest(tmp_path, "t", "r", {})
    path = write_manifest(m, tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["tenant_id"] == "t"
