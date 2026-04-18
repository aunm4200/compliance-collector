"""Configuration loading for controls and framework mappings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

_yaml = YAML(typ="safe")


class ControlEvidence(BaseModel):
    """A single piece of evidence referenced by a control."""

    collector: str = Field(..., description="Dotted collector name, e.g. 'conditional_access.policies'")
    required_fields: list[str] = Field(default_factory=list)


class Control(BaseModel):
    """A compliance control from a framework."""

    control_id: str
    framework: str
    title: str
    description: str = ""
    evidence: list[ControlEvidence]
    pass_criteria: dict[str, Any] = Field(default_factory=dict)


def load_controls(controls_dir: Path) -> list[Control]:
    """Load all YAML control files from a directory.

    Each YAML file is expected to contain a list of controls.
    """
    controls: list[Control] = []
    for yaml_file in sorted(controls_dir.glob("*.yaml")):
        with yaml_file.open("r", encoding="utf-8") as f:
            data = _yaml.load(f) or []
        for item in data:
            controls.append(Control(**item))
    return controls
