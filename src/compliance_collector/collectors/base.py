"""Base collector class that all evidence collectors inherit from."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from msgraph import GraphServiceClient


class BaseCollector(ABC):
    """Abstract base class for all collectors.

    Subclasses must set `name` and `version` class attributes and implement
    `collect()`. The `run()` method handles the file-writing side-effects so
    individual collectors focus purely on fetching data.
    """

    name: str = ""
    version: str = "0.1.0"

    def __init__(self, client: GraphServiceClient) -> None:
        self.client = client

    @abstractmethod
    async def collect(self) -> dict[str, Any]:
        """Fetch evidence from Microsoft Graph and return a serializable dict."""
        ...

    async def run(self, output_dir: Path) -> int:
        """Execute the collector and write results to output_dir.

        Returns the number of top-level items collected (for reporting).
        """
        if not self.name:
            raise ValueError(f"{type(self).__name__} must define a `name` class attribute.")

        data = await self.collect()

        out_path = output_dir / f"{self.name}.json"
        out_path.write_text(
            json.dumps(data, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

        # Count items if the payload has a `value` list (standard Graph shape),
        # else fall back to 1.
        if isinstance(data, dict) and isinstance(data.get("value"), list):
            return len(data["value"])
        return 1
