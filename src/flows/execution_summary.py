from __future__ import annotations

import logging

from src.flows.flow_result import FlowResult


def log_flow_execution_summary(
    logger: logging.Logger, flow_name: str, flow_result: FlowResult
) -> None:
    logger.info(
        "flow_execution_summary flow_name=%s success=%s step=%s current_url=%s run_id=%s artifact_dir=%s screenshot_path=%s post_publish_status=%s",
        flow_name,
        flow_result.success,
        flow_result.step,
        flow_result.current_url,
        flow_result.run_id,
        flow_result.artifact_dir,
        flow_result.screenshot_path,
        (
            flow_result.post_publish_outcome.status
            if flow_result.post_publish_outcome is not None
            else None
        ),
    )
