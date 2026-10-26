"""Message text + keyboards. HTML parse mode; every dynamic string is escaped.

One module per screen family; this package re-exports them so callers keep using `render.x`."""

from oathforge.bot.render.common import (
    ABILITY_ICON, ACTIVITY_ICON, creature_icon, CREATURE_ICONS, discipline_icon, discipline_label, hp_bar, item_stats,
    JOURNAL_TABS, journal_tabs, LEVEL_KEYS, MASTERY_ICON, MAX_MESSAGE, outcome_text, panel_only, REPORT_ICON, RULE,
    RULE_NUMBER, rule_numbers, SKINNING_TOOL, SLOT_ICONS, status_line,
)
from oathforge.bot.render.character import (
    ability_block, ability_mechanics, ability_owners, ability_tags, attribute, background_line, backgrounds_list,
    CLASS_ICONS, class_page, classes_list, hero, level_up_cards, lineages_list, path_choice, path_confirm, path_view,
    portrait_caption, rep_label, ROLE_ICON, rulebook, sheet, skill_page, spec_confirm,
)
from oathforge.bot.render.crafting import (
    activity_entries, activity_panel, activity_result, activity_title, craft_menu, crafts_tabs, END_RESULT,
    FIELD_MASTERIES, hobbies_view, hobby_lines, masteries_view, mastery_entry, mastery_lines, profession_page,
    professions_line, professions_view, recipe_card, RECIPE_FILTERS, recipes_list, RECIPES_PER_PAGE,
    RENAMED_PROFESSIONS, seller_of, specializations_view, swap_confirm, swap_menu, tools_view,
)
from oathforge.bot.render.world import (
    activities_view, bestiary_entry, bestiary_list, conversation, creature_caption, map_view, place_caption, room_view,
    rumors, scene, settings_view, talk_menu, zone_caption, ZONE_ICON, ZONE_INLINE,
)
from oathforge.bot.render.inventory import (
    _shop_group, inv_tab, INV_TABS, inventory_view, item_buttons, item_page, sell_menu, shop, SHOP_GROUPS, shop_menu,
)
from oathforge.bot.render.quests import (
    achievements_view, chronicle, FINISHED, fmt_int, journal, mission, missions, QUEST_ICONS, stats_view,
)
from oathforge.bot.render.combat import (
    combat_blocks, combat_help_text, combat_panel, combat_powers, combat_token, FOLLOW_UPS, full_report, PANEL_BLOCKS,
    report_page,
)
