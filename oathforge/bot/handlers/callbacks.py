"""Single router for in-game buttons (everything except creation)."""

import asyncio
import logging

from sqlalchemy.orm.exc import StaleDataError
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from oathforge.bot import render
from oathforge.bot.handlers import achievements
from oathforge.bot.handlers.common import (
    answer, answered, current_view, drop_buttons, edit_or_send, load, offer_keyboard, rate_ok, rng, send, send_activity_result,
    send_chronicle, send_outcome, send_photos, send_result,
)
from oathforge.bot.keyboards import btn, cb, markup, parse
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action, EncounterState, valid_targets
from oathforge.i18n import t
from oathforge.ai.intent_parser import Intent
from oathforge.services import (
    actions, activities, audit, bestiary, characters, combat_service, crafting, exploration, home, inventory, npcs, professions, quests, specializations,
)
from oathforge.services.events import Outcome, render_event

log = logging.getLogger(__name__)

# verbs that only show something (no nonce, no state change)
VIEWS = {"scene", "trv", "trvz", "trvs", "talkm", "talk", "bye", "inv", "hero", "sheet", "jr", "jrm", "jrc", "jrl", "jrs", "jq", "jrb", "jb", "jbi", "jrr",
         "shopm", "shop", "shopg", "sellm", "cbp", "lang", "city", "place", "cls", "clsl", "rep", "prof", "profsw", "profcf", "pg", "crf", "rb", "repf",
         "mst", "hob", "acts", "rcl", "rcp", "room", "spec", "specf", "tools"}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    verb, arg, n = parse(q.data or "")
    if not rate_ok(context, update.effective_user.id):
        await answer(update, t(context.user_data.get("lang", "es"), "err.rate"))
        answered(update)
        return
    if verb not in ("cb", "place", "city") and verb not in ACTS:  # these answer once they know (a refusal is a popup)
        await answer(update)
    try:
        if verb in ("ach", "achm"):
            await achievements.handle(update, context, arg, mutation=verb == "achm", nonce=n)
        elif verb in VIEWS:
            await _view(update, context, verb, arg)
        elif verb == "cb":
            await _combat(update, context, arg, n)
        elif verb == "roll":
            await do_roll(update, context)
        elif verb == "rollset":
            await set_manual_rolls(update, context, arg == "on")
        elif verb in ("set", "setl"):
            await settings(update, context, arg if verb == "setl" else None)
        else:
            await _act(update, context, verb, arg, n)
    except StaleDataError:  # someone else changed the hero meanwhile: the popup, and the current view in place
        lang = context.user_data.get("lang", "es")
        await answer(update, t(lang, "err.stale_popup"))
        async with session_scope() as session:
            _, char = await load(session, update)
            if char is not None:
                await edit_or_send(update, *await current_view(session, char, lang))
    finally:
        await answer(update)
        answered(update)


