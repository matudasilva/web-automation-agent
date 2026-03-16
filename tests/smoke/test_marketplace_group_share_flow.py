from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.marketplace_group_share_flow import run_marketplace_group_share_flow
from src.flows.run_context import RunContext


def test_marketplace_group_share_flow_runs_safe_group_share_path(tmp_path) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-marketplace-group-share"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-marketplace-group-share", artifact_dir=artifact_dir
    )

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
    logger = logging.getLogger("test.marketplace_group_share_flow")
    calls: list[tuple[str, str | None]] = []

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_marketplace_selling_loaded",
            lambda self, base_url, allowed_domain: calls.append(
                ("assert_marketplace_selling_loaded", None)
            ),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_listing_share_dialog",
            lambda self, listing_title, logger=None: calls.append(
                ("open_listing_share_dialog", listing_title)
            ),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_share_dialog_visible",
            lambda self: calls.append(("assert_share_dialog_visible", None)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_group_destination",
            lambda self: calls.append(("open_group_destination", None)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_picker_visible",
            lambda self, timeout_ms=5000: calls.append(
                ("assert_group_picker_visible", str(timeout_ms))
            ),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.select_group",
            lambda self, group_name: calls.append(("select_group", group_name)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_composer_content_ready",
            lambda self, listing_title: calls.append(
                ("assert_group_composer_content_ready", listing_title)
            ),
        )

        result = run_marketplace_group_share_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            listing_title="Botitas de gamuza tipo desert / urbanas – muy cómodas",
            group_name="Las Piedras, la paz Progreso, Colon",
        )

    assert page.goto_calls == [
        ("https://example.com/marketplace/you/selling", "domcontentloaded")
    ]
    assert page.load_states == ["domcontentloaded", "load"]
    assert calls == [
        ("assert_marketplace_selling_loaded", None),
        (
            "open_listing_share_dialog",
            "Botitas de gamuza tipo desert / urbanas – muy cómodas",
        ),
        ("assert_share_dialog_visible", None),
        ("open_group_destination", None),
        ("assert_group_picker_visible", "2000"),
        ("select_group", "Las Piedras, la paz Progreso, Colon"),
        (
            "assert_group_composer_content_ready",
            "Botitas de gamuza tipo desert / urbanas – muy cómodas",
        ),
    ]
    assert result == FlowResult(
        success=True,
        step="capture_checkpoint",
        current_url="https://example.com/marketplace/you/selling",
        run_id="run-marketplace-group-share",
        artifact_dir=artifact_dir,
        screenshot_path=artifact_dir / "marketplace_group_share_ready.png",
    )
    assert result.screenshot_path is not None
    assert result.screenshot_path.exists()


def test_marketplace_group_share_flow_captures_failure_evidence(
    tmp_path, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-marketplace-group-share-failure"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-marketplace-group-share-failure", artifact_dir=artifact_dir
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
    logger = logging.getLogger("test.marketplace_group_share_flow.failure")

    def fail_open_group_destination(*args, **kwargs) -> None:
        raise ExpectedFlowError("group destination missing")

    caplog.set_level(logging.ERROR, logger=logger.name)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_marketplace_selling_loaded",
            lambda self, base_url, allowed_domain: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_listing_share_dialog",
            lambda self, listing_title, logger=None: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_share_dialog_visible",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_group_destination",
            fail_open_group_destination,
        )

        with pytest.raises(ExpectedFlowError, match="group destination missing"):
            run_marketplace_group_share_flow(
                page=page,
                settings=settings,
                run_context=run_context,
                logger=logger,
                listing_title="Botitas",
                group_name="Las Piedras",
            )

    assert page.goto_calls == [
        ("https://example.com/marketplace/you/selling", "domcontentloaded")
    ]
    assert page.load_states == ["domcontentloaded", "load"]
    assert page.screenshot_paths == [
        str(artifact_dir / "marketplace_group_share_failure.png")
    ]
    assert (artifact_dir / "marketplace_group_share_failure.png").exists()
    assert "marketplace_group_share_flow_failed step=open_group_destination" in caplog.text


def test_marketplace_group_share_flow_retries_group_picker_and_succeeds_on_second_attempt(
    tmp_path, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-marketplace-group-share-retry"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-marketplace-group-share-retry", artifact_dir=artifact_dir
    )

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
    logger = logging.getLogger("test.marketplace_group_share_flow.retry")
    calls: list[tuple[str, str | None]] = []
    picker_attempts = {"count": 0}
    caplog.set_level(logging.INFO, logger=logger.name)

    def assert_group_picker_visible(self, timeout_ms=5000):
        picker_attempts["count"] += 1
        calls.append(("assert_group_picker_visible", str(timeout_ms)))
        if picker_attempts["count"] == 1:
            raise RuntimeError("group picker still closed")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_marketplace_selling_loaded",
            lambda self, base_url, allowed_domain: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_listing_share_dialog",
            lambda self, listing_title, logger=None: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_share_dialog_visible",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_group_destination",
            lambda self: calls.append(("open_group_destination", None)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_picker_visible",
            assert_group_picker_visible,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.get_current_dialog_heading_text",
            lambda self: "Compartir",
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.is_share_dialog_visible",
            lambda self: True,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.select_group",
            lambda self, group_name: calls.append(("select_group", group_name)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_composer_content_ready",
            lambda self, listing_title: calls.append(
                ("assert_group_composer_content_ready", listing_title)
            ),
        )

        result = run_marketplace_group_share_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            listing_title="Botitas",
            group_name="Las Piedras",
        )

    assert calls == [
        ("open_group_destination", None),
        ("assert_group_picker_visible", "2000"),
        ("open_group_destination", None),
        ("assert_group_picker_visible", "5000"),
        ("select_group", "Las Piedras"),
        ("assert_group_composer_content_ready", "Botitas"),
    ]
    assert page.screenshot_paths == [
        str(artifact_dir / "marketplace_group_picker_first_attempt_failed.png"),
        str(artifact_dir / "marketplace_group_share_ready.png"),
    ]
    assert result.screenshot_path == artifact_dir / "marketplace_group_share_ready.png"
    assert "marketplace_group_share_flow_group_picker_first_attempt_failed" in caplog.text
    assert "marketplace_group_share_flow_retrying_open_group_destination" in caplog.text


def test_marketplace_group_share_flow_reopens_share_dialog_when_it_disappears(
    tmp_path, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-marketplace-group-share-reopen"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-marketplace-group-share-reopen", artifact_dir=artifact_dir
    )

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
    logger = logging.getLogger("test.marketplace_group_share_flow.reopen")
    calls: list[tuple[str, str | None]] = []
    picker_attempts = {"count": 0}
    caplog.set_level(logging.INFO, logger=logger.name)

    def assert_group_picker_visible(self, timeout_ms=5000):
        picker_attempts["count"] += 1
        calls.append(("assert_group_picker_visible", str(timeout_ms)))
        if picker_attempts["count"] == 1:
            raise RuntimeError("group picker still closed")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_marketplace_selling_loaded",
            lambda self, base_url, allowed_domain: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_listing_share_dialog",
            lambda self, listing_title, logger=None: calls.append(("open_listing_share_dialog", listing_title)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_share_dialog_visible",
            lambda self: calls.append(("assert_share_dialog_visible", None)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_group_destination",
            lambda self: calls.append(("open_group_destination", None)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_picker_visible",
            assert_group_picker_visible,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.get_current_dialog_heading_text",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.is_share_dialog_visible",
            lambda self: False,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.select_group",
            lambda self, group_name: calls.append(("select_group", group_name)),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_composer_content_ready",
            lambda self, listing_title: calls.append(
                ("assert_group_composer_content_ready", listing_title)
            ),
        )

        result = run_marketplace_group_share_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            listing_title="Botitas",
            group_name="Las Piedras",
        )

    assert calls == [
        ("open_listing_share_dialog", "Botitas"),
        ("assert_share_dialog_visible", None),
        ("open_group_destination", None),
        ("assert_group_picker_visible", "2000"),
        ("open_listing_share_dialog", "Botitas"),
        ("assert_share_dialog_visible", None),
        ("open_group_destination", None),
        ("assert_group_picker_visible", "5000"),
        ("select_group", "Las Piedras"),
        ("assert_group_composer_content_ready", "Botitas"),
    ]
    assert page.screenshot_paths == [
        str(artifact_dir / "marketplace_group_picker_first_attempt_failed.png"),
        str(artifact_dir / "marketplace_group_share_ready.png"),
    ]
    assert result.screenshot_path == artifact_dir / "marketplace_group_share_ready.png"
    assert "marketplace_group_share_flow_reopening_share_dialog_before_retry" in caplog.text


def test_marketplace_group_share_flow_fails_after_reopening_share_dialog(
    tmp_path, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-marketplace-group-share-double-failure"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )
    run_context = RunContext(
        run_id="run-marketplace-group-share-double-failure", artifact_dir=artifact_dir
    )

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
    logger = logging.getLogger("test.marketplace_group_share_flow.double_failure")
    caplog.set_level(logging.INFO, logger=logger.name)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_marketplace_selling_loaded",
            lambda self, base_url, allowed_domain: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_listing_share_dialog",
            lambda self, listing_title, logger=None: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_share_dialog_visible",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.open_group_destination",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.assert_group_picker_visible",
            lambda self, timeout_ms=5000: (_ for _ in ()).throw(
                RuntimeError(f"group picker timeout {timeout_ms}")
            ),
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.get_current_dialog_heading_text",
            lambda self: None,
        )
        monkeypatch.setattr(
            "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.is_share_dialog_visible",
            lambda self: False,
        )

        with pytest.raises(
            RuntimeError,
            match="Group picker did not open after retrying the share dialog transition",
        ):
            run_marketplace_group_share_flow(
                page=page,
                settings=settings,
                run_context=run_context,
                logger=logger,
                listing_title="Botitas",
                group_name="Las Piedras",
            )

    assert page.screenshot_paths == [
        str(artifact_dir / "marketplace_group_picker_first_attempt_failed.png"),
        str(artifact_dir / "marketplace_group_picker_second_attempt_failed.png"),
        str(artifact_dir / "marketplace_group_share_failure.png"),
    ]
    assert (
        "marketplace_group_share_flow_group_picker_first_attempt_failed current_dialog_heading=None"
        in caplog.text
    )
    assert (
        "marketplace_group_share_flow_group_picker_second_attempt_failed current_dialog_heading=None"
        in caplog.text
    )
    assert "marketplace_group_share_flow_reopening_share_dialog_before_retry" in caplog.text
