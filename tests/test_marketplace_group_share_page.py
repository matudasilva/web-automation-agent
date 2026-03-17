from __future__ import annotations

import pytest

from src.core.post_publish_status import PostPublishOutcome
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


def test_marketplace_group_share_page_normalizes_listing_title_for_comparison(
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
                    FakeButton("Compartir Colchon 1 Plaza – Muy Firme – 28 cm de Alto"),
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

    share_button = marketplace_page.find_listing_share_button(
        "  Colchón 1 Plaza – Muy   Firme – 28 cm de Alto  "
    )

    assert share_button.get_attribute("aria-label") == (
        "Compartir Colchon 1 Plaza – Muy Firme – 28 cm de Alto"
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
        match=(
            r"requested_title='Botitas'.*"
            r"normalized_requested_title='botitas'.*"
            r"search_term_used='botitas'.*"
            r"discovery_passes=4.*"
            r"stop_reason=max_scrolls_exhausted.*"
            r"final_visible_candidate_titles=\['Compartir Último candidato visible'\]"
        ),
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

    with pytest.raises(ValueError, match="stop_reason=scroll_stalled"):
        marketplace_page.find_listing_share_button("Botitas")


def test_marketplace_group_share_page_stops_discovery_when_no_new_candidates(
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
                [FakeButton("Compartir Otro producto")],
                [FakeButton("Compartir Mismo candidato visible")],
                [FakeButton("Compartir Mismo candidato visible")],
            ]
            self.mouse = FakeMouse(self)

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
                return self.scroll_index * 1000
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            return None

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    with pytest.raises(
        ValueError,
        match=(
            r"stop_reason=no_new_candidates.*"
            r"final_visible_candidate_titles=\['Compartir Mismo candidato visible'\]"
        ),
    ):
        marketplace_page.find_listing_share_button("Botitas")

    assert page.mouse.calls == [
        (0, marketplace_page.listing_discovery_scroll_y_px),
        (0, marketplace_page.listing_discovery_scroll_y_px),
    ]


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
            self.page.filtered = value == "botitas"

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
    assert page.search_terms == ["", "botitas"]
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
            self.page.filtered = value == "botitas"

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
    assert page.search_terms == ["", "botitas", ""]
    assert page.mouse.calls == [(0, marketplace_page.listing_discovery_scroll_y_px)]


def test_marketplace_group_share_page_retries_search_snapshot_before_falling_back(
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
            self.page.filtered = value == "botitas"

    class FakeButtonLocatorGroup:
        def __init__(self, page) -> None:
            self.page = page
            self.first = FakeButton("Compartir Placeholder")

        def count(self) -> int:
            return len(self._current_buttons())

        def nth(self, index: int) -> FakeButton:
            return self._current_buttons()[index]

        def _current_buttons(self) -> list[FakeButton]:
            if self.page.filtered:
                if not self.page.search_retry_ready:
                    return [FakeButton("Compartir Otro producto")]
                return [FakeButton("Compartir Botitas de gamuza tipo desert")]
            return [FakeButton("Compartir Otro producto")]

    class FakePage:
        def __init__(self) -> None:
            self.search_terms: list[str] = []
            self.filtered = False
            self.search_retry_ready = False
            self.mouse = type(
                "FakeMouse",
                (),
                {"calls": [], "wheel": lambda self, delta_x, delta_y: self.calls.append((delta_x, delta_y))},
            )()
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
                return 0
            return None

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)
            if timeout_ms == marketplace_page.listing_search_retry_delay_ms:
                self.search_retry_ready = True

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )

    share_button = marketplace_page.find_listing_share_button("Botitas")

    assert share_button.get_attribute("aria-label") == (
        "Compartir Botitas de gamuza tipo desert"
    )
    assert page.search_terms == ["", "botitas"]
    assert marketplace_page.listing_search_retry_delay_ms in page.timeout_calls
    assert page.mouse.calls == []


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


def test_marketplace_group_share_page_builds_short_normalized_search_term(
    tmp_path,
) -> None:
    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )

    assert (
        marketplace_page.build_listing_search_term(
            "Colchón 1 Plaza – Muy Firme – 28 cm de Alto"
        )
        == "colchon 1 plaza"
    )


