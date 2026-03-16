from __future__ import annotations

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

    def __init__(self, page: Page, screenshot_dir: Path) -> None:
        super().__init__(page=page, screenshot_dir=screenshot_dir)
        self.labels = MarketplaceGroupShareLabels()

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

    def find_listing_container(self, listing_title: str) -> Locator:
        title_locator = self.page.get_by_text(listing_title, exact=False)
        wait_for_locator_visible(title_locator)
        share_button_locator = self.page.get_by_role(
            "button", name=self.labels.share_button
        )
        listing_container = (
            self.page.locator("div")
            .filter(has=title_locator)
            .filter(has=share_button_locator)
            .first
        )
        return wait_for_locator_visible(listing_container)

    def find_share_dialog(self) -> Locator:
        share_dialog_heading = self.page.get_by_role(
            "heading", name=self.labels.share_dialog_heading
        )
        share_dialog = self.page.locator("[role='dialog']").filter(
            has=share_dialog_heading
        ).first
        return wait_for_locator_visible(share_dialog)

    def open_listing_share_dialog(self, listing_title: str) -> None:
        listing_container = self.find_listing_container(listing_title)
        share_button = listing_container.get_by_role(
            "button", name=self.labels.share_button
        )
        click_locator_visible(share_button)

    def assert_share_dialog_visible(self) -> None:
        assert_locator_visible(self.find_share_dialog())

    def open_group_destination(self) -> None:
        share_dialog = self.find_share_dialog()
        group_option = share_dialog.get_by_text(
            self.labels.group_destination, exact=True
        )
        click_locator_visible(group_option)

    def find_group_picker_dialog(self) -> Locator:
        group_picker_heading = self.page.get_by_role(
            "heading", name=self.labels.group_picker_heading
        )
        group_picker_dialog = self.page.locator("[role='dialog']").filter(
            has=group_picker_heading
        ).first
        return wait_for_locator_visible(group_picker_dialog)

    def assert_group_picker_visible(self) -> None:
        assert_locator_visible(self.find_group_picker_dialog())

    def select_group(self, group_name: str) -> None:
        group_picker_dialog = self.find_group_picker_dialog()
        group_option = group_picker_dialog.get_by_text(group_name, exact=True)
        click_locator_visible(group_option)

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
        listing_preview = composer_dialog.get_by_text(listing_title, exact=False)
        try:
            assert_locator_visible(
                listing_preview, timeout_ms=self.composer_content_timeout_ms
            )
        except Exception as exc:
            raise ValueError(
                "Group composer is visible but the listing preview content is still loading "
                f"or missing for title fragment '{listing_title}'"
            ) from exc
