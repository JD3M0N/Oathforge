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
- `test_handlers.py` y `test_services.py` son grandes: busca el test con Grep en vez de leerlos enteros.
- Un cambio de economía, permisos o concurrencia necesita su test; uno de texto, no.
