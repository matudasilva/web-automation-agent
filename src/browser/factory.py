from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright

from src.core.config import Settings


def validate_allowed_domain(base_url: str, allowed_domain: str) -> None:
    hostname = urlparse(base_url).hostname
    if not hostname:
        raise ValueError(f"Invalid BASE_URL: {base_url}")

    normalized_allowed = allowed_domain.strip().lower()
    normalized_host = hostname.lower()
    if normalized_host == normalized_allowed:
        return
    if normalized_host.endswith(f".{normalized_allowed}"):
        return

    raise ValueError(
        f"BASE_URL domain '{normalized_host}' is outside ALLOWED_DOMAIN '{normalized_allowed}'"
    )


@contextmanager
def browser_session(settings: Settings) -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=settings.headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()
