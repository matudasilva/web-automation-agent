from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.core.logging import create_run_log_file_path


def test_create_run_log_file_path_uses_logs_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.core.logging.LOG_DIR", tmp_path / "logs")

    log_path = create_run_log_file_path(datetime(2026, 3, 17, 18, 45, 12))

    assert log_path == tmp_path / "logs" / "2026-03-17_18-45-12_src_main.log"
    assert log_path.parent.exists()


def test_configure_logging_writes_to_stream_and_file(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr("src.core.logging.LOG_DIR", tmp_path / "logs")

    from src.core.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger("test.logging")
    logger.info("hello logging")

    captured = capsys.readouterr()
    assert "hello logging" in captured.out

    log_files = list((tmp_path / "logs").glob("*_src_main.log"))
    assert len(log_files) == 1
    assert "hello logging" in log_files[0].read_text(encoding="utf-8")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