def test_marketplace_group_share_page_opens_group_destination(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeLocatorGroup:
        def __init__(self, locator) -> None:
            self.first = locator

    class FakeGroupOption:
        def __init__(self) -> None:
            self.scroll_calls = 0

        def is_visible(self) -> bool:
            return True

        def scroll_into_view_if_needed(self) -> None:
            self.scroll_calls += 1

    class FakeShareDialog:
        def get_by_role(self, role: str, name: str):
            calls.append(("get_by_role", role, name))
            if role == "button":
                return FakeLocatorGroup(group_option)
            return FakeLocatorGroup(hidden_option)

        def get_by_text(self, text: str, exact: bool):
            calls.append(("get_by_text", text, exact))
            return FakeLocatorGroup(hidden_option)

    class FakePage:
        pass

    class HiddenOption:
        def is_visible(self) -> bool:
            return False

        def scroll_into_view_if_needed(self) -> None:
            raise AssertionError("hidden option should not scroll")

    group_option = FakeGroupOption()
    hidden_option = HiddenOption()
    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    monkeypatch.setattr(
        marketplace_page,
        "find_share_dialog",
        lambda: calls.append("share_dialog") or FakeShareDialog(),
    )
    monkeypatch.setattr(
        marketplace_page,
        "capture_checkpoint",
        lambda name: calls.append(("checkpoint", name)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator, page=None: calls.append(locator),
    )
    monkeypatch.setattr(
        marketplace_page,
        "assert_group_picker_visible",
        lambda timeout_ms=5000: calls.append(("assert_group_picker_visible", timeout_ms)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        lambda locator, timeout_ms=5000: calls.append(("assert_locator_visible", locator, timeout_ms)),
    )

    marketplace_page.open_group_destination()

    assert calls == [
        "share_dialog",
        ("checkpoint", "marketplace_open_group_destination_before_click"),
        ("get_by_role", "button", "Grupo"),
        ("assert_locator_visible", group_option, 5000),
        group_option,
        ("assert_group_picker_visible", 1500),
    ]
    assert group_option.scroll_calls == 1


def test_marketplace_group_share_page_captures_evidence_when_group_picker_does_not_open(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeGroupOption:
        def is_visible(self) -> bool:
            return True

        def scroll_into_view_if_needed(self) -> None:
            calls.append("scroll_into_view_if_needed")

    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    group_option = FakeGroupOption()
    share_dialog = object()

    monkeypatch.setattr(
        marketplace_page,
        "find_share_dialog",
        lambda: calls.append("share_dialog") or share_dialog,
    )
    monkeypatch.setattr(
        marketplace_page,
        "find_group_destination_option",
        lambda share_dialog: calls.append(("find_group_destination_option", share_dialog))
        or group_option,
    )
    monkeypatch.setattr(
        marketplace_page,
        "capture_checkpoint",
        lambda name: calls.append(("checkpoint", name)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        lambda locator, timeout_ms=5000: calls.append(("assert_locator_visible", locator, timeout_ms)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator, page=None: calls.append(("click_locator_visible", locator, page)),
    )

    def fail_assert_group_picker_visible(timeout_ms=5000):
        calls.append(("assert_group_picker_visible", timeout_ms))
        raise RuntimeError("group picker did not open")

    monkeypatch.setattr(
        marketplace_page,
        "assert_group_picker_visible",
        fail_assert_group_picker_visible,
    )

    marketplace_page.open_group_destination()

    assert calls == [
        "share_dialog",
        ("checkpoint", "marketplace_open_group_destination_before_click"),
        ("find_group_destination_option", share_dialog),
        ("assert_locator_visible", group_option, 5000),
        "scroll_into_view_if_needed",
        (
            "click_locator_visible",
            group_option,
            marketplace_page.page,
        ),
        ("assert_group_picker_visible", 1500),
        ("checkpoint", "marketplace_open_group_destination_after_click_failed"),
    ]


def test_marketplace_group_share_page_opens_group_destination_when_group_picker_appears(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeGroupOption:
        def is_visible(self) -> bool:
            return True

        def scroll_into_view_if_needed(self) -> None:
            calls.append("scroll_into_view_if_needed")

    page = type("FakePage", (), {})()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )
    group_option = FakeGroupOption()
    share_dialog = object()

    monkeypatch.setattr(
        marketplace_page, "find_share_dialog", lambda: calls.append("share_dialog") or share_dialog
    )
    monkeypatch.setattr(
        marketplace_page,
        "find_group_destination_option",
        lambda resolved_share_dialog: calls.append(
            ("find_group_destination_option", resolved_share_dialog)
        )
        or group_option,
    )
    monkeypatch.setattr(
        marketplace_page,
        "capture_checkpoint",
        lambda name: calls.append(("checkpoint", name)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.assert_locator_visible",
        lambda locator, timeout_ms=5000: calls.append(("assert_locator_visible", locator, timeout_ms)),
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator, page=None: calls.append(("click_locator_visible", locator, page)),
    )
    monkeypatch.setattr(
        marketplace_page,
        "assert_group_picker_visible",
        lambda timeout_ms=5000: calls.append(("assert_group_picker_visible", timeout_ms)),
    )

    marketplace_page.open_group_destination()

    assert calls == [
        "share_dialog",
        ("checkpoint", "marketplace_open_group_destination_before_click"),
        ("find_group_destination_option", share_dialog),
        ("assert_locator_visible", group_option, 5000),
        "scroll_into_view_if_needed",
        ("click_locator_visible", group_option, page),
        ("assert_group_picker_visible", 1500),
    ]


def test_marketplace_group_share_page_selects_group_within_group_picker(
    monkeypatch, tmp_path
) -> None:
    calls: list[object] = []

    class FakeSearchInput:
        def is_visible(self) -> bool:
            return True

        def fill(self, value: str) -> None:
            calls.append(("fill", value))

    class FakeGroupOption:
        def __init__(self, label: str) -> None:
            self.label = label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.label

        def text_content(self) -> str:
            return self.label

    class FakeLocatorGroup:
        def __init__(self, items: list[object]) -> None:
            self._items = items
            self.first = items[0]

        def count(self) -> int:
            return len(self._items)

        def nth(self, index: int):
            return self._items[index]

    class FakeGroupPickerDialog:
        def __init__(self) -> None:
            self.search_input = FakeSearchInput()
            self.options = [
                FakeGroupOption("Ventas en las piedras la paz progreso"),
                FakeGroupOption("Venta De Todo La Paz Las Piedras"),
            ]

        def get_by_role(self, role: str, name):
            calls.append(("get_by_role", role))
            if role == "searchbox":
                return FakeLocatorGroup([self.search_input])
            if role == "textbox":
                return FakeLocatorGroup([type("HiddenTextbox", (), {"is_visible": lambda self: False})()])
            if role == "button":
                return FakeLocatorGroup(self.options)
            raise AssertionError(f"Unexpected role: {role}")

    class FakePage:
        def wait_for_timeout(self, timeout_ms: int) -> None:
            calls.append(("wait_for_timeout", timeout_ms))

    group_option = FakeGroupOption("Venta De Todo La Paz Las Piedras")
    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )
    group_picker_dialog = FakeGroupPickerDialog()

    monkeypatch.setattr(
        marketplace_page,
        "find_group_picker_dialog",
        lambda: calls.append("group_picker_dialog") or group_picker_dialog,
    )
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.click_locator_visible",
        lambda locator, page=None: calls.append(locator),
    )

    marketplace_page.select_group("Venta De Todo La Paz Las Piedras")

    assert calls[0] == "group_picker_dialog"
    assert ("fill", "") in calls
    assert ("fill", "Venta De Todo La Paz Las Piedras") in calls
    assert ("wait_for_timeout", marketplace_page.group_picker_search_settle_delay_ms) in calls
    assert calls[-1].label == "Venta De Todo La Paz Las Piedras"


def test_marketplace_group_share_page_matches_group_option_with_normalized_text(
    tmp_path,
) -> None:
    class FakeGroupOption:
        def __init__(self, label: str) -> None:
            self.label = label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.label

        def text_content(self) -> str:
            return self.label

    class FakeLocatorGroup:
        def __init__(self, items: list[object]) -> None:
            self._items = items
            self.first = items[0]

        def count(self) -> int:
            return len(self._items)

        def nth(self, index: int):
            return self._items[index]

    class FakeGroupPickerDialog:
        def get_by_role(self, role: str, name):
            if role == "button":
                return FakeLocatorGroup(
                    [
                        FakeGroupOption("compra y venta, Colón, la paz, las piedras.."),
                        FakeGroupOption("Ventas en las piedras la paz progreso"),
                    ]
                )
            raise AssertionError(f"Unexpected role: {role}")

    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )

    group_option = marketplace_page.find_group_picker_group_option(
        FakeGroupPickerDialog(),
        "Compra y venta, Colon, la paz, las piedras",
    )

    assert group_option.label == "compra y venta, Colón, la paz, las piedras.."


def test_marketplace_group_share_page_retries_group_picker_when_only_modal_controls_are_visible(
    tmp_path,
) -> None:
    class FakeGroupOption:
        def __init__(self, label: str) -> None:
            self.label = label

        def is_visible(self) -> bool:
            return True

        def get_attribute(self, name: str) -> str | None:
            if name != "aria-label":
                return None
            return self.label

        def text_content(self) -> str:
            return self.label

    class FakeLocatorGroup:
        def __init__(self, page, items_by_phase: list[list[object]]) -> None:
            self.page = page
            self.items_by_phase = items_by_phase
            self.first = items_by_phase[0][0]

        def count(self) -> int:
            return len(self.items_by_phase[self.page.phase])

        def nth(self, index: int):
            return self.items_by_phase[self.page.phase][index]

    class FakePage:
        def __init__(self) -> None:
            self.phase = 0
            self.timeout_calls: list[int] = []

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)
            if timeout_ms == marketplace_page.group_picker_search_retry_delay_ms:
                self.phase = 1

    class FakeGroupPickerDialog:
        def __init__(self, page) -> None:
            self.page = page
            self.options = FakeLocatorGroup(
                page,
                [
                    [FakeGroupOption("Volver"), FakeGroupOption("Cerrar")],
                    [FakeGroupOption("venta la paz, las piedras, abayuba,colon, paso molino , el dorado , etc.")],
                ],
            )

        def get_by_role(self, role: str, name):
            if role == "button":
                return self.options
            raise AssertionError(f"Unexpected role: {role}")

    page = FakePage()
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=tmp_path / "screenshots"
    )
    group_picker_dialog = FakeGroupPickerDialog(page)

    group_option = marketplace_page.find_group_picker_group_option_with_retry(
        group_picker_dialog,
        "venta la paz, las piedras, abayuba,colon, paso molino , el dorado , etc.",
    )

    assert group_option.label == (
        "venta la paz, las piedras, abayuba,colon, paso molino , el dorado , etc."
    )
    assert page.timeout_calls == [marketplace_page.group_picker_search_retry_delay_ms]


def test_marketplace_group_share_page_preserves_parentheses_in_group_search_term(
    monkeypatch, tmp_path
) -> None:
    calls: list[tuple[str, str] | tuple[str, int]] = []

    class FakeSearchInput:
        def is_visible(self) -> bool:
            return True

        def fill(self, value: str) -> None:
            calls.append(("fill", value))

    class FakeLocatorGroup:
        def __init__(self, items: list[object]) -> None:
            self._items = items
            self.first = items[0]

    class FakeGroupPickerDialog:
        def get_by_role(self, role: str, name):
            if role == "searchbox":
                return FakeLocatorGroup([FakeSearchInput()])
            if role == "textbox":
                return FakeLocatorGroup(
                    [type("HiddenTextbox", (), {"is_visible": lambda self: False})()]
                )
            raise AssertionError(f"Unexpected role: {role}")

    class FakePage:
        def wait_for_timeout(self, timeout_ms: int) -> None:
            calls.append(("wait_for_timeout", timeout_ms))

    marketplace_page = MarketplaceGroupSharePage(
        page=FakePage(), screenshot_dir=tmp_path / "screenshots"
    )

    marketplace_page.apply_group_picker_search_filter(
        FakeGroupPickerDialog(),
        "Compra y venta (Exclusivo La Paz, Canelones)",
    )

    assert calls == [
        ("fill", ""),
        ("fill", "Compra y venta (Exclusivo La Paz, Canelones)"),
        ("wait_for_timeout", marketplace_page.group_picker_search_settle_delay_ms),
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


def test_marketplace_group_share_page_detects_published_visible_from_toast(
    monkeypatch, tmp_path
) -> None:
    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(
        marketplace_page, "get_visible_toast_text", lambda: "Tu publicación se publicó."
    )
    monkeypatch.setattr(marketplace_page, "is_group_composer_visible", lambda: False)
    monkeypatch.setattr(marketplace_page, "get_visible_error_text", lambda: None)
    monkeypatch.setattr(
        marketplace_page, "get_visible_page_state_text", lambda: "Tus publicaciones"
    )

    outcome = marketplace_page.detect_post_publish_status()

    assert outcome == PostPublishOutcome(
        status="published_visible",
        observed_text=(
            "toast=Tu publicación se publicó. | composer_visible=False | "
            "error=<none> | page_state=Tus publicaciones"
        ),
        signal="toast",
    )


def test_marketplace_group_share_page_detects_submitted_for_approval_from_page_state(
    monkeypatch, tmp_path
) -> None:
    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(marketplace_page, "get_visible_toast_text", lambda: None)
    monkeypatch.setattr(marketplace_page, "is_group_composer_visible", lambda: False)
    monkeypatch.setattr(marketplace_page, "get_visible_error_text", lambda: None)
    monkeypatch.setattr(
        marketplace_page,
        "get_visible_page_state_text",
        lambda: "Tu publicación fue enviada para aprobación",
    )

    outcome = marketplace_page.detect_post_publish_status()

    assert outcome == PostPublishOutcome(
        status="submitted_for_approval",
        observed_text=(
            "toast=<none> | composer_visible=False | error=<none> | "
            "page_state=Tu publicación fue enviada para aprobación"
        ),
        signal="page_state",
    )


def test_marketplace_group_share_page_detects_publish_blocked_when_composer_error_visible(
    monkeypatch, tmp_path
) -> None:
    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(marketplace_page, "get_visible_toast_text", lambda: None)
    monkeypatch.setattr(marketplace_page, "is_group_composer_visible", lambda: True)
    monkeypatch.setattr(
        marketplace_page, "get_visible_error_text", lambda: "Algo no funciona"
    )
    monkeypatch.setattr(
        marketplace_page, "get_visible_page_state_text", lambda: "Crear publicación"
    )

    outcome = marketplace_page.detect_post_publish_status()

    assert outcome == PostPublishOutcome(
        status="publish_blocked_or_unavailable",
        observed_text=(
            "toast=<none> | composer_visible=True | error=Algo no funciona | "
            "page_state=Crear publicación"
        ),
        signal="composer+error",
    )


def test_marketplace_group_share_page_detects_publish_unconfirmed_without_signals(
    monkeypatch, tmp_path
) -> None:
    marketplace_page = MarketplaceGroupSharePage(
        page=type("FakePage", (), {})(), screenshot_dir=tmp_path / "screenshots"
    )
    monkeypatch.setattr(marketplace_page, "get_visible_toast_text", lambda: None)
    monkeypatch.setattr(marketplace_page, "is_group_composer_visible", lambda: False)
    monkeypatch.setattr(marketplace_page, "get_visible_error_text", lambda: None)
    monkeypatch.setattr(marketplace_page, "get_visible_page_state_text", lambda: None)

    outcome = marketplace_page.detect_post_publish_status()

    assert outcome == PostPublishOutcome(
        status="publish_unconfirmed",
        observed_text=(
            "toast=<none> | composer_visible=False | error=<none> | page_state=<none>"
        ),
        signal="fallback",
    )
