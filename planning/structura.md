# Structura — orden del proyecto para crecer

Checklist para que Oathforge aguante el crecimiento (ciudades, clases, objetos) con todo organizado, modular y comprobado solo. Se avanza **una fase por parche** en `josue-development`.

## Estado actual

- **Fase 0** hecha en 0.10.43, con el plan enlazado desde `CLAUDE.md` (0.10.44) y graphify (0.10.45). Solo queda de parte de Josue borrar las ramas antiguas de los testers (los pasos están en la propia fase).
- **Fase 2** hecha en 0.10.46–0.10.51, adelantada a petición de Josue: los cinco archivos grandes de código y los dos de tests son paquetes, y `tests/test_sizes.py` vigila el tamaño. Se verificó con la suite completa, el volcado de `load_content()` idéntico, los mismos números en `oath simulate` y `oath balance` y los mismos errores de validación sobre contenido roto a propósito.
- **Fase 3** hecha en 0.10.52–0.10.53: ruff (con un commit que solo formatea), import-linter, pyright, pre-commit, CI y tests de capas y de coherencia. Quedan de parte de Josue:
  - registrar el hook de ruff en `.claude/settings.json` (el agente no puede tocar sus propios permisos ni hooks; el texto está en la fase);
  - instalar pre-commit una vez y, si quiere, `git config blame.ignoreRevsFile .git-blame-ignore-revs`;
  - ver la CI en verde en el primer push y, en GitHub, exigirla para `main`;
  - decidir los rangos de estadísticas de los monstruos por nivel (ver la fase).
- **Fase 1** hecha en 0.10.54: clases, criaturas, objetos, PNJ y misiones tienen su carpeta, el cargador es genérico (`load_folder`) y los locales van por dominio. El volcado de `load_content()` sale idéntico (comparado con las claves ordenadas), los textos de la interfaz son los mismos y la suite está en verde. Dos cambios de orden menores, en el CHANGELOG.
- Siguiente: **Fase 4** (protocolos: plantillas, `oath new` y skills). Las plantillas van en `content/_templates/`, que el cargador ya ignora.
- Orden: 0 → 2 → 3 → 1 → 4 → 5 (la 2 se adelantó; el resto sigue igual).
- Después de cada merge a `main`: `/graphify . --update`.

## Cómo continuar (en otro chat)

1. Rama `josue-development`, `git fetch` y `git merge origin/main`.
2. Lee el **Estado actual** de arriba y solo la sección de la fase siguiente. No hace falta releer las fases cerradas.
3. Implementa esa fase entera, sin adelantar trabajo de otras.
4. Verifica (ver «Verificación de cada fase» al final). Si la fase mueve contenido o código, el volcado de `load_content()` y los números de `oath simulate` / `oath balance` tienen que salir iguales que antes.
5. Cierra:
   - marca las casillas y actualiza el **Estado actual** (fase hecha con su versión y la siguiente);
   - añade la fila en `planning/iter.md`;
   - escribe la entrada del CHANGELOG y sube la versión de parche;
   - si cambian reglas de trabajo, actualiza `AGENTS.md` o el `CLAUDE.md` de la zona.
6. Haz el commit `vX.Y.Z: structura fase N, …` y para para que Josue revise.

Decisiones ya tomadas (no se reabren):
- Proyecto de una sola persona: sin PR, sin testers y sin ramas por persona.
- La base va en inglés (ids, código, archivos, claves, skills, subcomandos) y todo texto visible en es y en.
- El orden era 0 → 3 → 1 → 2 → 4 → 5 (primero las comprobaciones y después los movimientos); Josue adelantó la 2, que se hizo sin ruff ni CI y se verificó a mano.
- Los permisos de `.claude/settings.json`:
  - **deny** para `.telegram/` (la sesión de Telethon equivale a una llave de la cuenta de prueba; `oath tgtest` la usa sin que el agente la lea), para `.env` (token del bot, clave de Gemini, contraseña de la BD; para saber qué variables hay está `.env.example`) y para `.venv/` (miles de archivos de terceros que solo gastan tokens; si hay que leer una librería, pasa a «ask»).
  - **ask** para `artifacts/` (partidas de jugadores reales: se abren solo para depurar y solo el archivo concreto) y para `content/officina/` (el laboratorio de Josue: solo si lo pide).
  - Estas reglas frenan accidentes de las herramientas de lectura, no son una caja fuerte. Lo que protege de verdad los secretos es que `.env` y `.telegram/` estén en `.gitignore`.