async def _view(update: Update, context, verb: str, arg: str) -> None:
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = user.language
        context.user_data["lang"] = lang
        if verb == "lang":
            if arg in ("es", "en"):
                user.language = lang = context.user_data["lang"] = arg
            if char is None:
                await edit_or_send(update, t(lang, "lang.changed"))
                return
        if verb == "rb":  # the rulebook too (it is offered in the very first message)
            read = await quests.on_read(session, char, arg, rng()) if char is not None else None
            await edit_or_send(update, *render.rulebook(lang, arg))
            if read is not None and read.events:  # "look it up in the rulebook" objectives
                await send_outcome(update, read, lang)
            return
        if verb in ("mst", "hob"):  # masteries and hobbies too
            text, kb = render.masteries_view(char, lang) if verb == "mst" else render.hobbies_view(char, lang)
            await edit_or_send(update, text, kb)
            return
        if verb in ("cls", "clsl"):  # class pages work without a character too
            text, kb = render.class_page(arg, lang, char) if verb == "cls" else render.classes_list(lang)
            await edit_or_send(update, text, kb)
            return
        if char is None:
            await edit_or_send(update, t(lang, "start.need_character"))
            return
        await offer_keyboard(update, user, lang)
        in_combat = char.state != "idle"  # fighting or busy with a field activity: no menus to leave
        loc = get_content().locations[char.location]
        if verb in ("place", "city") and not in_combat:  # city: the old "View city" button of earlier menus
            media, night = get_content().media, exploration.is_night()
            images, caption = media.location_images(char.location, night), render.place_caption(char.location, lang)
            if not images and loc.hub:  # a city's plaza shows the city
                images, caption = media.zone_images(loc.zone, night), render.zone_caption(loc.zone, lang)
            if not images:  # no art yet: a short popup, the scene stays as it is
                await answer(update, t(lang, "scene.no_image", place=loc.phrase()[lang]))
                return
            await send_photos(session, update, context, images, caption)
            text, kb = await current_view(session, char, lang)
            await send(update, text, kb)  # the scene again, so its buttons stay below the photo
            return
        if verb == "sheet":
            images = get_content().media.class_images(char.class_key, char.gender)
            if images:  # portrait first, then the sheet as a new message so its buttons stay below
                await send_photos(session, update, context, images, render.portrait_caption(char, lang))
                text, kb = await render.sheet(session, char, lang)
                await send(update, text, kb)
                return
        if verb == "jbi":
            images = get_content().media.monster_images(arg)
            if images and bestiary.tier((char.bestiary or {}).get(arg)):  # only creatures it has seen
                await send_photos(session, update, context, images, render.creature_caption(arg, lang))
            text, kb = render.bestiary_entry(char, arg, lang)
            await send(update, text, kb)  # the entry again, so its buttons stay below the photo
            return
        talked = None
        if verb == "talk" and not in_combat and arg in exploration.npcs_present(char.location):
            context.user_data["talk"] = arg
            talked = await quests.on_talk(session, char, arg, rng())  # "talk to Bram" objectives
            text, kb = await render.conversation(session, char, arg, lang)
        elif verb in ("trv", "trvz", "trvs") and not in_combat:
            text, kb = await render.map_view(session, char, lang, arg if verb == "trvz" else None,
                                             street=arg if verb == "trvs" else None)
        elif verb == "acts" and not in_combat:
            text, kb = await render.activities_view(session, char, lang)
        elif verb == "talkm" and not in_combat:
            text, kb = render.talk_menu(char, lang)
        elif verb == "inv":
            text, kb = await render.inventory_view(session, char, lang, arg)
        elif verb == "hero":
            text, kb = await render.hero(session, char, lang)
        elif verb == "sheet":
            text, kb = await render.sheet(session, char, lang)
        elif verb == "jr":
            text, kb = await render.journal(session, char, lang)
        elif verb == "jrm":
            text, kb = await render.missions(session, char, lang)
        elif verb in ("jrc", "jrl"):  # jrl: the old log button still works, now on the chronicle
            text, kb = await render.chronicle(session, char, lang, arg)
        elif verb == "jrs":
            text, kb = await render.stats_view(session, char, lang)
        elif verb == "jq":
            text, kb = await render.mission(session, char, arg, lang)
        elif verb == "rep":  # "<encounter_id>:<page>", or "-" for the latest battle
            enc_id, _, page = arg.partition(":")
            report = await combat_service.battle_report(session, char, int(enc_id) if enc_id.isdigit() else None)
            text, kb = render.report_page(report, int(page) if page.isdigit() else 0, lang)
        elif verb == "repf":  # the full report: every round, in as many messages as needed, then the summary
            report = await combat_service.battle_report(session, char, int(arg) if arg.isdigit() else None)
            for message in render.full_report(report, lang):
                await send(update, message)
            text, kb = render.report_page(report, 0, lang)
            await send(update, text, kb)
            return
        elif verb == "prof":
            text, kb = render.professions_view(char, lang)
        elif verb == "profsw" and not in_combat:
            text, kb = render.swap_menu(char, arg, lang)
        elif verb == "profcf" and not in_combat:
            text, kb = render.swap_confirm(char, arg, lang)
        elif verb == "pg":
            text, kb = render.profession_page(arg, lang, char)
        elif verb == "crf" and not in_combat:
            text, kb = await render.craft_menu(session, char, lang)
        elif verb == "tools":
            text, kb = await render.tools_view(session, char, lang)
        elif verb == "spec":
            text, kb = render.specializations_view(char, lang)
        elif verb == "specf":  # the confirmation, with its price
            text, kb = render.spec_confirm(char, arg, lang)
        elif verb == "room":
            text, kb = await render.room_view(session, char, lang)
        elif verb == "rcl":  # "<filter>:<page>"
            text, kb = await render.recipes_list(session, char, lang, arg)
        elif verb == "rcp":
            text, kb = await render.recipe_card(session, char, arg, lang)
        elif verb == "jrb":
            text, kb = render.bestiary_list(char, lang)
        elif verb == "jb":
            text, kb = render.bestiary_entry(char, arg, lang)
        elif verb == "jrr":
            text, kb = await render.rumors(session, lang)
        elif verb == "shopm" and not in_combat:
            text, kb = render.shop_menu(char, lang)
        elif verb == "shop" and not in_combat and arg in exploration.npcs_present(char.location):
            text, kb = await render.shop(session, char, arg, lang)
        elif verb == "shopg" and not in_combat and arg.partition(":")[0] in exploration.npcs_present(char.location):
            npc_key, _, group = arg.partition(":")
            text, kb = await render.shop(session, char, npc_key, lang, group)
        elif verb == "sellm" and not in_combat and arg in exploration.npcs_present(char.location):
            text, kb = await render.sell_menu(session, char, arg, lang)
        else:  # scene, cbp, bye, lang, or anything not allowed right now
            if verb == "bye":
                context.user_data.pop("talk", None)
            text, kb = await current_view(session, char, lang)
    if verb == "talk" and talked is not None and talked.events:
        await send_outcome(update, talked, lang)
        await send(update, text, kb)
        return
    await edit_or_send(update, text, kb)


