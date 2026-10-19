"""Transactional achievement progress, evidence, preferences and delivery leases."""
from collections import defaultdict, deque
from dataclasses import dataclass, field
import hashlib
import json
import time
import uuid

from sqlalchemy import select
from oathforge.content import get_content
from oathforge.content.achievement_schemas import EDITION
from oathforge.database.models import (
    Character, QuestProgress, FactionReputation,
    AchievementProgress, AchievementUnlock, HeroFact,
    AchievementPreferences, AchievementNotification,
)
from oathforge.engine.achievements import advance, progress, event_types
from oathforge.engine import gathering
from oathforge.services.events import Outcome
from oathforge.services import audit

# Challenge achievements (last_breath, against_many, no_reserves) only count these non-fixed encounters.
CHALLENGE_ENCOUNTERS = {"whispering_woods": ["grey_wolf", "grey_wolf"], "ironvein_mine": ["cave_bat", "cave_bat"]}
CHALLENGE_LEVELS = range(3, 6)

# What the chronicle keeps. Everything else is recorded for the stats but never shown as an entry.
NOTABLE_ALWAYS = {"quest", "decision", "unlock", "level", "discovery", "secrets"}
# Worth one entry the first time each value happens: the field of the data that makes it unique.
NOTABLE_FIRST = {"visit": ("location",), "craft": ("recipe",), "seen": ("monster",), "kill": ("monster",),
                 "quest_start": ("quest",), "profession": ("key", "rank"), "mastery": ("skill", "rank")}


def fact_marks(kind: str, data: dict) -> tuple[bool, str | None]:
    """Deterministic: is this fact a chronicle entry, and what makes it unique the first time."""
    if kind in NOTABLE_FIRST:
        fields = NOTABLE_FIRST[kind]
        if any(data.get(f) is None for f in fields):
            return False, None
        tag = ":".join([kind, *(str(data[f]) for f in fields)])[:64]
        return data.get("rank", 1) > 0, tag  # rank 0 is where everyone starts: nothing happened
    if kind == "combat":  # a victory shows up as its kill; a defeat is the entry
        return data.get("status") == "defeat", None
    return kind in NOTABLE_ALWAYS, None


@dataclass(frozen=True)
class GameplayEvent:
    event_id: str
    character_id: int
    kind: str
    data: dict = field(default_factory=dict)
    source: str = ""
    schema_version: int = 1
    retroactive: bool = False

_catalog = None
_index = {}


def event_index():
    global _catalog, _index
    catalog = get_content().achievements
    if catalog is not _catalog:
        index = defaultdict(list)
        for key, definition in catalog.items():
            for kind in event_types(definition.condition):
                index[kind].append(key)
        _catalog, _index = catalog, index
    return _index


def encounter_metrics(char, monster_keys, fixed_flag, hunt, night) -> dict:
    """Saved on the encounter at its start, so challenges never depend on the battle report."""
    eligible = (fixed_flag is None and char.level in CHALLENGE_LEVELS
                and CHALLENGE_ENCOUNTERS.get(char.location) == sorted(monster_keys))
    return {"version": 1, "initial_level": char.level, "monsters": list(monster_keys), "eligible": eligible,
            "consumed": 0, "period": "night" if night else "day", "hunt": hunt}


