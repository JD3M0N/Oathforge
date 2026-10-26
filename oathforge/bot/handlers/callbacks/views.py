"""Buttons that only show something: no nonce, no state change."""

from telegram import Update

from oathforge.bot import render
from oathforge.bot.handlers.common import (
    answer, current_view, edit_or_send, load, offer_keyboard, rng, send, send_outcome, send_photos,
)
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import bestiary, combat_service, exploration, quests


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
        elif verb == "path":
            text, kb = await render.path_view(session, char, lang)
        elif verb == "pathq":  # the options of one pending choice
            text, kb = render.path_choice(char, arg, lang) or await render.path_view(session, char, lang)
        elif verb == "pathv":  # the last question, before a choice that cannot be undone
            text, kb = render.path_confirm(char, arg, lang) or await render.path_view(session, char, lang)
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
