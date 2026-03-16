from __future__ import annotations

from playwright.sync_api import Locator, Page


DEFAULT_TIMEOUT_MS = 5000
DEFAULT_UI_ACTION_DELAY_MS = 700
_ui_action_delay_ms = DEFAULT_UI_ACTION_DELAY_MS


def configure_ui_action_delay(delay_ms: int) -> None:
    global _ui_action_delay_ms
    _ui_action_delay_ms = max(0, delay_ms)


def apply_ui_action_delay(page: Page) -> None:
    if _ui_action_delay_ms <= 0:
        return
    page.wait_for_timeout(_ui_action_delay_ms)


def wait_for_visible(
    page: Page, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> Locator:
    locator = page.locator(selector)
    return wait_for_locator_visible(locator=locator, timeout_ms=timeout_ms)


def wait_for_locator_visible(
    locator: Locator, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> Locator:
    locator.wait_for(state="visible", timeout=timeout_ms)
    return locator


def click_visible(
    page: Page, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    locator = wait_for_visible(page=page, selector=selector, timeout_ms=timeout_ms)
    locator.click()
    apply_ui_action_delay(page)


def click_locator_visible(
    locator: Locator, timeout_ms: int = DEFAULT_TIMEOUT_MS, page: Page | None = None
) -> None:
    wait_for_locator_visible(locator=locator, timeout_ms=timeout_ms)
    locator.click()
    if page is not None:
        apply_ui_action_delay(page)


def fill_visible(
    page: Page, selector: str, value: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    locator = wait_for_visible(page=page, selector=selector, timeout_ms=timeout_ms)
    locator.fill(value)
    apply_ui_action_delay(page)


def assert_visible(
    page: Page, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    wait_for_visible(page=page, selector=selector, timeout_ms=timeout_ms)


def assert_locator_visible(
    locator: Locator, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    wait_for_locator_visible(locator=locator, timeout_ms=timeout_ms)
