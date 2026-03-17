from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page

from src.browser.ui_actions import (
    assert_locator_visible,
    click_locator_visible,
    wait_for_locator_visible,
)
from src.core.post_publish_status import PostPublishOutcome
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
    group_destination_transition_timeout_ms = 1500
    listing_search_settle_delay_ms = 700
    listing_search_retry_delay_ms = 250
    group_picker_search_settle_delay_ms = 500
    group_picker_search_retry_delay_ms = 300
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
        normalized_listing_title = self.normalize_text_for_comparison(listing_title)
        search_term_used = self.build_listing_search_term(listing_title)
        share_buttons = self.page.get_by_role(
            "button", name=re.compile(self.labels.share_button, re.IGNORECASE)
        )
        wait_for_locator_visible(share_buttons.first)
        discovery_passes = 0

        if self.apply_listing_search_filter(search_term_used, logger=logger):
            matching_buttons, candidate_names = self.collect_search_matches_with_retry(
                share_buttons=share_buttons,
                listing_title=listing_title,
                logger=logger,
            )
            if logger is not None:
                logger.info(
                    "marketplace_listing_search_attempt matches=%s requested_title=%s normalized_requested_title=%s search_term=%s candidates=%s",
                    len(matching_buttons),
                    listing_title,
                    normalized_listing_title,
                    search_term_used,
                    candidate_names,
                )
            if len(matching_buttons) == 1:
                return matching_buttons[0]
            if len(matching_buttons) > 1:
                raise ValueError(
                    self._build_listing_resolution_error(
                        listing_title=listing_title,
                        normalized_listing_title=normalized_listing_title,
                        search_term_used=search_term_used,
                        discovery_passes=discovery_passes,
                        stop_reason="search_multiple_matches",
                        final_visible_candidate_titles=candidate_names,
                        match_count=len(matching_buttons),
                        phase="after search",
                    )
                )
            self.clear_listing_search_filter(logger=logger)

        self.reset_listing_discovery_position()
        last_candidate_names: list[str] = []
        last_scroll_y = self.get_vertical_scroll_position()
        stop_reason = "max_scrolls_exhausted"

        for discovery_attempt in range(self.listing_discovery_max_scrolls + 1):
            matching_buttons, candidate_names = self._collect_matching_share_buttons(
                share_buttons, listing_title
            )
            attempt_index = discovery_attempt + 1
            discovery_passes = attempt_index
            if logger is not None:
                logger.info(
                    "marketplace_listing_discovery_attempt index=%s max_scrolls=%s requested_title=%s normalized_requested_title=%s matches=%s candidates=%s",
                    attempt_index,
                    self.listing_discovery_max_scrolls,
                    listing_title,
                    normalized_listing_title,
                    len(matching_buttons),
                    candidate_names,
                )

            if len(matching_buttons) == 1:
                return matching_buttons[0]
            if len(matching_buttons) > 1:
                raise ValueError(
                    self._build_listing_resolution_error(
                        listing_title=listing_title,
                        normalized_listing_title=normalized_listing_title,
                        search_term_used=search_term_used,
                        discovery_passes=discovery_passes,
                        stop_reason="discovery_multiple_matches",
                        final_visible_candidate_titles=candidate_names,
                        match_count=len(matching_buttons),
                    )
                )
            if discovery_attempt == self.listing_discovery_max_scrolls:
                stop_reason = "max_scrolls_exhausted"
                last_candidate_names = candidate_names
                break
            if discovery_attempt > 0 and candidate_names == last_candidate_names:
                stop_reason = "no_new_candidates"
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
                stop_reason = "scroll_stalled"
                last_candidate_names = candidate_names
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
            self._build_listing_resolution_error(
                listing_title=listing_title,
                normalized_listing_title=normalized_listing_title,
                search_term_used=search_term_used,
                discovery_passes=discovery_passes,
                stop_reason=stop_reason,
                final_visible_candidate_titles=last_candidate_names,
                match_count=0,
            )
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
        self, search_term: str, logger: logging.Logger | None = None
    ) -> bool:
        search_input = self.find_listing_search_input()
        if search_input is None:
            if logger is not None:
                logger.info("marketplace_listing_search_unavailable")
            return False

        search_input.fill("")
        search_input.fill(search_term)
        self.page.wait_for_timeout(self.listing_search_settle_delay_ms)
        if logger is not None:
            logger.info("marketplace_listing_search_applied search_term=%s", search_term)
        return True

    def collect_search_matches_with_retry(
        self,
        *,
        share_buttons: Locator,
        listing_title: str,
        logger: logging.Logger | None = None,
    ) -> tuple[list[Locator], list[str]]:
        matching_buttons, candidate_names = self._collect_matching_share_buttons(
            share_buttons, listing_title
        )
        if matching_buttons:
            return matching_buttons, candidate_names

        self.page.wait_for_timeout(self.listing_search_retry_delay_ms)
        retry_matching_buttons, retry_candidate_names = self._collect_matching_share_buttons(
            share_buttons, listing_title
        )
        if logger is not None:
            logger.info(
                "marketplace_listing_search_retry matches=%s candidates=%s",
                len(retry_matching_buttons),
                retry_candidate_names,
            )
        return retry_matching_buttons, retry_candidate_names

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
        normalized_listing_title = self.normalize_text_for_comparison(listing_title)
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
            normalized_candidate_name = self.normalize_text_for_comparison(
                normalized_name
            )
            if normalized_listing_title in normalized_candidate_name:
                matching_buttons.append(candidate_button)

        return matching_buttons, candidate_names

    def normalize_text_for_comparison(self, value: str) -> str:
        normalized = value.strip().lower()
        normalized = " ".join(normalized.split())
        normalized = unicodedata.normalize("NFKD", normalized)
        return "".join(
            char for char in normalized if not unicodedata.combining(char)
        )

    def build_listing_search_term(self, listing_title: str) -> str:
        normalized_title = self.normalize_text_for_comparison(listing_title)
        search_tokens = re.findall(r"[a-z0-9]+", normalized_title)
        if not search_tokens:
            return listing_title.strip()
        return " ".join(search_tokens[:3])

    def _build_listing_resolution_error(
        self,
        *,
        listing_title: str,
        normalized_listing_title: str,
        search_term_used: str,
        discovery_passes: int,
        stop_reason: str,
        final_visible_candidate_titles: list[str],
        match_count: int,
        phase: str = "after discovery",
    ) -> str:
        return (
            "Expected a unique visible Marketplace share button matching listing title "
            f"'{listing_title}' {phase}, but found {match_count} matches. "
            f"requested_title={listing_title!r} "
            f"normalized_requested_title={normalized_listing_title!r} "
            f"search_term_used={search_term_used!r} "
            f"discovery_passes={discovery_passes} "
            f"stop_reason={stop_reason} "
            f"final_visible_candidate_titles={final_visible_candidate_titles}"
        )

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
        self.capture_checkpoint(name="marketplace_open_group_destination_before_click")
        group_option = self.find_group_destination_option(share_dialog)
        assert_locator_visible(group_option)
        self._scroll_locator_into_view_if_needed(group_option)
        click_locator_visible(group_option, page=self.page)
        try:
            self.assert_group_picker_visible(
                timeout_ms=self.group_destination_transition_timeout_ms
            )
        except Exception:
            self.capture_checkpoint(
                name="marketplace_open_group_destination_after_click_failed"
            )

    def find_group_destination_option(self, share_dialog: Locator) -> Locator:
        candidate_builders = [
            lambda: share_dialog.get_by_role("button", name=self.labels.group_destination),
            lambda: share_dialog.get_by_role("link", name=self.labels.group_destination),
            lambda: share_dialog.get_by_role("option", name=self.labels.group_destination),
            lambda: share_dialog.get_by_text(self.labels.group_destination, exact=True),
        ]
        for build_candidate in candidate_builders:
            candidate = build_candidate().first
            if self._is_locator_visible(candidate):
                return candidate

        raise ValueError(
            "Could not resolve a visible 'Grupo' destination option inside the share dialog"
        )

    def _scroll_locator_into_view_if_needed(self, locator: Locator) -> None:
        try:
            locator.scroll_into_view_if_needed()
        except Exception:
            return

    def _is_locator_visible(self, locator: Locator) -> bool:
        try:
            return locator.is_visible()
        except Exception:
            return False

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
        self.apply_group_picker_search_filter(group_picker_dialog, group_name)
        group_option = self.find_group_picker_group_option_with_retry(
            group_picker_dialog, group_name
        )
        click_locator_visible(group_option, page=self.page)

    def apply_group_picker_search_filter(
        self, group_picker_dialog: Locator, group_name: str
    ) -> None:
        search_input = self.find_group_picker_search_input(group_picker_dialog)
        if search_input is None:
            return
        search_term = group_name.strip()
        search_input.fill("")
        search_input.fill(search_term)
        self.page.wait_for_timeout(self.group_picker_search_settle_delay_ms)

    def find_group_picker_search_input(self, group_picker_dialog: Locator) -> Locator | None:
        candidates = [
            group_picker_dialog.get_by_role("searchbox", name=re.compile(".*")).first,
            group_picker_dialog.get_by_role("textbox", name=re.compile(".*")).first,
        ]
        for candidate in candidates:
            if self._is_locator_visible(candidate):
                return candidate
        return None

    def find_group_picker_group_option_with_retry(
        self, group_picker_dialog: Locator, group_name: str
    ) -> Locator:
        try:
            return self.find_group_picker_group_option(group_picker_dialog, group_name)
        except ValueError as first_error:
            if not self._group_picker_has_only_chrome_controls(first_error):
                raise
            self.page.wait_for_timeout(self.group_picker_search_retry_delay_ms)
            return self.find_group_picker_group_option(group_picker_dialog, group_name)

    def find_group_picker_group_option(
        self, group_picker_dialog: Locator, group_name: str
    ) -> Locator:
        group_options = group_picker_dialog.get_by_role("button", name=re.compile(".*"))
        normalized_group_name = self.normalize_text_for_comparison(group_name)
        matching_options: list[Locator] = []
        candidate_names: list[str] = []

        for index in range(group_options.count()):
            candidate_option = group_options.nth(index)
            if not candidate_option.is_visible():
                continue

            candidate_name = candidate_option.get_attribute("aria-label")
            if candidate_name is None:
                candidate_name = candidate_option.text_content()
            normalized_candidate_name = (candidate_name or "").strip()
            if not normalized_candidate_name:
                continue
            if self._is_group_picker_chrome_control(normalized_candidate_name):
                continue

            candidate_names.append(normalized_candidate_name)
            if normalized_group_name in self.normalize_text_for_comparison(
                normalized_candidate_name
            ):
                matching_options.append(candidate_option)

        if len(matching_options) == 1:
            return matching_options[0]
        if len(matching_options) > 1:
            raise ValueError(
                "Expected a unique visible Marketplace group option matching group name "
                f"'{group_name}', but found {len(matching_options)} matches. "
                f"Visible group option candidates: {candidate_names}"
            )
        raise ValueError(
            "Could not resolve a visible Marketplace group option matching group name "
            f"'{group_name}'. Visible group option candidates: {candidate_names}"
        )

    def _is_group_picker_chrome_control(self, candidate_name: str) -> bool:
        normalized_candidate_name = self.normalize_text_for_comparison(candidate_name)
        return normalized_candidate_name in {"volver", "cerrar"}

    def _group_picker_has_only_chrome_controls(self, error: ValueError) -> bool:
        error_text = str(error)
        return (
            "Visible group option candidates: []" in error_text
            or "Visible group option candidates: ['Volver', 'Cerrar']" in error_text
        )


    def get_visible_group_composer(self) -> Locator:
        composer_heading = self.page.get_by_role(
            "heading", name=self.labels.composer_heading
        )
        composer_dialog = self.page.locator("[role='dialog']").filter(
            has=composer_heading
        ).first
        return wait_for_locator_visible(composer_dialog)

    def is_group_composer_visible(self) -> bool:
        composer_heading = self.page.get_by_role(
            "heading", name=self.labels.composer_heading
        )
        composer_dialog = self.page.locator("[role='dialog']").filter(
            has=composer_heading
        ).first
        try:
            return composer_dialog.is_visible()
        except Exception:
            return False

    def detect_post_publish_status(self) -> PostPublishOutcome:
        toast_text = self.get_visible_toast_text()
        composer_visible = self.is_group_composer_visible()
        error_text = self.get_visible_error_text()
        page_state_text = self.get_visible_page_state_text()

        observed_text = " | ".join(
            [
                f"toast={toast_text or '<none>'}",
                f"composer_visible={composer_visible}",
                f"error={error_text or '<none>'}",
                f"page_state={page_state_text or '<none>'}",
            ]
        )

        if toast_text is not None:
            classified_status = self._classify_post_publish_toast_text(toast_text)
            if classified_status is not None:
                return PostPublishOutcome(
                    status=classified_status,
                    observed_text=observed_text,
                    signal=self._get_post_publish_toast_signal(classified_status),
                )

        if composer_visible:
            if error_text is not None:
                return PostPublishOutcome(
                    status="publish_blocked_or_unavailable",
                    observed_text=observed_text,
                    signal="composer+error",
                )
        else:
            if error_text is not None:
                return PostPublishOutcome(
                    status="publish_blocked_or_unavailable",
                    observed_text=observed_text,
                    signal="error",
                )

            if page_state_text is not None:
                classified_status = self._classify_publish_text(page_state_text)
                if classified_status is not None:
                    return PostPublishOutcome(
                        status=classified_status,
                        observed_text=observed_text,
                        signal="page_state",
                    )

        return PostPublishOutcome(
            status="publish_unconfirmed",
            observed_text=observed_text,
            signal="fallback",
        )

    def get_visible_toast_text(self) -> str | None:
        toast_candidates = [
            self.page.locator("[role='alert']").first,
            self.page.locator("[aria-live='assertive']").first,
            self.page.locator("[aria-live='polite']").first,
        ]
        return self._get_first_visible_text(toast_candidates)

    def get_visible_error_text(self) -> str | None:
        error_candidates = [
            self.page.get_by_text(
                re.compile(
                    r"Algo no funciona|No se pudo|Int[eé]ntalo de nuevo|Error",
                    re.IGNORECASE,
                )
            ).first,
            self.page.locator("[role='alert']").first,
        ]
        return self._get_first_visible_text(error_candidates)

    def get_visible_page_state_text(self) -> str | None:
        page_state_candidates = [
            self.page.get_by_role("heading", name=self.labels.selling_heading).first,
            self.page.locator("[role='dialog'] [role='heading']").first,
            self.page.locator("[role='main'] h1, [role='main'] h2").first,
        ]
        return self._get_first_visible_text(page_state_candidates)

    def _get_first_visible_text(self, candidates: list[Locator]) -> str | None:
        for candidate in candidates:
            text = self._get_visible_locator_text(candidate)
            if text is not None:
                return text
        return None

    def _get_visible_locator_text(self, locator: Locator) -> str | None:
        try:
            if not locator.is_visible():
                return None
            text = locator.text_content()
        except Exception:
            return None

        if text is None:
            return None
        normalized = " ".join(text.split())
        return normalized or None

    def _classify_post_publish_toast_text(self, text: str) -> str | None:
        normalized_text = self.normalize_text_for_comparison(text)
        if "se compartio en tu grupo" in normalized_text:
            return "publish_success_confirmed"
        if any(
            signal in normalized_text
            for signal in [
                "se envio a los administradores para su aprobacion",
                "se envio a los administradores para aprobacion",
                "enviada a los administradores para su aprobacion",
                "enviada a los administradores para aprobacion",
            ]
        ):
            return "submitted_for_approval"
        if any(
            signal in normalized_text
            for signal in [
                "no se pudo",
                "error",
                "intenta nuevamente",
                "algo no funciona. esto puede deberse a un error tecnico que estamos intentando solucionar.",
            ]
        ):
            return "publish_needs_retry"
        return self._classify_publish_text(text)

    def _get_post_publish_toast_signal(self, status: str) -> str:
        if status == "publish_success_confirmed":
            return "toast_success"
        if status == "submitted_for_approval":
            return "toast_approval"
        if status == "publish_needs_retry":
            return "toast_retry_or_error"
        return "toast"

    def _classify_publish_text(self, text: str) -> str | None:
        normalized_text = self.normalize_text_for_comparison(text)
        if any(
            signal in normalized_text
            for signal in [
                "se publico",
                "publicaste",
                "publicacion publicada",
                "publicacion publicada",
            ]
        ):
            return "published_visible"
        if any(
            signal in normalized_text
            for signal in [
                "aprobacion",
                "en revision",
                "pendiente de revision",
            ]
        ):
            return "submitted_for_approval"
        if any(
            signal in normalized_text
            for signal in [
                "algo no funciona",
                "no se pudo",
                "intentalo de nuevo",
                "error",
                "no disponible",
                "bloqueado",
            ]
        ):
            return "publish_blocked_or_unavailable"
        return None

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
