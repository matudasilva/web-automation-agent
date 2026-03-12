from __future__ import annotations

from pathlib import Path

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.main import run_bootstrap


def test_bootstrap_runs_landing_flow(tmp_path, monkeypatch) -> None:
    screenshot_dir = tmp_path / "screenshots"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    expected_path = screenshot_dir / "landing_ready.png"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_bytes(b"fake-image")

    calls: list[tuple[object, object, object]] = []

    class FakeContextManager:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, logger: calls.append((page, settings, logger))
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            screenshot_path=expected_path,
        ),
    )

    screenshot_path = run_bootstrap()

    assert len(calls) == 1
    assert calls[0][1] == settings
    assert screenshot_path == expected_path
