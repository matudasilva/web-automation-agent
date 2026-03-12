from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Page

from src.services.screenshot_service import capture_page_screenshot


class BasePage:
    def __init__(self, page: Page, screenshot_dir: Path) -> None:
        self.page = page
        self.screenshot_dir = screenshot_dir

    def wait_until_ready(self) -> None:
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_load_state("load")

    def assert_in_allowed_domain(self, allowed_domain: str) -> None:
        hostname = urlparse(self.page.url).hostname
        if not hostname:
            raise ValueError(f"Current page URL is invalid: {self.page.url}")

        normalized_host = hostname.lower()
        normalized_allowed = allowed_domain.strip().lower()
        if normalized_host == normalized_allowed:
            return
        if normalized_host.endswith(f".{normalized_allowed}"):
            return

        raise ValueError(
            f"Current page domain '{normalized_host}' is outside ALLOWED_DOMAIN '{normalized_allowed}'"
        )

    def assert_in_base_domain(self, base_url: str) -> None:
        expected_hostname = urlparse(base_url).hostname
        current_hostname = urlparse(self.page.url).hostname
        if not expected_hostname or not current_hostname:
            raise ValueError("Could not determine expected or current hostname")

        normalized_expected = expected_hostname.lower()
        normalized_current = current_hostname.lower()
        if normalized_current == normalized_expected:
            return
        if normalized_current.endswith(f".{normalized_expected}"):
            return

        raise ValueError(
            f"Current hostname '{current_hostname}' is outside BASE_URL hostname '{expected_hostname}'"
        )

    def capture_checkpoint(self, name: str) -> Path:
        return capture_page_screenshot(
            page=self.page, screenshot_dir=self.screenshot_dir, name=name
        )
