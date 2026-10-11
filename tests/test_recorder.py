"""Debug artifacts: written where configured, never break the game."""

import json

import pytest

from oathforge import __version__, recorder
from oathforge.ai.client import GeminiLLM
from oathforge.config import Settings, get_settings
from tests.ai.test_client import OpenBudget, ScriptedClient


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "artifacts_dir", tmp_path)
    return tmp_path


def test_conversation_transcript(root):
    recorder.incoming(42, "Lyra", "me escondo tras la barra")
    recorder.incoming(42, "Lyra", "cb|atk:main|n1", button=True)
    recorder.outgoing(42, "<b>Taberna</b> &amp; humo", ["🧭 Viajar", "💬 Hablar"])
    md = next((root / "conversations").glob("*/42.md")).read_text(encoding="utf-8")
    assert f"v{__version__}" in md
    assert "me escondo tras la barra" in md and "[botón cb|atk:main|n1]" in md
    assert "> Taberna & humo" in md and "`[💬 Hablar]`" in md
    events = next((root / "events").glob("*.jsonl")).read_text(encoding="utf-8").splitlines()
    assert [json.loads(e)["kind"] for e in events] == ["in", "in", "out"]


def test_battle_steps_accumulate(root):
    state = {"round": 1, "status": "active", "combatants": {}}
    recorder.battle(7, "sunken_crypt", character="Edda", actor_action=None,
                    lines=["<b>Edda</b> 15"], raw=[{"key": "combat.initiative"}], state=state)
    end = {"round": 2, "status": "victory",
           "combatants": {"p1": {"name": {"es": "Edda"}, "hp": 9, "max_hp": 12}}}
    recorder.battle(7, "sunken_crypt", character="Edda", actor_action={"kind": "attack"},
                    lines=["Edda golpea"], raw=[{"key": "combat.hit"}], state=end)
    md = next((root / "battles").glob("*/7-sunken_crypt.md")).read_text(encoding="utf-8")
    assert "- Edda 15" in md and "victory" in md and "Edda: 9/12" in md
    data = json.loads(next((root / "battles").glob("*/7-sunken_crypt.json")).read_text(encoding="utf-8"))
    assert len(data["steps"]) == 2 and data["status"] == "victory"


async def test_gemini_calls_are_recorded(root):
    llm = GeminiLLM(Settings(gemini_model_fast="fast", gemini_model_narrative="narr"),
                    client=ScriptedClient("Una sombra se mueve."))
    llm.budget = OpenBudget()
    assert await llm.text(tier="narrative", system="sys", prompt="hola", user_id=1) == "Una sombra se mueve."
    (call,) = list((root / "ai").glob("*/*-narrative-text.json"))
    data = json.loads(call.read_text(encoding="utf-8"))
    assert data["prompt"] == "hola" and data["response"] == "Una sombra se mueve." and data["model"] == "narr"


def test_disabled_or_broken_never_raises(root, monkeypatch):
    blocker = root / "not_a_dir"
    blocker.write_text("x")
    monkeypatch.setattr(get_settings(), "artifacts_dir", blocker)
    recorder.incoming(1, "x", "hola")  # mkdir under a file fails: swallowed
    recorder.error("test", ValueError("boom"))
    monkeypatch.setattr(get_settings(), "artifacts_enabled", False)
    recorder.outgoing(1, "hola")
    assert blocker.read_text() == "x"
