"""Shops, item pages and the inventory."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.i18n import t
from oathforge.services import characters, crafting, exploration, inventory, npcs
from oathforge.bot.render.common import (
    MAX_MESSAGE, RULE, SLOT_ICONS, _gear_line, creature_icon, discipline_icon, discipline_label, item_stats,
)


# ---------------------------------------------------------------- shop

def shop_menu(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rows = [[btn(f"🛒 {c.npcs[k].name.get(lang)}", cb("shop", k))]
            for k in exploration.npcs_present(char.location) if c.npcs[k].shop]
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return t(lang, "shop.choose"), markup(rows)


async def shop(session: AsyncSession, char: Character, npc_key: str, lang: str,
               group: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """A shop: first its categories (weapons, armor...), then the items of the one you pick, to buy."""
    c = get_content()
    npc = c.npcs[npc_key]
    rep = await npcs.reputation_with(session, char, npc.faction)
    n = nonce()
    lines = [t(lang, "shop.title", npc=escape(npc.name.get(lang)), gold=char.gold)]
    groups: dict[str, list[str]] = {}
    for key in npc.shop.items:
        groups.setdefault(_shop_group(c.items[key]), []).append(key)
    rows = []
    if group in groups:
        lines += ["", f"<b>{t(lang, f'shop.group.{group}')}</b>"]
        for key in groups[group]:
            item, price = c.items[key], inventory.buy_price(key, rep)
            stats = item_stats(key, lang)
            lines.append(f"• <b>{escape(item.label(lang))}</b>{' · ' + escape(stats) if stats else ''} · {price} 🪙"
                         f" · /item_{key}")
            rows.append([btn(f"{item.label(lang)} · {price} 🪙", cb("buy", f"{npc_key}:{key}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("shop", npc_key))])
        return "\n".join(lines), markup(rows)
    lines += ["", f"<i>{t(lang, 'shop.pick_group')}</i>"]
    rows += grid([btn(f"{t(lang, f'shop.group.{g}')} ({len(groups[g])})", cb("shopg", f"{npc_key}:{g}"))
                  for g in SHOP_GROUPS if groups.get(g)])
    if npc.shop.buys:
        rows.append([btn(t(lang, "btn.sell"), cb("sellm", npc_key))])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines), markup(rows)


SHOP_GROUPS = ("weapons", "armor", "consumables", "tools", "other")


def _shop_group(item) -> str:
    if item.type == "weapon":
        return "weapons"
    if item.type in ("armor", "shield"):
        return "armor"
    return {"consumable": "consumables", "tool": "tools"}.get(item.type, "other")


def item_page(key: str, lang: str, char: Character | None = None) -> tuple[str, InlineKeyboardMarkup | None]:
    """/item_<key>: what an item is, what it is for, where it comes from and what it is worth."""
    c = get_content()
    item = c.items.get(key)
    if item is None:
        return t(lang, "item.err.unknown"), None
    lines = [f"<b>{escape(item.label(lang))}</b>",
             f"<i>{t(lang, f'item.type.{item.type}')}</i>", RULE, escape(item.description.get(lang))]
    stats = item_stats(key, lang)
    if stats:
        lines += ["", t(lang, "item.use", what=escape(stats))]
    rows = []
    if item.type == "blueprint" and item.teaches in c.recipes:
        taught = c.recipes[item.teaches]
        made = c.items[next(iter(taught.outputs))].label(lang)
        known = char is not None and item.teaches in crafting.known(char)
        lines += ["", t(lang, "craft.teaches_known") if known else
                  t(lang, "craft.teaches", item=escape(made),
                    prof=escape(discipline_label(taught.profession, lang)), rank=taught.min_rank)]
        if char is not None and not known:
            rows = [[btn(t(lang, "btn.learn_recipe"), cb("bplearn", key, nonce()))]]
    used_in = sorted({c.items[next(iter(r.outputs))].name.get(lang) + f" ({discipline_icon(r.profession)})"
                      for r in c.recipes.values() if key in r.ingredients})
    if used_in:
        lines.append(t(lang, "item.ingredient", list=escape(", ".join(used_in))))
    sources = []
    sources += [loc.name.get(lang) for loc in c.locations.values()
                if any(r.item == key for g in loc.gathering for r in g.resources)]
    sources += [f"{creature_icon(m)} {m.name.get(lang)}" for m in c.monsters.values()
                if any(x.item == key for x in [*m.loot, *m.harvest])]
    sources += [discipline_label(r.profession, lang) for r in c.recipes.values() if key in r.outputs]
    sources += [f"🛒 {n.name.get(lang)}" for n in c.npcs.values() if n.shop and key in n.shop.items]
    sources += [f"📜 {q.name.get(lang)}" for q in c.quests.values()
                if any(key in (eff.get("give_item") or {}) for eff in q.rewards)]
    if sources:
        lines.append(t(lang, "item.sources", list=escape(", ".join(dict.fromkeys(sources)))))
    lines.append("")
    if item.sellable and item.value:
        lines.append(t(lang, "item.value", value=item.value, sell=inventory.sell_price(key, 0)))
    else:
        lines.append(t(lang, "item.no_value"))
    return "\n".join(lines)[:MAX_MESSAGE], (markup(rows) if rows else None)


async def sell_menu(session: AsyncSession, char: Character, npc_key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rep = await npcs.reputation_with(session, char, c.npcs[npc_key].faction)
    n = nonce()
    rows = []
    for inst in await inventory.items_of(session, char):
        item = c.items[inst.item_key]
        if not item.sellable or inst.equipped_slot:
            continue
        price = inventory.sell_price(inst.item_key, rep)
        qty = f" ×{inst.qty}" if inst.qty > 1 else ""
        rows.append([btn(f"{item.label(lang)}{qty} → {price} 🪙", cb("sell", f"{npc_key}:{inst.id}", n))])
    rows.append([btn(t(lang, "btn.back"), cb("shop", npc_key))])
    text = t(lang, "shop.sell_title") if len(rows) > 1 else t(lang, "shop.nothing_to_sell")
    return text, markup(rows)


# ---------------------------------------------------------------- inventory

# 🎒 tabs: equipment, consumables, materials (and trinkets to sell), tools (and quest items)
INV_TABS = {"gear": ("weapon", "armor", "shield"), "use": ("consumable",), "mat": ("material", "trinket"),
            "tools": ("tool", "quest")}


def inv_tab(item) -> str:
    return next(tab for tab, types in INV_TABS.items() if item.type in types)


def item_buttons(char: Character, inst, item, n: str, lang: str) -> list[list]:
    """Equip / take off, or use (a mana potion with several spells spent: pick which one comes back)."""
    if item.slot:
        label = t(lang, "btn.unequip" if inst.equipped_slot else "btn.equip", item=item.name.get(lang))
        label = f"{SLOT_ICONS.get(inst.equipped_slot or item.slot, '')} {label}".strip()
        return [[btn(label, cb("eq", str(inst.id), n))]]
    if not inventory.effects_of(item):
        return []
    spells = inventory.spell_choices(char, item)
    if len(spells) > 1:
        known = characters.abilities_of(char)
        return [[btn(t(lang, "btn.use_on", item=item.name.get(lang), ability=known[k].name.get(lang),
                       uses=char.resources.get(k, 0), max=known[k].uses), cb("use", f"{inst.item_key}:{k}", n))]
                for k in spells]
    return [[btn(t(lang, "btn.use", item=item.name.get(lang)), cb("use", inst.item_key, n))]]


async def inventory_view(session: AsyncSession, char: Character, lang: str,
                         tab: str = "-") -> tuple[str, InlineKeyboardMarkup]:
    """🎒 The summary (gold, what you wear, how much of each kind), or one tab: a line per item with its icon,
    ×quantity and /item_ link; equipment and consumables have their buttons there."""
    c = get_content()
    n = nonce()
    owned = sorted(await inventory.items_of(session, char), key=lambda i: not i.equipped_slot)  # worn first
    counts = {key: sum(1 for i in owned if inv_tab(c.items[i.item_key]) == key) for key in INV_TABS}
    lines = [t(lang, "inv.title", gold=char.gold), ""]
    rows = []
    if tab not in INV_TABS:
        worn = [_gear_line(i, lang) for i in owned if i.equipped_slot]
        lines += [f"<b>{t(lang, 'inv.worn')}</b>", *(worn or [t(lang, "inv.nothing_worn")]), ""]
        lines.append(" · ".join(f"{t(lang, f'inv.tab.{key}')} {count}" for key, count in counts.items()))
        lines += ["", f"<i>{t(lang, 'inv.pick_tab')}</i>"]
    else:
        lines.append(f"<b>{t(lang, f'inv.tab.{tab}')}</b>")
        mine = [i for i in owned if inv_tab(c.items[i.item_key]) == tab]
        for inst in mine:
            item = c.items[inst.item_key]
            qty = f" ×{inst.qty}" if inst.qty > 1 else ""
            lines.append(f"{escape(item.label(lang))}{qty}{' ✅' if inst.equipped_slot else ''} · /item_{inst.item_key}")
            rows += item_buttons(char, inst, item, n, lang)
        if not mine:
            lines.append(f"<i>{t(lang, 'inv.empty_tab')}</i>")
    rows += grid([btn(("• " if key == tab else "") + t(lang, f"inv.tab.{key}") + (" •" if key == tab else ""),
                      cb("inv", key)) for key in INV_TABS])
    rows.append([btn(t(lang, "btn.back"), cb("inv" if tab in INV_TABS else "scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
