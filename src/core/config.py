from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    base_url: str = Field(default="https://example.com")
    headless: bool = Field(default=True)
    screenshot_dir: Path = Field(default=Path("./screenshots"))
    allowed_domain: str = Field(default="example.com")


def load_environment() -> None:
    load_dotenv(ENV_FILE, override=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_environment()

    return Settings(
        base_url=_read_env("BASE_URL", "https://example.com"),
        headless=_read_bool("HEADLESS", True),
        screenshot_dir=Path(_read_env("SCREENSHOT_DIR", "./screenshots")),
        allowed_domain=_read_env("ALLOWED_DOMAIN", "example.com"),
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
