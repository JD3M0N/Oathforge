"""Debug artifacts: everything that happens in a game, written to ``artifacts/`` (git-ignored).

Not game state: nothing here is ever read back by the game. Every public
function swallows its own errors, because recording must never break play.

    artifacts/
      conversations/<day>/<telegram_id>.md     readable player <-> bot transcript
      events/<day>.jsonl                       every record, raw
      battles/<day>/<enc_id>-<location>.md     turn by turn, readable
      battles/<day>/<enc_id>-<location>.json   raw engine log and final state
      ai/<day>/<time>-<tier>-<purpose>.json    system, prompt, response, model, tokens, latency
      errors/<day>.log                         unhandled exceptions
"""

import functools
import html
import json
import logging
import re
from datetime import datetime
from pathlib import Path

from oathforge import __version__
from oathforge.config import get_settings

log = logging.getLogger(__name__)

_TAG = re.compile(r"<[^>]+>")


def _root() -> Path | None:
    s = get_settings()
    return Path(s.artifacts_dir) if s.artifacts_enabled else None


def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if _root() is None:
            return None
        try:
            return fn(*args, **kwargs)
        except Exception:  # never let debugging break the game
            log.debug("recorder.%s failed", fn.__name__, exc_info=True)
            return None
    return wrapper


def _day() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _clock() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def plain(text: str) -> str:
    """Telegram HTML -> plain text."""
    return html.unescape(_TAG.sub("", text or ""))


def _event(kind: str, data: dict) -> None:
    record = {"ts": datetime.now().isoformat(timespec="milliseconds"), "v": __version__, "kind": kind, **data}
    _append(_root() / "events" / f"{_day()}.jsonl", json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _transcript(telegram_id: int) -> Path:
    path = _root() / "conversations" / _day() / f"{telegram_id}.md"
    if not path.exists():
        _append(path, f"# Conversación {telegram_id} · {_day()} · v{__version__}\n\n")
    return path


# ---------------------------------------------------------------- conversation

@_safe
def incoming(telegram_id: int, name: str, text: str, *, button: bool = False) -> None:
    shown = f"`[botón {text}]`" if button else text
    _append(_transcript(telegram_id), f"**[{_clock()}] 🧑 {name}:** {shown}\n\n")
    _event("in", {"telegram_id": telegram_id, "name": name, "text": text, "button": button})


@_safe
def outgoing(telegram_id: int, text: str, buttons: list[str] | None = None, *, edited: bool = False) -> None:
    body = "\n".join(f"> {line}" if line else ">" for line in plain(text).splitlines())
    kb = " ".join(f"`[{b}]`" for b in buttons or [])
    tag = " (editado)" if edited else ""
    _append(_transcript(telegram_id), f"**[{_clock()}] 🤖 bot{tag}:**\n{body}\n" + (f"\n{kb}\n" if kb else "") + "\n")
    _event("out", {"telegram_id": telegram_id, "text": plain(text), "buttons": buttons or [], "edited": edited})


# ---------------------------------------------------------------- game

@_safe
def action(*, user_id: int, character_id: int | None, text: str, intent: dict | None,
           ok: bool, events: list[str], narration: str | None = None) -> None:
    _event("action", {"user_id": user_id, "character_id": character_id, "text": text, "intent": intent,
                      "ok": ok, "events": events, "narration": narration})


def _battle_paths(enc_id: int, location: str) -> tuple[Path, Path]:
    existing = list((_root() / "battles").glob(f"*/{enc_id}-*.md"))
    md = existing[0] if existing else _root() / "battles" / _day() / f"{enc_id}-{location}.md"
    return md, md.with_suffix(".json")


@_safe
def battle(enc_id: int, location: str, *, character: str, actor_action: dict | None,
           lines: list[str], raw: list[dict], state: dict) -> None:
    """Append one step (the start or a player action) of an encounter."""
    lines = [plain(line) for line in lines]
    md, js = _battle_paths(enc_id, location)
    if not md.exists():
        _append(md, f"# Combate {enc_id} · {location} · {character} · v{__version__}\n\n")
    what = f"acción `{json.dumps(actor_action, ensure_ascii=False)}`" if actor_action else "inicio"
    head = f"## [{_clock()}] {what} → ronda {state.get('round')}"
    _append(md, head + "\n" + "".join(f"- {line}\n" for line in lines) + "\n")

    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else {
        "encounter_id": enc_id, "location": location, "character": character, "version": __version__, "steps": [],
    }
    data["steps"].append({"ts": datetime.now().isoformat(timespec="seconds"), "action": actor_action, "log": raw})
    data["state"] = state
    data["status"] = state.get("status")
    _write_json(js, data)

    if state.get("status") != "active":
        hp = {c["name"]["es"]: f"{c['hp']}/{c['max_hp']}" for c in state.get("combatants", {}).values()}
        _append(md, f"## Resultado: **{state.get('status')}** en {state.get('round')} rondas\n\n"
                    + "".join(f"- {k}: {v} PV\n" for k, v in hp.items()) + "\n")
    _event("battle", {"encounter_id": enc_id, "action": actor_action, "status": state.get("status"),
                      "lines": lines})


# ---------------------------------------------------------------- AI

@_safe
def ai_call(*, tier: str, model: str | None, purpose: str, system: str, prompt: str, response: str | None,
            error: str | None, prompt_tokens: int, output_tokens: int, latency_ms: int,
            user_id: int | None) -> None:
    stamp = datetime.now().strftime("%H%M%S-%f")
    _write_json(_root() / "ai" / _day() / f"{stamp}-{tier}-{purpose}.json", {
        "version": __version__, "tier": tier, "model": model, "purpose": purpose, "user_id": user_id,
        "latency_ms": latency_ms, "prompt_tokens": prompt_tokens, "output_tokens": output_tokens,
        "error": error, "system": system, "prompt": prompt, "response": response,
    })
    _event("ai", {"tier": tier, "model": model, "purpose": purpose, "user_id": user_id, "ok": response is not None,
                  "error": error, "latency_ms": latency_ms, "tokens": prompt_tokens + output_tokens})


# ---------------------------------------------------------------- errors

@_safe
def error(where: str, exc: BaseException | None) -> None:
    import traceback

    tb = "".join(traceback.format_exception(exc)) if exc else ""
    _append(_root() / "errors" / f"{_day()}.log", f"--- {datetime.now().isoformat()} v{__version__} {where}\n{tb}\n")
    _event("error", {"where": where, "error": repr(exc)})
