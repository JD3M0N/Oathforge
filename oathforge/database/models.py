from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

Json = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(8), default="es")
    settings: Mapped[dict] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    character: Mapped["Character | None"] = relationship(back_populates="user", uselist=False)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(32))
    lineage: Mapped[str] = mapped_column(String(32))
    background: Mapped[str] = mapped_column(String(32))
    class_key: Mapped[str] = mapped_column(String(32))
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)  # male | female; None: created before 0.4.4
    specialization: Mapped[str | None] = mapped_column(String(32), nullable=True)
    abilities: Mapped[dict] = mapped_column(Json)
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    hp: Mapped[int] = mapped_column(Integer)
    max_hp: Mapped[int] = mapped_column(Integer)
    gold: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default="idle")  # idle | in_combat | busy (field activity)
    flags: Mapped[dict] = mapped_column(Json, default=dict)
    resources: Mapped[dict] = mapped_column(Json, default=dict)  # ability uses left
    conditions: Mapped[dict] = mapped_column(Json, default=dict)  # e.g. {"injured": true}
    bestiary: Mapped[dict] = mapped_column(Json, default=dict)  # monster -> {"seen": n, "killed": n}
    checks_tried: Mapped[dict] = mapped_column(Json, default=dict)  # check key -> [game day, level] of last attempt
    masteries: Mapped[dict] = mapped_column(Json, default=dict)  # gathering mastery -> xp
    professions: Mapped[dict] = mapped_column(Json, default=dict)  # {"active": [..], "xp": {profession: xp}}
    # {"known": [special recipes learned from a blueprint], "spec": {discipline: branch}, "tools": {discipline: item}}
    crafting: Mapped[dict] = mapped_column(Json, default=dict)
    home: Mapped[dict] = mapped_column(Json, default=dict)  # {"bed": true, "chest": level} once installed
    # progression choices, versioned: {"v": 1, "milestones": [...], "choices": {"training:5": …}, …}
    build: Mapped[dict] = mapped_column(Json, default=dict)
    pools: Mapped[dict] = mapped_column(Json, default=dict)  # the class's own bar: {"v": 1, "mana": 7}
    cooldowns: Mapped[dict] = mapped_column(Json, default=dict)  # key -> unix time when it is ready again
    # background "custom": {"title", "story", "skills"} written by the player and reviewed by the AI
    custom_background: Mapped[dict | None] = mapped_column(Json, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="character")

    __mapper_args__ = {"version_id_col": version}


class CharacterSkill(Base):
    __tablename__ = "character_skills"
    __table_args__ = (UniqueConstraint("character_id", "skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    skill: Mapped[str] = mapped_column(String(32))
    proficient: Mapped[bool] = mapped_column(Boolean, default=False)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    recent: Mapped[list] = mapped_column(Json, default=list)  # [[context, unix_ts], ...]


class ItemInstance(Base):
    __tablename__ = "item_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True, nullable=True
    )
    item_key: Mapped[str] = mapped_column(String(64))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    equipped_slot: Mapped[str | None] = mapped_column(String(16), nullable=True)
    container: Mapped[str | None] = mapped_column(String(16), nullable=True)  # None: the backpack · "chest": the room
    crafted_by: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), nullable=True)
    history: Mapped[list] = mapped_column(Json, default=list)


class Party(Base):
    """Reserved for co-op (phase 3)."""

    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    leader_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PartyMember(Base):
    __tablename__ = "party_members"
    __table_args__ = (UniqueConstraint("party_id", "character_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"), nullable=True)
    location: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")
    achievement_metrics: Mapped[dict | None] = mapped_column(Json, nullable=True)
    state: Mapped[dict] = mapped_column(Json)
    fixed_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    panel_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    panel_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __mapper_args__ = {"version_id_col": version}


class EncounterParticipant(Base):
    __tablename__ = "encounter_participants"
    __table_args__ = (UniqueConstraint("encounter_id", "character_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    combatant_id: Mapped[str] = mapped_column(String(8))


OPEN_ACTIVITY = "status IN ('running', 'awaiting_combat')"


class WorldActivity(Base):
    """A timed field activity (gather 5 min, stay 15 min, track 5 min).

    The timer lives here (unix seconds), never in memory, so a restart loses nothing; the result
    is rolled once at claim time and stored, so pressing "Claim" twice never pays twice.
    """

    __tablename__ = "world_activities"
    __table_args__ = (
        Index("uq_open_activity_per_character", "character_id", unique=True,
              postgresql_where=text(OPEN_ACTIVITY), sqlite_where=text(OPEN_ACTIVITY)),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    location: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))  # gather | stay | track
    skill: Mapped[str] = mapped_column(String(32))  # mastery that grows
    started_at: Mapped[float] = mapped_column(Float)
    ends_at: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running | awaiting_combat | done | cancelled
    seed: Mapped[int] = mapped_column(BigInteger)
    result: Mapped[dict] = mapped_column(Json, default=dict)  # outcome, items given or pending, xp, monsters
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True)
    chronicle: Mapped[str | None] = mapped_column(Text, nullable=True)
    chronicle_ai: Mapped[bool] = mapped_column(Boolean, default=False)  # counts against the daily chronicle budget
    resolved_at: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)


