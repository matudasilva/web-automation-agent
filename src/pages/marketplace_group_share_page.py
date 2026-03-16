from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page

from src.browser.ui_actions import (
    assert_locator_visible,
    click_locator_visible,
    wait_for_locator_visible,
)
from src.pages.base_page import BasePage


@dataclass(frozen=True)
class MarketplaceGroupShareLabels:
    selling_heading: str = "Tus publicaciones"
    selling_path: str = "/marketplace/you/selling"
    share_button: str = "Compartir"
    share_dialog_heading: str = "Compartir"
    group_destination: str = "Grupo"
    group_picker_heading: str = "Compartir en un grupo"
    composer_heading: str = "Crear publicación"
    publish_button: str = "Publicar"


class MarketplaceGroupSharePage(BasePage):
    composer_content_timeout_ms = 10000
    group_picker_retry_timeout_ms = 2000
    listing_discovery_max_scrolls = 3
    listing_discovery_scroll_y_px = 1200
    listing_discovery_scroll_delay_ms = 400

    def __init__(self, page: Page, screenshot_dir: Path) -> None:
        super().__init__(page=page, screenshot_dir=screenshot_dir)
        self.labels = MarketplaceGroupShareLabels()

    def configure_listing_discovery(
        self, *, max_scrolls: int, scroll_delay_ms: int
    ) -> None:
        self.listing_discovery_max_scrolls = max(0, max_scrolls)
        self.listing_discovery_scroll_delay_ms = max(0, scroll_delay_ms)

    def assert_marketplace_selling_loaded(
        self, *, base_url: str, allowed_domain: str
    ) -> None:
        self.assert_in_allowed_domain(allowed_domain=allowed_domain)
        self.assert_in_base_domain(base_url=base_url)
        current_path = urlparse(self.page.url).path
        if not current_path.startswith(self.labels.selling_path):
            raise ValueError(
                f"Current page path '{current_path}' is outside expected Marketplace selling path "
                f"'{self.labels.selling_path}'"
            )

        assert_locator_visible(
            self.page.get_by_role("heading", name=self.labels.selling_heading)
        )

    def find_listing_share_button(
        self, listing_title: str, logger: logging.Logger | None = None
    ) -> Locator:
        share_buttons = self.page.get_by_role(
            "button", name=re.compile(self.labels.share_button, re.IGNORECASE)
        )
        wait_for_locator_visible(share_buttons.first)

        if self.apply_listing_search_filter(listing_title, logger=logger):
            matching_buttons, candidate_names = self._collect_matching_share_buttons(
                share_buttons, listing_title
            )
            if logger is not None:
                logger.info(
                    "marketplace_listing_search_attempt matches=%s candidates=%s",
                    len(matching_buttons),
                    candidate_names,
                )
            if len(matching_buttons) == 1:
                return matching_buttons[0]
            if len(matching_buttons) > 1:
                raise ValueError(
                    "Expected a unique visible Marketplace share button matching listing title "
                    f"fragment '{listing_title}' after search, but found {len(matching_buttons)} matches. "
                    f"Visible share button candidates: {candidate_names}"
                )
            self.clear_listing_search_filter(logger=logger)

        self.reset_listing_discovery_position()
        last_candidate_names: list[str] = []
        last_scroll_y = self.get_vertical_scroll_position()

        for discovery_attempt in range(self.listing_discovery_max_scrolls + 1):
            matching_buttons, candidate_names = self._collect_matching_share_buttons(
                share_buttons, listing_title
            )
            attempt_index = discovery_attempt + 1
            if logger is not None:
                logger.info(
                    "marketplace_listing_discovery_attempt index=%s max_scrolls=%s matches=%s candidates=%s",
                    attempt_index,
                    self.listing_discovery_max_scrolls,
                    len(matching_buttons),
                    candidate_names,
                )

            if len(matching_buttons) == 1:
                return matching_buttons[0]
            if len(matching_buttons) > 1:
                raise ValueError(
                    "Expected a unique visible Marketplace share button matching listing title "
                    f"fragment '{listing_title}', but found {len(matching_buttons)} matches. "
                    f"Visible share button candidates: {candidate_names}"
                )
            if discovery_attempt == self.listing_discovery_max_scrolls:
                break
            if discovery_attempt > 0 and candidate_names == last_candidate_names:
                if logger is not None:
                    logger.info(
                        "marketplace_listing_discovery_stopped_no_new_candidates index=%s candidates=%s",
                        attempt_index,
                        candidate_names,
                    )
                break

            self.page.mouse.wheel(0, self.listing_discovery_scroll_y_px)
            self.page.wait_for_timeout(self.listing_discovery_scroll_delay_ms)
            new_scroll_y = self.get_vertical_scroll_position()
            if (
                last_scroll_y is not None
                and new_scroll_y is not None
                and new_scroll_y <= last_scroll_y
            ):
                if logger is not None:
                    logger.info(
                        "marketplace_listing_discovery_stopped_scroll_stalled index=%s scroll_y=%s",
                        attempt_index,
                        new_scroll_y,
                    )
                break

            last_candidate_names = candidate_names
            last_scroll_y = new_scroll_y

        raise ValueError(
            "Expected a unique visible Marketplace share button matching listing title "
            f"fragment '{listing_title}', but found 0 matches after "
            f"{self.listing_discovery_max_scrolls + 1} discovery passes. "
            f"Last visible share button candidates: {last_candidate_names}"
        )

    def find_listing_search_input(self) -> Locator | None:
        candidates = [
            self.page.get_by_role("searchbox", name=re.compile(".*")).first,
            self.page.get_by_role("textbox", name=re.compile(".*")).first,
        ]
        for candidate in candidates:
            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                continue
        return None

    def apply_listing_search_filter(
        self, listing_title: str, logger: logging.Logger | None = None
    ) -> bool:
        search_input = self.find_listing_search_input()
        if search_input is None:
            if logger is not None:
                logger.info("marketplace_listing_search_unavailable")
            return False

        search_input.fill("")
        search_input.fill(listing_title)
        self.page.wait_for_timeout(self.listing_discovery_scroll_delay_ms)
        if logger is not None:
            logger.info(
                "marketplace_listing_search_applied listing_title=%s", listing_title
            )
        return True

    def clear_listing_search_filter(
        self, logger: logging.Logger | None = None
    ) -> None:
        search_input = self.find_listing_search_input()
        if search_input is None:
            return
        search_input.fill("")
        self.page.wait_for_timeout(self.listing_discovery_scroll_delay_ms)
        if logger is not None:
            logger.info("marketplace_listing_search_cleared")

    def _collect_matching_share_buttons(
        self, share_buttons: Locator, listing_title: str
    ) -> tuple[list[Locator], list[str]]:
        normalized_listing_title = listing_title.strip().lower()
        matching_buttons: list[Locator] = []
        candidate_names: list[str] = []

        for index in range(share_buttons.count()):
            candidate_button = share_buttons.nth(index)
            if not candidate_button.is_visible():
                continue

            accessible_name = candidate_button.get_attribute("aria-label")
            if accessible_name is None:
                accessible_name = candidate_button.text_content()
            normalized_name = (accessible_name or "").strip()
            if not normalized_name:
                candidate_names.append(f"<unnamed button #{index}>")
                continue

            candidate_names.append(normalized_name)
            if normalized_listing_title in normalized_name.lower():
                matching_buttons.append(candidate_button)

        return matching_buttons, candidate_names

    def find_share_dialog(self) -> Locator:
        share_dialog_heading = self.page.get_by_role(
            "heading", name=self.labels.share_dialog_heading
        )
        share_dialog = self.page.locator("[role='dialog']").filter(
            has=share_dialog_heading
        ).first
        return wait_for_locator_visible(share_dialog)

    def is_share_dialog_visible(self) -> bool:
        share_dialog_heading = self.page.get_by_role(
            "heading", name=self.labels.share_dialog_heading
        )
        share_dialog = self.page.locator("[role='dialog']").filter(
            has=share_dialog_heading
        ).first
        try:
            return share_dialog.is_visible()
        except Exception:
            return False

    def open_listing_share_dialog(
        self, listing_title: str, logger: logging.Logger | None = None
    ) -> None:
        try:
            share_button = self.find_listing_share_button(listing_title, logger=logger)
        except Exception:
            self.capture_checkpoint(name="marketplace_listing_discovery_failed")
            raise
        click_locator_visible(share_button, page=self.page)

    def reset_listing_discovery_position(self) -> None:
        self.page.evaluate("window.scrollTo(0, 0)")
        self.page.wait_for_timeout(self.listing_discovery_scroll_delay_ms)

    def get_vertical_scroll_position(self) -> int | None:
        try:
            scroll_y = self.page.evaluate("window.scrollY")
        except Exception:
            return None
        if isinstance(scroll_y, int | float):
            return int(scroll_y)
        return None

    def assert_share_dialog_visible(self) -> None:
        assert_locator_visible(self.find_share_dialog())

    def open_group_destination(self) -> None:
        share_dialog = self.find_share_dialog()
        group_option = share_dialog.get_by_text(
            self.labels.group_destination, exact=True
        )
        click_locator_visible(group_option, page=self.page)

    def find_group_picker_dialog(self, timeout_ms: int = 5000) -> Locator:
        group_picker_heading = self.page.get_by_role(
            "heading", name=self.labels.group_picker_heading
        )
        group_picker_dialog = self.page.locator("[role='dialog']").filter(
            has=group_picker_heading
        ).first
        return wait_for_locator_visible(group_picker_dialog, timeout_ms=timeout_ms)

    def assert_group_picker_visible(self, timeout_ms: int = 5000) -> None:
        assert_locator_visible(
            self.find_group_picker_dialog(timeout_ms=timeout_ms), timeout_ms=timeout_ms
        )

    def get_current_dialog_heading_text(self) -> str | None:
        dialog_heading = self.page.locator("[role='dialog'] [role='heading']").first
        try:
            heading_text = dialog_heading.text_content()
        except Exception:
            return None

        if heading_text is None:
            return None
        normalized = heading_text.strip()
        return normalized or None

    def select_group(self, group_name: str) -> None:
        group_picker_dialog = self.find_group_picker_dialog()
        group_option = group_picker_dialog.get_by_text(group_name, exact=True)
        click_locator_visible(group_option, page=self.page)

    def get_visible_group_composer(self) -> Locator:
        composer_heading = self.page.get_by_role(
            "heading", name=self.labels.composer_heading
        )
        composer_dialog = self.page.locator("[role='dialog']").filter(
            has=composer_heading
        ).first
        return wait_for_locator_visible(composer_dialog)

    def assert_group_composer_content_ready(self, listing_title: str) -> None:
        composer_dialog = self.get_visible_group_composer()
        assert_locator_visible(composer_dialog)
        publish_button = composer_dialog.get_by_role(
            "button", name=self.labels.publish_button
        )
        assert_locator_visible(publish_button)

        listing_preview = composer_dialog.get_by_text(listing_title, exact=False).first
        try:
            assert_locator_visible(
                listing_preview, timeout_ms=self.composer_content_timeout_ms
            )
            return
        except Exception as title_exc:
            preview_image = composer_dialog.locator("img").first
            try:
                assert_locator_visible(
                    preview_image, timeout_ms=self.composer_content_timeout_ms
                )
                return
            except Exception as image_exc:
                raise ValueError(
                    "Group composer is visible but the publish content is still loading "
                    f"or missing for title fragment '{listing_title}'"
                ) from image_exc
