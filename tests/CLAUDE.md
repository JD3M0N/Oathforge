# tests/ — qué correr

| Tocaste | Corre |
|---|---|
| `engine/` | `.venv\Scripts\python -m pytest tests/engine -q` y `oath simulate --level 1-5` |
| `services/` | `.venv\Scripts\python -m pytest tests/services -q` |
| `bot/` | `.venv\Scripts\python -m pytest tests/bot tests/services/test_render.py -q` |
| `ai/` | `.venv\Scripts\python -m pytest tests/ai -q` |
| `content/` | `oath validate` y `.venv\Scripts\python -m pytest tests/test_content.py -q` |
| Antes del commit | `.venv\Scripts\python -m pytest -q` |

- La BD de pruebas es Postgres si `TEST_DATABASE_URL` conecta y, si no, SQLite. Las pruebas de concurrencia solo corren con Postgres.
- `conftest.py` manda los artefactos a una carpeta temporal y fija los ajustes que dependen de `.env`.
- `tests/ruins.py` es una mazmorra de pruebas para el motor: no la uses como contenido del juego.
- Los tests siguen la forma del código, un archivo por dominio. Lo compartido va en `helpers.py` de su carpeta (`tests/bot/helpers.py`: `Player`, `Chat`, `create`…; `tests/services/helpers.py`: `new_character`, `get_char`, `fight`), y `tests/bot/conftest.py` quita el límite de frecuencia a todos los tests de handlers.
- Para cambiar algo de un paquete partido con `monkeypatch`, parchea el submódulo donde vive el nombre (`callbacks.router.rate_ok`, `callbacks.rolls.DICE_SECONDS`): parchear el paquete no lo cambia.
- `test_sizes.py` vigila que ningún `.py` pase de 800 líneas ni ningún YAML de 40 KB.
- Un cambio de economía, permisos o concurrencia necesita su test; uno de texto, no.
