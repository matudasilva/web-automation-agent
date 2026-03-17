from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    base_url: str = Field(default="https://example.com")
    browser: str = Field(default="chromium")
    headless: bool = Field(default=True)
    browser_profile_dir: Path | None = Field(default=None)
    screenshot_dir: Path = Field(default=Path("./screenshots"))
    allowed_domain: str = Field(default="example.com")
    wait_for_manual_ready: bool = Field(default=False)
    wait_for_manual_publish_confirmation: bool = Field(default=False)
    auto_publish_to_groups: bool = Field(default=False)
    ui_action_delay_ms: int = Field(default=700)
    ui_iteration_delay_ms: int = Field(default=1500)
    marketplace_listing_discovery_max_scrolls: int = Field(default=3)
    marketplace_listing_discovery_scroll_delay_ms: int = Field(default=400)
    marketplace_group_targets_file: Path = Field(
        default=Path("./runtime/group_targets.txt")
    )
    marketplace_listing_title: str = Field(default="")
    marketplace_group_name: str = Field(default="")


def load_environment() -> None:
    load_dotenv(ENV_FILE, override=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_environment()

    return Settings(
        base_url=_read_env("BASE_URL", "https://example.com"),
        browser=_read_env("BROWSER", "chromium"),
        headless=_read_bool("HEADLESS", True),
        browser_profile_dir=_read_optional_path("BROWSER_PROFILE_DIR"),
        screenshot_dir=Path(_read_env("SCREENSHOT_DIR", "./screenshots")),
        allowed_domain=_read_env("ALLOWED_DOMAIN", "example.com"),
        wait_for_manual_ready=_read_bool("WAIT_FOR_MANUAL_READY", False),
        wait_for_manual_publish_confirmation=_read_bool(
            "WAIT_FOR_MANUAL_PUBLISH_CONFIRMATION", False
        ),
        auto_publish_to_groups=_read_bool("AUTO_PUBLISH_TO_GROUPS", False),
        ui_action_delay_ms=_read_int("UI_ACTION_DELAY_MS", 700),
        ui_iteration_delay_ms=_read_int("UI_ITERATION_DELAY_MS", 1500),
        marketplace_listing_discovery_max_scrolls=_read_int(
            "MARKETPLACE_LISTING_DISCOVERY_MAX_SCROLLS", 3
        ),
        marketplace_listing_discovery_scroll_delay_ms=_read_int(
            "MARKETPLACE_LISTING_DISCOVERY_SCROLL_DELAY_MS", 400
        ),
        marketplace_group_targets_file=Path(
            _read_env("MARKETPLACE_GROUP_TARGETS_FILE", "./runtime/group_targets.txt")
        ),
        marketplace_listing_title=_read_env("MARKETPLACE_LISTING_TITLE", ""),
        marketplace_group_name=_read_env("MARKETPLACE_GROUP_NAME", ""),
    )


def validate_allowed_domain(base_url: str, allowed_domain: str) -> None:
    hostname = urlparse(base_url).hostname
    if not hostname:
        raise ValueError(f"Invalid BASE_URL: {base_url}")

    normalized_allowed = allowed_domain.strip().lower()
    normalized_host = hostname.lower()
    if normalized_host == normalized_allowed:
        return
    if normalized_host.endswith(f".{normalized_allowed}"):
        return

    raise ValueError(
        f"BASE_URL domain '{normalized_host}' is outside ALLOWED_DOMAIN '{normalized_allowed}'"
    )


def _read_env(name: str, default: str) -> str:
    from os import getenv

    value = getenv(name)
    if value is None:
        return default
    return value.strip() or default


def _read_bool(name: str, default: bool) -> bool:
    from os import getenv

    value = getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _read_optional_path(name: str) -> Path | None:
    from os import getenv

    value = getenv(name)
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None
    return Path(normalized)


def _read_int(name: str, default: int) -> int:
    from os import getenv

    value = getenv(name)
    if value is None:
        return default

    normalized = value.strip()
    if not normalized:
        return default
    try:
        return int(normalized)
    except ValueError:
        return default
