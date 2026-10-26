"""Single router for in-game buttons (everything except creation)."""

from oathforge.bot.handlers.callbacks.acts import ACTS, ARRIVALS, IN_PLACE, ROLL_VERBS, _act, refused, roll_prompt
from oathforge.bot.handlers.callbacks.combat import NEEDS_TARGET, fresh_token
from oathforge.bot.handlers.callbacks.rolls import do_roll, set_manual_rolls, settings
from oathforge.bot.handlers.callbacks.router import VIEWS, handler, on_callback
