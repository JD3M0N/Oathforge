"""Typed achievement conditions and catalog validation."""
from typing import Literal
from string import Formatter
from pydantic import Field, model_validator
from oathforge.content.schemas import Strict, Text

EDITION = "v0_9"  # a fixed content edition: an expansion adds a new one instead of changing these

EVENT_FIELDS = {
    "visit": {"location", "outside"}, "flag": {"key"}, "discovery": {"key"},
    "combat": {"status", "eligible", "hp", "consumed", "enemies", "location", "period", "hunt"},
    "kill": {"monster"}, "scene": {"key"}, "craft": {"recipe"},
    "activity": {"skill", "tool"}, "mastery": {"rank", "skill"}, "quest": {"quest"},
    "decision": {"key"}, "reputation": {"faction", "value"},
    "seen": {"monster"}, "secrets": {"monster"}, "unlock": {"key"},
}

class AchievementCondition(Strict):
    kind: Literal["event", "counter", "distinct", "threshold", "sequence", "all", "any"]
    event: str | None = None
    match: dict[str, str | int | bool] = Field(default_factory=dict)
    field: str | None = None
    values: list[str] = Field(default_factory=list)
    target: int = Field(default=1, ge=1)
    children: list["AchievementCondition"] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid(self):
        if self.kind in ("all", "any", "sequence"):
            if not self.children or self.event or self.field or self.match or self.values or self.target != 1:
                raise ValueError("composite conditions require only children")
        else:
            if self.event not in EVENT_FIELDS or self.children:
                raise ValueError("unknown gameplay event or unexpected children")
            fields = EVENT_FIELDS[self.event]
            if set(self.match) - fields or (self.field and self.field not in fields):
                raise ValueError("unknown gameplay field")
            if self.kind in ("distinct", "threshold") and not self.field:
                raise ValueError("field required")
            if self.values and (not self.field or len(set(self.values)) != len(self.values)):
                raise ValueError("values require a field and must be distinct")
            if self.kind == "distinct" and self.values and self.target > len(self.values):
                raise ValueError("unreachable distinct target")
            if self.kind == "event" and self.target != 1:
                raise ValueError("event target must be one")
        return self

class Achievement(Strict):
    edition: Literal["v0_9"] = EDITION
    category: Literal["exploration", "combat", "crafting", "field", "story", "knowledge", "curiosity"]
    form: Literal["milestone", "series", "challenge", "narrative", "secret", "meta"] = "milestone"
    visibility: Literal["public", "hint", "hidden"] = "public"
    name: Text
    description: Text
    earned: Text
    hint: Text | None = None
    title: Text | None = None
    points: Literal[10, 20, 40, 80]
    condition: AchievementCondition

    @model_validator(mode="after")
    def bilingual(self):
        for value in (self.name, self.description, self.earned, self.hint, self.title):
            if value is not None:
                if not value.es.strip() or not value.en.strip():
                    raise ValueError("empty translation")
                fields = lambda s: {k for _, k, _, _ in Formatter().parse(s) if k is not None}
                if fields(value.es) != fields(value.en):
                    raise ValueError("translation placeholders differ")
        if self.visibility == "hint" and self.hint is None:
            raise ValueError("hint text required")
        return self

def validate_catalog(content):
    catalog = content.achievements
    edges = {key: set() for key in catalog}
    pools = {("visit", "location"): content.locations, ("combat", "location"): content.locations,
             ("craft", "recipe"): content.recipes, ("quest", "quest"): content.quests,
             ("reputation", "faction"): content.factions, ("unlock", "key"): catalog}
    for event in ("kill", "seen", "secrets"):
        pools[event, "monster"] = content.monsters
    pools["flag", "key"] = {"crypt_unlocked"}
    pools["discovery", "key"] = {f"{k}:{d}" for k, loc in content.locations.items() for d in loc.discoveries}
    from oathforge.engine.gathering import GATHER_SKILLS, MASTERIES
    pools["activity", "skill"] = GATHER_SKILLS
    pools["mastery", "skill"] = MASTERIES
    pools["decision", "key"] = {"covenant", "syndicate", "opened"}

    def walk(key, condition):
        for field, value in condition.match.items():
            pool = pools.get((condition.event, field))
            if pool is not None and value not in pool:
                raise ValueError(f"achievement {key}: unknown {field} {value}")
        pool = pools.get((condition.event, condition.field))
        if pool is not None and any(v not in pool for v in condition.values):
            raise ValueError(f"achievement {key}: unknown reference in values")
        if condition.event == "unlock":
            edges[key].update(condition.values)
            if "key" in condition.match:
                edges[key].add(condition.match["key"])
        for child in condition.children:
            walk(key, child)
    for key, achievement in catalog.items():
        if not key.isascii() or len(key) > 32 or not key.replace("_", "").isalnum():
            raise ValueError(f"invalid achievement id: {key}")
        walk(key, achievement.condition)
    visited, visiting = set(), set()
    def visit(key):
        if key in visiting:
            raise ValueError("cyclic achievement dependencies")
        if key in visited:
            return
        visiting.add(key)
        for dependency in edges[key]:
            visit(dependency)
        visiting.remove(key)
        visited.add(key)
    for key in edges:
        visit(key)
