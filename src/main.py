from __future__ import annotations

from pathlib import Path

from src.browser.factory import browser_session
from src.browser.ui_actions import configure_ui_action_delay
from src.core.config import get_settings, validate_allowed_domain
from src.core.logging import configure_logging, get_logger
from src.flows.execution_summary import log_flow_execution_summary
from src.flows.flow_result import FlowResult
from src.flows.landing_flow import run_landing_flow
from src.flows.marketplace_group_share_flow import run_marketplace_group_share_flow
from src.flows.run_context import RunContext, create_run_context
from src.services.screenshot_service import capture_page_screenshot


def run_bootstrap() -> Path:
    configure_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    configure_ui_action_delay(settings.ui_action_delay_ms)
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

        flow_result = run_marketplace_group_share_batch(
            page=page,
            settings=settings,
            run_context=run_context,
            logger=logger,
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


def wait_for_manual_publish_confirmation(*, page, screenshot_dir: Path, logger) -> None:
    logger.info("marketplace_group_share_flow_manual_publish_handoff")
    input(
        "Composer listo. Haz clic manualmente en Publicar, verifica que la publicación "
        "se haya enviado correctamente y luego presiona Enter para finalizar."
    )
    capture_page_screenshot(
        page=page,
        screenshot_dir=screenshot_dir,
        name="manual_publish_confirmed",
    )


def run_marketplace_group_share_batch(
    *, page, settings, run_context: RunContext, logger
) -> FlowResult:
    group_targets = resolve_group_targets(settings)
    total_groups = len(group_targets)
    last_flow_result: FlowResult | None = None

    for index, group_name in enumerate(group_targets, start=1):
        iteration_run_context = create_iteration_run_context(run_context, index)
        logger.info(
            "marketplace_group_share_batch_iteration_start index=%s total=%s group_name=%s",
            index,
            total_groups,
            group_name,
        )
        flow_result = run_marketplace_group_share_flow(
            page=page,
            settings=settings,
            run_context=iteration_run_context,
            logger=logger,
            listing_title=settings.marketplace_listing_title,
            group_name=group_name,
        )
        log_flow_execution_summary(
            logger=logger,
            flow_name="marketplace_group_share_flow",
            flow_result=flow_result,
        )

        if settings.wait_for_manual_publish_confirmation:
            wait_for_manual_publish_confirmation(
                page=page,
                screenshot_dir=iteration_run_context.artifact_dir,
                logger=logger,
            )
        last_flow_result = flow_result
        if index < total_groups:
            page.wait_for_timeout(settings.ui_iteration_delay_ms)

    if last_flow_result is None:
        raise RuntimeError("No marketplace group targets were resolved for execution")
    return last_flow_result


def resolve_group_targets(settings) -> list[str]:
    file_targets = load_group_targets_file(settings.marketplace_group_targets_file)
    if file_targets:
        return file_targets
    return [settings.marketplace_group_name]


def load_group_targets_file(group_targets_file: Path) -> list[str]:
    if not group_targets_file.exists():
        return []

    return [
        line.strip()
        for line in group_targets_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def create_iteration_run_context(
    base_run_context: RunContext, iteration_index: int
) -> RunContext:
    artifact_dir = base_run_context.artifact_dir / f"group-{iteration_index:02d}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(run_id=base_run_context.run_id, artifact_dir=artifact_dir)


if __name__ == "__main__":
    main()
