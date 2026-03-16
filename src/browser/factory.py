from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import BrowserType, Page, sync_playwright

from src.core.config import Settings


@contextmanager
def browser_session(settings: Settings) -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser_type = _get_browser_type(playwright, settings.browser)
        browser = None

        if settings.browser_profile_dir is not None:
            context = browser_type.launch_persistent_context(
                user_data_dir=str(settings.browser_profile_dir),
                headless=settings.headless,
            )
        else:
            browser = browser_type.launch(headless=settings.headless)
            context = browser.new_context()

        page = context.pages[0] if context.pages else context.new_page()
        try:
            yield page
        finally:
            context.close()
            if browser is not None:
                browser.close()


def _get_browser_type(playwright, browser_name: str) -> BrowserType:
    normalized = browser_name.strip().lower()
    browser_types = {
        "chromium": playwright.chromium,
        "firefox": playwright.firefox,
        "webkit": playwright.webkit,
    }
    try:
        return browser_types[normalized]
    except KeyError as exc:
        supported = ", ".join(sorted(browser_types))
        raise ValueError(
            f"Unsupported browser '{browser_name}'. Expected one of: {supported}"
        ) from exc
