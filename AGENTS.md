# AGENTS.md — cómo trabajar en Oathforge

Guía para cualquier agente de código (y para personas). Objetivo: cambios correctos con el mínimo de lectura. Las reglas de ramas y de commit de cada persona están en `CLAUDE.md`.

Oathforge es un RPG narrativo para Telegram: **un motor d20 determinista decide y Gemini narra.**

## Invariantes (no se rompen nunca)

1. **La IA nunca decide resultados.** El texto libre pasa a una intención estructurada (`ai/intent_parser.py`). El motor valida, tira y guarda; después la IA narra exactamente lo que pasó. La IA no da oro, XP, objetos, confianza ni hechos canónicos.
2. **Solo `oathforge/services/` escribe estado.** Los handlers seleccionan, llaman a un servicio y pintan. `engine/` es puro: sin BD, sin Telegram, sin IA y con RNG inyectable; todo azar pasa por `engine/dice.py`.
3. **Nada de E/S lenta con un lock abierto.** Ni Gemini ni Telegram dentro de `session_scope` con filas bloqueadas (`SELECT … FOR UPDATE` + versión). El flujo es leer contexto → interpretar → bloquear, revalidar y resolver → commit → enviar o narrar.
4. **Idempotencia.** Cada botón lleva nonce (`services/audit.py`); el combate usa `<encounter.version>.<turn_index>.<nonce>`. Un doble clic o un menú viejo no ejecuta dos veces.
5. **Español e inglés siempre.** Textos de interfaz en `oathforge/i18n/locales/{es,en}.yaml`; textos de contenido como `{es: …, en: …}` en `content/*.yaml`. Mismos marcadores en ambos.
6. **Gemini** (`google-genai`, `ai/client.py`) es el único proveedor. No se cambia sin que Josue lo pida.
7. Las excepciones de beta llevan la marca `# beta only` (sobre todo en `config.py`). No las extiendas sin marcarlas.

## Mapa del repo (dónde buscar)

| Busco… | Está en |
|---|---|
| Reglas puras: dados, pruebas, combate, recolección, progresión, compra por puntos | `oathforge/engine/` (`combat.py` es el grande) |
| Escrituras de estado por dominio | `oathforge/services/<dominio>.py` (`actions`, `combat_service`, `activities`, `quests`, `inventory`, `crafting`, `professions`, `exploration`, `world_map`, `npcs`, `chronicles`, `characters`, `media`, `audit`…) |
| IA: cliente y presupuesto, intérprete, narrador, diálogo, moderación, respaldos | `oathforge/ai/` |
| Handlers de Telegram | `oathforge/bot/handlers/` (`callbacks.py`, `commands.py`, `creation.py`, `text.py`, `common.py`) |
| Todo el HTML que ve el jugador | `oathforge/bot/render.py` (~84 KB: **no lo leas entero**) |
| Teclados | `oathforge/bot/keyboards.py` |
| Modelos de BD y migraciones | `oathforge/database/models.py`, `migrations/` (Alembic) |
| Validación del contenido | `oathforge/content/schemas.py` (Pydantic) y `loader.py` |
| Catálogo de imágenes | `oathforge/content/media.py` |
| Contenido del juego | `content/*.yaml`; mundo en `content/world/<continente>/<zona>/<lugar>/place.yaml`; respaldos de IA en `content/fallbacks/` |
| Comandos de consola | `oathforge/cli.py` (`COMMANDS`), simulador en `oathforge/tools/simulate.py`, `tgtest` en `oathforge/tools/tgtest.py` |
| Configuración y flags de beta | `oathforge/config.py`, `.env.example` |
| Diseño e ideas | `planning/` (ver abajo) |

## Leer barato