async def apply_events(session, character, events):
    """Caller owns the action transaction. Lock order is always character first."""
    await session.scalar(select(Character.id).where(Character.id == character.id).with_for_update())
    if any(event.character_id != character.id for event in events):
        raise ValueError("gameplay event belongs to another character")
    catalog = get_content().achievements
    index = event_index()
    if not events:
        return []
    from oathforge.services.exploration import game_day  # exploration emits facts; the clock comes back deferred
    today = game_day()
    # The character lock serializes writers, so one lookup covers the whole batch.
    seen = set(await session.scalars(select(HeroFact.event_id).where(
        HeroFact.character_id == character.id,
        HeroFact.event_id.in_([event.event_id for event in events]))))
    tags = {tag for tag in (fact_marks(e.kind, e.data)[1] for e in events) if tag}
    known_tags = set(await session.scalars(select(HeroFact.tag).where(
        HeroFact.character_id == character.id, HeroFact.tag.in_(tags)))) if tags else set()
    rows = {r.achievement_key: r for r in (await session.scalars(
        select(AchievementProgress).where(AchievementProgress.character_id == character.id,
                                          AchievementProgress.edition == EDITION))).all()}
    unlocked = {r.achievement_key for r in (await session.scalars(
        select(AchievementUnlock).where(AchievementUnlock.character_id == character.id,
                                        AchievementUnlock.edition == EDITION))).all()}
    granted = []
    queue = deque(events)
    while queue:
        event = queue.popleft()
        if event.event_id in seen:
            continue
        seen.add(event.event_id)
        notable, tag = fact_marks(event.kind, event.data)
        if tag:
            notable = tag not in known_tags
            known_tags.add(tag)
        session.add(HeroFact(character_id=character.id, event_id=event.event_id, kind=event.kind,
                             data=event.data, tag=tag, game_day=today, notable=notable,
                             retroactive=event.retroactive))
        for key in index.get(event.kind, ()):
            if key in unlocked:
                continue
            definition = catalog[key]
            row = rows.get(key)
            old = row.state if row is not None else {}
            state = advance(definition.condition, old, event.kind, event.data)
            if state == old:
                continue
            if row is None:
                row = AchievementProgress(character_id=character.id, achievement_key=key,
                                          edition=definition.edition, state=state)
                session.add(row)
                rows[key] = row
            else:
                row.state = state
            value, target = progress(definition.condition, state)
            if value < target:
                continue
            evidence = {"event_id": event.event_id, "kind": event.kind, "source": event.source,
                        "schema_version": event.schema_version, "data": event.data, "progress": state}
            session.add(AchievementUnlock(character_id=character.id, achievement_key=key,
                edition=definition.edition, points=definition.points, evidence=evidence,
                retroactive=event.retroactive))
            granted.append(key)
            unlocked.add(key)
            queue.append(GameplayEvent(f"unlock:{EDITION}:{key}", character.id, "unlock", {"key": key},
                                       event.source, retroactive=event.retroactive))
    if granted:
        prefs = await session.get(AchievementPreferences, character.id)
        if prefs:
            prefs.tracked = [key for key in prefs.tracked if key not in unlocked]
        # Reuse one batch throughout the outer transaction, including nested domain calls.
        batches = session.info.setdefault("achievement_batches", {})
        tx_key = (character.id, session.sync_session.get_transaction())
        batch = batches.get(tx_key)
        if batch is None:
            batch = AchievementNotification(character_id=character.id, unlocks=[], status="pending", lease_until=0)
            session.add(batch)
            batches[tx_key] = batch
        batch.unlocks = list(dict.fromkeys(batch.unlocks + granted))
    await session.flush()
    return granted


async def emit(session, char, out, kind, data, source=None):
    """One engine fact. Without a stable source the event is unique: repeatable facts (crafts, trips) all count."""
    source = source or f"fact:{uuid.uuid4().hex}"
    granted = await apply_events(session, char, [GameplayEvent(f"{source}:{kind}", char.id, kind, data, source)])
    out.achievement_unlocks = list(dict.fromkeys(out.achievement_unlocks + granted))


async def levels(session, char, out, before: int):
    """Every level the xp just granted reached; the source keeps each one unique."""
    for level in range(before + 1, char.level + 1):
        await emit(session, char, out, "level", {"level": level}, f"level:{level}")


async def profession(session, char, out, key: str):
    """The rank of a profession, after it grew."""
    rank = gathering.rank_for(((char.professions or {}).get("xp", {})).get(key, 0))
    await emit(session, char, out, "profession", {"key": key, "rank": rank}, f"prof:{key}:{rank}")


async def mastery(session, char, out, skill, source=None):
    """The current rank of a field mastery, after it grew."""
    if skill in gathering.MASTERIES:
        await emit(session, char, out, "mastery",
                   {"skill": skill, "rank": gathering.rank_for((char.masteries or {}).get(skill, 0))}, source)


