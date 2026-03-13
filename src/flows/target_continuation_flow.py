from __future__ import annotations

import logging

from playwright.sync_api import Page

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.pages.target_page import TargetPage


def run_target_continuation_flow(
    page: Page,
    settings: Settings,
    run_context: RunContext,
    logger: logging.Logger,
    *,
    item_text: str | None = None,
    item_selector: str | None = None,
) -> FlowResult:
    target_page = TargetPage(page=page, screenshot_dir=run_context.artifact_dir)
    current_step = "wait_ready"

    try:
        logger.info("target_continuation_flow_wait_ready")
        target_page.wait_until_ready()

        current_step = "validate_allowed_domain"
        logger.info("target_continuation_flow_validate_allowed_domain")
        target_page.assert_in_allowed_domain(allowed_domain=settings.allowed_domain)

        current_step = "assert_content_visible"
        logger.info("target_continuation_flow_assert_content_visible")
        target_page.assert_content_visible()

        current_step = "open_item_secondary_action"
        logger.info("target_continuation_flow_open_item_secondary_action")
        target_page.open_item_secondary_action(
            text=item_text, item_selector=item_selector
        )

        current_step = "assert_next_state_visible"
        logger.info("target_continuation_flow_assert_next_state_visible")
        target_page.assert_next_state_visible()

        current_step = "capture_checkpoint"
        logger.info("target_continuation_flow_capture_checkpoint")
        checkpoint_path = target_page.capture_checkpoint(
            name="target_continuation_ready"
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
        logger.exception("target_continuation_flow_failed step=%s", current_step)
        try:
            target_page.capture_checkpoint(name="target_continuation_failure")
        except Exception:
            logger.exception(
                "target_continuation_flow_failure_screenshot_failed step=%s",
                current_step,
            )
        raise
