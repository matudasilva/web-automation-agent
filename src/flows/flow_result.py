from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FlowResult:
    success: bool
    step: str
    current_url: str
    screenshot_path: Path | None
