"""Buttons that change something: each verb calls its service, then shows the result."""

from telegram import Update

from oathforge.bot import render
from oathforge.bot.handlers.common import (
    answer,
    current_view,
    drop_buttons,
    edit_or_send,
    load,
    rng,
    send,
    send_activity_result,
    send_chronicle,
    send_outcome,
    send_result,
)
from oathforge.bot.keyboards import btn, cb, markup
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import (
    actions,
    activities,
    audit,
    class_specializations,
    crafting,
    exploration,
    home,
    inventory,
    npcs,
    professions,
    quests,
    specializations,
)
from oathforge.services.events import Outcome, render_event

ROLL_VERBS = {"look", "qa"}  # button actions that can wait for the manual 🎲 button


async def _act(update: Update, context, verb: str, arg: str, n: str, rolled_at: str | None = None) -> None:
    """State-changing, non-combat actions. One transaction, idempotent by nonce.

    With manual rolls on, an action that needs a skill check is parked until the player presses 🎲
    (``rolled_at`` is then the location where it was asked, so a roll never lands somewhere else).
    """
    r = rng()
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        lang = context.user_data["lang"] = user.language
        if char is None:
            await send(update, t(lang, "start.need_character"))
            return
        early = None  # (text, kb) answered without acting: a roll to make, or a roll that no longer fits
        if rolled_at is not None and char.location != rolled_at:
            early = (t(lang, "roll.stale"), None)
        elif rolled_at is None and n != "-" and verb in ROLL_VERBS and actions.manual_rolls(user):
            skill = await actions.button_roll(session, char, verb, arg)
            if skill:
                context.user_data["pending_roll"] = {
                    "type": "button",
                    "verb": verb,
                    "arg": arg,
                    "n": n,
                    "location": char.location,
                }
                early = roll_prompt(skill, lang)
        if early is None:
            if (
                n == "-"
                or await audit.claim(
                    session,
                    f"{user.telegram_id}:{n}",
                    user_id=user.id,
                    character_id=char.id,
                    verb=verb,
                    payload={"arg": arg},
                )
                is None
            ):
                text, kb = await current_view(session, char, lang)
                stale = True
            else:
                stale = False
                out = await _dispatch(session, char, verb, arg, r, context)
                text, kb = await _after(session, char, lang, verb, arg, context, out)
                telegram_id = user.telegram_id
                in_combat = char.state == "in_combat"
    if early is not None:
        await answer(update)
        await send(update, *early)
        return
    if stale:  # an old menu or a double tap: nothing is spent, and the message becomes the current view
        await answer(update, t(lang, "err.stale_popup"))
        await edit_or_send(update, text, kb)
        return
    if verb == "actc" and out.error in ("activity.err.not_ready", "activity.err.none"):
        await answer(update)  # "🔄 Refresh" before the end (or after the bot delivered it): the view, in place
        await edit_or_send(update, text, kb)
        return
    if refused(out):  # nothing happened: a popup, and the panel stays (refreshed) where it was
        await answer(update, render_event(out.events[0], lang) if out.events else t(lang, out.error))
        await edit_or_send(update, text, kb)
        return
    await answer(update)
    if verb == "actc" and out.ok:  # pressed right as it ended: the same message the bot would send
        await drop_buttons(update)
        await send_activity_result(update.effective_chat, telegram_id, context.bot_data["llm"], out, lang, (text, kb))
    elif _started(out):  # the scene becomes the "you start working" panel
        await edit_or_send(update, text, kb)
    elif verb == "go" and out.ok and out.events and all(e.key in ARRIVALS for e in out.events):
        await edit_or_send(update, f"{render.outcome_text(out, lang)}\n\n{text}", kb)  # the map turns into the place
    elif verb in IN_PLACE and not render.level_up_cards(out, lang):  # a menu: the result on top, same message
        await edit_or_send(update, f"{render.outcome_text(out, lang)}\n\n{text}"[: render.MAX_MESSAGE], kb)
    elif out.activity_id or in_combat:  # a chronicle or a fight follows: their own messages
        await drop_buttons(update)
        if out.events:
            await send_outcome(update, out, lang)
        if out.activity_id:  # an ambushed stay or a tracked prey just ended: its chronicle
            await send_chronicle(update, context, out.activity_id, lang)
        await send(update, text, kb)
    else:  # the result and the buttons to carry on, in one message
        await send_result(update, out, lang, text, kb)


ARRIVALS = {"explore.arrived", "explore.arrived_via"}  # a quiet arrival: nothing else happened on the way
# buttons that change something (the rest only show a view): they answer the press once they know the result
ACTS = {
    "go",
    "look",
    "hunt",
    "rest",
    "heal",
    "act",
    "actc",
    "actx",
    "plearn",
    "craft",
    "qa",
    "qturn",
    "pathc",
    "eq",
    "use",
    "buy",
    "sell",
}
IN_PLACE = {"buy", "sell", "eq", "use", "plearn", "craft"}  # menus: the result goes on top of the same menu


def refused(out: Outcome) -> bool:
    """The action did not happen at all (only the reason why): a popup is enough."""
    return not out.ok and bool(out.error) and len(out.events) <= 1


def _started(out: Outcome) -> str | None:
    """The key of "you start working" when this action just started a timed activity."""
    return next((e.key for e in out.events if e.key.startswith("activity.started.")), None) if out.ok else None