class CombatAction(Base):
    __tablename__ = "combat_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"), index=True)
    round: Mapped[int] = mapped_column(Integer)
    actor: Mapped[str] = mapped_column(String(8))
    action: Mapped[dict] = mapped_column(Json)
    result: Mapped[list] = mapped_column(Json)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NpcMemory(Base):
    __tablename__ = "npc_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    npc_key: Mapped[str] = mapped_column(String(64), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="episodic")
    text: Mapped[str] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NpcRelationship(Base):
    __tablename__ = "npc_relationships"
    __table_args__ = (UniqueConstraint("npc_key", "character_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    npc_key: Mapped[str] = mapped_column(String(64))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    trust: Mapped[int] = mapped_column(Integer, default=0)
    fear: Mapped[int] = mapped_column(Integer, default=0)
    debt: Mapped[int] = mapped_column(Integer, default=0)


class FactionReputation(Base):
    __tablename__ = "faction_reputation"
    __table_args__ = (UniqueConstraint("character_id", "faction_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    faction_key: Mapped[str] = mapped_column(String(64))
    value: Mapped[int] = mapped_column(Integer, default=0)


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    __table_args__ = (UniqueConstraint("character_id", "quest_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    quest_key: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    counters: Mapped[dict] = mapped_column(Json, default=dict)  # objective index -> progress
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LocationState(Base):
    """Runtime state of a location; static data lives in content/world/."""

    __tablename__ = "location_state"

    location_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[dict] = mapped_column(Json, default=dict)


class WorldFact(Base):
    __tablename__ = "world_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[dict] = mapped_column(Json)
    tags: Mapped[list] = mapped_column(Json, default=list)
    source: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    verb: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(Json, default=dict)
    result: Mapped[dict] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AiUsage(Base):
    __tablename__ = "ai_usage"
    __table_args__ = (UniqueConstraint("user_id", "day", "model"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    day: Mapped[date] = mapped_column(Date)
    model: Mapped[str] = mapped_column(String(64))
    calls: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)


class MediaFile(Base):
    """Telegram file_id of an uploaded image, so it is sent again without re-uploading.

    A file_id only works for the bot that uploaded it, hence ``bot_id``; a new ``checksum``
    (the file was replaced) means the cached id is stale.
    """

    __tablename__ = "media_files"

    bot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    checksum: Mapped[str] = mapped_column(String(64))
    file_id: Mapped[str] = mapped_column(String(255))
    file_unique_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AchievementProgress(Base):
    __tablename__ = "achievement_progress"
    __table_args__ = (UniqueConstraint("character_id", "achievement_key", "edition"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    achievement_key: Mapped[str] = mapped_column(String(32))
    edition: Mapped[str] = mapped_column(String(16))
    state: Mapped[dict] = mapped_column(Json, default=dict)


class AchievementUnlock(Base):
    __tablename__ = "achievement_unlocks"
    __table_args__ = (UniqueConstraint("character_id", "achievement_key", "edition"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    achievement_key: Mapped[str] = mapped_column(String(32))
    edition: Mapped[str] = mapped_column(String(16))
    points: Mapped[int] = mapped_column(Integer)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    evidence: Mapped[dict] = mapped_column(Json)
    retroactive: Mapped[bool] = mapped_column(Boolean, default=False)


class HeroFact(Base):
    """One engine fact. Deduplicates achievement grants and feeds the chronicle and the stats."""

    __tablename__ = "hero_facts"
    __table_args__ = (
        UniqueConstraint("character_id", "event_id"),
        Index("ix_hero_facts_chronicle", "character_id", "notable", "id"),
        Index("ix_hero_facts_tag", "character_id", "tag"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(24))
    data: Mapped[dict] = mapped_column(Json, default=dict)
    # What makes a first-time fact unique ("visit:crownreach_market"); null when the kind repeats freely.
    tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    game_day: Mapped[int] = mapped_column(Integer, default=0)
    notable: Mapped[bool] = mapped_column(Boolean, default=False)
    retroactive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AchievementPreferences(Base):
    __tablename__ = "achievement_preferences"
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(32), nullable=True)
    featured: Mapped[list] = mapped_column(Json, default=list)
    tracked: Mapped[list] = mapped_column(Json, default=list)
    revealed: Mapped[list] = mapped_column(Json, default=list)


class AchievementNotification(Base):
    __tablename__ = "achievement_notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    unlocks: Mapped[list] = mapped_column(Json, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    token: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
