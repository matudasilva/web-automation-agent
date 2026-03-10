from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page


def capture_page_screenshot(
    page: Page, screenshot_dir: Path, name: str = "bootstrap"
) -> Path:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"{name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    return screenshot_path
