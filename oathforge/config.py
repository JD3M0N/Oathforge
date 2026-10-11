from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT_DIR / "content"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/oathforge"
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/oathforge_test"

    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-flash-lite-latest"
    gemini_model_narrative: str = "gemini-flash-latest"
    gemini_thinking_level: str = "low"  # narrative tier only; "" leaves the model default

    ai_user_daily_calls: int = 200
    ai_user_daily_tokens: int = 200_000
    ai_global_daily_calls: int = 5_000
    ai_timeout_seconds: float = 20.0
    ai_model_cooldown_seconds: float = 120.0

    default_language: str = "es"
    supported_languages: tuple[str, ...] = ("es", "en")


@lru_cache
def get_settings() -> Settings:
    return Settings()
