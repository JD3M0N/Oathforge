"""Outcome of a game action: a list of events rendered per language.

Each event is an i18n key plus params. Params that are localized texts
({"es": ..., "en": ...}) are resolved to the reader's language at render
time. The same events rendered in English are the *facts* the AI narrator
receives, so prose can never contradict mechanics.
"""

from dataclasses import dataclass, field

from oathforge.i18n import t


@dataclass
class Event:
    key: str
    params: dict = field(default_factory=dict)


@dataclass
class Outcome:
    events: list[Event] = field(default_factory=list)
    ok: bool = True
    encounter_id: int | None = None
    error: str | None = None  # i18n key when the action was refused
    activity_id: int | None = None  # a field activity that just finished (its chronicle follows)

    def add(self, key: str, **params) -> "Outcome":
        self.events.append(Event(key, params))
        return self

    def text(self, localized) -> "Outcome":
        """Narrative content text from YAML (a Text model or {es, en} dict)."""
        value = localized.model_dump() if hasattr(localized, "model_dump") else localized
        self.events.append(Event("text", {"text": value}))
        return self

    def extend(self, other: "Outcome") -> "Outcome":
        self.events += other.events
        if other.encounter_id:
            self.encounter_id = other.encounter_id
        if other.activity_id:
            self.activity_id = other.activity_id
        return self

    @classmethod
    def refused(cls, key: str, **params) -> "Outcome":
        return cls(events=[Event(key, params)], ok=False, error=key)


def localize(value, lang: str):
    if isinstance(value, dict) and "en" in value and "es" in value:
        return value.get(lang) or value["en"]
    return value


def render_event(ev: Event, lang: str, links: bool = True) -> str:
    params = {k: localize(v, lang) for k, v in ev.params.items()}
    if ev.key == "text":
        return str(params["text"])
    text = t(lang, ev.key, **params)
    if links and ev.key in ("loot.item", "loot.lost_item") and params.get("item_key"):
        text += f" · /item_{params['item_key']}"  # tappable: what it is and what it is for
    return text


def render(outcome: Outcome, lang: str) -> list[str]:
    return [render_event(e, lang) for e in outcome.events]


def facts(outcome: Outcome) -> list[str]:
    """What happened, in English, for the AI (no tappable links)."""
    return [render_event(e, "en", links=False) for e in outcome.events]
