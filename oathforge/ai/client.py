"""LLM access with hard limits.

The model is never trusted to limit itself: the per-user and global daily
budgets are checked *before* each call, usage is recorded after, and any
failure (timeout, quota, bad JSON) returns None so callers fall back to
deterministic templates.
"""

import asyncio
import logging
from datetime import date
from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select

from oathforge.config import Settings, get_settings
from oathforge.database.models import AiUsage
from oathforge.database.session import session_scope

log = logging.getLogger(__name__)

Tier = Literal["fast", "narrative"]
M = TypeVar("M", bound=BaseModel)


class LLM(Protocol):
    async def json(self, *, tier: Tier, system: str, prompt: str, schema: type[M], user_id: int | None) -> M | None: ...
    async def text(self, *, tier: Tier, system: str, prompt: str, user_id: int | None) -> str | None: ...


class NullLLM:
    """No API key configured: every call falls back to templates."""

    async def json(self, **_) -> None:
        return None

    async def text(self, **_) -> None:
        return None


class Budget:
    def __init__(self, settings: Settings):
        self.s = settings

    async def allow(self, user_id: int | None) -> bool:
        today = date.today()
        async with session_scope() as session:
            global_calls = await session.scalar(
                select(func.coalesce(func.sum(AiUsage.calls), 0)).where(AiUsage.day == today)
            )
            if global_calls >= self.s.ai_global_daily_calls:
                log.warning("global AI budget exhausted")
                return False
            if user_id is None:
                return True
            row = (await session.execute(
                select(func.coalesce(func.sum(AiUsage.calls), 0),
                       func.coalesce(func.sum(AiUsage.prompt_tokens + AiUsage.output_tokens), 0))
                .where(AiUsage.day == today, AiUsage.user_id == user_id)
            )).one()
            return row[0] < self.s.ai_user_daily_calls and row[1] < self.s.ai_user_daily_tokens

    async def record(self, user_id: int | None, model: str, prompt_tokens: int, output_tokens: int) -> None:
        today = date.today()
        async with session_scope() as session:
            row = await session.scalar(
                select(AiUsage).where(AiUsage.day == today, AiUsage.model == model,
                                      AiUsage.user_id.is_(None) if user_id is None else AiUsage.user_id == user_id)
                .with_for_update()
            )
            if row is None:
                row = AiUsage(user_id=user_id, day=today, model=model, calls=0, prompt_tokens=0, output_tokens=0)
                session.add(row)
            row.calls += 1
            row.prompt_tokens += prompt_tokens
            row.output_tokens += output_tokens


class GeminiLLM:
    def __init__(self, settings: Settings | None = None):
        from google import genai

        self.s = settings or get_settings()
        self.client = genai.Client(api_key=self.s.gemini_api_key)
        self.budget = Budget(self.s)

    def _model(self, tier: Tier) -> str:
        return self.s.gemini_model_fast if tier == "fast" else self.s.gemini_model_narrative

    async def _generate(self, tier: Tier, system: str, prompt: str, user_id: int | None, schema=None):
        from google.genai import types

        if not await self.budget.allow(user_id):
            return None
        model = self._model(tier)
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2 if schema else 0.9,
            response_mime_type="application/json" if schema else None,
            response_schema=schema,
        )
        for attempt in range(2):
            try:
                resp = await asyncio.wait_for(
                    self.client.aio.models.generate_content(model=model, contents=prompt, config=config),
                    timeout=self.s.ai_timeout_seconds,
                )
            except Exception as e:  # network, quota, timeout: degrade gracefully
                log.warning("gemini call failed (attempt %d): %s", attempt + 1, e)
                if attempt == 0:
                    await asyncio.sleep(0.5)
                continue
            usage = resp.usage_metadata
            await self.budget.record(
                user_id, model,
                getattr(usage, "prompt_token_count", 0) or 0,
                (getattr(usage, "candidates_token_count", 0) or 0) + (getattr(usage, "thoughts_token_count", 0) or 0),
            )
            return resp.text
        return None

    async def json(self, *, tier: Tier, system: str, prompt: str, schema: type[M], user_id: int | None) -> M | None:
        raw = await self._generate(tier, system, prompt, user_id, schema)
        if not raw:
            return None
        try:
            return schema.model_validate_json(raw)
        except ValidationError as e:
            log.warning("gemini returned invalid JSON for %s: %s", schema.__name__, e)
            return None

    async def text(self, *, tier: Tier, system: str, prompt: str, user_id: int | None) -> str | None:
        raw = await self._generate(tier, system, prompt, user_id)
        return raw.strip() if raw else None


def build_llm(settings: Settings | None = None) -> LLM:
    settings = settings or get_settings()
    if not settings.gemini_api_key:
        log.warning("GEMINI_API_KEY not set: AI narration disabled, using templates")
        return NullLLM()
    return GeminiLLM(settings)
