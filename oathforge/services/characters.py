"""Users, character creation, derived stats and progression."""

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import ABILITIES
from oathforge.database.models import Character, CharacterSkill, FactionReputation, ItemInstance, QuestProgress, User
from oathforge.engine import class_build, gathering, pointbuy, progression
from oathforge.engine.checks import modifier, proficiency_bonus
from oathforge.engine.combat import AttackProfile, Combatant
from oathforge.i18n import normalize_lang, t
from oathforge.services.events import Outcome

NAME_MAX = 24
DEFEAT_GOLD_PCT = 10  # a defeat costs this share of the gold you carry
ASI_LEVEL = 4  # the level that raises the class's primary ability by 2


# ---------------------------------------------------------------- users

async def get_or_create_user(session: AsyncSession, telegram_id: int, language_code: str | None) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, language=normalize_lang(language_code), settings={})
        session.add(user)
        await session.flush()
    return user


async def get_character(session: AsyncSession, user_id: int, lock: bool = False) -> Character | None:
    stmt = select(Character).where(Character.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    return await session.scalar(stmt)


def add_check(out: Outcome, res) -> Outcome:
    """"🎲 Supervivencia: 2 + 1 = 3 vs CD 13 · ❌ Fallo": the d20, the bonus, the total, the DC and the verdict."""
    sign = "−" if res.bonus < 0 else "+"
    verdict = "check.success" if res.success else "check.failure"
    return out.add("check.result", skill=get_content().skills[res.skill].name.model_dump(), roll=res.kept,
                   bonus=f"{sign} {abs(res.bonus)}", total=res.total, dc=res.dc, result="✅" if res.success else "❌",
                   verdict={lang: t(lang, verdict) for lang in ("es", "en")})


def ensure_free(char: Character) -> Outcome | None:
    """A refusal while fighting or busy with a field activity (mining, a long stay, tracking); None if free."""
    if char.state == "in_combat":
        return Outcome.refused("explore.err.in_combat")
    if char.state == "busy":
        return Outcome.refused("activity.err.busy")
    return None


def set_setting(user: User, key: str, value) -> None:
    """Per-player preferences (e.g. manual_rolls); a new dict so the JSON column notices the change."""
    user.settings = {**(user.settings or {}), key: value}


def valid_name(name: str) -> bool:
    name = name.strip()
    return 2 <= len(name) <= NAME_MAX and all(ch.isalpha() or ch in " '-" for ch in name)


# ---------------------------------------------------------------- creation

CUSTOM_SKILLS = 2  # a player-written background picks this many skills, like a D&D background


def background_name(char: Character, lang: str) -> str:
    custom = char.custom_background
    return custom["title"] if custom else get_content().backgrounds[char.background].name.get(lang)


def background_story(char: Character, lang: str) -> str:
    custom = char.custom_background
    return custom["story"] if custom else get_content().backgrounds[char.background].description.get(lang)


def valid_custom(custom: dict | None) -> bool:
    c = get_content()
    skills = (custom or {}).get("skills") or []
    return (bool(custom) and bool(custom.get("title")) and bool(custom.get("story"))
            and len(set(skills)) == CUSTOM_SKILLS == len(skills) and all(s in c.skills for s in skills))


def starting_scores(class_key: str, lineage_key: str, base: dict[str, int] | None = None) -> dict[str, int]:
    """Point-buy scores (or the class's recommended array) plus lineage bonuses."""
    c = get_content()
    scores = dict(base) if base is not None and pointbuy.valid(base) else dict(c.classes[class_key].array)
    for ability, bonus in c.lineages[lineage_key].bonuses.items():
        scores[ability] = min(20, scores[ability] + bonus)
    return scores


async def create_character(
    session: AsyncSession, user: User, name: str, lineage: str, background: str, class_key: str,
    gender: str | None = None, scores: dict[str, int] | None = None, custom: dict | None = None,
) -> Character:
    """custom: the player-written background ({"title", "story", "skills"}) when the background is a custom one."""
    c = get_content()
    cls, bg, lin = c.classes[class_key], c.backgrounds[background], c.lineages[lineage]
    if bg.custom != valid_custom(custom):
        raise ValueError("a custom background needs a title, a story and exactly 2 known skills")
    custom = {k: custom[k] for k in ("title", "story", "skills")} if bg.custom else None
    scores = starting_scores(class_key, lineage, scores)
    hp = progression.max_hp(cls.hit_die, modifier(scores["con"]), 1)
    char = Character(
        user_id=user.id, name=name.strip()[:NAME_MAX], lineage=lineage, background=background,
        class_key=class_key, gender=gender, abilities=scores, level=1, xp=0, hp=hp, max_hp=hp, gold=bg.gold,
        location=c.start_location, state="idle", flags={}, conditions={},
        resources=full_resources(class_key, 1), custom_background=custom,
    )
    session.add(char)
    await session.flush()

    proficient = set(cls.skills) | set(custom["skills"] if custom else bg.skills) | set(lin.skills)
    for skill in c.skills:
        session.add(CharacterSkill(character_id=char.id, skill=skill, proficient=skill in proficient, xp=0, recent=[]))

    items: dict[str, int] = {}
    for source in (cls.items, bg.items):
        for key, qty in source.items():
            items[key] = items.get(key, 0) + qty
    for key, qty in items.items():
        item = c.items[key]
        if item.stackable:
            session.add(ItemInstance(owner_character_id=char.id, item_key=key, qty=qty, history=[]))
        else:
            for i in range(qty):
                slot = item.slot if key in cls.equip and i == 0 else None
                session.add(ItemInstance(owner_character_id=char.id, item_key=key, qty=1, equipped_slot=slot, history=[]))

    for faction in c.factions:
        session.add(FactionReputation(character_id=char.id, faction_key=faction, value=0))
    for qkey, quest in c.quests.items():
        session.add(QuestProgress(character_id=char.id, quest_key=qkey, stage=quest.start_stage,
                                  state=quest.stages[quest.start_stage].state))
    await session.flush()
    return char


def full_resources(class_key: str, level: int) -> dict[str, int | None]:
    cls = get_content().classes[class_key]
    return {k: a.uses for k, a in cls.abilities.items() if a.level <= level and a.kind != "passive"}


# ---------------------------------------------------------------- derived stats

def mods(char: Character) -> dict[str, int]:
    return {a: modifier(char.abilities[a]) for a in ABILITIES}


async def skills_of(session: AsyncSession, char: Character) -> dict[str, CharacterSkill]:
    rows = await session.scalars(select(CharacterSkill).where(CharacterSkill.character_id == char.id))
    return {r.skill: r for r in rows}


def skill_bonus(char: Character, skills: dict[str, CharacterSkill], skill: str) -> int:
    c = get_content()
    row = skills.get(skill)
    bonus = mods(char)[c.skills[skill].ability]
    if row is not None:
        if row.proficient:
            bonus += proficiency_bonus(char.level)
        bonus += progression.skill_rank(row.xp)
    return bonus


def all_skill_bonuses(char: Character, skills: dict[str, CharacterSkill]) -> dict[str, int]:
    return {s: skill_bonus(char, skills, s) for s in get_content().skills}


async def equipped(session: AsyncSession, char: Character) -> dict[str, ItemInstance]:
    rows = await session.scalars(
        select(ItemInstance).where(ItemInstance.owner_character_id == char.id, ItemInstance.equipped_slot.is_not(None))
    )
    return {r.equipped_slot: r for r in rows}


def class_passives(char: Character) -> list:
    cls = get_content().classes[char.class_key]
    return [a for a in cls.abilities.values() if a.kind == "passive" and a.level <= char.level]


def immunities(char: Character) -> list[str]:
    poison = {"poisoned"} if "poison_resilience" in get_content().lineages[char.lineage].traits else set()
    return sorted({s for p in class_passives(char) for s in p.immune} | poison)


def spell_stats(char: Character) -> tuple[int, int, int]:
    """(casting modifier, spell attack bonus, save DC); casting is 0 for classes without spells."""
    cls = get_content().classes[char.class_key]
    casting = mods(char)[cls.casting] if cls.casting else 0
    pb = proficiency_bonus(char.level)
    return casting, casting + pb, 8 + casting + pb


def armor_class(char: Character, gear: dict[str, ItemInstance]) -> int:
    c = get_content()
    dex = mods(char)["dex"]
    body = gear.get("body")
    if body:
        item = c.items[body.item_key]
        ac = (item.base_ac or 10) + min(dex, item.dex_cap if item.dex_cap is not None else dex)
    else:
        ac = 10 + dex
    if "off_hand" in gear:
        ac += c.items[gear["off_hand"].item_key].ac_bonus
    ac += sum(p.ac_bonus + (0 if body else p.ac_bonus_unarmored) for p in class_passives(char))
    return ac


def attack_profiles(char: Character, gear: dict[str, ItemInstance]) -> list[AttackProfile]:
    c = get_content()
    m = mods(char)
    pb = proficiency_bonus(char.level)
    out = []
    for slot in ("main_hand", "ranged"):
        inst = gear.get(slot)
        if not inst:
            continue
        item = c.items[inst.item_key]
        w = item.weapon
        ability = m["dex"] if w.ranged else (max(m["str"], m["dex"]) if w.finesse else m["str"])
        sign = "+" if ability >= 0 else "-"
        out.append(AttackProfile(
            key="main" if slot == "main_hand" else "ranged", name=item.name.model_dump(),
            to_hit=ability + pb, damage=f"{w.damage}{sign}{abs(ability)}", damage_type=w.damage_type,
            ranged=w.ranged, finesse=w.finesse,
        ))
    if not any(not a.ranged for a in out):
        sign = "+" if m["str"] >= 0 else "-"
        out.insert(0, AttackProfile(key="main", name={"es": "Puños", "en": "Fists"}, to_hit=m["str"] + pb,
                                    damage=f"1{sign}{abs(m['str'])}", damage_type="bludgeoning"))
    return out


async def build_combatant(session: AsyncSession, char: Character, cid: str = "p1") -> Combatant:
    return combatant_from(char, await equipped(session, char), await skills_of(session, char), cid)


def combatant_from(char: Character, gear: dict[str, ItemInstance], skills: dict[str, CharacterSkill],
                   cid: str = "p1") -> Combatant:
    """The player's combat stats from already loaded gear and skills (no database; also used by the simulator)."""
    c = get_content()
    passives = class_passives(char)
    lineage = c.lineages[char.lineage]
    sneak = 0
    for p in passives:
        for lvl, dice in sorted(p.sneak_dice.items()):
            if char.level >= lvl:
                sneak = dice
    cls = c.classes[char.class_key]
    casting_mod, spell_to_hit, spell_dc = spell_stats(char)
    bonus = next((p for p in passives if p.bonus_damage), None)
    return Combatant(
        id=cid, side="player", ref=str(char.id), name={"es": char.name, "en": char.name},
        hp=char.hp, max_hp=char.max_hp, ac=armor_class(char, gear),
        row="front" if cls.primary == "str" else "back",
        dex_mod=mods(char)["dex"], passive_perception=10 + skill_bonus(char, skills, "perception"),
        attacks=attack_profiles(char, gear), immune=immunities(char), level=char.level,
        skill_bonus=all_skill_bonuses(char, skills), abilities=dict(char.resources),
        sneak_dice=sneak, extra_attack=any(p.extra_attack for p in passives),
        halve_first_hit=any(p.halve_first_hit for p in passives),
        relentless="relentless" in lineage.traits,
        crit_range=min([p.crit_range for p in passives if p.crit_range] or [20]),
        casting_mod=casting_mod, spell_to_hit=spell_to_hit, spell_dc=spell_dc,
        spell_damage_bonus=casting_mod if any(p.spell_damage_bonus for p in passives) else 0,
        bonus_damage=bonus.bonus_damage if bonus else None,
        bonus_damage_type=(bonus.bonus_damage_type or "radiant") if bonus else "radiant",
    )


# ---------------------------------------------------------------- progression

BUILD_VERSION = 1
MILESTONES = "milestones"  # char.build: the narrative gates already crossed


def build_of(char: Character) -> dict:
    return char.build or {"v": BUILD_VERSION}


def milestones_of(char: Character) -> list[str]:
    return list(build_of(char).get(MILESTONES, []))


def eligible_level(char: Character) -> int:
    """XP proves experience and a milestone opens a border: the level needs both (roadmap_balance §4.1)."""
    return class_build.eligible_level(char.xp, milestones_of(char), get_content().progression)


def level_gate(char: Character) -> str | None:
    """The milestone holding the hero back from the level their XP already earned, if any."""
    return class_build.blocked_by(char.xp, milestones_of(char), get_content().progression)


def grant_xp(char: Character, amount: int, out: Outcome) -> None:
    """Experience always counts, even against a closed gate: it is kept and applied when it opens."""
    if amount <= 0:
        return
    char.xp += amount
    out.add("progress.xp", amount=amount)
    apply_levels(char, out)


def grant_milestone(char: Character, key: str, out: Outcome) -> bool:
    """Cross a narrative border. Granted once; the levels its XP already paid for arrive with it."""
    done = milestones_of(char)
    if key in done or key not in get_content().progression.milestones:
        return False
    char.build = {**build_of(char), "v": BUILD_VERSION, MILESTONES: [*done, key]}
    out.add("progress.milestone", milestone=get_content().progression.milestones[key].name.model_dump())
    apply_levels(char, out)
    return True


def apply_levels(char: Character, out: Outcome) -> None:
    """Raise the hero to the level they are entitled to. Called after XP and after a milestone."""
    c = get_content()
    cls = c.classes[char.class_key]
    target = eligible_level(char)
    while char.level < target:
        char.level += 1
        if char.level == ASI_LEVEL:
            scores = dict(char.abilities)
            scores[cls.primary] = min(20, scores[cls.primary] + 2)
            char.abilities = scores
            out.add("progress.asi", ability=c.abilities[cls.primary].name.model_dump())
        old_max = char.max_hp
        char.max_hp = progression.max_hp(cls.hit_die, modifier(char.abilities["con"]), char.level)
        char.hp += char.max_hp - old_max
        resources = full_resources(char.class_key, char.level)
        resources.update({k: v for k, v in char.resources.items() if k in resources})
        for key, ability in cls.abilities.items():
            if ability.level == char.level:
                resources[key] = ability.uses if ability.kind != "passive" else None
                out.add("progress.new_ability", ability=ability.name.model_dump(), cls=char.class_key, ability_key=key)
        char.resources = {k: v for k, v in resources.items() if k in full_resources(char.class_key, char.level)}
        out.add("progress.level_up", level=char.level, max_hp=char.max_hp, prev_max_hp=old_max,
                cls=char.class_key)
        if char.level == 5:
            out.add("progress.specialization_soon")


def mastery_name(skill: str) -> dict:
    return {lang: t(lang, f"mastery.name.{skill}") for lang in ("es", "en")}


STATS = "stats"  # char.flags: counters for the journal's statistics (since v0.7.23)


def stats(char: Character) -> dict:
    return dict((char.flags or {}).get(STATS) or {})


def bump_stats(char: Character, **amounts: int) -> None:
    """Add to the character's counters (yards walked, battles won, dodges...)."""
    if not any(amounts.values()):
        return
    st = stats(char)
    for key, n in amounts.items():
        st[key] = int(st.get(key, 0)) + n
    char.flags = {**(char.flags or {}), STATS: st}


def visited(char: Character, location: str) -> None:
    st = stats(char)
    places = list(st.get("places", []))
    if location not in places:
        st["places"] = places + [location]
        char.flags = {**(char.flags or {}), STATS: st}


PENDING_SKIN = "pending_skin"  # char.flags: the beasts just killed, waiting for /skin where they fell


def pending_skin(char: Character) -> list[str]:
    pending = (char.flags or {}).get(PENDING_SKIN) or {}
    return list(pending.get("monsters", [])) if pending.get("location") == char.location else []


def drop_pending_skin(char: Character) -> None:
    """Leaving or starting something else: the carcasses are left behind."""
    if PENDING_SKIN in (char.flags or {}):
        char.flags = {k: v for k, v in char.flags.items() if k != PENDING_SKIN}


def hobby_of(skill: str) -> str | None:
    """The hobby practised through this field activity (fishing), if any."""
    return next((k for k, p in get_content().professions.items() if p.practice == skill), None)


def mastery_xp(char: Character, skill: str) -> int:
    hobby = hobby_of(skill)
    if hobby is not None:
        return int((char.professions or {}).get("xp", {}).get(hobby, 0))
    return int((char.masteries or {}).get(skill, 0))


def grant_mastery(char: Character, skill: str, amount: int, out: Outcome) -> None:
    """Gathering masteries (mining, tracking...) grow 0-5 with use, apart from d20 skills. Fishing levels
    the Fishing hobby instead, stored with the professions like Cooking."""
    if amount <= 0:
        return
    before = mastery_xp(char, skill)
    hobby = hobby_of(skill)
    if hobby is not None:
        profs = char.professions or {}
        char.professions = {"active": list(profs.get("active", [])), "xp": {**profs.get("xp", {}), hobby: before + amount}}
        name = get_content().professions[hobby].name.model_dump()
        out.add("prof.xp", prof=name, amount=amount)
        rank = gathering.rank_for(before + amount)
        if rank > gathering.rank_for(before):
            out.add("prof.rank", prof=name, rank=rank)
            from oathforge.services import professions  # its techniques, like any other discipline
            professions.announce_techniques(hobby, gathering.rank_for(before), rank, out)
        return
    char.masteries = {**(char.masteries or {}), skill: before + amount}
    out.add("mastery.xp", skill=mastery_name(skill), amount=amount)
    rank = gathering.rank_for(before + amount)
    if rank > gathering.rank_for(before):
        out.add("mastery.rank", skill=mastery_name(skill), rank=rank)


async def practice(session: AsyncSession, char: Character, skill: str, tier: str, context: str, out: Outcome) -> None:
    """Use-based skill growth with diminishing returns for repetition."""
    if tier == "trivial":
        return
    row = await session.scalar(
        select(CharacterSkill).where(CharacterSkill.character_id == char.id, CharacterSkill.skill == skill)
    )
    if row is None:
        return
    now = int(time.time())
    recent = [r for r in row.recent if now - r[1] < progression.RECENT_WINDOW_SECONDS]
    repeats = sum(1 for r in recent if r[0] == context)
    gain = progression.skill_gain(tier, repeats)
    row.recent = (recent + [[context, now]])[-20:]
    if gain <= 0:
        return
    before = progression.skill_rank(row.xp)
    row.xp += gain
    after = progression.skill_rank(row.xp)
    if after > before:
        out.add("progress.skill_rank", skill=get_content().skills[skill].name.model_dump(), rank=after)


async def defeat_penalty(char: Character, out: Outcome) -> None:
    c = get_content()
    lost = char.gold * DEFEAT_GOLD_PCT // 100
    char.gold -= lost
    char.hp = max(1, char.max_hp // 2)
    char.location = c.respawn_location
    char.flags = {k: v for k, v in (char.flags or {}).items() if k != "trip"}  # exploration.TRIP: the trip ends here
    char.state = "idle"
    char.conditions = {**char.conditions, "injured": True}
    out.add("combat.defeat_penalty" if lost else "combat.defeat_penalty_free", gold=lost, place=c.locations[c.respawn_location].phrase())
