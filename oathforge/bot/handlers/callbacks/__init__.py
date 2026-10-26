"""Single router for in-game buttons (everything except creation)."""

from oathforge.bot.handlers.callbacks.rolls import do_roll, set_manual_rolls, settings
from oathforge.bot.handlers.callbacks.acts import _act, ACTS, ARRIVALS, IN_PLACE, refused, roll_prompt, ROLL_VERBS
from oathforge.bot.handlers.callbacks.combat import fresh_token, NEEDS_TARGET
from oathforge.bot.handlers.callbacks.router import handler, on_callback, VIEWS
