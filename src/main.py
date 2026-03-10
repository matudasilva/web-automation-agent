from __future__ import annotations

from pathlib import Path

from src.browser.factory import browser_session
from src.core.config import get_settings, validate_allowed_domain
from src.core.logging import configure_logging, get_logger
from src.services.screenshot_service import capture_page_screenshot


def run_bootstrap() -> Path:
    configure_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    validate_allowed_domain(
        base_url=settings.base_url, allowed_domain=settings.allowed_domain
    )

    logger.info("bootstrap_start")
    with browser_session(settings) as page:
        logger.info("open_base_url")
        page.goto(settings.base_url, wait_until="domcontentloaded")
        logger.info("capture_screenshot")
        screenshot_path = capture_page_screenshot(
            page=page, screenshot_dir=settings.screenshot_dir, name="bootstrap"
        )
        # TODO: Add target-site page objects and deterministic business flow steps.

    logger.info("bootstrap_complete")
    return screenshot_path


def main() -> None:
    run_bootstrap()


if __name__ == "__main__":
    main()
