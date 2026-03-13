from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.flows.target_flow import run_target_flow


def test_target_flow_runs_non_destructive_interaction_and_screenshots(tmp_path) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-target"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(run_id="run-target", artifact_dir=artifact_dir)

    class FakePage:
        def __init__(self) -> None:
            self.url = "about:blank"
            self.goto_calls: list[tuple[str, str]] = []
            self.load_states: list[str] = []
            self.screenshot_path: str | None = None

        def goto(self, url: str, wait_until: str) -> None:
            self.goto_calls.append((url, wait_until))
            self.url = url

        def wait_for_load_state(self, state: str) -> None:
            self.load_states.append(state)

        def screenshot(self, path: str, full_page: bool) -> None:
            self.screenshot_path = path
            Path(path).write_bytes(b"fake-image")
            assert full_page is True

    page = FakePage()
    logger = logging.getLogger("test.target_flow")
    calls: list[tuple[str, str | None]] = []

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.target_page.assert_visible",
            lambda page, selector: calls.append(("assert_visible", selector)),
        )
        monkeypatch.setattr(
            "src.pages.target_page.fill_visible",
            lambda page, selector, value: calls.append((selector, value)),
        )

        result = run_target_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            input_value="preview",
        )

    assert page.goto_calls == [("https://example.com", "domcontentloaded")]
    assert page.load_states == ["domcontentloaded", "load"]
    assert calls == [
        ("assert_visible", "[data-testid='target-content']"),
        ("[data-testid='target-input']", "preview"),
    ]
    assert result == FlowResult(
        success=True,
        step="capture_checkpoint",
        current_url="https://example.com",
        run_id="run-target",
        artifact_dir=artifact_dir,
        screenshot_path=artifact_dir / "target_ready.png",
    )
    assert page.screenshot_path == str(result.screenshot_path)
    assert result.screenshot_path is not None
    assert result.screenshot_path.exists()


def test_target_flow_captures_failure_evidence_after_navigation(tmp_path, caplog) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-target-failure"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-target-failure", artifact_dir=artifact_dir
    )

    class ExpectedFlowError(RuntimeError):
        pass

    class FakePage:
        def __init__(self) -> None:
            self.url = "about:blank"
            self.goto_calls: list[tuple[str, str]] = []
            self.load_states: list[str] = []
            self.screenshot_paths: list[str] = []

        def goto(self, url: str, wait_until: str) -> None:
            self.goto_calls.append((url, wait_until))
            self.url = url

        def wait_for_load_state(self, state: str) -> None:
            self.load_states.append(state)

        def screenshot(self, path: str, full_page: bool) -> None:
            self.screenshot_paths.append(path)
            Path(path).write_bytes(b"fake-image")
            assert full_page is True

    page = FakePage()
    logger = logging.getLogger("test.target_flow.failure")

    def fail_assert_content_visible(*args, **kwargs) -> None:
        raise ExpectedFlowError("content missing")

    caplog.set_level(logging.ERROR, logger=logger.name)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.assert_content_visible",
            fail_assert_content_visible,
        )

        with pytest.raises(ExpectedFlowError, match="content missing"):
            run_target_flow(
                page=page,
                settings=settings,
                run_context=run_context,
                logger=logger,
            )

    assert page.goto_calls == [("https://example.com", "domcontentloaded")]
    assert page.load_states == ["domcontentloaded", "load"]
    assert page.screenshot_paths == [str(artifact_dir / "target_failure.png")]
    assert (artifact_dir / "target_failure.png").exists()
    assert "target_flow_failed step=assert_content_visible" in caplog.text
