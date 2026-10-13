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
    # one model for everything for now (v0.7.0): Gemini 3.1 Flash-Lite
    gemini_model_fast: str = "gemini-3.1-flash-lite"
    gemini_model_narrative: str = "gemini-3.1-flash-lite"
    gemini_thinking_level: str = "low"  # narrative tier only; "" leaves the model default
    gemini_model_chronicle: str = "gemini-3.1-flash-lite"  # expedition chronicles (gather, stay, track)

    ai_user_daily_calls: int = 150  # testing phase (0.2.x)
    ai_user_daily_tokens: int = 200_000
    ai_user_daily_chronicles: int = 15  # AI-written expedition chronicles per player and day; then generic texts
    ai_global_daily_calls: int = 5_000
    ai_timeout_seconds: float = 10.0  # then the generic text, and the model cools down
    ai_chronicle_timeout_seconds: float = 8.0
    ai_model_cooldown_seconds: float = 120.0

    # debug artifacts (conversations, battles, AI calls); git-ignored, see oathforge/recorder.py
    artifacts_enabled: bool = True
    artifacts_dir: Path = ROOT_DIR / "artifacts"

    # oathforge tgtest: a real Telegram test account that plays the bot (https://my.telegram.org)
    tg_test_api_id: int = 0
    tg_test_api_hash: str = ""
    tg_test_bot: str = ""  # the bot's @username

    default_language: str = "es"
    supported_languages: tuple[str, ...] = ("es", "en")


@lru_cache
def get_settings() -> Settings:
    return Settings()
