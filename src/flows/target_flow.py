from __future__ import annotations

import logging

from playwright.sync_api import Page

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.pages.target_page import TargetPage


def run_target_flow(
    page: Page,
    settings: Settings,
    run_context: RunContext,
    logger: logging.Logger,
    input_value: str = "preview",
) -> FlowResult:
    target_page = TargetPage(page=page, screenshot_dir=run_context.artifact_dir)
    current_step = "open_base_url"
    navigation_started = False

    try:
        logger.info("target_flow_open_base_url")
        navigation_started = True
        page.goto(settings.base_url, wait_until="domcontentloaded")

        current_step = "wait_ready"
        logger.info("target_flow_wait_ready")
        target_page.wait_until_ready()

        current_step = "validate_page"
        logger.info("target_flow_validate_page")
        target_page.assert_loaded(
            base_url=settings.base_url, allowed_domain=settings.allowed_domain
        )

        current_step = "assert_content_visible"
        logger.info("target_flow_assert_content_visible")
        target_page.assert_content_visible()

        current_step = "fill_text_input"
        logger.info("target_flow_fill_text_input")
        target_page.fill_text_input(value=input_value)

        current_step = "capture_checkpoint"
        logger.info("target_flow_capture_checkpoint")
        checkpoint_path = target_page.capture_checkpoint(name="target_ready")
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
            logger.exception("target_flow_failed step=%s", current_step)
            try:
                target_page.capture_checkpoint(name="target_failure")
            except Exception:
                logger.exception(
                    "target_flow_failure_screenshot_failed step=%s", current_step
                )
        raise
