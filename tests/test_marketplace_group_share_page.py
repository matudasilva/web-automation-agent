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


def test_marketplace_group_share_page_opens_matching_listing_share_button(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            calls.append((state, timeout))

    class FakeButtonLocatorGroup:
        def __init__(self, buttons: list[FakeButton]) -> None:
            self._buttons = buttons
            self.first = buttons[0]

        def count(self) -> int:
            return len(self._buttons)

        def nth(self, index: int) -> FakeButton:
            return self._buttons[index]

    class FakePage:
        def __init__(self) -> None:
            self.role_calls: list[tuple[str, object]] = []
            self.mouse = type("FakeMouse", (), {"calls": []})()
            self.evaluate_calls: list[str] = []
            self.searchbox = None

        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            self.role_calls.append((role, name))
            return FakeButtonLocatorGroup(
                [
                    FakeButton("Compartir Jarra cervecera de madera"),
                    FakeButton("Compartir Botitas de gamuza tipo desert"),
                ]
            )

        def evaluate(self, script: str):
            self.evaluate_calls.append(script)
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            calls.append(("wait_for_timeout", timeout_ms))

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator, page=None: calls.append(locator),
    )

    marketplace_page.open_listing_share_dialog("Botitas")

    assert page.role_calls[0][0] == "button"
    assert calls[-1].aria_label == "Compartir Botitas de gamuza tipo desert"
    assert page.mouse.calls == []
    assert page.evaluate_calls == ["window.scrollTo(0, 0)", "window.scrollY"]


def test_marketplace_group_share_page_finds_unique_matching_share_button_with_multiple_listings(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str, visible: bool = True) -> None:
            self.aria_label = aria_label
            self.visible = visible

        def is_visible(self) -> bool:
            return self.visible

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeButtonLocatorGroup:
        def __init__(self, buttons: list[FakeButton]) -> None:
            self._buttons = buttons
            self.first = buttons[0]

        def count(self) -> int:
            return len(self._buttons)

        def nth(self, index: int) -> FakeButton:
            return self._buttons[index]

    class FakePage:
        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(
                [
                    FakeButton("Compartir Jarra cervecera de madera"),
                    FakeButton("Compartir Botitas de gamuza tipo desert"),
                    FakeButton("Compartir Otro producto"),
                ]
            )

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            return None

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    share_button = marketplace_page.find_listing_share_button("Botitas de gamuza")

    assert share_button.get_attribute("aria-label") == (
        "Compartir Botitas de gamuza tipo desert"
    )


