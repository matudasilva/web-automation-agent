from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.flows.target_continuation_flow import run_target_continuation_flow


def test_target_continuation_flow_runs_from_current_page_and_screenshots(
    tmp_path,
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-target-continuation"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-target-continuation", artifact_dir=artifact_dir
    )

    class FakePage:
        def __init__(self) -> None:
            self.url = "https://example.com/current"
            self.load_states: list[str] = []
            self.screenshot_path: str | None = None

        def wait_for_load_state(self, state: str) -> None:
            self.load_states.append(state)

        def screenshot(self, path: str, full_page: bool) -> None:
            self.screenshot_path = path
            Path(path).write_bytes(b"fake-image")
            assert full_page is True

    page = FakePage()
    logger = logging.getLogger("test.target_continuation_flow")
    calls: list[tuple[str, str | None]] = []

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.assert_content_visible",
            lambda self: calls.append(("assert_content_visible", None)),
        )
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.open_item_secondary_action",
            lambda self, text=None, item_selector=None: calls.append(
                ("open_item_secondary_action", text or item_selector)
            ),
        )
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.assert_next_state_visible",
            lambda self: calls.append(("assert_next_state_visible", None)),
        )

        result = run_target_continuation_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            item_text="Sample Item",
        )

    assert page.load_states == ["domcontentloaded", "load"]
    assert calls == [
        ("assert_content_visible", None),
        ("open_item_secondary_action", "Sample Item"),
        ("assert_next_state_visible", None),
    ]
    assert result == FlowResult(
        success=True,
        step="capture_checkpoint",
        current_url="https://example.com/current",
        run_id="run-target-continuation",
        artifact_dir=artifact_dir,
        screenshot_path=artifact_dir / "target_continuation_ready.png",
    )
    assert result.screenshot_path is not None
    assert result.screenshot_path.exists()


def test_target_continuation_flow_captures_failure_evidence(tmp_path, caplog) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-target-continuation-failure"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-target-continuation-failure", artifact_dir=artifact_dir
    )

    class ExpectedFlowError(RuntimeError):
        pass

    class FakePage:
        def __init__(self) -> None:
            self.url = "https://example.com/current"
            self.load_states: list[str] = []
            self.screenshot_paths: list[str] = []

        def wait_for_load_state(self, state: str) -> None:
            self.load_states.append(state)

        def screenshot(self, path: str, full_page: bool) -> None:
            self.screenshot_paths.append(path)
            Path(path).write_bytes(b"fake-image")
            assert full_page is True

    page = FakePage()
    logger = logging.getLogger("test.target_continuation_flow.failure")

    def fail_assert_next_state_visible(*args, **kwargs) -> None:
        raise ExpectedFlowError("next state missing")

    caplog.set_level(logging.ERROR, logger=logger.name)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.assert_content_visible",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.open_item_secondary_action",
            lambda self, text=None, item_selector=None: None,
        )
        monkeypatch.setattr(
            "src.pages.target_page.TargetPage.assert_next_state_visible",
            fail_assert_next_state_visible,
        )

        with pytest.raises(ExpectedFlowError, match="next state missing"):
            run_target_continuation_flow(
                page=page,
                settings=settings,
                run_context=run_context,
                logger=logger,
                item_selector="[data-testid='item-row']",
            )

    assert page.load_states == ["domcontentloaded", "load"]
    assert page.screenshot_paths == [
        str(artifact_dir / "target_continuation_failure.png")
    ]
    assert (artifact_dir / "target_continuation_failure.png").exists()
    assert "target_continuation_flow_failed step=assert_next_state_visible" in caplog.text
