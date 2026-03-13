from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page

from src.browser.ui_actions import assert_visible, fill_visible
from src.pages.base_page import BasePage


@dataclass(frozen=True)
class TargetPageSelectors:
    # TODO: Replace these placeholder selectors when the real target page is defined.
    content_region: str = "[data-testid='target-content']"
    text_input: str = "[data-testid='target-input']"


class TargetPage(BasePage):
    def __init__(self, page: Page, screenshot_dir: Path) -> None:
        super().__init__(page=page, screenshot_dir=screenshot_dir)
        self.selectors = TargetPageSelectors()

    def assert_loaded(self, base_url: str, allowed_domain: str) -> None:
        self.assert_in_allowed_domain(allowed_domain=allowed_domain)
        self.assert_in_base_domain(base_url=base_url)

    def assert_content_visible(self) -> None:
        assert_visible(page=self.page, selector=self.selectors.content_region)

    def fill_text_input(self, value: str) -> None:
        fill_visible(page=self.page, selector=self.selectors.text_input, value=value)
