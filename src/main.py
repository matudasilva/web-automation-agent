from __future__ import annotations

from pathlib import Path

from src.browser.factory import browser_session
from src.core.config import get_settings, validate_allowed_domain
from src.core.logging import configure_logging, get_logger
from src.flows.landing_flow import run_landing_flow
from src.flows.run_context import create_run_context


def run_bootstrap() -> Path:
    configure_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    validate_allowed_domain(
        base_url=settings.base_url, allowed_domain=settings.allowed_domain
    )
    run_context = create_run_context(settings.screenshot_dir)

    logger.info("bootstrap_start")
    with browser_session(settings) as page:
        flow_result = run_landing_flow(
            page=page, settings=settings, run_context=run_context, logger=logger
        )

    if flow_result.screenshot_path is None:
        raise RuntimeError("Landing flow completed without a screenshot path")

    logger.info("bootstrap_complete")
    return flow_result.screenshot_path


def main() -> None:
    run_bootstrap()


if __name__ == "__main__":
    main()