## Diagnóstico (0.10.42)

- **Archivos enormes** que cuestan tokens y son difíciles de revisar: `bot/render.py` (125 KB), `engine/combat.py` (52 KB), `content/loader.py` (40 KB), `content/schemas.py` (35 KB), `bot/handlers/callbacks.py` (31 KB), `content/class_specializations.yaml` (156 KB), `content/quests.yaml` (100 KB), `content/classes.yaml` (91 KB), los `locales/*.yaml` (54 KB cada uno), `CHANGELOG.md` (137 KB) y `planning/Possibilium.md` (612 KB).
- **Contenido repartido**: una clase está en `classes.yaml`, `class_specializations.yaml` y `content/classes/<id>/images/`. Un monstruo, en `monsters.yaml` y `content/monsters/<id>/images/`. Una ciudad nueva toca cinco o seis YAML planos (`npcs`, `quests`, `fallbacks/dialogue`, `items`, `recipes`…).
- **Nada automatizaba la calidad**: no hay CI ni linter ni comprobación de tipos ni pre-commit. Tampoco había `.claude/`.
- **No había protocolos** escritos para crear contenido.

---

## Fase 0 — Configuración para agentes (0.10.43)

- [x] **Proyecto de una sola persona**:
  - [x] Fuera `TODO-rayko.md` y `TODO-edian.md` (eran plantillas vacías).
  - [x] `CLAUDE.md`, `AGENTS.md`, `CODEOWNERS`, `README.md`, `TODO.md` y `planning/README.md` ya no hablan de testers ni de sus ramas.
  - [ ] **Josue**: borrar las ramas `rayko-development` (solo tiene un commit de prueba) y `edian-development` (no tiene commits propios), en local y en GitHub: `git branch -D rayko-development edian-development` y `git push origin --delete rayko-development edian-development`.
  - [ ] **Josue**, en GitHub: quitar del ruleset de `main` la excepción de los TODO y, si quiere, retirar a los colaboradores.
- [x] **CLAUDE.md en capas**: la raíz se queda corta, y cada zona tiene el suyo, que se carga solo al trabajar allí: `content/`, `oathforge/engine/`, `oathforge/services/`, `oathforge/bot/` y `tests/`.
- [x] **`.claude/settings.json`** (en git):
  - Permisos `allow` para pytest, `oath validate|content-index|simulate|balance|help` y git de solo lectura.
  - `ask` para leer `artifacts/` y `content/officina/`: se pueden abrir, pero solo cuando se pide.
  - `deny` para `.venv/`, `.env` y `.telegram/` (secretos).
- [x] **Hook `PostToolUse`** (`.claude/hooks/validate_content.py`): al editar un `content/*.yaml` ejecuta `oath validate` y, si hay errores, se los devuelve al agente. Si todo va bien, reescribe `content/INDEX.md`.
- [x] Hook de `ruff` sobre `*.py`: `.claude/hooks/ruff_python.py` (0.10.53). Falta registrarlo en `.claude/settings.json` (ver la Fase 3).
- [x] **`oath validate`**: carga `content/` como al arrancar el bot, sin Telegram ni BD.
- [x] **`oath content-index`** escribe `content/INDEX.md` con una línea por id (nombre en inglés y archivo). `tests/test_content.py` comprueba que está al día.
- [x] **Regla de nombres** en `AGENTS.md` («Nombres e idiomas»): la base va en inglés y todo texto visible en es y en. Un test exige ids y rutas de `content/` en ASCII.
- [x] **graphify** (0.10.45): instalado con `uv tool install graphifyy` (el paquete lleva dos «y»; el comando es `graphify`, en `~/.local/bin`) y registrado con `graphify install`.
  - Un solo grafo de `oathforge/` y `tests/` juntos, para que cada test quede unido al código que prueba: 130 archivos, unos 2.660 nodos y 87 comunidades. Sale solo del AST y gasta 0 tokens de IA.
  - `.graphifyignore` deja fuera `content/`, `planning/`, `migrations/`, `tools/`, los locales y los `.md`. Los patrones llevan `/` delante para no tapar `oathforge/content/` ni `oathforge/tools/`.
  - Regenerarlo con `/graphify . --update` después de cada merge a `main` y tras cambios grandes de código.
  - Con este tamaño el ahorro es moderado. Lo que más reduce tokens es la Fase 2.

## Fase 1 — Contenido modular: «una carpeta por cosa» (0.10.54)

