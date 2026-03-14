from __future__ import annotations

import logging

from playwright.sync_api import Page

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.pages.marketplace_group_share_page import MarketplaceGroupSharePage


def run_marketplace_group_share_flow(
    page: Page,
    settings: Settings,
    run_context: RunContext,
    logger: logging.Logger,
    *,
    listing_title: str,
    group_name: str,
) -> FlowResult:
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=run_context.artifact_dir
    )
    current_step = "open_base_url"
    navigation_started = False

    try:
        logger.info("marketplace_group_share_flow_open_base_url")
        navigation_started = True
        page.goto(settings.base_url, wait_until="domcontentloaded")

        current_step = "wait_ready"
        logger.info("marketplace_group_share_flow_wait_ready")
        marketplace_page.wait_until_ready()

        current_step = "validate_marketplace_selling_page"
        logger.info("marketplace_group_share_flow_validate_marketplace_selling_page")
        marketplace_page.assert_marketplace_selling_loaded(
            base_url=settings.base_url, allowed_domain=settings.allowed_domain
        )

        current_step = "open_listing_share_dialog"
        logger.info("marketplace_group_share_flow_open_listing_share_dialog")
        marketplace_page.open_listing_share_dialog(listing_title)

        current_step = "assert_share_dialog_visible"
        logger.info("marketplace_group_share_flow_assert_share_dialog_visible")
        marketplace_page.assert_share_dialog_visible()

        current_step = "open_group_destination"
        logger.info("marketplace_group_share_flow_open_group_destination")
        marketplace_page.open_group_destination()

        current_step = "assert_group_picker_visible"
        logger.info("marketplace_group_share_flow_assert_group_picker_visible")
        marketplace_page.assert_group_picker_visible()

        current_step = "select_group"
        logger.info("marketplace_group_share_flow_select_group")
        marketplace_page.select_group(group_name)

        current_step = "assert_group_composer_visible"
        logger.info("marketplace_group_share_flow_assert_group_composer_visible")
        marketplace_page.assert_group_composer_visible()

        current_step = "capture_checkpoint"
        logger.info("marketplace_group_share_flow_capture_checkpoint")
        checkpoint_path = marketplace_page.capture_checkpoint(
            name="marketplace_group_share_ready"
        )
        return FlowResult(
            success=True,
            step=current_step,
            current_url=page.url,
            run_id=run_context.run_id,
            artifact_dir=run_context.artifact_dir,
            screenshot_path=checkpoint_path,
        )
    except Exception:
        if navigation_started:
            logger.exception("marketplace_group_share_flow_failed step=%s", current_step)
            try:
                marketplace_page.capture_checkpoint(name="marketplace_group_share_failure")
            except Exception:
                logger.exception(
                    "marketplace_group_share_flow_failure_screenshot_failed step=%s",
                    current_step,
                )
        raise
