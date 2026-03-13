from __future__ import annotations

from playwright.sync_api import Locator, Page


DEFAULT_TIMEOUT_MS = 5000


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


def click_locator_visible(
    locator: Locator, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    wait_for_locator_visible(locator=locator, timeout_ms=timeout_ms)
    locator.click()


def fill_visible(
    page: Page, selector: str, value: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    locator = wait_for_visible(page=page, selector=selector, timeout_ms=timeout_ms)
    locator.fill(value)


def assert_visible(
    page: Page, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    wait_for_visible(page=page, selector=selector, timeout_ms=timeout_ms)


def assert_locator_visible(
    locator: Locator, timeout_ms: int = DEFAULT_TIMEOUT_MS
) -> None:
    wait_for_locator_visible(locator=locator, timeout_ms=timeout_ms)