async def _dispatch(session, char, verb: str, arg: str, r, context) -> Outcome:
    present = exploration.npcs_present(char.location)
    if char.state == "in_combat" and verb != "use":
        return Outcome.refused("explore.err.in_combat")
    if verb == "go":
        context.user_data.pop("talk", None)
        return await exploration.travel(session, char, arg, r)
    if verb == "look":
        return await exploration.investigate(session, char, r)
    if verb == "hunt":
        return await exploration.hunt(session, char, r)
    if verb == "rest":  # a long rest: 80 minutes asleep at the inn
        return await activities.start(session, char, "rest", "rest")
    if verb == "heal":
        return await exploration.cure_wounds(session, char, r)
    if verb == "act":  # "<gather|stay|track>:<mastery>"
        kind, _, skill = arg.partition(":")
        return await activities.start(session, char, kind, skill)
    if verb == "actc":
        return await activities.claim(session, char)
    if verb == "actx":
        return await activities.cancel(session, char)
    if verb == "plearn":  # "<profession>" or "<profession>:<the one it replaces>"
        key, _, old = arg.partition(":")
        return await professions.learn(session, char, key, old or None)
    if verb == "toolc":  # which specialized tool this discipline uses
        return await activities.select_tool(session, char, arg)
    if verb == "specc":  # take a branch, or come back to a paused one
        return await specializations.choose(session, char, arg)
    if verb == "pathc":  # "<b|r>:<branch>" or "o:<choice>:<option>": the class path, for good
        mode, _, rest = arg.partition(":")
        if mode == "b":
            return await class_specializations.choose_branch(session, char, rest)
        if mode == "r":
            return await class_specializations.reroll_branch(session, char, rest)
        choice_key, _, option = rest.rpartition(":")
        return await class_specializations.choose_option(session, char, choice_key, option)
    if verb in ("stash", "take"):  # "<item>:<how many>": move it between the backpack and the chest
        key, _, qty = arg.partition(":")
        n = int(qty) if qty.isdigit() else 1
        return await (home.deposit if verb == "stash" else home.withdraw)(session, char, key, n)
    if verb == "bplearn":  # read a blueprint: it teaches its recipe and is spent
        return await crafting.learn_blueprint(session, char, arg)
    if verb == "craft":  # "<recipe>" or "<recipe>:<how many>"
        key, _, qty = arg.partition(":")
        return await crafting.craft(session, char, key, r, qty=int(qty) if qty.isdigit() else 1)
    if verb == "qa":
        return await quests.perform(session, char, arg, present, r)
    if verb == "qturn":  # hand a finished mission to the one who gave it, and get paid
        return await quests.turn_in(session, char, arg, present, r)
    if verb == "eq":
        return await inventory.equip(session, char, int(arg)) if arg.isdigit() else Outcome.refused("inv.err.not_found")
    if verb == "use":
        if char.state == "in_combat":
            return Outcome.refused("inv.err.in_combat_use")
        key, _, ability = arg.partition(":")  # "<item>" or "<item>:<spell to restore>"
        return await inventory.use_item_outside_combat(session, char, key, r, ability=ability or None)
    if verb in ("buy", "sell"):
        npc_key, _, what = arg.partition(":")
        if npc_key not in present:
            return Outcome.refused("talk.err.not_here")
        rep = await npcs.reputation_with(session, char, get_content().npcs[npc_key].faction)
        if verb == "buy":
            return await inventory.buy(session, char, npc_key, what, rep)
        if not what.isdigit():
            return Outcome.refused("inv.err.not_found")
        return await inventory.sell(session, char, npc_key, int(what), rep)
    return Outcome.refused("err.unknown")


async def _after(session, char, lang: str, verb: str, arg: str, context, out: Outcome | None = None):
    """Which view to show after an action."""
    await session.flush()
    if out is not None and _started(out):  # a nice "you start working" panel instead of the scene again
        ev = next(e for e in out.events if e.key.startswith("activity.started."))
        return await render.scene(session, char, lang, started=render_event(ev, lang))
    if char.state == "in_combat":
        return await current_view(session, char, lang)
    npc = context.user_data.get("talk")
    if verb == "qa" and npc in exploration.npcs_present(char.location):
        return await render.conversation(session, char, npc, lang)
    if verb in ("buy", "sell"):
        npc_key = arg.partition(":")[0]
        if verb == "buy":
            what = arg.partition(":")[2]
            group = render._shop_group(get_content().items[what]) if what in get_content().items else None
            return await render.shop(session, char, npc_key, lang, group)
        return await render.sell_menu(session, char, npc_key, lang)
    if verb in ("eq", "use"):  # back to the tab it was pressed in
        return await render.inventory_view(session, char, lang, "gear" if verb == "eq" else "use")
    if verb == "plearn":
        return render.professions_view(char, lang)
    if verb == "pathc":
        return await render.path_view(session, char, lang)
    if verb == "craft":
        return await render.craft_menu(session, char, lang)
    if out is not None and refused(out):  # nothing happened: the same view, refreshed in place
        if verb in ("act", "hunt", "rest", "heal"):
            return await render.activities_view(session, char, lang)
        return await render.scene(session, char, lang)
    # the scene again; under a result only its heading (after travelling, the whole new place)
    arrived = verb == "go" and out is not None and out.ok
    return await render.scene(session, char, lang, compact=not arrived)


def roll_prompt(skill: str, lang: str):
    name = get_content().skills[skill].name.get(lang)
    return t(lang, "roll.prompt", skill=name), markup([[btn(t(lang, "btn.roll"), cb("roll"))]])
