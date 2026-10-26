"""Turn-based combat. Pure: state in, state + log out. No I/O, no AI.

The whole encounter is a pydantic model so it can be stored as JSON and
reloaded between Telegram updates. Log entries are i18n keys plus params;
combatant ids in params are resolved to names at render time.

One module per stage (state → resolve → entities → turns → actions); this package
re-exports the public names so callers keep using `combat.x`.
"""

from oathforge.engine.combat.actions import _use_ability, player_act
from oathforge.engine.combat.entities import _converge, _run_entities, _summon, spawn

# the engine tests drive these steps one by one
from oathforge.engine.combat.resolve import _apply_damage, _apply_status, _attack
from oathforge.engine.combat.state import (
    BLESS_BONUS,
    BOSS_CONTROL_TURNS,
    COMMAND_FLOOR,
    CONVERGENCE_DAMAGE,
    CONVERGENCE_TO_HIT,
    DOT,
    FLEE_DC_BASE,
    FLEE_DC_PER_FOE,
    HARD_CONTROL,
    HEX_DIE,
    INSPIRATION_DIE,
    MARK_DIE,
    MAX_BY_KIND,
    NEGATIVE_STATUSES,
    SKIP_TURN,
    Action,
    AttackProfile,
    Combatant,
    CombatError,
    EncounterState,
    Entity,
    EntityTemplate,
    LogEntry,
    SceneObjectState,
    Shape,
    affordable,
    available_bonus_actions,
    gain_resource,
    melee_targets,
    valid_targets,
)
from oathforge.engine.combat.turns import _enemy_turn, start
