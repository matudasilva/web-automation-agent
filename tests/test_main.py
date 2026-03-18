from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from src.core.config import Settings
from src.core.post_publish_status import PostPublishOutcome
from src.main import (
    execute_auto_publish,
    finalize_group_publish,
    get_local_now,
    load_group_targets_file,
    resolve_group_targets,
)


def test_load_group_targets_file_ignores_blank_lines(tmp_path) -> None:
    group_targets_file = tmp_path / "group_targets.txt"
    group_targets_file.write_text("\nGrupo Uno\n\nGrupo Dos\n", encoding="utf-8")

    targets = load_group_targets_file(group_targets_file)

    assert targets == ["Grupo Uno", "Grupo Dos"]


def test_get_local_now_uses_uruguay_timezone(monkeypatch) -> None:
    expected_now = datetime(2026, 3, 18, 10, 15, tzinfo=ZoneInfo("America/Montevideo"))

    class FakeDateTime:
        @staticmethod
        def now(tz):
            assert tz == ZoneInfo("America/Montevideo")
            return expected_now

    monkeypatch.setattr("src.main.datetime", FakeDateTime)

    assert get_local_now() == expected_now


def test_resolve_group_targets_falls_back_to_single_group_when_file_missing(
    tmp_path,
) -> None:
    settings = Settings(
        base_url="https://example.com",
        marketplace_group_targets_file=tmp_path / "missing.txt",
        marketplace_group_name="Grupo Fallback",
    )

    targets = resolve_group_targets(settings)

    assert targets == ["Grupo Fallback"]


def test_finalize_group_publish_keeps_manual_mode_by_default(
    tmp_path, monkeypatch
) -> None:
    settings = Settings(
        auto_publish_to_groups=False,
        wait_for_manual_publish_confirmation=True,
    )
    expected_outcome = PostPublishOutcome(
        status="publish_success_confirmed",
        observed_text="toast=Se compartió en tu grupo. Ver",
        signal="toast_success",
    )
    expected_path = tmp_path / "manual_publish_result.png"

    monkeypatch.setattr(
        "src.main.wait_for_manual_publish_confirmation",
        lambda page, screenshot_dir, logger: (expected_outcome, expected_path),
    )

    result = finalize_group_publish(
        page=object(),
        settings=settings,
        screenshot_dir=tmp_path,
        logger=logging.getLogger("test.main.manual_publish"),
    )

    assert result == (expected_outcome, expected_path)


def test_finalize_group_publish_uses_auto_publish_when_enabled(
    tmp_path, monkeypatch
) -> None:
    settings = Settings(
        auto_publish_to_groups=True,
        wait_for_manual_publish_confirmation=True,
    )
    expected_outcome = PostPublishOutcome(
        status="publish_success_confirmed",
        observed_text="toast=Se compartió en tu grupo. Ver",
        signal="toast_success",
    )
    expected_path = tmp_path / "auto_publish_result.png"

    monkeypatch.setattr(
        "src.main.execute_auto_publish",
        lambda page, screenshot_dir, logger: (expected_outcome, expected_path),
    )

    result = finalize_group_publish(
        page=object(),
        settings=settings,
        screenshot_dir=tmp_path,
        logger=logging.getLogger("test.main.auto_publish"),
    )

    assert result == (expected_outcome, expected_path)


def test_execute_auto_publish_runs_publish_and_post_publish_detection(
    tmp_path, monkeypatch
) -> None:
    expected_outcome = PostPublishOutcome(
        status="publish_success_confirmed",
        observed_text="toast=Se compartió en tu grupo. Ver",
        signal="toast_success",
    )
    calls: list[str] = []

    class FakeMarketplacePage:
        def __init__(self, *, page, screenshot_dir) -> None:
            assert screenshot_dir == tmp_path

        def publish_group_composer(self) -> None:
            calls.append("publish_group_composer")

        def wait_for_post_publish_signal(self) -> None:
            calls.append("wait_for_post_publish_signal")

        def detect_post_publish_status(self) -> PostPublishOutcome:
            calls.append("detect_post_publish_status")
            return expected_outcome

    monkeypatch.setattr(
        "src.main.MarketplaceGroupSharePage",
        FakeMarketplacePage,
    )
    monkeypatch.setattr(
        "src.main.capture_page_screenshot",
        lambda page, screenshot_dir, name: tmp_path / f"{name}.png",
    )

    outcome, screenshot_path = execute_auto_publish(
        page=object(),
        screenshot_dir=tmp_path,
        logger=logging.getLogger("test.main.execute_auto_publish"),
    )

    assert calls == [
        "publish_group_composer",
        "wait_for_post_publish_signal",
        "detect_post_publish_status",
    ]
    assert outcome == expected_outcome
    assert screenshot_path == tmp_path / "auto_publish_result.png"
