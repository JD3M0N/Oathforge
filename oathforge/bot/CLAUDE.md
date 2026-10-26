# bot/ — Telegram: seleccionar, llamar a un servicio y pintar

- Los handlers (`handlers/`) no escriben en la BD: llaman a `services.*` y pintan el resultado con `render.*`.
- **`render/`** pinta todo lo que ve el jugador, un módulo por familia de pantallas: `common` (piezas compartidas: iconos, `RULE`, `item_stats`, `journal_tabs`, `rule_numbers`), `character` (hoja, habilidades, senda, clases, reglamento), `crafting` (actividades, maestrías, oficios, recetas), `world` (escena, mapa, conversaciones, bestiario), `inventory` (tiendas e inventario), `quests` (diario, misiones, crónica, logros) y `combat`.
  - `render/__init__.py` lo reexporta todo: quien llama sigue usando `render.x`. Una función nueva se añade a su módulo y a la lista de `__init__.py`.
  - Las dependencias van en un solo sentido (`common` ← `crafting` ← `character` y `world`; el resto solo usa `common`). Si dos módulos necesitan lo mismo, súbelo a `common` en vez de crear un ciclo.
- **`handlers/callbacks/`** reparte los botones por `verb` (el primer trozo del `callback_data`): `router` (entrada, `VIEWS` y `on_callback`), `views` (lo que solo muestra), `acts` (lo que cambia estado: `_dispatch` y `_after`), `rolls` (la 🎲 manual y los ajustes) y `combat`. Busca `verb == "<verbo>"` y lee alrededor.
- Todo texto de interfaz sale de `i18n/locales/{es,en}/<dominio>.yaml` con la misma clave y los mismos marcadores. No escribas texto suelto en el código.
- Cada botón que cambia estado lleva un nonce (ver `services/audit.py`). El combate usa `<encounter.version>.<turn_index>.<nonce>`.
- Para probar de verdad: `oath tgtest send "/start"` (en Git Bash con `MSYS_NO_PATHCONV=1`), además de `tests/bot/`.
