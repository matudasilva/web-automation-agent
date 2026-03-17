from __future__ import annotations

import logging
from pathlib import Path

from src.core.config import Settings
from src.core.post_publish_status import PostPublishOutcome
from src.flows.flow_result import FlowResult
from src.flows.run_context import RunContext
from src.main import run_bootstrap


def test_bootstrap_runs_landing_flow(tmp_path, monkeypatch, caplog) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-123"
    settings = Settings(
        base_url="https://example.com",
        browser="firefox",
        headless=True,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
        wait_for_manual_ready=False,
        wait_for_manual_publish_confirmation=False,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=tmp_path / "group_targets.txt",
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Las Piedras, la paz Progreso, Colon",
    )
    expected_path = artifact_dir / "group-01" / "marketplace_group_share_ready.png"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_bytes(b"fake-image")

    landing_calls: list[tuple[object, object, object, object]] = []
    marketplace_calls: list[tuple[object, object, object, object, str, str]] = []

    class FakeContextManager:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    caplog.set_level(logging.INFO, logger="src.main")
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(
            run_id="run-123", artifact_dir=artifact_dir
        ),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: landing_calls.append(
            (page, settings, run_context, logger)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            run_id="run-123",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: marketplace_calls.append(
            (page, settings, run_context, logger, listing_title, group_name)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com/marketplace/you/selling",
            run_id="run-123",
            artifact_dir=run_context.artifact_dir,
            screenshot_path=expected_path,
        ),
    )

    screenshot_path = run_bootstrap()

    assert len(landing_calls) == 1
    assert landing_calls[0][1] == settings
    assert landing_calls[0][2] == RunContext(run_id="run-123", artifact_dir=artifact_dir)
    assert len(marketplace_calls) == 1
    assert marketplace_calls[0][1] == settings
    assert marketplace_calls[0][2] == RunContext(
        run_id="run-123", artifact_dir=artifact_dir / "group-01"
    )
    assert marketplace_calls[0][4:] == (
        "Botitas de gamuza tipo desert",
        "Las Piedras, la paz Progreso, Colon",
    )
    assert screenshot_path == expected_path
    assert (
        "flow_execution_summary flow_name=landing_flow success=True "
        "step=capture_checkpoint current_url=https://example.com run_id=run-123 "
        f"artifact_dir={artifact_dir} screenshot_path={artifact_dir / 'landing_ready.png'} "
        "post_publish_status=None"
    ) in caplog.text
    assert (
        "flow_execution_summary flow_name=marketplace_group_share_flow success=True "
        "step=capture_checkpoint current_url=https://example.com/marketplace/you/selling "
        f"run_id=run-123 artifact_dir={artifact_dir / 'group-01'} screenshot_path={expected_path} "
        "post_publish_status=None"
    ) in caplog.text


def test_bootstrap_waits_for_manual_ready_when_enabled(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-456"
    settings = Settings(
        base_url="https://www.facebook.com",
        browser="firefox",
        headless=False,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="facebook.com",
        wait_for_manual_ready=True,
        wait_for_manual_publish_confirmation=False,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=tmp_path / "group_targets.txt",
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Las Piedras, la paz Progreso, Colon",
    )
    page = type(
        "FakePage",
        (),
        {
            "goto_calls": [],
            "goto": lambda self, url, wait_until: self.goto_calls.append(
                (url, wait_until)
            ),
            "wait_for_timeout": lambda self, timeout_ms: None,
        },
    )()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(run_id="run-456", artifact_dir=artifact_dir),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com",
            run_id="run-456",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com/marketplace/you/selling",
            run_id="run-456",
            artifact_dir=artifact_dir / "group-01",
            screenshot_path=artifact_dir / "group-01" / "marketplace_group_share_ready.png",
        ),
    )
    prompts: list[str] = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    caplog.set_level(logging.INFO, logger="src.main")

    run_bootstrap()

    assert page.goto_calls == [("https://www.facebook.com", "domcontentloaded")]
    assert prompts == ["Manual login/session ready. Press Enter to continue..."]
    assert "manual_ready_waiting_for_enter" in caplog.text


