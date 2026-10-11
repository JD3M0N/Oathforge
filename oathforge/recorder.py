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
      logs/<day>.log                           warnings and errors from any logger

State changes (HP, gold, items, quests, NPC memories, button actions...) go to
events as ``state`` and inline in the player's conversation; see ``start``.
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


# ---------------------------------------------------------------- state changes
#
# Every committed change to player state (HP, gold, XP, flags, items, quests, NPC
# relations...) as a diff, whatever code path made it. Rows are snapshotted when
# loaded and compared after commit; rolled-back changes are never recorded.

_TRACKED = ("characters", "item_instances", "character_skills", "quest_progress", "npc_relationships",
            "npc_memories", "faction_reputation", "action_logs", "world_facts")
_INSERT_ONLY = {"npc_memories", "action_logs", "world_facts"}  # append-only logs: record new rows only
_SKIP = {"version", "created_at", "updated_at", "history", "recent"}
_LABEL = ("name", "item_key", "skill", "quest_key", "npc_key", "faction_key", "verb", "key")
_NOUN = {"item_instances": "objeto", "character_skills": "habilidad", "quest_progress": "misión",
         "npc_relationships": "relación", "faction_reputation": "reputación"}
_known: dict[tuple, dict] = {}  # (table, pk) -> last committed values seen
_telegram: dict[int, int] = {}  # users.id -> telegram_id


def _table(obj) -> str | None:
    name = getattr(obj, "__tablename__", None)
    return name if name in _TRACKED else None


def _snap(obj) -> dict:
    """Loaded column values, JSON-safe and detached (no lazy loads: this runs in sync ORM hooks)."""
    from sqlalchemy import inspect

    state = inspect(obj)
    data = {c.key: state.dict[c.key] for c in state.mapper.column_attrs if c.key not in _SKIP and c.key in state.dict}
    return json.loads(json.dumps(data, ensure_ascii=False, default=str))


def _key(obj) -> tuple:
    from sqlalchemy import inspect

    return (obj.__tablename__, inspect(obj).identity)


def _diff(old: dict, new: dict) -> dict:
    return {k: [old.get(k), v] for k, v in new.items() if old.get(k) != v}


def _fmt_value(old, new) -> str:
    if isinstance(old, dict) or isinstance(new, dict):
        old, new = old or {}, new or {}
        parts = [f"+{k}" + ("" if new[k] is True else f"={new[k]}") for k in new if k not in old]
        parts += [f"-{k}" for k in old if k not in new]
        parts += [f"{k} {old[k]}→{new[k]}" for k in new if k in old and old[k] != new[k]]
        return "{" + ", ".join(parts) + "}"
    return f"{old}→{new}"


def _describe(table: str, op: str, row: dict, diff: dict) -> str:
    label = next((str(row[k]) for k in _LABEL if row.get(k)), "")
    if table == "action_logs":
        return f"▶ {label} {json.dumps(row.get('payload') or {}, ensure_ascii=False)}"
    if table == "npc_memories":
        return f"🧠 {row.get('npc_key')} recuerda: {row.get('text')}"
    if table == "world_facts":
        return f"🌍 {label}: {json.dumps(row.get('value'), ensure_ascii=False)}"
    if table == "item_instances" and op != "update":
        return f"{'+' if op == 'insert' else '−'}{label} ×{row.get('qty')}"
    if op == "insert" and table == "characters":
        return (f"personaje creado: {label} ({row.get('class_key')}, {row.get('lineage')}, {row.get('background')}) "
                f"PV {row.get('hp')}/{row.get('max_hp')}, oro {row.get('gold')}, en {row.get('location')}")
    noun = _NOUN.get(table, table)
    if op == "delete":
        return f"{noun} {label} borrado"
    shown = {k: v for k, v in diff.items() if not k.endswith("_id") and k != "id" and row.get(k) != label}
    if op == "insert":
        return f"+{noun} {label}: " + ", ".join(f"{k}={v[1]}" for k, v in shown.items())
    changes = ", ".join(f"{k} {_fmt_value(*v)}" for k, v in shown.items())
    return changes if table == "characters" else f"{noun} {label}: {changes}"


def _owner(table: str, row: dict) -> tuple[int | None, int | None]:
    """(character_id, telegram_id) of a row."""
    char_id = row.get("id") if table == "characters" else row.get("character_id") or row.get("owner_character_id")
    user_id = row.get("user_id") if table in ("characters", "action_logs") else None
    if user_id is None and char_id is not None:
        user_id = _known.get(("characters", (char_id,)), {}).get("user_id")
    return char_id, _telegram.get(user_id)