La regla es la misma que ya sigue el mundo: cada entidad tiene su carpeta, con su ficha, sus imágenes y sus prompts.

- [x] **Clases**: `content/classes/<class>/class.yaml` (sale de `classes.yaml`) y `content/classes/<class>/specializations.yaml` (sale de `class_specializations.yaml`); `images/` ya existía. `order: N` en la ficha conserva el orden de los menús.
- [x] **Monstruos**: `content/monsters/<id>/monster.yaml` (sale de `monsters.yaml`) junto a su `images/`.
- [x] **Objetos**: `content/items/<type>/<id>/item.yaml` (la categoría es el `type`; un test lo comprueba). Las recetas, en `content/items/<type>/recipes.yaml` según su primer producto (los muebles, en `furniture/`).
  - [ ] Los iconos (`images/icon.jpg`, `icon.prompt.md`, `media.yaml`) se pueden poner junto a la ficha, pero el catálogo de imágenes todavía no los lee: no hay iconos de objetos que mostrar.
- [x] **Ciudades autocontenidas**:
  - [x] `world/<cont>/<zone>/npcs/<npc>/npc.yaml` y `dialogue.fallback.yaml` (en `fallbacks/dialogue.yaml` queda solo `default`).
  - [x] `world/<cont>/<zone>/quests/<quest>.yaml`.
  - Las tiendas se quedan en el `shop` del `npc.yaml`, no en el `place.yaml`: el modelo ya las guarda en el PNJ y moverlas habría sido un cambio de esquema, no de carpetas.
- [x] **Locales por dominio**: `oathforge/i18n/locales/{es,en}/<domain>.yaml` (diez dominios). `translator.flat` los une y falla si una clave está en dos archivos.
- [x] **Loader genérico**: `load_folder(root, filename, model)` (más `load_files` para `quests/<id>.yaml` y `load_merged` para los archivos con varios ids). Comprueba ids únicos, nombra la ruta en cada error e ignora las carpetas que empiezan por `_`. `content/index.py` lee la ruta real de cada ficha.
  - `media.py` no cambia: las imágenes de clases y criaturas ya estaban junto a su ficha.
- [x] **Seguridad del cambio**: el volcado de `load_content()` (con claves ordenadas) sale idéntico antes y después, y los dos locales aplanados son iguales a los de antes.

## Fase 2 — Código modular (0.10.46–0.10.51)

Cada archivo grande pasa a ser un paquete con un `__init__.py` que reexporta lo de antes, para que quien llama siga usando `render.x`, `combat.y`…

- [x] `bot/render.py` → `bot/render/` (`common`, `character`, `crafting`, `world`, `inventory`, `quests`, `combat`), 0.10.46. Lo que usaban varias pantallas sube a `common`, y las dependencias van en un solo sentido.
- [x] `engine/combat.py` → `engine/combat/` (`state`, `resolve`, `entities`, `turns`, `actions`), 0.10.47. Los nombres cambian respecto al borrador (`effects` y `monster_ai` no existían como bloques: el daño y los estados van en `resolve`, el turno enemigo en `turns`, y las invocaciones y formas en `entities`). `__init__` reexporta también los pasos privados que usan los tests del motor.
- [x] `content/schemas.py` → `content/schemas/` (`common`, `classes`, `items`, `monsters`, `professions`, `world`, `quests`), 0.10.48.
- [x] `content/loader.py` → `loader.py` (lectura) + `validation/` (`classes`, `world`, `items`, `crafting`, `fallbacks`, `quests`), 0.10.49. `validate_references` las corre todas; solo cambia el orden en que se listan los errores.
- [x] `bot/handlers/callbacks.py` → `callbacks/` (`router`, `views`, `acts`, `rolls`, `combat`), 0.10.50.
- [x] Los tests siguen la misma forma (0.10.50): `tests/bot/test_handlers.py` → `helpers.py`, `conftest.py` y `test_flow`, `test_creation`, `test_combat_buttons`, `test_views`, `test_activities`; `tests/services/test_services.py` → `helpers.py` y `test_characters`, `test_exploration`, `test_inventory`, `test_combat_service`, `test_quests`, `test_npcs`, `test_hunting`.
- [x] **Límite de tamaño** (0.10.51): `tests/test_sizes.py` falla si un `.py` de `oathforge/` o `tests/` pasa de 800 líneas o un YAML de 40 KB. Las excepciones (`classes`, `class_specializations`, `quests`, `fallbacks/chronicles` y los locales) esperan a la fase 1, y el test avisa cuando una ya cabe.
- [x] Un commit por archivo partido. `git mv` no guarda nada en git (los renombres se deducen al comparar), así que la historia de un trozo se sigue con `git log --follow` o `git blame -C -C` sobre el archivo antiguo.

