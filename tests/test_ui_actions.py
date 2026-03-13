from __future__ import annotations

import pytest

from src.browser.ui_actions import (
    DEFAULT_TIMEOUT_MS,
    assert_locator_visible,
    assert_visible,
    click_locator_visible,
    click_visible,
    fill_visible,
    wait_for_locator_visible,
    wait_for_visible,
)


class FakeLocator:
    def __init__(self) -> None:
        self.wait_calls: list[tuple[str, int]] = []
        self.click_calls = 0
        self.fill_calls: list[str] = []

    def wait_for(self, state: str, timeout: int) -> None:
        self.wait_calls.append((state, timeout))

    def click(self) -> None:
        self.click_calls += 1

    def fill(self, value: str) -> None:
        self.fill_calls.append(value)


class FakePage:
    def __init__(self, locator: FakeLocator) -> None:
        self._locator = locator
        self.locator_calls: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        self.locator_calls.append(selector)
        return self._locator


def test_wait_for_visible_returns_locator_after_waiting() -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    result = wait_for_visible(page=page, selector="[data-test='cta']")

    assert result is locator
    assert page.locator_calls == ["[data-test='cta']"]
    assert locator.wait_calls == [("visible", DEFAULT_TIMEOUT_MS)]


def test_click_visible_waits_before_clicking() -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    click_visible(page=page, selector="#submit", timeout_ms=2000)

    assert page.locator_calls == ["#submit"]
    assert locator.wait_calls == [("visible", 2000)]
    assert locator.click_calls == 1


def test_fill_visible_waits_before_filling() -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    fill_visible(page=page, selector="input[name='email']", value="user@example.com")

    assert page.locator_calls == ["input[name='email']"]
    assert locator.wait_calls == [("visible", DEFAULT_TIMEOUT_MS)]
    assert locator.fill_calls == ["user@example.com"]


def test_assert_visible_waits_for_selector() -> None:
    locator = FakeLocator()
    page = FakePage(locator)

    assert_visible(page=page, selector=".status")

    assert page.locator_calls == [".status"]
    assert locator.wait_calls == [("visible", DEFAULT_TIMEOUT_MS)]


def test_click_visible_propagates_locator_wait_errors() -> None:
    class FailingLocator(FakeLocator):
        def wait_for(self, state: str, timeout: int) -> None:
            raise RuntimeError("not visible")

    locator = FailingLocator()
    page = FakePage(locator)

    with pytest.raises(RuntimeError, match="not visible"):
        click_visible(page=page, selector="#submit")


def test_wait_for_locator_visible_returns_locator_after_waiting() -> None:
    locator = FakeLocator()

    result = wait_for_locator_visible(locator=locator, timeout_ms=1500)

    assert result is locator
    assert locator.wait_calls == [("visible", 1500)]


def test_click_locator_visible_waits_before_clicking() -> None:
    locator = FakeLocator()

    click_locator_visible(locator=locator)

    assert locator.wait_calls == [("visible", DEFAULT_TIMEOUT_MS)]
    assert locator.click_calls == 1


def test_assert_locator_visible_waits_for_locator() -> None:
    locator = FakeLocator()

    assert_locator_visible(locator=locator, timeout_ms=2500)

    assert locator.wait_calls == [("visible", 2500)]
