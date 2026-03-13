from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class RunContext:
    run_id: str
    artifact_dir: Path


def create_run_context(
    artifact_base_dir: Path, run_id: str | None = None
) -> RunContext:
    resolved_run_id = run_id or uuid4().hex[:12]
    artifact_dir = artifact_base_dir / resolved_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(run_id=resolved_run_id, artifact_dir=artifact_dir)
