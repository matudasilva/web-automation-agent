from __future__ import annotations

import pytest

from src.pages.marketplace_group_share_page import MarketplaceGroupSharePage


def test_marketplace_group_share_page_asserts_expected_management_area(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakePage:
        url = "https://example.com/marketplace/you/selling"

        def get_by_role(self, role: str, name: str):
            calls.append((role, name))
            return heading_locator

    page = FakePage()
    heading_locator = object()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    monkeypatch.setattr(
        marketplace_page,
        "assert_in_allowed_domain",
        lambda allowed_domain: calls.append(("allowed_domain", allowed_domain)),
    )
    monkeypatch.setattr(
        marketplace_page,
        "assert_in_base_domain",
        lambda base_url: calls.append(("base_url", base_url)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        lambda locator: calls.append(locator),
    )

    marketplace_page.assert_marketplace_selling_loaded(
        base_url="https://example.com/marketplace/you/selling",
        allowed_domain="example.com",
    )

    assert calls == [
        ("allowed_domain", "example.com"),
        ("base_url", "https://example.com/marketplace/you/selling"),
        ("heading", "Tus publicaciones"),
        heading_locator,
    ]


def test_marketplace_group_share_page_requires_expected_management_path(tmp_path) -> None:
    class FakePage:
        url = "https://example.com/login"

        def get_by_role(self, role: str, name: str):
            raise AssertionError("get_by_role should not be called")

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    marketplace_page.assert_in_allowed_domain = lambda allowed_domain: None
    marketplace_page.assert_in_base_domain = lambda base_url: None

    with pytest.raises(ValueError, match="Marketplace selling path"):
        marketplace_page.assert_marketplace_selling_loaded(
            base_url="https://example.com/marketplace/you/selling",
            allowed_domain="example.com",
        )


def test_marketplace_group_share_page_opens_share_within_listing_container(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeShareButton:
        pass

    class FakeListingContainer:
        def get_by_role(self, role: str, name: str) -> FakeShareButton:
            calls.append((role, name))
            return share_button

    class FakePage:
        pass

    share_button = FakeShareButton()
    listing_container = FakeListingContainer()
    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    monkeypatch.setattr(
        marketplace_page,
        "find_listing_container",
        lambda listing_title: calls.append(("listing", listing_title))
        or listing_container,
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator: calls.append(locator),
    )

    marketplace_page.open_listing_share_dialog("Botitas")

    assert calls == [
        ("listing", "Botitas"),
        ("button", "Compartir"),
        share_button,
    ]


def test_marketplace_group_share_page_opens_group_destination(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeShareDialog:
        def get_by_text(self, text: str, exact: bool):
            calls.append((text, exact))
            return group_option

    class FakePage:
        pass

    group_option = object()
    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    monkeypatch.setattr(
        marketplace_page,
        "find_share_dialog",
        lambda: calls.append("share_dialog") or FakeShareDialog(),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator: calls.append(locator),
    )

    marketplace_page.open_group_destination()

    assert calls == ["share_dialog", ("Grupo", True), group_option]


def test_marketplace_group_share_page_selects_group_within_group_picker(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeGroupPickerDialog:
        def get_by_text(self, text: str, exact: bool):
            calls.append((text, exact))
            return group_option

    class FakePage:
        pass

    group_option = object()
    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    monkeypatch.setattr(
        marketplace_page,
        "find_group_picker_dialog",
        lambda: calls.append("group_picker_dialog") or FakeGroupPickerDialog(),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator: calls.append(locator),
    )

    marketplace_page.select_group("Las Piedras, la paz Progreso, Colon")

    assert calls == [
        "group_picker_dialog",
        ("Las Piedras, la paz Progreso, Colon", True),
        group_option,
    ]


def test_marketplace_group_share_page_asserts_group_composer_content_ready(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeComposerDialog:
        def get_by_role(self, role: str, name: str):
            locator = f"{role}:{name}"
            calls.append(locator)
            return locator

        def get_by_text(self, text: str, exact: bool):
            locator = type(
                "FakeTextLocator",
                (),
                {"first": f"text:{text}:{exact}:first"},
            )()
            calls.append(locator)
            return locator

        def locator(self, selector: str):
            locator = type(
                "FakeImageLocator",
                (),
                {"first": f"locator:{selector}:first"},
            )()
            calls.append(locator)
            return locator

    class FakePage:
        pass

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    composer_dialog = FakeComposerDialog()
    monkeypatch.setattr(
        marketplace_page,
        "get_visible_group_composer",
        lambda: calls.append("composer_dialog") or composer_dialog,
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        lambda locator, timeout_ms=5000: calls.append(("visible", locator, timeout_ms)),
    )

    marketplace_page.assert_group_composer_content_ready(
        "Botitas de gamuza tipo desert"
    )

    assert calls[0:4] == [
        "composer_dialog",
        ("visible", composer_dialog, 5000),
        "button:Publicar",
        ("visible", "button:Publicar", 5000),
    ]
    assert calls[4].first == "text:Botitas de gamuza tipo desert:False:first"
    assert calls[5] == (
        "visible",
        "text:Botitas de gamuza tipo desert:False:first",
        10000,
    )


def test_marketplace_group_share_page_fails_when_group_composer_content_is_still_loading(
    monkeypatch, tmp_path
) -> None:
    class FakeComposerDialog:
        def get_by_role(self, role: str, name: str):
            return f"{role}:{name}"

        def get_by_text(self, text: str, exact: bool):
            return type(
                "FakeTextLocator",
                (),
                {"first": f"text:{text}:{exact}:first"},
            )()

        def locator(self, selector: str):
            return type(
                "FakeImageLocator",
                (),
                {"first": f"locator:{selector}:first"},
            )()

    class FakePage:
        pass

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(
        marketplace_page,
        "get_visible_group_composer",
        lambda: FakeComposerDialog(),
    )

    def fake_assert_locator_visible(locator, timeout_ms=5000):
        if str(locator).startswith("text:") or str(locator).startswith("locator:img"):
            raise RuntimeError("still loading")

    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        fake_assert_locator_visible,
    )

    with pytest.raises(
        ValueError, match="publish content is still loading or missing"
    ):
        marketplace_page.assert_group_composer_content_ready("Botitas")


def test_marketplace_group_share_page_accepts_visible_image_as_content_signal(
    monkeypatch, tmp_path
) -> None:
    calls: list[tuple[str, str, int]] = []

    class FakeComposerDialog:
        def get_by_role(self, role: str, name: str):
            return f"{role}:{name}"

        def get_by_text(self, text: str, exact: bool):
            return type(
                "FakeTextLocator",
                (),
                {"first": f"text:{text}:{exact}:first"},
            )()

        def locator(self, selector: str):
            return type(
                "FakeImageLocator",
                (),
                {"first": f"locator:{selector}:first"},
            )()

    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(
        marketplace_page,
        "get_visible_group_composer",
        lambda: FakeComposerDialog(),
    )

    def fake_assert_locator_visible(locator, timeout_ms=5000):
        locator_str = str(locator)
        calls.append(("visible", locator_str, timeout_ms))
        if locator_str.startswith("text:"):
            raise RuntimeError("multiple text matches")

    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        fake_assert_locator_visible,
    )

    marketplace_page.assert_group_composer_content_ready("Botitas")

    assert ("visible", "locator:img:first", 10000) in calls
