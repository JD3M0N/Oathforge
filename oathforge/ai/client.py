"""LLM access with hard limits.

The model is never trusted to limit itself: the per-user and global daily
budgets are checked *before* each call, usage is recorded after, and any
failure (timeout, quota, bad JSON) returns None so callers fall back to
deterministic templates.
"""

import asyncio
import logging
import re
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

Tier = Literal["fast", "narrative", "chronicle"]
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
# overload answers arrive in a second or two, so the last model gets one more go right away
OVERLOAD_CODES = {500, 502, 503, 504}
OVERLOAD_RETRY_DELAY = 1.0
MAX_COOLDOWN_SECONDS = 24 * 3600
_RETRY_DELAY = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s")


def cooldown_for(error: Exception, default: float) -> float:
    """How long to skip a model after a transient error.

    A 429 carries Google's own ``retryDelay``; when the daily quota is gone that is
    hours, and retrying every couple of minutes only wastes a round-trip per call.
    """
    text = str(error)
    m = _RETRY_DELAY.search(text)
    if getattr(error, "code", None) != 429 or m is None:
        return default
    delay = float(m.group(1))
    if "PerDay" in text:
        return min(delay, MAX_COOLDOWN_SECONDS)
    return min(max(default, delay), MAX_COOLDOWN_SECONDS)


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
        return {"fast": self.s.gemini_model_fast, "chronicle": self.s.gemini_model_chronicle}.get(
            tier, self.s.gemini_model_narrative)

    def _candidates(self, tier: Tier) -> list[str]:
        """Models to try in order: the tier's model, then (narrative only) the fast one if it is different,
        then the optional fallback model (any tier).

        A model that recently failed (overload, quota, timeout) is skipped while it cools down. Only the
        last model left retries itself, once, and only after an overload answer: a timeout goes straight
        to the generic text so the player never waits for a second one.
        """
        now = time.monotonic()
        models = [self._model(tier)]
        if tier == "narrative" and self.s.gemini_model_fast not in models:
            models.append(self.s.gemini_model_fast)
        if self.s.gemini_model_fallback and self.s.gemini_model_fallback not in models:
            models.append(self.s.gemini_model_fallback)
        return [m for m in models if self._cooldown_until.get(m, 0) <= now]

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
        timeout = self.s.ai_chronicle_timeout_seconds if tier == "chronicle" else self.s.ai_timeout_seconds
        for attempt, model in enumerate(models):
            config = self._config(tier if model == self._model(tier) else "fast", system, schema)
            last = attempt == len(models) - 1
            resp = None
            for tries in (1, 2):
                try:
                    resp = await asyncio.wait_for(
                        self.client.aio.models.generate_content(model=model, contents=prompt, config=config),
                        timeout=timeout,
                    )
                    break
                except Exception as e:  # network, quota, timeout: degrade gracefully
                    error = f"{model}: {str(e) or type(e).__name__}"
                    code = getattr(e, "code", None)
                    if isinstance(code, int) and code not in TRANSIENT_CODES:
                        log.error("gemini call to %s rejected (%s), check the configuration: %s", model, code, e)
                        self._record(tier, model, purpose, system, prompt, None, error, None, started, user_id)
                        return None
                    if last and tries == 1 and code in OVERLOAD_CODES:
                        log.warning("gemini call to %s overloaded (%s), trying once more", model, code)
                        await asyncio.sleep(OVERLOAD_RETRY_DELAY)
                        continue
                    cooldown = cooldown_for(e, self.s.ai_model_cooldown_seconds)
                    self._cooldown_until[model] = time.monotonic() + cooldown
                    if cooldown > self.s.ai_model_cooldown_seconds:
                        log.warning("gemini model %s out of quota, skipping it for %.0f min", model, cooldown / 60)
                    else:
                        log.warning("gemini call to %s failed (attempt %d): %s", model, attempt + 1,
                                    str(e) or type(e).__name__)
                    break
            if resp is None:
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
        return (raw.strip() or None) if raw else None


def build_llm(settings: Settings | None = None) -> LLM:
    settings = settings or get_settings()
    if not settings.gemini_api_key:
        log.warning("GEMINI_API_KEY not set: AI narration disabled, using templates")
        return NullLLM()
    return GeminiLLM(settings)