def test_bootstrap_waits_for_manual_publish_confirmation_when_enabled(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-789"
    settings = Settings(
        base_url="https://www.facebook.com",
        browser="firefox",
        headless=False,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="facebook.com",
        wait_for_manual_ready=False,
        wait_for_manual_publish_confirmation=True,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=tmp_path / "group_targets.txt",
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Las Piedras, la paz Progreso, Colon",
    )
    page = object()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(run_id="run-789", artifact_dir=artifact_dir),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com",
            run_id="run-789",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com/marketplace/you/selling",
            run_id="run-789",
            artifact_dir=artifact_dir / "group-01",
            screenshot_path=artifact_dir / "group-01" / "marketplace_group_share_ready.png",
        ),
    )
    prompts: list[str] = []
    screenshots: list[tuple[object, Path, str]] = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    monkeypatch.setattr(
        "src.pages.marketplace_group_share_page.MarketplaceGroupSharePage.detect_post_publish_status",
        lambda self: PostPublishOutcome(
            status="publish_success_confirmed",
            observed_text="toast=Se compartió en tu grupo. Ver",
            signal="toast_success",
        ),
    )
    monkeypatch.setattr(
        "src.main.capture_page_screenshot",
        lambda page, screenshot_dir, name: screenshots.append(
            (page, screenshot_dir, name)
        )
        or artifact_dir / f"{name}.png",
    )
    caplog.set_level(logging.INFO, logger="src.main")

    run_bootstrap()

    assert prompts == [
        "Composer listo. Haz clic manualmente en Publicar, verifica que la publicación se haya enviado correctamente y luego presiona Enter para finalizar."
    ]
    assert screenshots == [(page, artifact_dir / "group-01", "manual_publish_result")]
    assert "marketplace_group_share_flow_manual_publish_handoff" in caplog.text
    assert (
        "marketplace_group_share_flow_manual_publish_result "
        "status=publish_success_confirmed signal=toast_success observed_text=toast=Se compartió en tu grupo. Ver"
    ) in caplog.text
    assert "post_publish_status=publish_success_confirmed" in caplog.text


def test_bootstrap_runs_marketplace_group_share_batch_from_targets_file(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-batch"
    group_targets_file = tmp_path / "group_targets.txt"
    group_targets_file.write_text("Grupo Uno\n\nGrupo Dos\n", encoding="utf-8")
    settings = Settings(
        base_url="https://example.com",
        browser="firefox",
        headless=True,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
        wait_for_manual_ready=False,
        wait_for_manual_publish_confirmation=False,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=group_targets_file,
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Fallback Group",
    )
    expected_path = artifact_dir / "group-02" / "marketplace_group_share_ready.png"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_bytes(b"fake-image")

    marketplace_calls: list[tuple[object, object, object, object, str, str]] = []

    class FakePage:
        def __init__(self) -> None:
            self.timeout_calls: list[int] = []

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    caplog.set_level(logging.INFO, logger="src.main")
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(
            run_id="run-batch", artifact_dir=artifact_dir
        ),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            run_id="run-batch",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )
    monkeypatch.setattr(
        "src.main.run_marketplace_group_share_flow",
        lambda page, settings, run_context, logger, listing_title, group_name: marketplace_calls.append(
            (page, settings, run_context, logger, listing_title, group_name)
        )
        or FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com/marketplace/you/selling",
            run_id="run-batch",
            artifact_dir=run_context.artifact_dir,
            screenshot_path=run_context.artifact_dir / "marketplace_group_share_ready.png",
        ),
    )

    screenshot_path = run_bootstrap()

    assert screenshot_path == expected_path
    assert [call[5] for call in marketplace_calls] == ["Grupo Uno", "Grupo Dos"]
    assert marketplace_calls[0][2] == RunContext(
        run_id="run-batch", artifact_dir=artifact_dir / "group-01"
    )
    assert marketplace_calls[1][2] == RunContext(
        run_id="run-batch", artifact_dir=artifact_dir / "group-02"
    )
    assert page.timeout_calls == [1500]
    assert (
        "marketplace_group_share_batch_iteration_start index=1 total=2 group_name=Grupo Uno"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_iteration_start index=2 total=2 group_name=Grupo Dos"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Uno attempts=1 post_publish_status=none final_result=success"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Dos attempts=1 post_publish_status=none final_result=success"
        in caplog.text
    )


