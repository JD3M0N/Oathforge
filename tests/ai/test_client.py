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
    llm = GeminiLLM(Settings(gemini_model_fast=FAST, gemini_model_narrative=NARRATIVE, gemini_model_fallback=""),
                    client=client)
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


async def test_the_last_model_retries_once_after_an_overload(monkeypatch):
    monkeypatch.setattr("oathforge.ai.client.OVERLOAD_RETRY_DELAY", 0)
    llm, client = make_llm(api_error(503), "ok")
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) == "ok"
    assert client.calls == [FAST, FAST]


async def test_two_overloads_in_a_row_go_generic_and_cool_down(monkeypatch):
    monkeypatch.setattr("oathforge.ai.client.OVERLOAD_RETRY_DELAY", 0)
    llm, client = make_llm(api_error(503), api_error(503), "never used")
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None  # cooling down: no call
    assert client.calls == [FAST, FAST]


async def test_timeouts_are_not_retried():
    llm, client = make_llm(TimeoutError(), "never used")
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None
    assert client.calls == [FAST]


async def test_the_backup_model_is_used_last_for_every_tier():
    client = ScriptedClient(api_error(503), api_error(503), "from backup")
    llm = GeminiLLM(Settings(gemini_model_fast=FAST, gemini_model_narrative=NARRATIVE, gemini_model_chronicle=FAST,
                             gemini_model_fallback="backup"),
                    client=client)
    llm.budget = OpenBudget()
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) == "from backup"
    assert client.calls == [NARRATIVE, FAST, "backup"]
    llm._cooldown_until.clear()
    client.outcomes = [api_error(503), "chronicle from backup"]
    assert await llm.text(tier="chronicle", system="s", prompt="p", user_id=None) == "chronicle from backup"
    assert client.calls[-2:] == [FAST, "backup"]


async def test_one_model_for_everything_goes_generic_while_it_cools_down():
    client = ScriptedClient(TimeoutError(), "never used")
    llm = GeminiLLM(Settings(gemini_model_fast=FAST, gemini_model_narrative=FAST, gemini_model_chronicle=FAST,
                             gemini_model_fallback=""),
                    client=client)
    llm.budget = OpenBudget()
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) is None
    for tier in ("fast", "narrative", "chronicle"):  # no call, no wait: the caller uses its generic text
        assert await llm.text(tier=tier, system="s", prompt="p", user_id=None) is None
    assert client.calls == [FAST]


def quota_error(per_day: bool, delay: str) -> errors.APIError:
    quota = "GenerateRequestsPerDayPerProjectPerModel-FreeTier" if per_day else "GenerateRequestsPerMinute"
    return errors.APIError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": quota}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay},
    ]}})


def test_cooldown_follows_google_retry_delay():
    from oathforge.ai.client import MAX_COOLDOWN_SECONDS, cooldown_for

    assert cooldown_for(quota_error(True, "79622s"), 120) == 79622
    assert cooldown_for(quota_error(True, "999999s"), 120) == MAX_COOLDOWN_SECONDS
    assert cooldown_for(quota_error(False, "30s"), 120) == 120
    assert cooldown_for(quota_error(False, "300s"), 120) == 300
    assert cooldown_for(api_error(503), 120) == 120
    assert cooldown_for(TimeoutError(), 120) == 120


async def test_daily_quota_skips_the_model_for_hours(monkeypatch):
    import time as time_mod

    llm, client = make_llm(quota_error(True, "80000s"), "first", "second")
    await llm.text(tier="narrative", system="s", prompt="p", user_id=None)
    now = time_mod.monotonic()
    monkeypatch.setattr("oathforge.ai.client.time.monotonic", lambda: now + 3600)  # an hour later
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) == "second"
    assert client.calls == [NARRATIVE, FAST, FAST]


async def test_invalid_json_returns_none():
    from oathforge.ai.intent_parser import Intent

    llm, client = make_llm("not valid json")
    result = await llm.json(tier="fast", system="s", prompt="p", schema=Intent, user_id=None)
    assert result is None and client.calls == [FAST]


async def test_empty_narration_returns_none():
    llm, client = make_llm("   ")
    assert await llm.text(tier="narrative", system="s", prompt="p", user_id=None) is None
    assert client.calls == [NARRATIVE]


async def test_no_api_key_uses_null_client():
    from oathforge.ai.client import NullLLM, build_llm

    llm = build_llm(Settings(gemini_api_key=""))
    assert isinstance(llm, NullLLM)
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None


async def test_global_budget_blocks_provider(database):
    llm, client = make_llm("must not be called")
    from oathforge.ai.client import Budget

    llm.budget = Budget(Settings(ai_global_daily_calls=0))
    assert await llm.text(tier="fast", system="s", prompt="p", user_id=None) is None
    assert client.calls == []
