from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.browser.factory import browser_session
from src.browser.ui_actions import configure_ui_action_delay
from src.core.config import get_settings, validate_allowed_domain
from src.core.post_publish_status import PostPublishOutcome
from src.core.logging import configure_logging, get_logger
from src.flows.execution_summary import log_flow_execution_summary
from src.flows.flow_result import FlowResult
from src.flows.landing_flow import run_landing_flow
from src.flows.marketplace_group_share_flow import run_marketplace_group_share_flow
from src.flows.run_context import RunContext, create_run_context
from src.pages.marketplace_group_share_page import MarketplaceGroupSharePage
from src.runtime.job_selector import diagnose_runtime_job_selection
from src.runtime.runtime_loader import load_runtime_planning
from src.services.screenshot_service import capture_page_screenshot

MARKETPLACE_GROUP_MAX_ATTEMPTS = 3


def run_bootstrap() -> Path:
    configure_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    configure_ui_action_delay(settings.ui_action_delay_ms)
    run_context = create_run_context(settings.screenshot_dir)

    if settings.runtime_planning_dry_run:
        runtime_planning = load_runtime_planning(settings)
        logger.info(
            "runtime_planning_summary articles=%s categories=%s cohorts=%s posting_windows=%s",
            runtime_planning.article_count,
            len(runtime_planning.categories),
            len(runtime_planning.cohorts),
            runtime_planning.posting_window_count,
        )
        selection_diagnostic = diagnose_runtime_job_selection(
            runtime_planning,
            current_datetime=get_local_now(),
        )
        selected_job = selection_diagnostic.selected_job
        if selected_job is None:
            logger.info(
                "no_eligible_runtime_job reason=%s",
                selection_diagnostic.no_selection_reason,
            )
        else:
            logger.info(
                "runtime_job_selected article_title=%s category=%s cohort=%s group_name=%s posting_window=%s",
                selected_job.article_title,
                selected_job.category,
                selected_job.cohort,
                selected_job.group_name,
                selected_job.matched_posting_window,
            )
        logger.info("runtime_planning_dry_run_complete")
        return run_context.artifact_dir

    validate_allowed_domain(
        base_url=settings.base_url, allowed_domain=settings.allowed_domain
    )

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


def get_local_now() -> datetime:
    return datetime.now(ZoneInfo("America/Montevideo"))


def wait_for_manual_ready(*, page, base_url: str, logger) -> None:
    logger.info("manual_ready_open_base_url")
    page.goto(base_url, wait_until="domcontentloaded")
    logger.info("manual_ready_waiting_for_enter")
    input("Manual login/session ready. Press Enter to continue...")


def wait_for_manual_publish_confirmation(
    *, page, screenshot_dir: Path, logger
) -> tuple[PostPublishOutcome, Path]:
    logger.info("marketplace_group_share_flow_manual_publish_handoff")
    input(
        "Composer listo. Haz clic manualmente en Publicar, verifica que la publicación "
        "se haya enviado correctamente y luego presiona Enter para finalizar."
    )
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=screenshot_dir
    )
    post_publish_outcome = marketplace_page.detect_post_publish_status()
    logger.info(
        "marketplace_group_share_flow_manual_publish_result status=%s signal=%s observed_text=%s",
        post_publish_outcome.status,
        post_publish_outcome.signal,
        post_publish_outcome.observed_text,
    )
    screenshot_path = capture_page_screenshot(
        page=page,
        screenshot_dir=screenshot_dir,
        name="manual_publish_result",
    )
    return post_publish_outcome, screenshot_path


def execute_auto_publish(
    *, page, screenshot_dir: Path, logger
) -> tuple[PostPublishOutcome, Path]:
    logger.info("marketplace_group_share_flow_auto_publish_start")
    marketplace_page = MarketplaceGroupSharePage(
        page=page, screenshot_dir=screenshot_dir
    )
    marketplace_page.publish_group_composer()
    marketplace_page.wait_for_post_publish_signal()
    post_publish_outcome = marketplace_page.detect_post_publish_status()
    logger.info(
        "marketplace_group_share_flow_auto_publish_result status=%s signal=%s observed_text=%s",
        post_publish_outcome.status,
        post_publish_outcome.signal,
        post_publish_outcome.observed_text,
    )
    screenshot_path = capture_page_screenshot(
        page=page,
        screenshot_dir=screenshot_dir,
        name="auto_publish_result",
    )
    return post_publish_outcome, screenshot_path


