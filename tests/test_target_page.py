from __future__ import annotations

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
