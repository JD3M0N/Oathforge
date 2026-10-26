"""Combat buttons: attacks, abilities, items and targets, guarded by the encounter token."""

from telegram import Update

from oathforge.bot import render
from oathforge.bot.handlers.common import (
    answer,
    current_view,
    edit_or_send,
    load,
    rng,
    send_activity_result,
    send_outcome,
)
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action, EncounterState, valid_targets
from oathforge.i18n import t
from oathforge.services import audit, combat_service
from oathforge.services.events import Outcome


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

        if kind == "hlp":  # 💡 What do I do?: rules, no AI, nothing is spent
            await answer(update, render.combat_help_text(state, me, combat_service.ability_defs(char), lang))
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

        if (
            await audit.claim(
                session,
                f"{user.telegram_id}:{n}",
                user_id=user.id,
                character_id=char.id,
                verb="combat",
                payload={"arg": arg},
            )
            is None
        ):
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
        summary = Outcome(
            events=[
                e for e in out.events if not e.key.startswith("combat.") or e.key.startswith("combat.defeat_penalty")
            ],
            activity_id=out.activity_id,
        )
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
        if a is None or a.kind not in ("strike", "spell", "save", "curse", "command"):
            return False
        return len(valid_targets(state, me, ranged=a.kind != "strike" or a.ranged)) > 1
    if kind == "obj":
        obj = state.scene_objects.get(key)
        return obj is not None and obj.targets == "one" and len(state.enemies_of(me)) > 1
    if kind == "itm":
        item = get_content().items.get(key)
        return (
            item is not None
            and item.combat is not None
            and item.combat.kind in ("spell", "save")
            and len(state.enemies_of(me)) > 1
        )
    return False