def test_bootstrap_retries_group_after_publish_warning_and_continues(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-retry-warning"
    group_targets_file = tmp_path / "group_targets.txt"
    group_targets_file.write_text("Grupo Uno\nGrupo Dos\n", encoding="utf-8")
    settings = Settings(
        base_url="https://www.facebook.com",
        browser="firefox",
        headless=False,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="facebook.com",
        wait_for_manual_ready=False,
        wait_for_manual_publish_confirmation=True,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=group_targets_file,
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Fallback Group",
    )

    class FakePage:
        def __init__(self) -> None:
            self.timeout_calls: list[int] = []

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    caplog.set_level(logging.INFO, logger="src.main")
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(
            run_id="run-retry-warning", artifact_dir=artifact_dir
        ),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com",
            run_id="run-retry-warning",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )

    marketplace_calls: list[str] = []

    def fake_run_marketplace_group_share_flow(
        page, settings, run_context, logger, listing_title, group_name
    ):
        marketplace_calls.append(group_name)
        return FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://www.facebook.com/marketplace/you/selling",
            run_id="run-retry-warning",
            artifact_dir=run_context.artifact_dir,
            screenshot_path=run_context.artifact_dir / "marketplace_group_share_ready.png",
        )

    outcomes = iter(
        [
            PostPublishOutcome(
                status="publish_needs_retry",
                observed_text="toast=No se pudo compartir.",
                signal="toast_retry_or_error",
            ),
            PostPublishOutcome(
                status="publish_needs_retry",
                observed_text="toast=No se pudo compartir.",
                signal="toast_retry_or_error",
            ),
            PostPublishOutcome(
                status="publish_needs_retry",
                observed_text="toast=No se pudo compartir.",
                signal="toast_retry_or_error",
            ),
            PostPublishOutcome(
                status="publish_success_confirmed",
                observed_text="toast=Se compartió en tu grupo. Ver",
                signal="toast_success",
            ),
        ]
    )

    monkeypatch.setattr("src.main.run_marketplace_group_share_flow", fake_run_marketplace_group_share_flow)
    monkeypatch.setattr(
        "src.main.wait_for_manual_publish_confirmation",
        lambda page, screenshot_dir, logger: (
            next(outcomes),
            screenshot_dir / "manual_publish_result.png",
        ),
    )

    screenshot_path = run_bootstrap()

    assert marketplace_calls == ["Grupo Uno", "Grupo Uno", "Grupo Uno", "Grupo Dos"]
    assert screenshot_path == artifact_dir / "group-02" / "manual_publish_result.png"
    assert (
        "marketplace_group_share_batch_group_attempt_result group_name=Grupo Uno attempt=1 post_publish_status=publish_needs_retry final_result=publish_needs_retry"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_skipped_after_publish_retry_exhausted group_name=Grupo Uno attempts=3"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Uno attempts=3 post_publish_status=publish_needs_retry final_result=skipped_after_publish_retry_exhausted"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Dos attempts=1 post_publish_status=publish_success_confirmed final_result=success"
        in caplog.text
    )


def test_bootstrap_retries_group_flow_failure_and_continues(
    tmp_path, monkeypatch, caplog
) -> None:
    screenshot_dir = tmp_path / "screenshots"
    artifact_dir = screenshot_dir / "run-retry-failure"
    group_targets_file = tmp_path / "group_targets.txt"
    group_targets_file.write_text("Grupo Uno\nGrupo Dos\n", encoding="utf-8")
    settings = Settings(
        base_url="https://example.com",
        browser="firefox",
        headless=True,
        browser_profile_dir=tmp_path / "profile",
        screenshot_dir=screenshot_dir,
        allowed_domain="example.com",
        wait_for_manual_ready=False,
        wait_for_manual_publish_confirmation=False,
        ui_action_delay_ms=700,
        ui_iteration_delay_ms=1500,
        marketplace_group_targets_file=group_targets_file,
        marketplace_listing_title="Botitas de gamuza tipo desert",
        marketplace_group_name="Fallback Group",
    )

    class FakePage:
        def __init__(self) -> None:
            self.timeout_calls: list[int] = []

        def wait_for_timeout(self, timeout_ms: int) -> None:
            self.timeout_calls.append(timeout_ms)

    page = FakePage()

    class FakeContextManager:
        def __enter__(self):
            return page

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("src.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.main.browser_session", lambda _settings: FakeContextManager())
    monkeypatch.setattr("src.main.configure_ui_action_delay", lambda delay_ms: None)
    monkeypatch.setattr("src.main.configure_logging", lambda: None)
    caplog.set_level(logging.INFO, logger="src.main")
    monkeypatch.setattr(
        "src.main.create_run_context",
        lambda _artifact_base_dir: RunContext(
            run_id="run-retry-failure", artifact_dir=artifact_dir
        ),
    )
    monkeypatch.setattr(
        "src.main.run_landing_flow",
        lambda page, settings, run_context, logger: FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com",
            run_id="run-retry-failure",
            artifact_dir=artifact_dir,
            screenshot_path=artifact_dir / "landing_ready.png",
        ),
    )

    marketplace_calls: list[str] = []

    def fake_run_marketplace_group_share_flow(
        page, settings, run_context, logger, listing_title, group_name
    ):
        marketplace_calls.append(group_name)
        if group_name == "Grupo Uno":
            raise RuntimeError("group picker did not open")
        return FlowResult(
            success=True,
            step="capture_checkpoint",
            current_url="https://example.com/marketplace/you/selling",
            run_id="run-retry-failure",
            artifact_dir=run_context.artifact_dir,
            screenshot_path=run_context.artifact_dir / "marketplace_group_share_ready.png",
        )

    monkeypatch.setattr("src.main.run_marketplace_group_share_flow", fake_run_marketplace_group_share_flow)

    screenshot_path = run_bootstrap()

    assert marketplace_calls == ["Grupo Uno", "Grupo Uno", "Grupo Uno", "Grupo Dos"]
    assert screenshot_path == artifact_dir / "group-02" / "marketplace_group_share_ready.png"
    assert (
        "marketplace_group_share_batch_group_skipped_after_attempt_failures group_name=Grupo Uno attempts=3"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Uno attempts=3 post_publish_status=none final_result=skipped_after_attempt_failures"
        in caplog.text
    )
    assert (
        "marketplace_group_share_batch_group_final_result group_name=Grupo Dos attempts=1 post_publish_status=none final_result=success"
        in caplog.text
    )