## Fase 3 — Calidad automática (0.10.52–0.10.53)

- [x] **ruff** (lint + formato) en `pyproject.toml`: líneas de 120, reglas `E F W I UP B` (sin `E501`, que es cosa del formateador, ni `B905`), y `skip-magic-trailing-comma` para mantener el estilo compacto.
  - [x] 0.10.52: un commit que **solo formatea** (122 archivos, el árbol sintáctico idéntico al de antes). Está en `.git-blame-ignore-revs`.
  - [x] 0.10.53: los arreglos del linter (imports sin usar u ordenados, variables muertas, nombres ambiguos, `lambda` asignadas).
  - [x] Hook de Claude `.claude/hooks/ruff_python.py`: al editar un `.py` lo arregla y formatea, y devuelve lo que quede (exit 2). **Josue**: registrarlo en `.claude/settings.json`, junto al de contenido, dentro de `hooks.PostToolUse[0].hooks`:
    ```json
    {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.venv/Scripts/python.exe\" \"$CLAUDE_PROJECT_DIR/.claude/hooks/ruff_python.py\"", "timeout": 30, "statusMessage": "ruff on the edited .py"}
    ```
    y, si quiere, permitir en `permissions.allow` `Bash(.venv/Scripts/python -m ruff *)`, `Bash(.venv/Scripts/lint-imports)` y `Bash(.venv/Scripts/pyright)` (y sus versiones `PowerShell(...)`).
- [x] **import-linter** (`lint-imports`, contratos en `pyproject.toml`): `engine` no importa `database`, `services`, `bot`, `ai`, `telegram`, `sqlalchemy` ni `google`; `services`, `content` y `database` no suben a `bot` ni a `telegram`; solo `ai/client.py` importa `google`.
  - [x] «`bot` no escribe modelos» no se ve en los imports (el bot lee modelos y abre transacciones): lo comprueba `tests/test_layers.py` sobre el árbol sintáctico. Al hacerlo aparecieron dos escrituras directas de `user.language`, que pasan a `characters.set_language`.
- [x] **pyright** en modo básico para `engine/` y `services/`: 74 errores, todos de valores que pueden ser `None`. `Content.progression` pasa a ser obligatorio; el resto se arregla con comprobaciones explícitas (un registro borrado entre dos transacciones devuelve `None` o «sin efecto») o con `assert` donde la validación del contenido ya lo garantiza. `oath simulate` y `oath balance` dan los mismos números.
- [x] **pre-commit** (`.pre-commit-config.yaml`, hooks locales con el `.venv`): ruff, `oath validate` si el commit toca `content/`, `tools/check_release.py` (la versión subió y el CHANGELOG empieza por su entrada) y el asunto `vX.Y.Z: ` en la fase `commit-msg`. **Josue**: instalarlo una vez con `.venv\Scripts\pre-commit install --hook-type pre-commit --hook-type commit-msg`.
- [x] **CI en GitHub Actions** (`.github/workflows/ci.yml`) en cada push a `josue-development` y a `main`, y en los PR a `main`:
  - ruff, import-linter y pyright;
  - `oath validate` y pytest con SQLite y con Postgres como servicio;
  - Antes de llevar nada a `main` tiene que estar en verde. **Josue**: comprobar el primer run tras el push y, si quiere, exigirlo en el ruleset de `main`.
- [x] **Coherencia del contenido** (`tests/test_coherence.py`): todo objeto se puede conseguir (tienda, botín, receta, recolección, descubrimiento, misión o equipo inicial), todo monstruo está en una tabla de encuentros, todo PNJ tiene horario, y dentro de un mismo tipo y ranura el equipo de más nivel no es más barato.
  - [ ] **Josue**: los rangos de estadísticas de los monstruos por nivel. Los monstruos no tienen nivel propio; el único dato es el rival previsto de `oath balance` (`STANDARDS`), y en él ni la vida ni la XP suben siempre (el estándar de 17 tiene menos vida que el de 13; la XP del élite de 9 es menor que la del de 5). Hace falta una regla de diseño (bandas de vida, CA y XP por nivel, o un margen) antes de convertirla en test.