def test_marketplace_group_share_page_finds_share_button_after_scroll_discovery(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeMouse:
        def __init__(self, page) -> None:
            self.page = page
            self.calls: list[tuple[int, int]] = []

        def wheel(self, delta_x: int, delta_y: int) -> None:
            self.calls.append((delta_x, delta_y))
            self.page.scroll_index += 1

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = page.button_sets[0][0]

        def count(self) -> int:
            return len(self.page.button_sets[self.page.scroll_index])

        def nth(self, index: int) -> FakeButton:
            return self.page.button_sets[self.page.scroll_index][index]

    class FakePage:
        def __init__(self) -> None:
            self.scroll_index = 0
            self.button_sets = [
                [FakeButton("Compartir Jarra cervecera de madera")],
                [FakeButton("Compartir Botitas de gamuza tipo desert")],
            ]
            self.mouse = FakeMouse(self)
            self.timeout_calls: list[int] = []
            self.evaluate_calls: list[str] = []

        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(self)

        def evaluate(self, script: str):
            self.evaluate_calls.append(script)
            if script == "window.scrollY":
                return self.scroll_index * 1000
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    share_button = marketplace_page.find_listing_share_button("Botitas")

    assert share_button.get_attribute("aria-label") == (
        "Compartir Botitas de gamuza tipo desert"
    )
    assert page.mouse.calls == [(0, marketplace_page.listing_discovery_scroll_y_px)]
    assert page.timeout_calls == [marketplace_page.listing_discovery_scroll_delay_ms] * 2


def test_marketplace_group_share_page_fails_when_share_button_match_is_not_unique(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeButtonLocatorGroup:
        def __init__(self, buttons: list[FakeButton]) -> None:
            self._buttons = buttons
            self.first = buttons[0]

        def count(self) -> int:
            return len(self._buttons)

        def nth(self, index: int) -> FakeButton:
            return self._buttons[index]

    class FakePage:
        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(
                [
                    FakeButton("Compartir Botitas de gamuza tipo desert"),
                    FakeButton("Compartir Botitas de gamuza tipo desert - otra copia"),
                ]
            )

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            return None

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    with pytest.raises(ValueError, match="Expected a unique visible Marketplace share button"):
        marketplace_page.find_listing_share_button("Botitas de gamuza")


def test_marketplace_group_share_page_fails_after_exhausting_scroll_discovery(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeMouse:
        def __init__(self, page) -> None:
            self.page = page
            self.calls: list[tuple[int, int]] = []

        def wheel(self, delta_x: int, delta_y: int) -> None:
            self.calls.append((delta_x, delta_y))
            if self.page.scroll_index < len(self.page.button_sets) - 1:
                self.page.scroll_index += 1

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = page.button_sets[0][0]

        def count(self) -> int:
            return len(self.page.button_sets[self.page.scroll_index])

        def nth(self, index: int) -> FakeButton:
            return self.page.button_sets[self.page.scroll_index][index]

    class FakePage:
        def __init__(self) -> None:
            self.scroll_index = 0
            self.button_sets = [
                [FakeButton("Compartir Jarra cervecera de madera")],
                [FakeButton("Compartir Otro producto")],
                [FakeButton("Compartir Más artículos")],
                [FakeButton("Compartir Último candidato visible")],
            ]
            self.mouse = FakeMouse(self)
            self.timeout_calls: list[int] = []
            self.evaluate_calls: list[str] = []

        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(self)

        def evaluate(self, script: str):
            self.evaluate_calls.append(script)
            if script == "window.scrollY":
                return self.scroll_index * 1000
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    with pytest.raises(
        ValueError,
        match="found 0 matches after 4 discovery passes",
    ):
        marketplace_page.find_listing_share_button("Botitas")

    assert page.mouse.calls == [
        (0, marketplace_page.listing_discovery_scroll_y_px),
        (0, marketplace_page.listing_discovery_scroll_y_px),
        (0, marketplace_page.listing_discovery_scroll_y_px),
    ]


def test_marketplace_group_share_page_stops_discovery_when_scroll_stalls(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeMouse:
        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def wheel(self, delta_x: int, delta_y: int) -> None:
            self.calls.append((delta_x, delta_y))

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = page.buttons[0]

        def count(self) -> int:
            return len(self.page.buttons)

        def nth(self, index: int) -> FakeButton:
            return self.page.buttons[index]

    class FakePage:
        def __init__(self) -> None:
            self.buttons = [FakeButton("Compartir Otro producto")]
            self.mouse = FakeMouse()
            self.timeout_calls: list[int] = []

        def get_by_role(self, role: str, name):
            if role in {"searchbox", "textbox"}:
                return type(
                    "HiddenSearchInput",
                    (),
                    {"first": type("HiddenSearchLocator", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(self)

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    with pytest.raises(ValueError, match="found 0 matches after 4 discovery passes"):
        marketplace_page.find_listing_share_button("Botitas")

    assert page.mouse.calls == [(0, marketplace_page.listing_discovery_scroll_y_px)]


def test_marketplace_group_share_page_uses_search_as_primary_listing_strategy(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeSearchLocator:
        def __init__(self, page) -> None:
            self.page = page

        def is_visible(self) -> bool:
            return True

        def fill(self, value: str) -> None:
            self.page.search_terms.append(value)
            self.page.filtered = value == "Botitas"

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = FakeButton("Compartir Botitas de gamuza tipo desert")

        def count(self) -> int:
            return len(self._current_buttons())

        def nth(self, index: int) -> FakeButton:
            return self._current_buttons()[index]

        def _current_buttons(self) -> list[FakeButton]:
            if self.page.filtered:
                return [FakeButton("Compartir Botitas de gamuza tipo desert")]
            return [
                FakeButton("Compartir Jarra cervecera de madera"),
                FakeButton("Compartir Otro producto"),
            ]

    class FakePage:
        def __init__(self) -> None:
            self.search_terms: list[str] = []
            self.filtered = False
            self.mouse = type(
                "FakeMouse",
                (),
                {"calls": [], "wheel": lambda self, delta_x, delta_y: self.calls.append((delta_x, delta_y))},
            )()

        def get_by_role(self, role: str, name):
            if role == "searchbox":
                return type("SearchboxGroup", (), {"first": FakeSearchLocator(self)})()
            if role == "textbox":
                return type(
                    "HiddenTextboxGroup",
                    (),
                    {"first": type("HiddenTextbox", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(self)

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            return None

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    share_button = marketplace_page.find_listing_share_button("Botitas")

    assert share_button.get_attribute("aria-label") == (
        "Compartir Botitas de gamuza tipo desert"
    )
    assert page.search_terms == ["", "Botitas"]
    assert page.mouse.calls == []


def test_marketplace_group_share_page_falls_back_to_scroll_when_search_has_no_result(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeSearchLocator:
        def __init__(self, page) -> None:
            self.page = page

        def is_visible(self) -> bool:
            return True

        def fill(self, value: str) -> None:
            self.page.search_terms.append(value)
            self.page.filtered = value == "Botitas"

    class FakeMouse:
        def __init__(self, page) -> None:
            self.page = page
            self.calls: list[tuple[int, int]] = []

        def wheel(self, delta_x: int, delta_y: int) -> None:
            self.calls.append((delta_x, delta_y))
            self.page.scroll_index += 1

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = FakeButton("Compartir Otro producto")

        def count(self) -> int:
            return len(self._current_buttons())

        def nth(self, index: int) -> FakeButton:
            return self._current_buttons()[index]

        def _current_buttons(self) -> list[FakeButton]:
            if self.page.filtered:
                return [FakeButton("Compartir Otro producto")]
            button_sets = [
                [FakeButton("Compartir Jarra cervecera de madera")],
                [FakeButton("Compartir Botitas de gamuza tipo desert")],
            ]
            return button_sets[self.page.scroll_index]

    class FakePage:
        def __init__(self) -> None:
            self.search_terms: list[str] = []
            self.filtered = False
            self.scroll_index = 0
            self.mouse = FakeMouse(self)
            self.timeout_calls: list[int] = []

        def get_by_role(self, role: str, name):
            if role == "searchbox":
                return type("SearchboxGroup", (), {"first": FakeSearchLocator(self)})()
            if role == "textbox":
                return type(
                    "HiddenTextboxGroup",
                    (),
                    {"first": type("HiddenTextbox", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup(self)

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return self.scroll_index * 1000
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)
            if self.filtered and len(self.search_terms) >= 2 and self.search_terms[-1] == "":
                self.filtered = False

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    share_button = marketplace_page.find_listing_share_button("Botitas")

    assert share_button.get_attribute("aria-label") == (
        "Compartir Botitas de gamuza tipo desert"
    )
    assert page.search_terms == ["", "Botitas", ""]
    assert page.mouse.calls == [(0, marketplace_page.listing_discovery_scroll_y_px)]


def test_marketplace_group_share_page_fails_when_search_returns_multiple_matches(
    tmp_path,
) -> None:
    class FakeButton:
        def __init__(self, aria_label: str) -> None:
            self.aria_label = aria_label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.aria_label

        def text_content(self) -> str:
            return self.aria_label

        def wait_for(self, state: str, timeout: int) -> None:
            return None

    class FakeSearchLocator:
        def is_visible(self) -> bool:
            return True

        def fill(self, value: str) -> None:
            return None

    class FakeButtonLocatorGroup:
        def __init__(self) -> None:
            self.first = FakeButton("Compartir Botitas de gamuza tipo desert")

        def count(self) -> int:
            return 2

        def nth(self, index: int) -> FakeButton:
            buttons = [
                FakeButton("Compartir Botitas de gamuza tipo desert"),
                FakeButton("Compartir Botitas de gamuza tipo desert - otra copia"),
            ]
            return buttons[index]

    class FakePage:
        def __init__(self) -> None:
            self.mouse = type(
                "FakeMouse",
                (),
                {"calls": [], "wheel": lambda self, delta_x, delta_y: self.calls.append((delta_x, delta_y))},
            )()

        def get_by_role(self, role: str, name):
            if role == "searchbox":
                return type("SearchboxGroup", (), {"first": FakeSearchLocator()})()
            if role == "textbox":
                return type(
                    "HiddenTextboxGroup",
                    (),
                    {"first": type("HiddenTextbox", (), {"is_visible": lambda self: False})()},
                )()
            return FakeButtonLocatorGroup()

        def evaluate(self, script: str):
            if script == "window.scrollY":
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            return None

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    with pytest.raises(ValueError, match="after search, but found 2 matches"):
        marketplace_page.find_listing_share_button("Botitas")


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
        lambda locator, page=None: calls.append(locator),
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
        lambda locator, page=None: calls.append(locator),
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
