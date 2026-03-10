from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from src.core.config import Settings
from src.main import run_bootstrap


def test_bootstrap_opens_base_url_and_captures_screenshot(tmp_path, monkeypatch) -> None:
    screenshot_dir = tmp_path / "screenshots"
    settings = Settings(
        base_url="https://example.com",
        headless=True,
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
    )

    class FakePage:
        def __init__(self) -> None:
            self.visited_url = None
            self.wait_until = None
            self.saved_screenshot_path = None

        def goto(self, url: str, wait_until: str) -> None:
            self.visited_url = url
            self.wait_until = wait_until

        def screenshot(self, path: str, full_page: bool) -> None:
            self.saved_screenshot_path = path
            Path(path).write_bytes(b"fake-image")
            assert full_page is True

    page = FakePage()

    @contextmanager
    def fake_browser_session(_settings: Settings):
        yield page

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", fake_browser_session)

    screenshot_path = run_bootstrap()

    assert page.visited_url == "https://example.com"
    assert page.wait_until == "domcontentloaded"
    assert page.saved_screenshot_path == str(screenshot_path)
    assert screenshot_path.exists()
