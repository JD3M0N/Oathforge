# AGENTS.md — cómo trabajar en Oathforge

Guía para cualquier agente de código (y para personas). Objetivo: cambios correctos con el mínimo de lectura. Las reglas de rama y de commit están en `CLAUDE.md`.

Oathforge es un RPG narrativo para Telegram: **un motor d20 determinista decide y Gemini narra.**

## Invariantes (no se rompen nunca)

1. **La IA nunca decide resultados.** El texto libre pasa a una intención estructurada (`ai/intent_parser.py`). El motor valida, tira y guarda; después la IA narra exactamente lo que pasó. La IA no da oro, XP, objetos, confianza ni hechos canónicos.
2. **Solo `oathforge/services/` escribe estado.** Los handlers seleccionan, llaman a un servicio y pintan. `engine/` es puro: sin BD, sin Telegram, sin IA y con RNG inyectable; todo azar pasa por `engine/dice.py`.
3. **Nada de E/S lenta con un lock abierto.** Ni Gemini ni Telegram dentro de `session_scope` con filas bloqueadas (`SELECT … FOR UPDATE` + versión). El flujo es leer contexto → interpretar → bloquear, revalidar y resolver → commit → enviar o narrar.
4. **Idempotencia.** Cada botón lleva nonce (`services/audit.py`); el combate usa `<encounter.version>.<turn_index>.<nonce>`. Un doble clic o un menú viejo no ejecuta dos veces.
5. **Español e inglés siempre.** Textos de interfaz en `oathforge/i18n/locales/{es,en}/<dominio>.yaml`; textos de contenido como `{es: …, en: …}` en las fichas de `content/`. Mismos marcadores en ambos.
6. **Gemini** (`google-genai`, `ai/client.py`) es el único proveedor. No se cambia sin que Josue lo pida.
7. Las excepciones de beta llevan la marca `# beta only` (sobre todo en `config.py`). No las extiendas sin marcarlas.

Flujo de una acción libre: `leer contexto (tx corta) → Gemini interpreta → bloquear + validar + resolver (tx) → Gemini narra`.

**Seguridad ante la IA**:
- El texto del jugador va delimitado como datos (`<player_text>`), nunca dentro de las instrucciones.
- Los ids que propone la IA deben existir en el contexto; si no, la acción pasa a `narrate_only`.
- Las dificultades que sugiere se limitan a un rango permitido.
- El presupuesto diario de IA, por usuario y global (`ai_usage`), se comprueba **antes** de cada llamada.
- Si la IA falla o se agota el presupuesto, el juego sigue con textos de plantilla (`content/fallbacks/`).
- Hay límite de frecuencia por usuario y registro auditable de cada acción (`action_logs`).

## Mapa del repo (dónde buscar)

| Busco… | Está en |
|---|---|
| Reglas puras: dados, pruebas, combate, recolección, progresión, compra por puntos | `oathforge/engine/` (el combate es el paquete `combat/`) |
| Escrituras de estado por dominio | `oathforge/services/<dominio>.py` (`actions`, `combat_service`, `activities`, `quests`, `inventory`, `crafting`, `professions`, `exploration`, `world_map`, `npcs`, `chronicles`, `characters`, `media`, `audit`…) |
| IA: cliente y presupuesto, intérprete, narrador, diálogo, moderación, respaldos | `oathforge/ai/` |
| Handlers de Telegram | `oathforge/bot/handlers/` (`callbacks/`, `commands.py`, `creation.py`, `text.py`, `common.py`) |
| Todo el HTML que ve el jugador | `oathforge/bot/render/` (un módulo por familia de pantallas; `render.x` sigue funcionando) |
| Teclados | `oathforge/bot/keyboards.py` |
| Modelos de BD y migraciones | `oathforge/database/models.py`, `migrations/` (Alembic) |
| Validación del contenido | `oathforge/content/schemas/` (Pydantic, un módulo por dominio), `loader.py` (lectura) y `validation/` (referencias cruzadas por dominio) |
| Catálogo de imágenes | `oathforge/content/media.py` |
| Contenido del juego | una carpeta por cosa: `content/classes/<clase>/`, `monsters/<id>/`, `items/<tipo>/<id>/`; mundo en `content/world/<continente>/<zona>/` (`<lugar>/place.yaml`, `npcs/<pnj>/`, `quests/<misión>.yaml`); lo demás en `content/*.yaml`; respaldos de IA en `content/fallbacks/` |
| Comandos de consola | `oathforge/cli.py` (`COMMANDS`), simulador en `oathforge/tools/simulate.py`, `tgtest` en `oathforge/tools/tgtest.py` |
| Configuración y flags de beta | `oathforge/config.py`, `.env.example` |
| Diseño e ideas | `planning/` (ver abajo) |

## Leer barato

