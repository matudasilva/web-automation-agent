from __future__ import annotations

import pytest

from src.pages.target_page import TargetPage


def test_target_page_asserts_content_visibility(monkeypatch, tmp_path) -> None:
    calls: list[tuple[object, str]] = []

    class FakePage:
        pass

    page = FakePage()
    target_page = TargetPage(page=page, screenshot_dir=tmp_path / "screenshots")

    monkeypatch.setattr(
        "src.pages.target_page.assert_visible",
        lambda page, selector: calls.append((page, selector)),
    )

    target_page.assert_content_visible()

    assert calls == [(page, "[data-testid='target-content']")]


def test_target_page_fills_text_input(monkeypatch, tmp_path) -> None:
    calls: list[tuple[object, str, str]] = []

    class FakePage:
        pass

    page = FakePage()
    target_page = TargetPage(page=page, screenshot_dir=tmp_path / "screenshots")

    monkeypatch.setattr(
        "src.pages.target_page.fill_visible",
        lambda page, selector, value: calls.append((page, selector, value)),
    )

    target_page.fill_text_input(value="preview")

    assert calls == [(page, "[data-testid='target-input']", "preview")]


def test_target_page_finds_item_by_text_within_content_region(monkeypatch, tmp_path) -> None:
    class FakeItemLocator:
        pass

    class FakeContentLocator:
        def __init__(self) -> None:
            self.text_calls: list[str] = []

        def get_by_text(self, text: str) -> FakeItemLocator:
            self.text_calls.append(text)
            return item_locator

    class FakePage:
        pass

    content_locator = FakeContentLocator()
    item_locator = FakeItemLocator()
    page = FakePage()
    target_page = TargetPage(page=page, screenshot_dir=tmp_path / "screenshots")
    waited_locators: list[object] = []

    monkeypatch.setattr(
        "src.pages.target_page.wait_for_visible",
        lambda page, selector: content_locator,
    )
    monkeypatch.setattr(
        "src.pages.target_page.wait_for_locator_visible",
        lambda locator: waited_locators.append(locator) or locator,
    )

    result = target_page.find_item(text="Sample Item")

    assert result is item_locator
    assert content_locator.text_calls == ["Sample Item"]
    assert waited_locators == [item_locator]


def test_target_page_finds_item_by_selector_within_content_region(
    monkeypatch, tmp_path
) -> None:
    class FakeItemLocator:
        pass

    class FakeContentLocator:
        def __init__(self) -> None:
            self.locator_calls: list[str] = []

        def locator(self, selector: str) -> FakeItemLocator:
            self.locator_calls.append(selector)
            return item_locator

    class FakePage:
        pass

    content_locator = FakeContentLocator()
    item_locator = FakeItemLocator()
    page = FakePage()
    target_page = TargetPage(page=page, screenshot_dir=tmp_path / "screenshots")
    waited_locators: list[object] = []

    monkeypatch.setattr(
        "src.pages.target_page.wait_for_visible",
        lambda page, selector: content_locator,
    )
    monkeypatch.setattr(
        "src.pages.target_page.wait_for_locator_visible",
        lambda locator: waited_locators.append(locator) or locator,
    )

    result = target_page.find_item(item_selector="[data-testid='item-row']")

    assert result is item_locator
    assert content_locator.locator_calls == ["[data-testid='item-row']"]
    assert waited_locators == [item_locator]


def test_target_page_opens_item_secondary_action(monkeypatch, tmp_path) -> None:
    calls: list[object] = []

    class FakeActionLocator:
        pass

    class FakeItemLocator:
        def locator(self, selector: str) -> FakeActionLocator:
            calls.append(selector)
            return action_locator

    class FakePage:
        pass

    page = FakePage()
    action_locator = FakeActionLocator()
    item_locator = FakeItemLocator()
    target_page = TargetPage(page=page, screenshot_dir=tmp_path / "screenshots")

    monkeypatch.setattr(
        target_page,
        "find_item",
        lambda text=None, item_selector=None: item_locator,
    )
    monkeypatch.setattr(
        "src.pages.target_page.click_locator_visible",
        lambda locator: calls.append(locator),
    )

    target_page.open_item_secondary_action(item_selector="[data-testid='item-row']")

    assert calls == ["[data-testid='target-secondary-action']", action_locator]


def test_target_page_requires_exactly_one_item_lookup_strategy(tmp_path) -> None:
    class FakePage:
        pass

    target_page = TargetPage(page=FakePage(), screenshot_dir=tmp_path / "screenshots")

    with pytest.raises(
        ValueError, match="Provide exactly one of 'text' or 'item_selector'"
    ):
        target_page.find_item()
