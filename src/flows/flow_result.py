from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FlowResult:
    success: bool
    step: str
    current_url: str
    run_id: str
    artifact_dir: Path
    screenshot_path: Path | None