- **Busca antes de abrir.** Grep o Glob por el símbolo, la clave i18n o el id de contenido; abre solo el archivo que aparece.
- **Grafo del código**: si existe `graphify-out/`, consúltalo (`/graphify query "…"`, o `graphify-out/GRAPH_REPORT.md`) para saber quién llama a qué y qué test cubre qué antes de hacer Grep por todo el repo. Cubre solo `oathforge/` y `tests/` (lo limita `.graphifyignore`). Se regenera con `/graphify . --update` **después de cada merge a `main`** y tras cambios grandes de código; sale del AST y no gasta tokens de IA.
- **Contenido**: `content/INDEX.md` tiene una línea por id (nombre en inglés y archivo). Lo escribe `oath content-index` y un test comprueba que está al día.
- **Lee por rangos** los archivos grandes: `i18n/locales/*/*.yaml`, `CHANGELOG.md` y `planning/Possibilium.md`. Localiza la función con Grep y lee unas decenas de líneas alrededor.
- **No releas** un archivo que acabas de editar, ni uno que ya tienes en contexto.
- **CHANGELOG**: lee solo las primeras entradas (las últimas versiones) para saber qué cambió hace poco.
- **No leas** salvo que la tarea lo pida:
  - `planning/archivum/` (lo hecho y cerrado: CHANGELOG 0.1–0.9, anexos de Possibilium §32, fases B00–B13, fichas F01/F03/F04 y lo hecho de `TODO.md`), salvo que Josue pida todo lo que se ha hecho; el resto de `planning/` es la entrada de trabajo;
  - `artifacts/` (registros locales de partidas, `oathforge/recorder.py`; se apaga con `ARTIFACTS_ENABLED=false`). Si hace falta depurar, abre solo el archivo concreto:
    - `conversations/<día>/<telegram_id>.md`: chat jugador ↔ bot, con los cambios de estado como «⚙️ estado»;
    - `battles/<día>/<id>-<lugar>.md`: un combate turno a turno;
    - `ai/<día>/…json`: llamadas a Gemini (prompt, respuesta, tokens, latencia);
    - `errors/<día>.log` y `logs/<día>.log`: errores y avisos; `events/<día>.jsonl`: todo en crudo;
  - `.venv/`, `migrations/versions/` antiguas y `content/officina/` (pruebas de imágenes de Josue).
- **Orden de consulta**: el código y `content/` son la verdad → el resumen latino del tema en `planning/` → el capítulo de `Possibilium.md` que ese resumen enlaza.
- No pidas a un subagente lo que resuelven uno o dos Grep.

## planning/

- `Possibilium.md`: libro de ideas, alternativas y preguntas, con IDs (`CLA-01`, `MIN-01`, `COO-01`…).
- `archivum/`: lo hecho y cerrado, apartado; no se lee salvo petición. Cuando una fase se cierra del todo, su ficha se mueve allí y queda un puntero de una línea.
- `decisions/`: decisiones de arquitectura (ADR) cortas, `NNN-title.md`; una nueva sustituye a la anterior, que se marca *sustituida*.
- Resúmenes por tema con nombre latino: `ordines` (clases), `progressio` (personaje y juramentos), `pugna` (combate y descanso), `opificia` (actividades y oficios), `mercatura` (comercio y equipo), `mundus` (mundo, viaje y misiones), `bestiarium`, `societas` (multijugador), `narratio` (IA), `facies` (interfaz Telegram), `ars` (audiovisual), `structura` (orden del proyecto y herramientas).
- `iter.md`: la hoja de ruta por versión.
- Cuando implementes o decidas algo, actualiza el **Estado actual** del resumen latino y, si cambia el plan, `iter.md`. Possibilium solo cambia si cambia una idea o su estado.

## Cambiar código

- Imita el código de alrededor: nombres, densidad de comentarios, estilo. Sin abstracciones, capas ni comentarios que el código no necesita. Cambio mínimo que resuelve la tarea.
- Reutiliza lo que hay: `render.*` para pintar, `services.*` para escribir, `ai/fallbacks.pick` para respaldos, `engine/dice` para tiradas.
- **Contenido nuevo**: un objeto, misión, criatura o lugar va en YAML. Lo valida `load_content()` al arrancar; si algo no cuadra, el bot no arranca y dice qué es. Se crea con `oath new` (plantillas en `content/_templates/`) y su skill:

| Quiero crear… | Skill | Primer paso |
|---|---|---|
| un objeto | `new-item` | `oath new item <id> --category <tipo>` |
| una criatura o jefe | `new-monster` | `oath new monster <id>` |
| un PNJ | `new-npc` | `oath new npc <id> --zone <zona>` |
| una misión | `new-quest` | `oath new quest <id> --zone <zona> [--giver <pnj>]` |
| una ciudad o zona (con sus lugares) | `new-city` | `oath new zone <id>` y `oath new place <id> --zone <zona>` |
| una clase o una rama de clase | `new-class` | `oath new class <id>` |
| una imagen | `new-image` | el `.prompt.md` que dejó `oath new` |
| cerrar una versión y anunciarla | `release` | pruebas → versión → CHANGELOG → commit |

  Lo que falta por escribir en una ficha nueva lleva la marca `TODO(new)`; `tests/test_content.py` falla mientras quede alguna en `content/`.
