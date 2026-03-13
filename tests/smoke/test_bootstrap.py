from __future__ import annotations

import logging
from pathlib import Path

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.main import run_bootstrap


def test_bootstrap_runs_landing_flow(tmp_path, monkeypatch, caplog) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-123"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    expected_path = artifact_dir / "landing_ready.png"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_bytes(b"fake-image")

    calls: list[tuple[object, object, object, object]] = []

    class FakeContextManager:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    caplog.set_level(logging.INFO, logger="src.main")
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(
            run_id="run-123", artifact_dir=artifact_dir
        ),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: calls.append(
            (page, settings, run_context, logger)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            run_id="run-123",
            artifact_dir=artifact_dir,
            screenshot_path=expected_path,
        ),
    )

    screenshot_path = run_bootstrap()

    assert len(calls) == 1
    assert calls[0][1] == settings
    assert calls[0][2] == RunContext(run_id="run-123", artifact_dir=artifact_dir)
    assert screenshot_path == expected_path
    assert (
        "flow_execution_summary flow_name=landing_flow success=True "
        "step=capture_checkpoint current_url=https://example.com run_id=run-123 "
        f"artifact_dir={artifact_dir} screenshot_path={expected_path}"
    ) in caplog.text
