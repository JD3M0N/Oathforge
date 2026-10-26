"""Turn-based combat. Pure: state in, state + log out. No I/O, no AI.

The whole encounter is a pydantic model so it can be stored as JSON and
reloaded between Telegram updates. Log entries are i18n keys plus params;
combatant ids in params are resolved to names at render time.

One module per stage (state → resolve → entities → turns → actions); this package
re-exports the public names so callers keep using `combat.x`.
"""

from oathforge.engine.combat.state import (
    Action,
    affordable,
    AttackProfile,
    available_bonus_actions,
    BLESS_BONUS,
    BOSS_CONTROL_TURNS,
    Combatant,
    CombatError,
    COMMAND_FLOOR,
    CONVERGENCE_DAMAGE,
    CONVERGENCE_TO_HIT,
    DOT,
    EncounterState,
    Entity,
    EntityTemplate,
    FLEE_DC_BASE,
    FLEE_DC_PER_FOE,
    gain_resource,
    HARD_CONTROL,
    HEX_DIE,
    INSPIRATION_DIE,
    LogEntry,
    MARK_DIE,
    MAX_BY_KIND,
    melee_targets,
    NEGATIVE_STATUSES,
    SceneObjectState,
    Shape,
    SKIP_TURN,
    valid_targets,
)
from oathforge.engine.combat.entities import spawn
from oathforge.engine.combat.turns import start
from oathforge.engine.combat.actions import player_act

# the engine tests drive these steps one by one
from oathforge.engine.combat.resolve import _apply_damage, _apply_status, _attack
from oathforge.engine.combat.entities import _converge, _run_entities, _summon
from oathforge.engine.combat.turns import _enemy_turn
from oathforge.engine.combat.actions import _use_ability
