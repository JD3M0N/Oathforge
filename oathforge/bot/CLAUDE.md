# bot/ — Telegram: seleccionar, llamar a un servicio y pintar

- Los handlers (`handlers/`) no escriben en la BD: llaman a `services.*` y pintan el resultado con `render.*`.
- **`render.py` es enorme (~125 KB): no lo leas entero.** Está dividido en secciones con cabeceras `# ---- scene`, `shop`, `character`, `rulebook`, `classes`, `bestiary`, `combat`… Busca con Grep la función o la cabecera y lee solo esa parte.
- `handlers/callbacks.py` también es grande: reparte por `verb` (el primer trozo del `callback_data`). Busca `verb == "<verbo>"` y lee alrededor.
- Todo texto de interfaz sale de `i18n/locales/{es,en}.yaml` con la misma clave y los mismos marcadores. No escribas texto suelto en el código.
- Cada botón que cambia estado lleva un nonce (ver `services/audit.py`). El combate usa `<encounter.version>.<turn_index>.<nonce>`.
- Para probar de verdad: `oath tgtest send "/start"` (en Git Bash con `MSYS_NO_PATHCONV=1`), además de `tests/bot/`.
