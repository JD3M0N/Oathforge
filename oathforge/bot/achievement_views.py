"""Achievement menus with localized text and stable callback IDs."""

from html import escape

from oathforge.bot.keyboards import btn, cb, markup, nonce
from oathforge.i18n import t

PAGE_SIZE = 6


def label(entry, lang):
    return escape(entry["definition"].name.get(lang)) if entry["revealed"] else t(lang, "achievements.mystery")


def short(entry, lang):
    suffix = "✅" if entry["unlock"] else f"{entry['current']}/{entry['target']}"
    return f"{label(entry, lang)} — {suffix}"


def view(data, lang, arg="-"):
    entries, prefs = data["entries"], data["preferences"]
    by_key = {e["key"]: e for e in entries}
    parts, rows = arg.split(":"), []
    if parts[0] == "d" and len(parts) == 2 and parts[1] in by_key:
        entry = by_key[parts[1]]
        definition, key = entry["definition"], entry["key"]
        lines = [f"<b>{label(entry, lang)}</b>", ""]
        text = definition.description if entry["revealed"] else definition.hint
        lines.append(escape(text.get(lang)) if text else t(lang, "achievements.mystery"))
        if entry["revealed"]:
            lines.append(t(lang, "achievements.progress", current=entry["current"], target=entry["target"]))
        points = entry["unlock"].points if entry["unlock"] else definition.points
        lines.append(t(lang, "achievements.reward", points=points))
        if definition.title and entry["revealed"]:
            lines.append(t(lang, "achievements.title_reward", title=escape(definition.title.get(lang))))
        n = nonce()
        if entry["unlock"]:
            unlocked = entry["unlock"]
            lines += [
                t(lang, "achievements.date", date=unlocked.unlocked_at.strftime("%Y-%m-%d")),
                f"<i>{escape(definition.earned.get(lang))}</i>",
            ]
            if unlocked.retroactive:
                lines.append(t(lang, "achievements.retroactive"))
            rows.append(
                [
                    btn(
                        t(lang, "achievements.unfeature" if key in prefs["featured"] else "achievements.feature"),
                        cb("achm", f"feature:{key}", n),
                    )
                ]
            )
            if definition.title:
                rows.append(
                    [
                        btn(
                            t(lang, "achievements.untitle" if prefs["title"] == key else "achievements.equip"),
                            cb("achm", "title:-" if prefs["title"] == key else f"title:{key}", n),
                        )
                    ]
                )
        else:
            rows.append(
                [
                    btn(
                        t(lang, "achievements.untrack" if key in prefs["tracked"] else "achievements.track"),
                        cb("achm", f"track:{key}", n),
                    )
                ]
            )
        if definition.visibility == "hint" and not entry["revealed"]:
            rows.append([btn(t(lang, "achievements.reveal"), cb("achm", f"reveal:{key}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("ach"))])
        return "\n".join(lines), markup(rows)
    if parts[0] == "replace" and len(parts) == 3:
        operation, key = parts[1:]
        if operation in ("feature", "track") and key in by_key:
            field, n = ("featured" if operation == "feature" else "tracked"), nonce()
            for old in prefs[field]:
                if old in by_key:
                    rows.append([btn(label(by_key[old], lang), cb("achm", f"{operation}:{key}:{old}", n))])
            rows.append([btn(t(lang, "btn.back"), cb("ach", f"d:{key}"))])
            return t(lang, "achievements.replace"), markup(rows)
    if parts[0] == "categories":
        for category in dict.fromkeys(e["definition"].category for e in entries):
            rows.append([btn(t(lang, f"achievements.categories.{category}"), cb("ach", f"l:{category}:0"))])
        rows.append([btn(t(lang, "btn.back"), cb("ach"))])
        return t(lang, "achievements.categories_title"), markup(rows)
    if parts[0] == "l":
        category = parts[1] if len(parts) > 1 else "pending"
        selected = [
            e
            for e in entries
            if (category == "earned" and e["unlock"])
            or (category == "pending" and not e["unlock"])
            or (category == "featured" and e["key"] in prefs["featured"])
            or (category == "near" and not e["unlock"] and e["revealed"] and e["current"] > 0)
            or e["definition"].category == category
        ]
        if category == "near":
            selected.sort(key=lambda e: (-e["current"] / e["target"], e["key"]))
        try:
            page = max(0, int(parts[2])) if len(parts) > 2 else 0
        except ValueError:
            page = 0
        page = min(page, max(0, (len(selected) - 1) // PAGE_SIZE))
        lines = [t(lang, "achievements.heading"), ""]
        for entry in selected[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
            lines.append(short(entry, lang))
            rows.append([btn(label(entry, lang), cb("ach", f"d:{entry['key']}"))])
        if not selected:
            lines.append(t(lang, "achievements.empty"))
        navigation = []
        if page:
            navigation.append(btn("◀", cb("ach", f"l:{category}:{page - 1}")))
        if (page + 1) * PAGE_SIZE < len(selected):
            navigation.append(btn("▶", cb("ach", f"l:{category}:{page + 1}")))
        rows += [navigation, [btn(t(lang, "btn.back"), cb("ach"))]]
        return "\n".join(lines), markup(rows)
    lines = [
        t(lang, "achievements.heading"),
        t(lang, "achievements.summary", count=data["count"], points=data["points"]),
        "",
    ]
    earned = [e for e in entries if e["unlock"]]
    if earned:
        last = max(earned, key=lambda e: e["unlock"].id)
        lines += [t(lang, "achievements.latest"), label(last, lang), ""]
    near = sorted(
        (e for e in entries if not e["unlock"] and e["revealed"] and e["current"] > 0),
        key=lambda e: (-e["current"] / e["target"], e["key"]),
    )[:3]
    if near:
        lines += [t(lang, "achievements.near")] + [short(e, lang) for e in near]
    rows = [
        [
            btn(t(lang, "achievements.categories_title"), cb("ach", "categories")),
            btn(t(lang, "achievements.near"), cb("ach", "l:near:0")),
        ],
        [
            btn(t(lang, "achievements.earned"), cb("ach", "l:earned:0")),
            btn(t(lang, "achievements.pending"), cb("ach", "l:pending:0")),
        ],
        [btn(t(lang, "achievements.featured"), cb("ach", "l:featured:0")), btn(t(lang, "btn.back"), cb("hero"))],
    ]
    return "\n".join(lines), markup(rows)


def title_of(data, lang) -> str | None:
    """The equipped title, if it is really unlocked: the sheet, the book and the narrator all show it."""
    entries = {e["key"]: e for e in data["entries"]}
    title = entries.get(data["preferences"]["title"])
    if title and title["unlock"] and title["definition"].title:
        return title["definition"].title.get(lang)
    return None


def identity(data, lang):
    prefs = data["preferences"]
    entries = {e["key"]: e for e in data["entries"]}
    lines = []
    title = title_of(data, lang)
    if title:
        lines.append(f"🏅 <b>{escape(title)}</b>")
    featured = [label(entries[k], lang) for k in prefs["featured"] if k in entries and entries[k]["unlock"]]
    if featured:
        lines.append("🏆 " + " · ".join(featured))
    return lines


def tracked(data, lang):
    entries = {e["key"]: e for e in data["entries"]}
    selected = [entries[k] for k in data["preferences"]["tracked"] if k in entries and not entries[k]["unlock"]]
    return [t(lang, "achievements.tracked")] + [short(e, lang) for e in selected] if selected else []