ROLL_VERBS = {"look", "qa"}  # button actions that can wait for the manual 🎲 button
DICE_SECONDS = 3.5  # Telegram's dice animation, before the engine's d20 appears


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
                context.user_data["pending_roll"] = {"type": "button", "verb": verb, "arg": arg, "n": n,
                                                     "location": char.location}
                early = roll_prompt(skill, lang)
        if early is None:
            if n == "-" or await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id,
                                             character_id=char.id, verb=verb, payload={"arg": arg}) is None:
                text, kb = await current_view(session, char, lang)
                stale = True
            else:
                stale = False
                char_id = char.id
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
        await edit_or_send(update, f"{render.outcome_text(out, lang)}\n\n{text}"[:render.MAX_MESSAGE], kb)
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
ACTS = {"go", "look", "hunt", "rest", "heal", "act", "actc", "actx", "plearn", "craft", "qa", "eq", "use", "buy", "sell"}
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
    if verb == "craft":
        return await render.craft_menu(session, char, lang)
    if out is not None and refused(out):  # nothing happened: the same view, refreshed in place
        if verb in ("act", "hunt", "rest", "heal"):
            return await render.activities_view(session, char, lang)
        return await render.scene(session, char, lang)
    # the scene again; under a result only its heading (after travelling, the whole new place)
    arrived = verb == "go" and out is not None and out.ok
    return await render.scene(session, char, lang, compact=not arrived)


# ---------------------------------------------------------------- manual rolls

def roll_prompt(skill: str, lang: str):
    name = get_content().skills[skill].name.get(lang)
    return t(lang, "roll.prompt", skill=name), markup([[btn(t(lang, "btn.roll"), cb("roll"))]])


async def do_roll(update: Update, context) -> None:
    """The 🎲 button: animate Telegram's die (decoration only), then resolve the parked action with the
    engine's d20."""
    pending = context.user_data.pop("pending_roll", None)
    if pending is None:
        await settings(update, context)
        return
    try:
        await update.effective_chat.send_dice(emoji="🎲")
        await asyncio.sleep(DICE_SECONDS)
    except Exception:  # the animation is decoration; the roll is the engine's
        log.warning("could not send the dice animation", exc_info=True)
    if pending["type"] == "button":
        await _act(update, context, pending["verb"], pending["arg"], pending["n"], rolled_at=pending["location"])
        return
    from oathforge.bot.handlers.text import show_free_text  # text imports this module

    result = await actions.execute_free_text(context.bot_data["llm"], pending["user_id"], pending["text"],
                                             Intent.model_validate(pending["intent"]), False, rng(),
                                             location=pending["location"])
    await show_free_text(update, context, result)


async def settings(update: Update, context, new_lang: str | None = None) -> None:
    """⚙️ Settings: language and manual rolls (also /settings)."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        if new_lang in ("es", "en"):
            user.language = new_lang
        lang = context.user_data["lang"] = user.language
        text, kb = render.settings_view(user, lang)
    await edit_or_send(update, text, kb)


async def set_manual_rolls(update: Update, context, on: bool) -> None:
    """Off by default. Turning them on warns that Telegram's die is only decoration."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = context.user_data["lang"] = user.language
        characters.set_setting(user, "manual_rolls", on)
        text, kb = render.settings_view(user, lang)
    if not on:
        context.user_data.pop("pending_roll", None)
    head = t(lang, "roll.warning") if on else t(lang, "roll.changed", state=t(lang, "roll.off"))
    await edit_or_send(update, f"{head}\n\n{text}", kb)


