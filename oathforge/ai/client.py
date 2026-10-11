"""LLM access with hard limits.

The model is never trusted to limit itself: the per-user and global daily
budgets are checked *before* each call, usage is recorded after, and any
failure (timeout, quota, bad JSON) returns None so callers fall back to
deterministic templates.
"""

import asyncio
import logging
import time
from datetime import date
from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select

from oathforge import recorder
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


async def usage_today(session, user_id: int) -> tuple[int, int]:
    """(calls, tokens) the player has spent today. Read-only; the hero sheet shows it."""
    row = (await session.execute(
        select(func.coalesce(func.sum(AiUsage.calls), 0),
               func.coalesce(func.sum(AiUsage.prompt_tokens + AiUsage.output_tokens), 0))
        .where(AiUsage.day == date.today(), AiUsage.user_id == user_id)
    )).one()
    return int(row[0]), int(row[1])


def user_exhausted(calls: int, tokens: int, settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return calls >= s.ai_user_daily_calls or tokens >= s.ai_user_daily_tokens


class Budget:
    def __init__(self, settings: Settings):
        self.s = settings
        self._warned_day: date | None = None

    async def allow(self, user_id: int | None) -> bool:
        today = date.today()
        async with session_scope() as session:
            global_calls = await session.scalar(
                select(func.coalesce(func.sum(AiUsage.calls), 0)).where(AiUsage.day == today)
            )
            if global_calls >= self.s.ai_global_daily_calls:
                log.warning("global AI budget exhausted")
                return False
            if global_calls >= 0.8 * self.s.ai_global_daily_calls and self._warned_day != today:
                self._warned_day = today
                log.warning("global AI budget at %d/%d calls today", global_calls, self.s.ai_global_daily_calls)
            if user_id is None:
                return True
            return not user_exhausted(*await usage_today(session, user_id), self.s)

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


# HTTP codes worth another try (on this model later, or on the fallback now).
TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}


class GeminiLLM:
    def __init__(self, settings: Settings | None = None, client=None):
        self.s = settings or get_settings()
        if client is None:
            from google import genai

            client = genai.Client(api_key=self.s.gemini_api_key)
        self.client = client
        self.budget = Budget(self.s)
        self._cooldown_until: dict[str, float] = {}

    def _model(self, tier: Tier) -> str:
        return self.s.gemini_model_fast if tier == "fast" else self.s.gemini_model_narrative

    def _candidates(self, tier: Tier) -> list[str]:
        """Models to try in order. Narrative falls back to the fast model; fast retries itself once.

        A model that recently failed with an overload/quota error is skipped while
        another one is available, so players don't wait for a timeout on every call.
        """
        primary = self._model(tier)
        fallback = self.s.gemini_model_fast if tier == "narrative" else primary
        now = time.monotonic()
        if primary != fallback and self._cooldown_until.get(primary, 0) > now:
            return [fallback]
        return [primary, fallback]

    def _config(self, tier: Tier, system: str, schema):
        from google.genai import types

        level = self.s.gemini_thinking_level if tier == "narrative" else ""
        return types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2 if schema else 0.9,
            response_mime_type="application/json" if schema else None,
            response_schema=schema,
            thinking_config=types.ThinkingConfig(thinking_level=level) if level else None,
        )

    async def _generate(self, tier: Tier, system: str, prompt: str, user_id: int | None, schema=None):
        purpose = schema.__name__ if schema else "text"
        if not await self.budget.allow(user_id):
            self._record(tier, None, purpose, system, prompt, None, "budget exhausted", None, None, user_id)
            return None
        started = time.monotonic()
        error = None
        models = self._candidates(tier)
        for attempt, model in enumerate(models):
            if attempt and model == models[attempt - 1]:
                await asyncio.sleep(0.5)
            config = self._config(tier if model == self._model(tier) else "fast", system, schema)
            try:
                resp = await asyncio.wait_for(
                    self.client.aio.models.generate_content(model=model, contents=prompt, config=config),
                    timeout=self.s.ai_timeout_seconds,
                )
            except Exception as e:  # network, quota, timeout: degrade gracefully
                error = f"{model}: {str(e) or type(e).__name__}"
                code = getattr(e, "code", None)
                if isinstance(code, int) and code not in TRANSIENT_CODES:
                    log.error("gemini call to %s rejected (%s), check the configuration: %s", model, code, e)
                    self._record(tier, model, purpose, system, prompt, None, error, None, started, user_id)
                    return None
                self._cooldown_until[model] = time.monotonic() + self.s.ai_model_cooldown_seconds
                log.warning("gemini call to %s failed (attempt %d): %s", model, attempt + 1,
                            str(e) or type(e).__name__)
                continue
            usage = resp.usage_metadata
            await self.budget.record(
                user_id, model,
                getattr(usage, "prompt_token_count", 0) or 0,
                (getattr(usage, "candidates_token_count", 0) or 0) + (getattr(usage, "thoughts_token_count", 0) or 0),
            )
            self._record(tier, model, purpose, system, prompt, resp.text, error, usage, started, user_id)
            return resp.text
        self._record(tier, None, purpose, system, prompt, None, error, None, started, user_id)
        return None

    @staticmethod
    def _record(tier, model, purpose, system, prompt, response, error, usage, started, user_id) -> None:
        """Debug copy of the call in artifacts/ai/ (error = earlier failed attempt, if any)."""
        recorder.ai_call(
            tier=tier, model=model, purpose=purpose, system=system, prompt=prompt, response=response,
            error=error, user_id=user_id,
            prompt_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=(getattr(usage, "candidates_token_count", 0) or 0)
            + (getattr(usage, "thoughts_token_count", 0) or 0),
            latency_ms=int((time.monotonic() - started) * 1000) if started else 0,
        )

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
