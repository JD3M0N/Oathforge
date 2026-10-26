# Structura — orden del proyecto para crecer

Checklist para que Oathforge aguante el crecimiento (ciudades, clases, objetos) con todo organizado, modular y comprobado solo. Se avanza **una fase por parche** en `josue-development`.

## Estado actual

- **Fase 0** hecha en 0.10.43 (y el plan enlazado desde `CLAUDE.md` en 0.10.44), salvo dos cosas que dependen de Josue: borrar las ramas antiguas de los testers e instalar graphify (los pasos están en la propia fase).
- Siguiente: **Fase 3** (calidad automática). Las comprobaciones van primero para que los movimientos de las fases 1 y 2 sean seguros.
- Orden: 0 → 3 → 1 → 2 → 4 → 5.

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
- El orden es 0 → 3 → 1 → 2 → 4 → 5: primero las comprobaciones y después los movimientos.
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
- [ ] Hook de `ruff` sobre `*.py`: se añade en la Fase 3, junto con ruff.
- [x] **`oath validate`**: carga `content/` como al arrancar el bot, sin Telegram ni BD.
- [x] **`oath content-index`** escribe `content/INDEX.md` con una línea por id (nombre en inglés y archivo). `tests/test_content.py` comprueba que está al día.
- [x] **Regla de nombres** en `AGENTS.md` («Nombres e idiomas»): la base va en inglés y todo texto visible en es y en. Un test exige ids y rutas de `content/` en ASCII.
- [ ] **graphify** (pendiente de instalar en la máquina de Josue; `graphify-out/` ya está en `.gitignore` y `AGENTS.md` ya lo menciona):
  - Instalarlo: `pip install graphifyy` (el paquete lleva dos «y»; el comando es `graphify`), o `uv tool install graphifyy` / `pipx install graphifyy` si tienes uv o pipx.
  - Registrar la skill: `graphify install`. Después, reiniciar Claude Code.
  - Generar el grafo solo del código, en Claude Code: `/graphify oathforge` y `/graphify tests`. Nada de `planning/` ni del CHANGELOG, porque indexar documentos pasa por el LLM y cuesta tokens.
  - Regenerarlo tras cada merge de `main`.
  - Con unos 150 archivos de código el ahorro es moderado. Lo que más reduce tokens es la Fase 2.

## Fase 1 — Contenido modular: «una carpeta por cosa»

La regla es la misma que ya sigue el mundo: cada entidad tiene su carpeta, con su ficha, sus imágenes y sus prompts.

- [ ] **Clases**: `content/classes/<class>/class.yaml` (sale de `classes.yaml`) y `content/classes/<class>/specializations.yaml` (sale de `class_specializations.yaml`); `images/` ya existe.
- [ ] **Monstruos**: `content/monsters/<id>/monster.yaml` (sale de `monsters.yaml`) junto a su `images/`.
- [ ] **Objetos**: `content/items/<category>/<id>/item.yaml`, más `images/icon.jpg`, `icon.prompt.md` y `media.yaml` opcionales. Las recetas van junto al objeto que producen o en `content/items/<category>/recipes.yaml`.
- [ ] **Ciudades autocontenidas**: todo lo de una zona vive dentro de su carpeta. Crear una ciudad es crear una carpeta.
  - `world/<cont>/<zone>/npcs/<npc>/npc.yaml` y `dialogue.fallback.yaml` (sale de `fallbacks/dialogue.yaml`).
  - `world/<cont>/<zone>/quests/<quest>.yaml` (sale de `quests.yaml`).
  - Las tiendas, en el `place.yaml` de su lugar.
- [ ] **Locales por dominio**: `oathforge/i18n/locales/{es,en}/<domain>.yaml`. `translator.py` los une y avisa si una clave se repite.
- [ ] **Loader genérico**: una función `load_folder(root, filename, model)` que recorre carpetas, comprueba que los ids son únicos y señala la ruta en cada error. `media.py` usa la misma convención, y las carpetas que empiezan por `_` (como `_templates/`) se ignoran. `content/index.py` pasa a leer la ruta real de cada ficha.
- [ ] **Seguridad del cambio**: antes de mover nada, se vuelca `load_content()` a JSON. Después de cada movimiento, el volcado tiene que salir idéntico.

## Fase 2 — Código modular

Cada archivo grande pasa a ser un paquete con un `__init__.py` que reexporta lo de antes, para que quien llama siga usando `render.x`, `combat.y`…

- [ ] `bot/render.py` → `bot/render/` (`character`, `combat`, `world`, `inventory`, `quests`, `crafting`, `common`).
- [ ] `bot/handlers/callbacks.py` → un enrutador por `verb` y un módulo por dominio.
- [ ] `engine/combat.py` → `engine/combat/` (`state`, `actions`, `effects`, `monster_ai`, `resolve`).
- [ ] `content/schemas.py` → `content/schemas/<domain>.py`; `content/loader.py` → `loader.py` (lectura) + `validation/<domain>.py`.
- [ ] Los tests siguen la misma forma: `tests/bot/test_handlers.py` y `tests/services/test_services.py` se parten por dominio.
- [ ] **Límite de tamaño**: un test falla si un `.py` pasa de unas 800 líneas o un YAML de unos 40 KB (con una lista de excepciones explícita).
- [ ] Mover con `git mv`, que conserva el historial, y hacer un commit por archivo partido.

## Fase 3 — Calidad automática

- [ ] **ruff** (lint + formato) en `pyproject.toml`. Primero se pasa una vez sobre todo el código, en un commit que solo formatea. Después, el hook de Claude sobre `*.py`.
- [ ] **import-linter**, que comprueba por código las invariantes 2 y 6: `engine` no importa `database`, `bot`, `ai` ni `services`; `bot` no escribe modelos; solo `ai/client.py` importa `google.genai`.
- [ ] **pyright** en modo básico para `engine/` y `services/`.
- [ ] **pre-commit**: ruff, `oath validate` si el commit toca `content/`, y un script que comprueba que la versión subió y que el CHANGELOG tiene su entrada.
- [ ] **CI en GitHub Actions** en cada push a `josue-development` y a `main`:
  - ruff, import-linter y pyright;
  - pytest con SQLite y con Postgres como servicio;
  - `oath simulate --level 1-5`.
  - Antes de llevar nada a `main` tiene que estar en verde.
- [ ] **Coherencia del contenido**: todo objeto se puede conseguir, todo monstruo aparece en algún lugar, todo PNJ está colocado, y precios y estadísticas están dentro del rango de su nivel.

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
