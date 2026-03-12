from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Page

from src.core.config import Settings
from src.pages.landing_page import LandingPage


def run_landing_flow(page: Page, settings: Settings, logger: logging.Logger) -> Path:
    landing_page = LandingPage(page=page, screenshot_dir=settings.screenshot_dir)

    logger.info("landing_flow_open_base_url")
    page.goto(settings.base_url, wait_until="domcontentloaded")

    logger.info("landing_flow_wait_ready")
    landing_page.wait_until_ready()

    logger.info("landing_flow_validate_page")
    landing_page.assert_loaded(
        base_url=settings.base_url, allowed_domain=settings.allowed_domain
    )

    logger.info("landing_flow_capture_checkpoint")
    checkpoint_path = landing_page.capture_checkpoint(name="landing_ready")
    # TODO: Add target-site-specific checks when real selectors are defined.
    return checkpoint_path