## Fase 4 — Protocolos (fichas + prompts listos)

Cada tipo de contenido tiene tres piezas que se mantienen juntas:

1. **Plantilla** en `content/_templates/<type>/` (`item`, `monster`, `npc`, `quest`, `zone`, `place`, `class`), comentada con todos los campos y sus rangos.
2. **Generador**: `oath new <type> <id> [--zone …] [--category …]` crea la carpeta desde la plantilla, con `images/media.yaml` y un `<name>.prompt.md` ya relleno. El prompt combina el bloque de estilo común (`content/_templates/prompts/style.md`, que sale de `ars.md`) con la descripción de la ficha.
3. **Skill de Claude** en `.claude/skills/<protocol>/SKILL.md` con los pasos y una lista de cierre:
   - [ ] `new-item`: ficha `{es,en}` → nivel y precio (`oath balance`) → de dónde sale (receta, botín, tienda o recompensa) → prompt del icono → `oath validate` → CHANGELOG.
   - [ ] `new-monster`: ficha → estadísticas según su nivel → dónde aparece y su botín → prompt del retrato → `oath simulate` → bestiario.
   - [ ] `new-city`: carpeta de la zona y grafo de lugares, PNJ con sus 12 respaldos por idioma, tiendas, misiones, monstruos, imágenes de día y de noche con su prompt, balance del rango de niveles, `tests/features.md` y un recorrido con `oath tgtest`.
   - [ ] `new-quest`, `new-npc`, `new-class` / `new-specialization` (incluye la progresión 1–20).
   - [ ] `new-image`: prompt → `tools/prepare_image.py` → `media.yaml` con créditos.
   - [ ] `release`: versión → CHANGELOG → `iter.md` → anuncio en inglés y su traducción al español con el formato de los canales.
- [ ] `AGENTS.md` enlaza cada protocolo en una tabla: «quiero crear X → usa la skill Y».

## Herramientas recomendadas

**Skills incluidas en Claude Code, para usar como rutina**
- [ ] `/code-review` antes de llevar cambios a `main`; `/security-review` cuando se toquen la IA, el texto del jugador o los permisos.
- [ ] `/simplify` después de cada fase de la refactorización.
- [ ] `/fewer-permission-prompts` para ajustar los permisos de `.claude/settings.json` a tu uso real.
- [ ] `/skill-creator` para escribir y probar las skills de la Fase 4.
- [ ] `/schedule`: una tarea semanal que ejecute `oath balance` y las pruebas de coherencia y abra una issue si algo se desvía.

**Skills propias** (`.claude/skills/`, en git)
- [ ] Las de la Fase 4, más `series-phase` (siguiente fase de la serie en curso), `debug-session` (abre solo los artefactos de un jugador y un día) y `translate` (mismas claves y marcadores en es y en).

**Subagentes** (`.claude/agents/`, de solo lectura y con un modelo barato cuando baste)
- [ ] `lore-keeper` (coherencia con el mundo), `balance-reviewer` (`oath simulate` y `oath balance` sobre el rango tocado), `invariants-reviewer` (revisa un diff contra las invariantes de `AGENTS.md`) e `i18n-checker`.

**Hooks**
- [ ] `SessionStart`: muestra la rama, la versión y si hay commits de `origin/main` sin traer.
- [ ] `PreToolUse` sobre `git commit`: bloquea el commit en `main` o si la versión no subió.

**MCP**
- [ ] Postgres en solo lectura (BD local o de staging) para consultar sin escribir scripts.
- [ ] Context7, con la documentación al día de python-telegram-bot, SQLAlchemy, google-genai y Alembic.
- [ ] GitHub: con `gh` basta.

## Fase 5 — Documentación sin peso muerto

- [ ] `CHANGELOG.md`: queda solo la serie actual; las anteriores van al archivo.
- [ ] `Possibilium.md`: los anexos de §32 pasan a `planning/archivum/`.
- [ ] `roadmap.md` y `roadmap_balance.md`: las fases cerradas pasan al archivo.
- [ ] Decisiones de arquitectura (ADR) cortas en `planning/decisions/NNN-title.md`.

## Verificación de cada fase

- `.venv\Scripts\python -m pytest -q` en verde.
- Fases 1 y 2: el volcado JSON de `load_content()` sale idéntico al de antes.
- `oath simulate --level 1-5` y `oath balance` sin cambios en los números, si la fase no toca el balance.
- Un recorrido corto con `oath tgtest`.