async def backfill_character(session, char):
    """Only facts the saved state proves; never infer historical challenges or decisions."""
    from oathforge.services.bestiary import KILLS_FOR_SECRETS
    c = get_content()
    events = []
    def fact(kind, data):
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:24]
        events.append(GameplayEvent(f"state:{EDITION}:{kind}:{digest}", char.id, kind, data,
                                   "saved_state", retroactive=True))
    for place in (char.flags or {}).get("stats", {}).get("places", []):
        if place in c.locations:
            # Having been there proves it: a place outside the city was reached from the city.
            fact("visit", {"location": place, "outside": c.locations[place].zone != "crownreach"})
    for level in range(2, char.level + 1):
        fact("level", {"level": level})
    if (char.flags or {}).get("crypt_unlocked"):
        fact("flag", {"key": "crypt_unlocked"})
    # Discovery flags shared with quest rewards cannot prove that discovery was resolved.
    for monster, entry in (char.bestiary or {}).items():
        if monster not in c.monsters:
            continue
        if entry.get("seen", 0) or entry.get("killed", 0):
            fact("seen", {"monster": monster})
        if entry.get("killed", 0):
            fact("kill", {"monster": monster})
        if entry.get("killed", 0) >= KILLS_FOR_SECRETS:
            fact("secrets", {"monster": monster})
    stats = (char.flags or {}).get("stats", {})
    if any(entry.get("killed", 0) for entry in (char.bestiary or {}).values()):
        fact("combat", {"status": "victory", "eligible": False})
    if stats.get("battles_fled", 0):
        fact("combat", {"status": "fled", "eligible": False})
    for skill in gathering.MASTERIES:
        fact("mastery", {"skill": skill, "rank": gathering.rank_for((char.masteries or {}).get(skill, 0))})
    quests = (await session.scalars(select(QuestProgress).where(QuestProgress.character_id == char.id))).all()
    completed = {q.quest_key for q in quests if q.state == "completed"}
    for key, quest in c.quests.items():
        if key in completed or any(old in completed for old in quest.legacy_done):
            fact("quest", {"quest": key})
    # Delivered/sold stages and their corresponding endings preserve the decision.
    for q in quests:
        if q.quest_key == "sealed_box":
            if q.stage in ("returned_covenant", "completed_covenant"):
                fact("decision", {"key": "covenant"})
            elif q.stage in ("sold_syndicate", "completed_syndicate"):
                fact("decision", {"key": "syndicate"})
            elif q.stage == "opened_box":
                fact("decision", {"key": "opened"})
    for row in (await session.scalars(select(FactionReputation).where(
            FactionReputation.character_id == char.id))).all():
        fact("reputation", {"faction": row.faction_key, "value": row.value})
    return await apply_events(session, char, events)


async def equipped_title(session, char):
    """The title the hero wears, as content Text, or None. Cheap: one row and a catalog lookup."""
    prefs = await session.get(AchievementPreferences, char.id)
    if prefs is None or not prefs.title:
        return None
    definition = get_content().achievements.get(prefs.title)
    if definition is None or definition.title is None:
        return None
    unlocked = await session.scalar(select(AchievementUnlock.id).where(
        AchievementUnlock.character_id == char.id, AchievementUnlock.achievement_key == prefs.title,
        AchievementUnlock.edition == EDITION))
    return definition.title if unlocked else None


async def snapshot(session, character):
    catalog = get_content().achievements
    rows = {r.achievement_key: r for r in (await session.scalars(select(AchievementProgress).where(
        AchievementProgress.character_id == character.id, AchievementProgress.edition == EDITION))).all()}
    unlocks = {r.achievement_key: r for r in (await session.scalars(select(AchievementUnlock).where(
        AchievementUnlock.character_id == character.id, AchievementUnlock.edition == EDITION))).all()}
    prefs = await session.get(AchievementPreferences, character.id)
    preferences = {"title": prefs.title if prefs else None,
                   **{k: list(getattr(prefs, k)) if prefs else [] for k in ("featured", "tracked", "revealed")}}
    entries = []
    for key, definition in catalog.items():
        unlock = unlocks.get(key)
        if definition.visibility == "hidden" and unlock is None:
            continue
        current, target = progress(definition.condition, rows[key].state if key in rows else {})
        entries.append({"key": key, "definition": definition, "current": current, "target": target,
                        "unlock": unlock, "revealed": bool(unlock) or definition.visibility == "public"
                        or key in preferences["revealed"]})
    return {"entries": entries, "preferences": preferences, "count": len(unlocks),
            "points": sum(u.points for u in unlocks.values())}