- **Imágenes**: cada imagen integrada lleva `media.yaml` en su carpeta `images/` y `<nombre>.prompt.md` al lado (lo exige `tests/test_content.py`). Las pruebas van en `content/officina/`, que el catálogo no lee.
- **BD**: cualquier cambio de modelo lleva su migración de Alembic.
- **Comandos de consola**: un comando nuevo va a su grupo en `COMMANDS` de `oathforge/cli.py`.

## Nombres e idiomas

- **La base va en inglés**: ids, variables, funciones, archivos y carpetas, claves de YAML y de i18n, plantillas, skills y subagentes, subcomandos de `oath` y sus flags. Los ids y las rutas de `content/` son ASCII en minúsculas (`[a-z0-9_]`); lo comprueba `tests/test_content.py`.
- **Todo texto que ve el jugador está en los dos idiomas**: `{es: …, en: …}` en el contenido y `i18n/locales/{es,en}/<dominio>.yaml` en la interfaz. Sin excepciones.
- El diseño en `planning/` sigue en español, con sus nombres latinos.

## Probar

```powershell
.venv\Scripts\python -m pytest tests/<área> -q     # lo que tocaste (engine, services, ai, bot)
.venv\Scripts\oath validate                        # carga content/ como al arrancar el bot (segundos)
.venv\Scripts\python -m pytest tests/test_content.py -q   # siempre que toques content/
.venv\Scripts\python -m pytest -q                  # suite completa antes del commit
.venv\Scripts\oath simulate --level 1-5            # balance de combate
.venv\Scripts\oath tgtest send "/start"            # de punta a punta con la cuenta de prueba (en Git Bash, MSYS_NO_PATHCONV=1)
.venv\Scripts\python -m ruff check . --fix; .venv\Scripts\python -m ruff format .   # estilo (también el hook .claude/hooks/ruff_python.py al editar)
.venv\Scripts\lint-imports                        # invariantes por imports: engine puro, solo ai/client.py habla con Gemini
.venv\Scripts\pyright                             # tipos de engine/ y services/
```

- **Calidad automática** (`planning/structura.md`, fase 3): ruff (líneas de 120), import-linter y pyright se configuran en `pyproject.toml`. `tests/test_layers.py` comprueba que el bot no escribe modelos y `tests/test_coherence.py`, que todo objeto se puede conseguir, todo monstruo vive en algún lugar y todo PNJ está colocado.
- **pre-commit** (`.pre-commit-config.yaml`, se instala una vez: `.venv\Scripts\pre-commit install --hook-type pre-commit --hook-type commit-msg`): ruff, `oath validate` si el commit toca `content/`, que la versión subió con su entrada en el CHANGELOG y que el asunto empieza por `vX.Y.Z: ` (`tools/check_release.py`).
- **CI** (`.github/workflows/ci.yml`) en cada push a `josue-development` y a `main`: ruff, import-linter, pyright y pytest con SQLite y con Postgres. **Nada va a `main` sin la CI en verde.**

- Postgres si `TEST_DATABASE_URL` conecta; si no, SQLite. Las pruebas de concurrencia solo corren con Postgres.
- `tgtest` usa una cuenta de prueba con Telethon: `TG_TEST_API_ID`, `TG_TEST_API_HASH` y `TG_TEST_BOT` en `.env`, login con `oath tgtest login <teléfono>` (ver `oathforge/tools/tgtest.py`).
- Ronda de pruebas limpia: para el bot y `oath reset-players --yes`; un solo jugador, `oath delete-player <nombre|id> --yes`.
- Tras una feature grande, repasa `tests/features.md` jugando con la cuenta de prueba y añade sus casillas.
- Un cambio de texto no necesita tests nuevos; uno de economía, permisos o concurrencia sí.
- **Tamaño**: `tests/test_sizes.py` falla si un `.py` pasa de 800 líneas o un YAML de 40 KB (con su lista de excepciones). Antes de llegar, parte el archivo en un paquete cuyo `__init__.py` reexporte lo de antes, como `bot/render/` o `engine/combat/`.

## Versionado y commits

- La versión vive solo en `oathforge/__init__.py`. Cada commit con cambios la sube: **parche** para arreglos y cambios pequeños, **menor** para una feature grande; `1.0.0` reservado.
- En el mismo commit: la entrada en `CHANGELOG.md` (Añadido / Cambiado / Arreglado / Eliminado) y, si cambia el plan, `planning/iter.md`.
- Asunto `vX.Y.Z: resumen corto`; cuerpo con la misma lista que el CHANGELOG. El hook de pre-commit lo comprueba.
- Un commit que solo formatea va a `.git-blame-ignore-revs`, para que `git blame` lo salte.
- **`README.md` raíz**: es la presentación del juego, simple y sin estado de versión. No lo actualices con cada cambio: se rehace al final, cuando Josue lo pida.
- Cada versión se anuncia en los canales [inglés](https://t.me/OathForge) y [español](https://t.me/OathForge_es) con el mismo formato (título `🛡 Oathforge vX.Y.Z: …`, bloques con emoji y viñetas); el de español es la traducción del inglés.