# ---------------------------------------------------------------- combat

NEEDS_TARGET = {"atk", "abl", "obj", "itm"}


async def _combat(update: Update, context, arg: str, n: str) -> None:
    parts = arg.split(":")
    kind = parts[0]
    r = rng()
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        lang = context.user_data["lang"] = user.language
        if char is None:
            return
        enc = await combat_service.active_encounter(session, char, lock=True)
        if enc is None:
            text, kb = await current_view(session, char, lang)
            await edit_or_send(update, text, kb)
            return
        state = EncounterState.model_validate(enc.state)
        me = state.combatants["p1"]

        # A button from an older panel (double click, another turn): show the current panel instead.
        if not fresh_token(n, enc.version, state.turn_index):
            text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
            await edit_or_send(update, text, kb)
            return

        if kind in ("itms", "pwrs"):  # the list of scrolls and bombs, or of class powers
            menu = "items" if kind == "itms" else "powers"
            text, kb = render.combat_panel(char, enc.state, lang, target_menu=menu, version=enc.version)
            await edit_or_send(update, text, kb)
            return

        # Ask for a target first when there is a real choice.
        if kind in NEEDS_TARGET and len(parts) == 2:
            need = _needs_target(state, me, kind, parts[1], combat_service.ability_defs(char))
            if need:
                text, kb = render.combat_panel(char, enc.state, lang, target_menu=arg, version=enc.version)
                await edit_or_send(update, text, kb)
                return

        if await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id, character_id=char.id,
                             verb="combat", payload={"arg": arg}) is None:
            text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
            await edit_or_send(update, text, kb)
            return

        target = parts[2] if len(parts) > 2 else None
        action = {
            "atk": lambda: Action(kind="attack", weapon=parts[1], target=target),
            "abl": lambda: Action(kind="ability", ability=parts[1], target=target),
            "obj": lambda: Action(kind="interact", object=parts[1], target=target),
            "itm": lambda: Action(kind="item", ability=parts[1], target=target),
            "def": lambda: Action(kind="defend"),
            "pot": lambda: Action(kind="heal_item"),
            "mov": lambda: Action(kind="move"),
            "flee": lambda: Action(kind="flee"),
            "end": lambda: Action(kind="end_turn"),
        }.get(kind)
        if action is None:
            return
        out = await combat_service.act(session, char, enc, action(), r)
        await session.flush()  # bumps enc.version, so the new buttons carry it
        text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
        finished = enc.status != "active"
        # rewards / quest updates appear after the panel; per-hit logs already live in the panel
        summary = Outcome(events=[e for e in out.events if not e.key.startswith("combat.")
                                  or e.key.startswith("combat.defeat_penalty")], activity_id=out.activity_id)
        error = out.error
        telegram_id = user.telegram_id

    await answer(update, "⚠️ " + t(lang, error) if error else None)  # a refusal is a popup
    await edit_or_send(update, text, kb)
    if finished and out.activity_id:  # an ambushed stay or a tracked prey: rewards and chronicle together
        await send_activity_result(update.effective_chat, telegram_id, context.bot_data["llm"], summary, lang)
    elif finished and summary.events:
        await send_outcome(update, summary, lang)


def fresh_token(token: str, version: int | None, turn_index: int) -> bool:
    """Combat buttons carry "<version>.<turn_index>.<nonce>"; anything else is stale."""
    parts = token.split(".")
    return len(parts) == 3 and parts[0] == str(version or 0) and parts[1] == str(turn_index)


def _needs_target(state, me, kind: str, key: str, defs) -> bool:
    if kind == "atk":
        ranged = any(a.key == key and a.ranged for a in me.attacks)
        return len(valid_targets(state, me, ranged)) > 1
    if kind == "abl":
        a = defs.get(key)
        if a is None or a.kind not in ("strike", "spell", "save", "curse"):
            return False
        return len(valid_targets(state, me, ranged=a.kind != "strike")) > 1
    if kind == "obj":
        obj = state.scene_objects.get(key)
        return obj is not None and obj.targets == "one" and len(state.enemies_of(me)) > 1
    if kind == "itm":
        item = get_content().items.get(key)
        return (item is not None and item.combat is not None and item.combat.kind in ("spell", "save")
                and len(state.enemies_of(me)) > 1)
    return False


def handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(on_callback)
