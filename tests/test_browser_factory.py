from __future__ import annotations

from pathlib import Path

import pytest

from src.browser.factory import browser_session
from src.core.config import Settings


class FakePage:
    pass


class FakeContext:
    def __init__(self, page: object | None = None) -> None:
        self.pages = [] if page is None else [page]
        self.new_page_calls = 0
        self.closed = False

    def new_page(self) -> object:
        self.new_page_calls += 1
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, context: FakeContext) -> None:
        self.context = context
        self.new_context_calls = 0
        self.closed = False

    def new_context(self) -> FakeContext:
        self.new_context_calls += 1
        return self.context

    def close(self) -> None:
        self.closed = True


class FakeBrowserType:
    def __init__(self, label: str) -> None:
        self.label = label
        self.launch_calls: list[bool] = []
        self.persistent_calls: list[tuple[str, bool]] = []
        self.browser: FakeBrowser | None = None
        self.context: FakeContext | None = None

    def launch(self, *, headless: bool) -> FakeBrowser:
        self.launch_calls.append(headless)
        assert self.browser is not None
        return self.browser

    def launch_persistent_context(
        self, *, user_data_dir: str, headless: bool
    ) -> FakeContext:
        self.persistent_calls.append((user_data_dir, headless))
        assert self.context is not None
        return self.context


class FakePlaywright:
    def __init__(self) -> None:
        self.chromium = FakeBrowserType("chromium")
        self.firefox = FakeBrowserType("firefox")
        self.webkit = FakeBrowserType("webkit")


class FakePlaywrightManager:
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright

    def __enter__(self) -> FakePlaywright:
        return self.playwright

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_browser_session_uses_configured_browser_engine(monkeypatch) -> None:
    context = FakeContext()
    browser = FakeBrowser(context)
    playwright = FakePlaywright()
    playwright.firefox.browser = browser

    monkeypatch.setattr(
        "src.browser.factory.sync_playwright",
        lambda: FakePlaywrightManager(playwright),
    )

    settings = Settings(
        base_url="https://example.com",
        browser="firefox",
        headless=False,
        screenshot_dir=Path("./screenshots"),
        allowed_domain="example.com",
    )

    with browser_session(settings) as page:
        assert isinstance(page, FakePage)

    assert playwright.firefox.launch_calls == [False]
    assert browser.new_context_calls == 1
    assert context.new_page_calls == 1
    assert context.closed is True
    assert browser.closed is True
    assert playwright.chromium.launch_calls == []
    assert playwright.webkit.launch_calls == []


def test_browser_session_uses_persistent_profile_when_configured(monkeypatch, tmp_path) -> None:
    existing_page = FakePage()
    context = FakeContext(page=existing_page)
    playwright = FakePlaywright()
    playwright.firefox.context = context

    monkeypatch.setattr(
        "src.browser.factory.sync_playwright",
        lambda: FakePlaywrightManager(playwright),
    )

    settings = Settings(
        base_url="https://example.com",
        browser="firefox",
        headless=True,
        browser_profile_dir=tmp_path / "firefox-profile",
        screenshot_dir=Path("./screenshots"),
        allowed_domain="example.com",
    )

    with browser_session(settings) as page:
        assert page is existing_page

    assert playwright.firefox.persistent_calls == [
        (str(tmp_path / "firefox-profile"), True)
    ]
    assert context.new_page_calls == 0
    assert context.closed is True


def test_browser_session_rejects_unsupported_browser(monkeypatch) -> None:
    playwright = FakePlaywright()
    monkeypatch.setattr(
        "src.browser.factory.sync_playwright",
        lambda: FakePlaywrightManager(playwright),
    )

    settings = Settings(
        base_url="https://example.com",
        browser="opera",
        headless=True,
        screenshot_dir=Path("./screenshots"),
        allowed_domain="example.com",
    )

    with pytest.raises(ValueError, match="Unsupported browser 'opera'"):
        with browser_session(settings):
            pass
