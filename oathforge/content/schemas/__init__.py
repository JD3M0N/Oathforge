"""Pydantic schemas for the YAML content files.

Every player-facing string is a ``Text`` ({es: ..., en: ...}). Prompt-only
fields (NPC persona, secrets) are plain English strings because only the LLM
reads them.

One module per domain; this package re-exports them so callers keep importing from ``schemas``.
"""

from oathforge.content.schemas.classes import (
    MAX_CHARACTER_LEVEL,
    AbilityInfo,
    AbilityPatch,
    Background,
    ClassAbility,
    ClassSpecialization,
    EntityDef,
    EntityKind,
    EntityRole,
    FormAttack,
    FormDef,
    GameClass,
    Lineage,
    Milestone,
    Modifier,
    Progression,
    ResourceDef,
    Role,
    Skill,
    Training,
    TrainingEffects,
)
from oathforge.content.schemas.common import (
    ABILITIES,
    CHRONICLE_KEYS,
    CHRONICLE_OUTCOMES,
    CHRONICLE_PLACEHOLDERS,
    CHRONICLE_SKILLS,
    DC_TIERS,
    FALLBACK_KEYS,
    FALLBACK_PLACEHOLDERS,
    STATUSES,
    T1_MIN_RANK,
    CreatureType,
    DamageType,
    Row,
    Station,
    Strict,
    Text,
    Tier,
)
from oathforge.content.schemas.items import (
    TYPE_ICONS,
    Item,
    ItemCombat,
    ItemEffect,
    RestoreHp,
    RestoreSpellCharge,
    ShortRest,
    ToolProfile,
    WeaponStats,
)
from oathforge.content.schemas.monsters import BossPattern, HarvestEntry, LootEntry, Monster, MonsterAttack, StatusApply
from oathforge.content.schemas.professions import Profession, Recipe, SpecEffects, Specialization, Technique
from oathforge.content.schemas.quests import (
    Effect,
    Quest,
    QuestAction,
    QuestCheck,
    QuestObjective,
    QuestStage,
    QuestTrigger,
)
from oathforge.content.schemas.world import (
    Article,
    Continent,
    Discovery,
    EncounterEntry,
    Exit,
    Faction,
    FixedEncounter,
    Gathering,
    GatherResource,
    Healer,
    Location,
    Npc,
    RuleSection,
    SceneEffect,
    SceneObject,
    Shop,
    WorldGuide,
    Zone,
)