def _remember_user(obj) -> None:
    if getattr(obj, "__tablename__", None) == "users" and obj.id is not None:
        _telegram[obj.id] = obj.telegram_id


@_safe
def _on_load(obj, *_) -> None:
    _remember_user(obj)
    if _table(obj):
        _known[_key(obj)] = _snap(obj)


@_safe
def _before_flush(session, *_) -> None:
    pending = session.info.setdefault("recorder", {})
    for obj in list(session.new) + list(session.dirty):
        if getattr(obj, "__tablename__", None) == "users":
            pending[id(obj)] = ("user", obj)
        if _table(obj):
            pending[id(obj)] = ("upsert", obj)
    for obj in session.deleted:
        if _table(obj):
            pending[id(obj)] = ("delete", obj, _snap(obj))


@_safe
def _after_commit(session) -> None:
    pending = session.info.pop("recorder", {})
    lines: dict[int, list[str]] = {}
    for entry in [e for e in pending.values() if e[0] == "user"]:
        _remember_user(entry[1])
    for entry in [e for e in pending.values() if e[0] != "user"]:
        table = entry[1].__tablename__
        if entry[0] == "delete":
            row, op, diff = entry[2], "delete", {}
            _known.pop(_key(entry[1]), None)
        else:
            key = _key(entry[1])
            row = _snap(entry[1])
            op = "update" if key in _known else "insert"
            if op == "update" and table in _INSERT_ONLY:
                continue
            diff = _diff(_known.get(key, {}), row)
            _known[key] = row
            if not diff:
                continue
        char_id, tg = _owner(table, row)
        text = _describe(table, op, row, diff)
        _event("state", {"telegram_id": tg, "character_id": char_id, "table": table, "op": op,
                         "row_id": row.get("id"), "diff": diff if op == "update" else row, "text": text})
        quiet = table == "character_skills" and op == "insert" and not row.get("proficient")
        if tg is not None and not quiet:  # untrained skills at creation: events only
            lines.setdefault(tg, []).append(text)
    for tg, texts in lines.items():
        _append(_transcript(tg), f"**[{_clock()}] ⚙️ estado:**\n" + "".join(f"- {t}\n" for t in texts) + "\n")


def _after_rollback(session) -> None:
    session.info.pop("recorder", None)


# ---------------------------------------------------------------- logs and boot

class _LogHandler(logging.Handler):
    """Warnings and errors from any logger (Gemini retries, invalid JSON...) into logs/<day>.log."""

    def emit(self, record: logging.LogRecord) -> None:
        if not record.name.startswith(__name__):
            _log_record(self.format(record), record)


@_safe
def _log_record(text: str, record: logging.LogRecord) -> None:
    _append(_root() / "logs" / f"{_day()}.log", text + "\n")
    _event("log", {"level": record.levelname, "logger": record.name, "message": record.getMessage()})


_started = False


def start(settings) -> None:
    """Hook the recorder into logging and the ORM, and mark the boot. Call once at startup."""
    global _started
    if _started:
        return
    _started = True
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from oathforge.database.models import Base

    handler = _LogHandler(logging.WARNING)
    handler.setFormatter(logging.Formatter(f"%(asctime)s v{__version__} %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)
    for mapper in Base.registry.mappers:
        if mapper.local_table.name in _TRACKED or mapper.local_table.name == "users":
            event.listen(mapper.class_, "load", _on_load)
            event.listen(mapper.class_, "refresh", _on_load)
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    _boot(settings)


@_safe
def _boot(settings) -> None:
    import subprocess

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                timeout=5, cwd=Path(__file__).parent).stdout.strip() or None
    except Exception:
        commit = None
    _event("boot", {"commit": commit, "model_fast": settings.gemini_model_fast,
                    "model_narrative": settings.gemini_model_narrative, "ai_enabled": bool(settings.gemini_api_key),
                    "database": str(settings.database_url).split("@")[-1]})


# ---------------------------------------------------------------- errors

@_safe
def error(where: str, exc: BaseException | None) -> None:
    import traceback

    tb = "".join(traceback.format_exception(exc)) if exc else ""
    _append(_root() / "errors" / f"{_day()}.log", f"--- {datetime.now().isoformat()} v{__version__} {where}\n{tb}\n")
    _event("error", {"where": where, "error": repr(exc)})