- **Busca antes de abrir.** Grep o Glob por el símbolo, la clave i18n o el id de contenido; abre solo el archivo que aparece.
- **Lee por rangos** los archivos grandes: `bot/render.py`, `bot/handlers/callbacks.py`, `engine/combat.py`, `i18n/locales/*.yaml`, `content/quests.yaml`, `CHANGELOG.md` y `planning/Possibilium.md`. Localiza la función con Grep y lee unas decenas de líneas alrededor.
- **No releas** un archivo que acabas de editar, ni uno que ya tienes en contexto.
- **CHANGELOG**: lee solo las primeras entradas (las últimas versiones) para saber qué cambió hace poco.
- **No leas** salvo que la tarea lo pida:
  - los anexos de Possibilium (§32, a partir de `<a id="s32">`: texto íntegro de los PDF retirados e instantáneas antiguas);
  - `artifacts/` (registros locales de partidas). Si hace falta depurar, localiza el archivo concreto por fecha, `telegram_id` o id de combate y lee solo ese;
  - `.venv/`, `migrations/versions/` antiguas y `content/officina/` (pruebas de imágenes de Josue).
- **Orden de consulta**: el código y `content/` son la verdad → el resumen latino del tema en `planning/` → el capítulo de `Possibilium.md` que ese resumen enlaza.
- No pidas a un subagente lo que resuelven uno o dos Grep.

## planning/

- `Possibilium.md`: libro de ideas, alternativas y preguntas, con IDs (`CLA-01`, `MIN-01`, `COO-01`…).
- Resúmenes por tema con nombre latino: `ordines` (clases), `progressio` (personaje y juramentos), `pugna` (combate y descanso), `opificia` (actividades y oficios), `mercatura` (comercio y equipo), `mundus` (mundo, viaje y misiones), `bestiarium`, `societas` (multijugador), `narratio` (IA), `facies` (interfaz Telegram), `ars` (audiovisual).
- `iter.md`: la hoja de ruta por versión.
- Cuando implementes o decidas algo, actualiza el **Estado actual** del resumen latino y, si cambia el plan, `iter.md`. Possibilium solo cambia si cambia una idea o su estado.

## Cambiar código

- Imita el código de alrededor: nombres, densidad de comentarios, estilo. Sin abstracciones, capas ni comentarios que el código no necesita. Cambio mínimo que resuelve la tarea.
- Reutiliza lo que hay: `render.*` para pintar, `services.*` para escribir, `ai/fallbacks.pick` para respaldos, `engine/dice` para tiradas.
- **Contenido nuevo**: un objeto, misión, criatura o lugar va en YAML. Lo valida `load_content()` al arrancar; si algo no cuadra, el bot no arranca y dice qué es.
- **Imágenes**: cada imagen integrada lleva `media.yaml` en su carpeta `images/` y `<nombre>.prompt.md` al lado (lo exige `tests/test_content.py`). Las pruebas van en `content/officina/`, que el catálogo no lee.
- **BD**: cualquier cambio de modelo lleva su migración de Alembic.
- **Comandos de consola**: un comando nuevo va a su grupo en `COMMANDS` de `oathforge/cli.py`.

## Probar

```powershell
.venv\Scripts\python -m pytest tests/<área> -q     # lo que tocaste (engine, services, ai, bot)
.venv\Scripts\python -m pytest tests/test_content.py -q   # siempre que toques content/
.venv\Scripts\python -m pytest -q                  # suite completa antes del commit
.venv\Scripts\oath simulate --level 1-5            # balance de combate
.venv\Scripts\oath tgtest send "/start"            # de punta a punta con la cuenta de prueba (en Git Bash, MSYS_NO_PATHCONV=1)
```

- Postgres si `TEST_DATABASE_URL` conecta; si no, SQLite. Las pruebas de concurrencia solo corren con Postgres.
- Tras una feature grande, repasa `tests/features.md` jugando con la cuenta de prueba y añade sus casillas.
- Un cambio de texto no necesita tests nuevos; uno de economía, permisos o concurrencia sí.

## Versionado y commits

- La versión vive solo en `oathforge/__init__.py`. Cada commit con cambios la sube: **parche** para arreglos y cambios pequeños, **menor** para una feature grande; `1.0.0` reservado.
- En el mismo commit: la entrada en `CHANGELOG.md` (Añadido / Cambiado / Arreglado / Eliminado) y, si cambia el plan, `planning/iter.md`.
- Asunto `vX.Y.Z: resumen corto`; cuerpo con la misma lista que el CHANGELOG.
