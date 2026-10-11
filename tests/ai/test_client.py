"""GeminiLLM retry policy: fallback, cooldown and non-transient errors, with a scripted client."""

from types import SimpleNamespace

from google.genai import errors

from oathforge.ai.client import GeminiLLM
from oathforge.config import Settings

FAST, NARRATIVE = "fast-model", "narrative-model"


def api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"code": code, "message": "scripted", "status": "X"}})


class ScriptedClient:
    """Mimics client.aio.models.generate_content; each call pops the next outcome."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls: list[str] = []
        self.aio = SimpleNamespace(models=self)

    async def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        usage = SimpleNamespace(prompt_token_count=3, candidates_token_count=2, thoughts_token_count=None)
        return SimpleNamespace(text=outcome, usage_metadata=usage)


class OpenBudget:
    def __init__(self):
        self.recorded: list[str] = []

    async def allow(self, user_id):
        return True

    async def record(self, user_id, model, prompt_tokens, output_tokens):
        self.recorded.append(model)


def make_llm(*outcomes) -> tuple[GeminiLLM, ScriptedClient]:
    client = ScriptedClient(*outcomes)
    llm = GeminiLLM(Settings(gemini_model_fast=FAST, gemini_model_narrative=NARRATIVE), client=client)
    llm.budget = OpenBudget()
    return llm, client


async def test_narrative_falls_back_to_fast_model_on_overload():
    llm, client = make_llm(api_error(503), "fallback line")
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) == "fallback line"
    assert client.calls == [NARRATIVE, FAST]
    assert llm.budget.recorded == [FAST]


async def test_overloaded_model_is_skipped_during_cooldown():
    llm, client = make_llm(api_error(429), "first", "second")
    await llm.text(tier="narrative", system="s", prompt="p", user_id=None)
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) == "second"
    assert client.calls == [NARRATIVE, FAST, FAST]


async def test_timeout_also_triggers_fallback():
    llm, client = make_llm(TimeoutError(), "ok")
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) == "ok"
    assert client.calls == [NARRATIVE, FAST]


async def test_invalid_request_is_not_retried():
    llm, client = make_llm(api_error(400), "never used")
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None
    assert client.calls == [FAST]


async def test_fast_tier_retries_itself_once():
    llm, client = make_llm(api_error(503), "ok")
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) == "ok"
    assert client.calls == [FAST, FAST]
