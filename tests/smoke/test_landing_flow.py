from __future__ import annotations

import logging
from pathlib import Path

from src.core.config import Settings
from src.flows.landing_flow import run_landing_flow


def test_landing_flow_opens_url_validates_and_screenshots(tmp_path) -> None:
    screenshot_dir = tmp_path / "screenshots"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
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
    logger = logging.getLogger("test.landing_flow")

    screenshot_path = run_landing_flow(page=page, settings=settings, logger=logger)

    assert page.goto_calls == [("https://example.com", "domcontentloaded")]
    assert page.load_states == ["domcontentloaded", "load"]
    assert screenshot_path == screenshot_dir / "landing_ready.png"
    assert page.screenshot_path == str(screenshot_path)
    assert screenshot_path.exists()
