from __future__ import annotations

from pathlib import Path

from src.core.config import get_settings


def test_get_settings_reads_browser_profile_and_manual_ready(monkeypatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://www.facebook.com")
    monkeypatch.setenv("BROWSER", "firefox")
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setenv("BROWSER_PROFILE_DIR", "./runtime/profiles/firefox-marketplace")
    monkeypatch.setenv("SCREENSHOT_DIR", "./screenshots")
    monkeypatch.setenv("ALLOWED_DOMAIN", "facebook.com")
    monkeypatch.setenv("WAIT_FOR_MANUAL_READY", "true")
    monkeypatch.setenv("MARKETPLACE_LISTING_TITLE", "Botitas de gamuza tipo desert")
    monkeypatch.setenv("MARKETPLACE_GROUP_NAME", "Las Piedras, la paz Progreso, Colon")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.base_url == "https://www.facebook.com"
    assert settings.browser == "firefox"
    assert settings.headless is False
    assert settings.browser_profile_dir == Path(
        "./runtime/profiles/firefox-marketplace"
    )
    assert settings.screenshot_dir == Path("./screenshots")
    assert settings.allowed_domain == "facebook.com"
    assert settings.wait_for_manual_ready is True
    assert settings.marketplace_listing_title == "Botitas de gamuza tipo desert"
    assert settings.marketplace_group_name == "Las Piedras, la paz Progreso, Colon"
    get_settings.cache_clear()