async def preference(session, char, operation, key, nonce, replace=None):
    await session.scalar(select(Character.id).where(Character.id == char.id).with_for_update())
    out = Outcome()
    if not nonce or nonce == "-":
        return Outcome.refused("achievements.invalid")
    if await audit.claim(session, f"achievement:{char.user_id}:{nonce}", user_id=char.user_id,
                         character_id=char.id, verb="achievement_preference") is None:
        return Outcome.refused("achievements.stale")
    definition = get_content().achievements.get(key)
    unlock = await session.scalar(select(AchievementUnlock.id).where(
        AchievementUnlock.character_id == char.id, AchievementUnlock.achievement_key == key,
        AchievementUnlock.edition == EDITION))
    if key == "-" and operation != "title":  # "-" only means "take off the title"
        return Outcome.refused("achievements.invalid")
    if key != "-" and (definition is None or (definition.visibility == "hidden" and unlock is None)):
        return Outcome.refused("achievements.invalid")
    if operation in ("title", "feature") and key != "-" and unlock is None:
        return Outcome.refused("achievements.invalid")
    if operation == "title" and key != "-" and definition.title is None:
        return Outcome.refused("achievements.invalid")
    if operation == "track" and (definition is None or unlock is not None):
        return Outcome.refused("achievements.invalid")
    prefs = await session.get(AchievementPreferences, char.id)
    if prefs is None:
        prefs = AchievementPreferences(character_id=char.id, featured=[], tracked=[], revealed=[])
        session.add(prefs)
    if operation == "title":
        prefs.title = None if key == "-" else key
    elif operation == "reveal":
        if definition is None or definition.visibility != "hint":
            return Outcome.refused("achievements.invalid")
        prefs.revealed = list(dict.fromkeys(prefs.revealed + [key]))
    elif operation in ("feature", "track"):
        field = "featured" if operation == "feature" else "tracked"
        values = list(getattr(prefs, field))
        if key in values:
            values.remove(key)
        elif replace is not None:
            if replace not in values:
                return Outcome.refused("achievements.stale")
            values[values.index(replace)] = key
        elif len(values) >= 3:
            return Outcome.refused("achievements.full")
        else:
            values.append(key)
        setattr(prefs, field, values)
    else:
        return Outcome.refused("achievements.invalid")
    return out.add("achievements.saved")


async def claim_notification(session, character_id, now=None):
    now = time.time() if now is None else now
    await session.scalar(select(Character.id).where(Character.id == character_id).with_for_update())
    rows = (await session.scalars(select(AchievementNotification).where(
        AchievementNotification.character_id == character_id,
        AchievementNotification.status != "sent").order_by(AchievementNotification.id).with_for_update())).all()
    if not rows or any(r.status == "sending" and r.lease_until > now for r in rows):
        return None
    token = uuid.uuid4().hex
    for row in rows:
        row.status, row.token, row.lease_until = "sending", token, now + 120
    return token, list(dict.fromkeys(k for r in rows for k in r.unlocks))


async def finish_notification(session, character_id, token, delivered):
    await session.scalar(select(Character.id).where(Character.id == character_id).with_for_update())
    rows = (await session.scalars(select(AchievementNotification).where(
        AchievementNotification.character_id == character_id, AchievementNotification.token == token,
        AchievementNotification.status == "sending"))).all()
    for row in rows:
        row.status = "sent" if delivered else "pending"
        row.token, row.lease_until = None, 0