def finalize_group_publish(
    *, page, settings, screenshot_dir: Path, logger
) -> tuple[PostPublishOutcome, Path] | None:
    if settings.auto_publish_to_groups:
        return execute_auto_publish(
            page=page,
            screenshot_dir=screenshot_dir,
            logger=logger,
        )
    if settings.wait_for_manual_publish_confirmation:
        return wait_for_manual_publish_confirmation(
            page=page,
            screenshot_dir=screenshot_dir,
            logger=logger,
        )
    return None


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
        flow_result = run_group_with_retries(
            page=page,
            settings=settings,
            run_context=iteration_run_context,
            logger=logger,
            group_name=group_name,
        )
        if flow_result is not None:
            last_flow_result = flow_result
            log_flow_execution_summary(
                logger=logger,
                flow_name="marketplace_group_share_flow",
                flow_result=flow_result,
            )
        if index < total_groups:
            page.wait_for_timeout(settings.ui_iteration_delay_ms)

    if last_flow_result is None:
        raise RuntimeError("No marketplace group targets were resolved for execution")
    return last_flow_result


def run_group_with_retries(
    *, page, settings, run_context: RunContext, logger, group_name: str
) -> FlowResult | None:
    for attempt in range(1, MARKETPLACE_GROUP_MAX_ATTEMPTS + 1):
        logger.info(
            "marketplace_group_share_batch_group_attempt_start group_name=%s attempt=%s max_attempts=%s",
            group_name,
            attempt,
            MARKETPLACE_GROUP_MAX_ATTEMPTS,
        )
        try:
            flow_result = run_marketplace_group_share_flow(
                page=page,
                settings=settings,
                run_context=run_context,
                logger=logger,
                listing_title=settings.marketplace_listing_title,
                group_name=group_name,
            )
            publish_result = finalize_group_publish(
                page=page,
                settings=settings,
                screenshot_dir=run_context.artifact_dir,
                logger=logger,
            )
            if publish_result is not None:
                post_publish_outcome, screenshot_path = publish_result
                flow_result = replace(
                    flow_result,
                    screenshot_path=screenshot_path,
                    post_publish_outcome=post_publish_outcome,
                )
            if publish_result is not None:
                if post_publish_outcome.status == "publish_needs_retry":
                    logger.info(
                        "marketplace_group_share_batch_group_attempt_result group_name=%s attempt=%s post_publish_status=%s final_result=%s",
                        group_name,
                        attempt,
                        post_publish_outcome.status,
                        "publish_needs_retry",
                    )
                    logger.warning(
                        "marketplace_group_share_batch_group_attempt_publish_retry_needed group_name=%s attempt=%s max_attempts=%s",
                        group_name,
                        attempt,
                        MARKETPLACE_GROUP_MAX_ATTEMPTS,
                    )
                    if attempt < MARKETPLACE_GROUP_MAX_ATTEMPTS:
                        continue
                    logger.error(
                        "marketplace_group_share_batch_group_skipped_after_publish_retry_exhausted group_name=%s attempts=%s",
                        group_name,
                        MARKETPLACE_GROUP_MAX_ATTEMPTS,
                    )
                    logger.info(
                        "marketplace_group_share_batch_group_final_result group_name=%s attempts=%s post_publish_status=%s final_result=%s",
                        group_name,
                        MARKETPLACE_GROUP_MAX_ATTEMPTS,
                        post_publish_outcome.status,
                        "skipped_after_publish_retry_exhausted",
                    )
                    return None
            logger.info(
                "marketplace_group_share_batch_group_attempt_result group_name=%s attempt=%s post_publish_status=%s final_result=%s",
                group_name,
                attempt,
                _get_post_publish_status(flow_result),
                "success",
            )
            logger.info(
                "marketplace_group_share_batch_group_final_result group_name=%s attempts=%s post_publish_status=%s final_result=%s",
                group_name,
                attempt,
                _get_post_publish_status(flow_result),
                "success",
            )
            return flow_result
        except Exception:
            logger.exception(
                "marketplace_group_share_batch_group_attempt_failed group_name=%s attempt=%s max_attempts=%s",
                group_name,
                attempt,
                MARKETPLACE_GROUP_MAX_ATTEMPTS,
            )
            if attempt >= MARKETPLACE_GROUP_MAX_ATTEMPTS:
                logger.error(
                    "marketplace_group_share_batch_group_skipped_after_attempt_failures group_name=%s attempts=%s",
                    group_name,
                    MARKETPLACE_GROUP_MAX_ATTEMPTS,
                )
                logger.info(
                    "marketplace_group_share_batch_group_final_result group_name=%s attempts=%s post_publish_status=%s final_result=%s",
                    group_name,
                    MARKETPLACE_GROUP_MAX_ATTEMPTS,
                    "none",
                    "skipped_after_attempt_failures",
                )
                return None
    return None


def _get_post_publish_status(flow_result: FlowResult) -> str:
    if flow_result.post_publish_outcome is None:
        return "none"
    return flow_result.post_publish_outcome.status


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
