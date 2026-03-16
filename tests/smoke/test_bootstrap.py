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
        browser="firefox",
        headless=True,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
        wait_for_manual_ready=False,
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Las Piedras, la paz Progreso, Colon",
    )
    expected_path = artifact_dir / "marketplace_group_share_ready.png"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_bytes(b"fake-image")

    landing_calls: list[tuple[object, object, object, object]] = []
    marketplace_calls: list[tuple[object, object, object, object, str, str]] = []

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
        lambda page, settings, run_context, logger: landing_calls.append(
            (page, settings, run_context, logger)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            run_id="run-123",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: marketplace_calls.append(
            (page, settings, run_context, logger, listing_title, group_name)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com/marketplace/you/selling",
            run_id="run-123",
            artifact_dir=artifact_dir,
            screenshot_path=expected_path,
        ),
    )

    screenshot_path = run_bootstrap()

    assert len(landing_calls) == 1
    assert landing_calls[0][1] == settings
    assert landing_calls[0][2] == RunContext(run_id="run-123", artifact_dir=artifact_dir)
    assert len(marketplace_calls) == 1
    assert marketplace_calls[0][1] == settings
    assert marketplace_calls[0][2] == RunContext(
        run_id="run-123", artifact_dir=artifact_dir
    )
    assert marketplace_calls[0][4:] == (
        "Botitas de gamuza tipo desert",
        "Las Piedras, la paz Progreso, Colon",
    )
    assert screenshot_path == expected_path
    assert (
        "flow_execution_summary flow_name=landing_flow success=True "
        "step=capture_checkpoint current_url=https://example.com run_id=run-123 "
        f"artifact_dir={artifact_dir} screenshot_path={artifact_dir / 'landing_ready.png'}"
    ) in caplog.text
    assert (
        "flow_execution_summary flow_name=marketplace_group_share_flow success=True "
        "step=capture_checkpoint current_url=https://example.com/marketplace/you/selling "
        f"run_id=run-123 artifact_dir={artifact_dir} screenshot_path={expected_path}"
    ) in caplog.text


def test_bootstrap_waits_for_manual_ready_when_enabled(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-456"
    settings = Settings(
        base_url="https://www.facebook.com",
        browser="firefox",
        headless=False,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="facebook.com",
        wait_for_manual_ready=True,
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Las Piedras, la paz Progreso, Colon",
    )
    page = type("FakePage", (), {"goto_calls": [], "goto": lambda self, url, wait_until: self.goto_calls.append((url, wait_until))})()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(run_id="run-456", artifact_dir=artifact_dir),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com",
            run_id="run-456",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com/marketplace/you/selling",
            run_id="run-456",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "marketplace_group_share_ready.png",
        ),
    )
    prompts: list[str] = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    caplog.set_level(logging.INFO, logger="src.main")

    run_bootstrap()

    assert page.goto_calls == [("https://www.facebook.com", "domcontentloaded")]
    assert prompts == ["Manual login/session ready. Press Enter to continue..."]
    assert "manual_ready_waiting_for_enter" in caplog.text
