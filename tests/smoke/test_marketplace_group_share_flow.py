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
            lambda self, listing_title: calls.append(
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
            lambda self: calls.append(("assert_group_picker_visible", None)),
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
        ("assert_group_picker_visible", None),
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
            lambda self, listing_title: None,
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
