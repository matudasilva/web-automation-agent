from __future__ import annotations

from pathlib import Path

from src.browser.factory import browser_session
from src.core.config import get_settings, validate_allowed_domain
from src.core.logging import configure_logging, get_logger
from src.flows.execution_summary import log_flow_execution_summary
from src.flows.landing_flow import run_landing_flow
from src.flows.marketplace_group_share_flow import run_marketplace_group_share_flow
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
        if settings.wait_for_manual_ready:
            wait_for_manual_ready(page=page, base_url=settings.base_url, logger=logger)

        landing_result = run_landing_flow(
            page=page, settings=settings, run_context=run_context, logger=logger
        )
        log_flow_execution_summary(
            logger=logger, flow_name="landing_flow", flow_result=landing_result
        )

        flow_result = run_marketplace_group_share_flow(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
            listing_title=settings.marketplace_listing_title,
            group_name=settings.marketplace_group_name,
        )
        log_flow_execution_summary(
            logger=logger,
            flow_name="marketplace_group_share_flow",
            flow_result=flow_result,
        )

    if flow_result.screenshot_path is None:
        raise RuntimeError(
            "Marketplace group share flow completed without a screenshot path"
        )

    logger.info("bootstrap_complete")
    return flow_result.screenshot_path


def main() -> None:
    run_bootstrap()


def wait_for_manual_ready(*, page, base_url: str, logger) -> None:
    logger.info("manual_ready_open_base_url")
    page.goto(base_url, wait_until="domcontentloaded")
    logger.info("manual_ready_waiting_for_enter")
    input("Manual login/session ready. Press Enter to continue...")


if __name__ == "__main__":
    main()
