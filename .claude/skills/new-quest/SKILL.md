---
name: new-quest
description: Crear una misión nueva de Oathforge (etapas, objetivos, recompensas, diario en es/en y encadenado con otras). Úsala cuando Josue pida una misión, un encargo o una cadena de misiones.
---

# Nueva misión

1. **Ficha**: `.venv\Scripts\oath new quest <id> --zone <zona> [--giver <pnj>] [--place <lugar>] --name "…" --desc "…"`. Crea `content/world/<continente>/<zona>/quests/<id>.yaml`. La zona de la misión es la de quien la da. Mira una parecida en esa carpeta antes de escribir.
2. **Objetivos**: los tipos (`kill`, `hunt`, `talk`, `visit`, `gather`, `skin`, `craft`, `rest`, `heal`, `buy`, `sell`, `equip`…) están en `QuestObjective` de `oathforge/content/schemas/quests.py`; cada `target` tiene que existir. Los objetivos se cumplen solos al jugarlos.
3. **Etapas**: `start_stage`, una etapa por momento del diario con su `journal` en es y en, `objective_stage` (donde cuentan los objetivos) y `complete_stage` (`state: completed`). Con `giver`, añade `turn_in_stage` (`state: ready`) y la misión se entrega en persona. `location_text` pone texto extra en un lugar mientras la etapa está activa.
4. **Encadenado**: tras otra, `start_stage: locked` (etapa `state: locked`), `unlock_stage: active` y `after: <misión>` (o `unlock_flag`). `order` fija su sitio en el diario.
5. **Recompensas**: `xp`, `gold`, `give_item`, `milestone`, `set_flag`, `reputation`, `trust`, `npc_memory`, `world_rumor`, `profession_xp`. Las cifras tienen que encajar con las misiones del mismo rango de niveles (`planning/roadmap_balance.md`, la fase que toca) y con `.venv\Scripts\oath balance --quick`. La IA nunca da recompensas: solo el motor.
6. **Textos**: `name`, `summary`, `hint` y cada `journal` en es y en, sin `TODO(new)`. Si es del tutorial, `tutorial: true` (cuenta en `oath tutorial-stats`).
7. **Cierre**: `.venv\Scripts\oath validate`, `.venv\Scripts\python -m pytest tests/test_content.py tests/test_campaign.py -q`, juega la misión con `.venv\Scripts\oath tgtest send …` y añade su casilla a `tests/features.md`; CHANGELOG y commit (skill `release`).

Lista de cierre: objetivos con ids reales · etapas y diario en es y en · recompensa acorde al rango · desbloqueo comprobado · jugada de punta a punta.
