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
    monkeypatch.setenv("WAIT_FOR_MANUAL_PUBLISH_CONFIRMATION", "true")
    monkeypatch.setenv("AUTO_PUBLISH_TO_GROUPS", "true")
    monkeypatch.setenv("RUNTIME_PLANNING_DRY_RUN", "true")
    monkeypatch.setenv("RUNTIME_ARTICLE_ROUTING_FILE", "./runtime/article_routing.csv")
    monkeypatch.setenv(
        "RUNTIME_CATEGORY_ROUTING_FILE", "./runtime/category_routing.csv"
    )
    monkeypatch.setenv("RUNTIME_GROUP_COHORTS_FILE", "./runtime/group_cohorts.csv")
    monkeypatch.setenv(
        "RUNTIME_POSTING_WINDOWS_FILE", "./runtime/posting_windows.csv"
    )
    monkeypatch.setenv("UI_ACTION_DELAY_MS", "700")
    monkeypatch.setenv("UI_ITERATION_DELAY_MS", "1500")
    monkeypatch.setenv("MARKETPLACE_LISTING_DISCOVERY_MAX_SCROLLS", "4")
    monkeypatch.setenv("MARKETPLACE_LISTING_DISCOVERY_SCROLL_DELAY_MS", "450")
    monkeypatch.setenv("MARKETPLACE_GROUP_TARGETS_FILE", "./runtime/group_targets.txt")
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
    assert settings.wait_for_manual_publish_confirmation is True
    assert settings.auto_publish_to_groups is True
    assert settings.runtime_planning_dry_run is True
    assert settings.ui_action_delay_ms == 700
    assert settings.ui_iteration_delay_ms == 1500
    assert settings.runtime_article_routing_file == Path("./runtime/article_routing.csv")
    assert settings.runtime_category_routing_file == Path(
        "./runtime/category_routing.csv"
    )
    assert settings.runtime_group_cohorts_file == Path("./runtime/group_cohorts.csv")
    assert settings.runtime_posting_windows_file == Path(
        "./runtime/posting_windows.csv"
    )
    assert settings.marketplace_listing_discovery_max_scrolls == 4
    assert settings.marketplace_listing_discovery_scroll_delay_ms == 450
    assert settings.marketplace_group_targets_file == Path("./runtime/group_targets.txt")
    assert settings.marketplace_listing_title == "Botitas de gamuza tipo desert"
    assert settings.marketplace_group_name == "Las Piedras, la paz Progreso, Colon"
    get_settings.cache_clear()


def test_get_settings_reads_explicit_manual_auto_publish_setting(monkeypatch) -> None:
    monkeypatch.setenv("AUTO_PUBLISH_TO_GROUPS", "false")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.auto_publish_to_groups is False
    get_settings.cache_clear()
