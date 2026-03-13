from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Locator, Page

from src.browser.ui_actions import (
    assert_visible,
    click_locator_visible,
    fill_visible,
    wait_for_locator_visible,
    wait_for_visible,
)
from src.pages.base_page import BasePage


@dataclass(frozen=True)
class TargetPageSelectors:
    # TODO: Replace these placeholder selectors when the real target page is defined.
    content_region: str = "[data-testid='target-content']"
    text_input: str = "[data-testid='target-input']"
    secondary_action: str = "[data-testid='target-secondary-action']"
    next_state_region: str = "[data-testid='target-next-state']"


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

    def find_item(
        self, *, text: str | None = None, item_selector: str | None = None
    ) -> Locator:
        if bool(text) == bool(item_selector):
            raise ValueError("Provide exactly one of 'text' or 'item_selector'")

        content_region = wait_for_visible(
            page=self.page, selector=self.selectors.content_region
        )
        if text is not None:
            item_locator = content_region.get_by_text(text)
        else:
            item_locator = content_region.locator(item_selector)

        return wait_for_locator_visible(locator=item_locator)

    def open_item_secondary_action(
        self, *, text: str | None = None, item_selector: str | None = None
    ) -> None:
        item_locator = self.find_item(text=text, item_selector=item_selector)
        action_locator = item_locator.locator(self.selectors.secondary_action)
        click_locator_visible(locator=action_locator)

    def assert_next_state_visible(self) -> None:
        assert_visible(page=self.page, selector=self.selectors.next_state_region)
