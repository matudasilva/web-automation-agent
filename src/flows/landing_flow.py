from __future__ import annotations

import logging

from playwright.sync_api import Page

from src.core.config import Settings
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.pages.landing_page import LandingPage


def run_landing_flow(
    page: Page, settings: Settings, run_context: RunContext, logger: logging.Logger
) -> FlowResult:
    landing_page = LandingPage(page=page, screenshot_dir=run_context.artifact_dir)
    current_step = "open_base_url"
    navigation_started = False

    try:
        logger.info("landing_flow_open_base_url")
        navigation_started = True
        page.goto(settings.base_url, wait_until="domcontentloaded")

        current_step = "wait_ready"
        logger.info("landing_flow_wait_ready")
        landing_page.wait_until_ready()

        current_step = "validate_page"
        logger.info("landing_flow_validate_page")
        landing_page.assert_loaded(
            base_url=settings.base_url, allowed_domain=settings.allowed_domain
        )

        current_step = "capture_checkpoint"
        logger.info("landing_flow_capture_checkpoint")
        checkpoint_path = landing_page.capture_checkpoint(name="landing_ready")
        # TODO: Add target-site-specific checks when real selectors are defined.
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
            logger.exception("landing_flow_failed step=%s", current_step)
            try:
                landing_page.capture_checkpoint(name="landing_failure")
            except Exception:
                logger.exception(
                    "landing_flow_failure_screenshot_failed step=%s", current_step
                )
        raise
