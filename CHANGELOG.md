# Changelog

Todos los cambios relevantes de Oathforge. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado `0.x.y` (ver `planning/iter.md`).

Cada versión corresponde a un commit cuyo asunto es `vX.Y.Z: resumen` y cuyo cuerpo repite esta lista.

## [0.10.58] - 2026-10-26

Lo hecho de `TODO.md` sale al archivo.

### Cambiado
- `TODO.md` queda solo con lo pendiente; las casillas hechas y la sección «Hecho» están en `planning/archivum/TODO-hecho.md` (archivo, no se lee salvo petición).
- Dos notas sueltas del final pasan a la sección «Sin clasificar».

## [0.10.57] - 2026-10-26

Structura, fase 5: la documentación deja de arrastrar lo ya hecho.

### Añadido
- `planning/archivum/`: lo hecho y cerrado, que no se lee salvo que se pida todo lo hecho (`AGENTS.md` lo dice y `.claude/settings.json` lo pone en `ask`).
- `planning/decisions/`: siete decisiones de arquitectura (ADR) cortas.

### Cambiado
- `CHANGELOG.md` conserva solo la serie 0.10 (de 152 KB a 84 KB); las series 0.1 a 0.9 están en `planning/archivum/CHANGELOG-0.1-0.9.md`.
- `Possibilium.md` pasa de 612 KB a 92 KB: los anexos de §32 están en `planning/archivum/Possibilium-anexos.md`, con las mismas anclas.
- `roadmap_balance.md` (fases B00–B13) y `roadmap.md` (fichas F01, F03 y F04) dejan un puntero de una línea y su texto va al archivo.

## [0.10.56] - 2026-10-26

Structura, fase 4: **protocolos.** Crear contenido ya no es copiar una ficha parecida: hay plantillas, un comando que las rellena y una skill por tipo con sus pasos de cierre.

### Añadido
- `content/_templates/` (el cargador la ignora): una plantilla comentada por tipo (`item`, `monster`, `npc`, `quest`, `zone`, `place`, `class`), el estilo común de los prompts de imagen (`prompts/style.md`, de `ars.md` §5) y el esqueleto de los `.prompt.md`. Cada plantilla es una ficha válida; lo pendiente lleva la marca `TODO(new)`.
- `oath new <tipo> <id>` (`oathforge/tools/new.py`): crea la carpeta desde la plantilla con `--zone`, `--category`, `--continent`, `--kind`, `--place`, `--giver`, `--to`, `--name` y `--desc`; deja `images/media.yaml` y un `.prompt.md` por imagen ya escrito (estilo + descripción); conecta un lugar nuevo con su hub y añade la ruta de vuelta; un PNJ trae sus 12 respaldos de diálogo. Después valida el contenido y reescribe `content/INDEX.md`.
- Ocho skills en `.claude/skills/`: `new-item`, `new-monster`, `new-city`, `new-quest`, `new-npc`, `new-class` (clase y rama de clase), `new-image` y `release`, cada una con sus pasos y su lista de cierre.
- `AGENTS.md`: tabla «quiero crear X → usa la skill Y».
- Tests (`tests/test_new.py`): cada plantilla, creada en una copia de `content/`, se carga como al arrancar el bot; el prompt lleva el estilo y la descripción; los errores de uso no escriben nada; y ningún `TODO(new)` puede quedar en `content/`.

### Cambiado
- `content/CLAUDE.md` y `CLAUDE.md` mandan a `oath new` en vez de copiar una ficha.

## [0.10.55] - 2026-10-26

Registro del hook de ruff.

### Cambiado
- `.claude/settings.json`: el hook `ruff_python.py` queda registrado junto al de contenido (pendiente de la fase 3).

## [0.10.54] - 2026-10-26

Structura, fase 1: **una carpeta por cosa.** Clases, criaturas, objetos, PNJ y misiones salen de los YAML planos y los textos de la interfaz se reparten por dominio. El volcado de `load_content()` sale idéntico al de antes.

### Añadido
- `load_folder`, `load_files` y `load_merged` en `content/loader.py`: recorren las carpetas, comprueban que los ids son únicos, nombran el archivo en cada error e ignoran las carpetas que empiezan por `_` (plantillas). Una `order: N` opcional al final de una ficha fija su posición en los menús.
- `README.md` en `content/classes/`, `content/monsters/`, `content/items/` y `content/world/` con el esquema de cada carpeta y las notas que estaban en las cabeceras de los YAML.
- Tests: cada ficha vive en la carpeta que le toca (tipo del objeto, zona del PNJ y de quien da la misión, clase de la rama) y el comportamiento del cargador (orden, plantillas, ids repetidos, errores con ruta).

### Cambiado
- `classes.yaml` → `content/classes/<clase>/class.yaml`, y `class_specializations.yaml` → `content/classes/<clase>/specializations.yaml`.
- `monsters.yaml` → `content/monsters/<id>/monster.yaml`.
- `items.yaml` → `content/items/<tipo>/<id>/item.yaml`, y `recipes.yaml` → `content/items/<tipo>/recipes.yaml` (según el tipo de su primer producto; los muebles, en `furniture/`).
- `npcs.yaml` → `content/world/<continente>/<zona>/npcs/<pnj>/npc.yaml`, con el diálogo de respaldo de cada uno en `dialogue.fallback.yaml` (en `fallbacks/dialogue.yaml` queda solo `default`).
- `quests.yaml` → `content/world/<continente>/<zona>/quests/<misión>.yaml` (la zona es la de quien da la misión).
- `oathforge/i18n/locales/{es,en}.yaml` → `locales/{es,en}/<dominio>.yaml` (`ui`, `creation`, `world`, `character`, `inventory`, `crafting`, `quests`, `combat`, `bestiary`, `activities`); `translator.flat` los une y falla si una clave está en dos archivos.
- `content/INDEX.md` apunta a la ruta real de cada ficha.
- Los mensajes de validación del diálogo de respaldo nombran el archivo del PNJ.
- `tests/test_sizes.py`: salen de la lista de archivos grandes `classes`, `class_specializations`, `quests` y los dos locales.
- `AGENTS.md` y los `CLAUDE.md` de `content/` y `bot/`: las rutas nuevas.
- Dos cosas cambian de sitio sin que el contenido cambie: las misiones `tut_chapel` y `old_tusk` comparten `order: 10` y ahora el diario las lista por id; y las recetas del mismo oficio y rango van agrupadas por categoría en vez de por el orden del archivo antiguo.
- Las tiendas siguen en el `shop` de su PNJ (el modelo ya las guarda ahí), no en el `place.yaml`.

## [0.10.53] - 2026-10-26

Structura, fase 3: **la calidad se comprueba sola.** Linter, contratos de imports, tipos, pre-commit y CI.

### Añadido
- **ruff** como linter (reglas `E F W I UP B`) y su hook de Claude, `.claude/hooks/ruff_python.py`: al editar un `.py` lo arregla y formatea, y devuelve al agente lo que no puede arreglar solo.
- **import-linter** (`lint-imports`): el motor no importa base de datos, servicios, bot, IA, Telegram ni SQL; servicios, contenido y base de datos no suben a Telegram; solo `ai/client.py` habla con Gemini.
- **pyright** en modo básico para `engine/` y `services/`.
- **pre-commit** (`.pre-commit-config.yaml`): ruff, `oath validate` si el commit toca `content/`, y `tools/check_release.py`, que exige versión nueva, su entrada en el CHANGELOG y el asunto `vX.Y.Z: `.
- **CI** en GitHub Actions (`.github/workflows/ci.yml`): ruff, import-linter, pyright, `oath validate` y pytest con SQLite y con Postgres, en cada push a `josue-development` y a `main`.
- `tests/test_layers.py`: el bot no escribe modelos (invariante 2).
- `tests/test_coherence.py`: todo objeto se puede conseguir, todo monstruo vive en algún lugar, todo PNJ está colocado y el equipo de más nivel no es más barato.
- `.git-blame-ignore-revs` con el commit que solo formateó (0.10.52).

### Cambiado
- `Content.progression` es obligatorio (el loader siempre lo carga).
- `pyproject.toml`: las herramientas nuevas en las dependencias de desarrollo y su configuración.
- `AGENTS.md`, `CLAUDE.md` y los `CLAUDE.md` de `tests/` y `engine/`: cómo correr cada comprobación.
- `planning/structura.md`: fase 3 hecha; lo que queda de parte de Josue y la siguiente, la 1.

### Arreglado
- El bot cambiaba `user.language` por su cuenta; ahora lo hace `characters.set_language`.
- Una acción libre de mover, usar o completar una misión sin objetivo, o una prueba sin habilidad, ya no falla: no tiene efecto.
- Si un personaje o una actividad desaparecen mientras la IA escribe (una crónica, una respuesta de PNJ), el servicio lo nota en vez de fallar.
- Imports sin usar, variables muertas y nombres ambiguos que señaló el linter.

## [0.10.52] - 2026-10-26

Structura, fase 3: todo el código pasa por ruff format. Solo formatea; no cambia nada más.

### Añadido
- `pyproject.toml`: configuración de ruff (líneas de 120, Python 3.12, sin `migrations/versions`, `content/` ni `artifacts/`) y ruff en las dependencias de desarrollo.

### Cambiado
- `ruff format` sobre `oathforge/`, `tests/`, `migrations/env.py` y los hooks: 122 archivos. El árbol sintáctico de cada archivo es idéntico al de antes (solo cambian espacios dentro de los docstrings).

## [0.10.51] - 2026-10-26

Structura, fase 2 cerrada: límite de tamaño y graphify tras cada merge.

### Añadido
- `tests/test_sizes.py`: falla si un `.py` de `oathforge/` o `tests/` pasa de 800 líneas o un YAML de 40 KB. Las excepciones (`classes`, `class_specializations`, `quests`, `fallbacks/chronicles` y los locales) esperan a la fase 1, y el test avisa cuando una ya cabe.

### Cambiado
- `CLAUDE.md` y `AGENTS.md`: después de cada merge a `main` se regenera el grafo del código con `/graphify . --update`.
- `AGENTS.md` y `tests/CLAUDE.md`: el nuevo mapa (paquetes en vez de archivos grandes), dónde van los helpers de los tests, cómo parchear un paquete partido y el límite de tamaño.
- `planning/structura.md`: fase 2 hecha (adelantada a la 3 y la 1); siguiente, la 3.

## [0.10.50] - 2026-10-26

Structura, fase 2: los botones y los tests grandes, partidos por dominio.

### Cambiado
- `oathforge/bot/handlers/callbacks.py` pasa a `oathforge/bot/handlers/callbacks/`: `router` (entrada y verbos que solo muestran), `views`, `acts` (lo que cambia estado), `rolls` (la 🎲 manual y los ajustes) y `combat`.
- `tests/bot/test_handlers.py` (1.100 líneas) se parte en `helpers.py`, `conftest.py` (sin límite de frecuencia) y `test_flow`, `test_creation`, `test_combat_buttons`, `test_views` y `test_activities`.
- `tests/services/test_services.py` (877 líneas) se parte en `helpers.py` (`new_character`, `get_char`, `fight`) y `test_characters`, `test_exploration`, `test_inventory`, `test_combat_service`, `test_quests`, `test_npcs` y `test_hunting`.
- Los tests que cambian `rate_ok` o `DICE_SECONDS` parchean el submódulo donde viven.
- `oathforge/bot/CLAUDE.md` explica el reparto de los botones.

## [0.10.49] - 2026-10-26

Structura, fase 2: la validación del contenido sale del loader.

### Cambiado
- `oathforge/content/loader.py` se queda con la lectura (216 líneas). Las referencias cruzadas pasan a `oathforge/content/validation/`, una función por dominio: `classes`, `world`, `items`, `crafting`, `fallbacks` y `quests`. `validate_references` las corre todas y falla con todos los errores a la vez.
- Los errores son los mismos que antes (comprobado rompiendo el contenido de once maneras); solo cambia el orden en que se listan.
- `content/CLAUDE.md` y los tests que usaban las funciones de validación apuntan a `validation/`.

## [0.10.48] - 2026-10-26

Structura, fase 2: los esquemas del contenido partidos por dominio.

### Cambiado
- `oathforge/content/schemas.py` (903 líneas) pasa a `oathforge/content/schemas/`: `common`, `classes`, `items`, `monsters`, `professions`, `world` y `quests`. `schemas/__init__.py` lo reexporta todo y `load_content()` da exactamente lo mismo.

## [0.10.47] - 2026-10-26

Structura, fase 2: el combate del motor partido en un paquete.

### Cambiado
- `oathforge/engine/combat.py` (1.138 líneas) pasa a `oathforge/engine/combat/`, un módulo por etapa: `state` (constantes, modelos, consultas y fin del combate), `resolve` (salvaciones, ataques, daño, estados y curación), `entities` (invocaciones y formas), `turns` (inicio, flujo de turnos y turno enemigo) y `actions` (el turno del jugador). Las dependencias van en ese orden.
- `combat/__init__.py` reexporta lo público y los pasos privados que usan los tests del motor; `oath simulate` y `oath balance` dan los mismos números.
- `oathforge/engine/CLAUDE.md` explica el reparto.

## [0.10.46] - 2026-10-25

Structura, fase 2: `render.py` partido en un paquete.

### Cambiado
- `oathforge/bot/render.py` (2.339 líneas) pasa a `oathforge/bot/render/`, un módulo por familia de pantallas: `common`, `character`, `crafting`, `world`, `inventory`, `quests` y `combat`. Ninguno pasa de 610 líneas.
- `render/__init__.py` reexporta todo: quien llama sigue usando `render.x` y nada cambia para el jugador.
- Las piezas que usaban varias pantallas (iconos, `RULE`, `item_stats`, `journal_tabs`, `rule_numbers`, `_go_button`) suben a `render/common.py`, y las dependencias entre módulos van en un solo sentido.
- `AGENTS.md` y `oathforge/bot/CLAUDE.md` explican el reparto.

### Eliminado
- El import sin usar de `engine.progression` en `render`.

## [0.10.45] - 2026-10-25

Structura: grafo del código con graphify.

### Añadido
- `.graphifyignore`: el grafo de graphify cubre solo `oathforge/` y `tests/`, sin contenido, planificación, locales ni Markdown. Sale del AST y no gasta tokens de IA.

### Cambiado
- `AGENTS.md`: cómo consultar el grafo (`/graphify query`) y regenerarlo (`/graphify . --update`).
- `planning/structura.md`: graphify instalado y su grafo generado; de la fase 0 solo queda borrar las ramas antiguas.

## [0.10.44] - 2026-10-25

Structura: el plan se puede retomar desde cualquier chat.

### Cambiado
- `CLAUDE.md`: sección «Structura», que manda a `planning/structura.md` cuando la tarea es ordenar el proyecto.
- `planning/structura.md`: sección «Cómo continuar» (pasos para cerrar una fase) y las decisiones ya tomadas, con el porqué de cada permiso de `.claude/settings.json`.

## [0.10.43] - 2026-10-25

Structura, fase 0: **el proyecto se prepara para crecer.** Reglas cerca de donde se trabaja, contenido comprobado al editarlo y un índice para encontrar cualquier id sin abrir YAML grandes. Oathforge pasa a ser un proyecto de una sola persona.

### Añadido
- `planning/structura.md`: la checklist por fases para crecer ordenado (contenido en una carpeta por entidad, archivos grandes partidos, calidad automática, protocolos para crear objetos, monstruos y ciudades, y herramientas para agentes).
- **`oath validate`**: carga `content/` como al arrancar el bot y dice qué falla, sin Telegram ni BD.
- **`oath content-index`** y `content/INDEX.md`: una línea por id de contenido con su nombre en inglés y su archivo. Un test comprueba que está al día.
- `CLAUDE.md` por zona (`content/`, `oathforge/engine/`, `oathforge/services/`, `oathforge/bot/`, `tests/`), con sus reglas; solo se cargan al trabajar allí.
- `.claude/settings.json`: permisos para las pruebas y los comandos de consola habituales; leer `artifacts/` y `content/officina/` pide confirmación; `.venv/`, `.env` y `.telegram/` no se leen.
- Hook de Claude Code (`.claude/hooks/validate_content.py`): al editar un `content/*.yaml`, ejecuta `oath validate`, devuelve los errores y actualiza `content/INDEX.md`.
- `AGENTS.md`, «Nombres e idiomas»: la base (ids, código, archivos, claves) va en inglés y todo texto visible en es y en. Un test exige ids y rutas de `content/` en ASCII.

### Cambiado
- `CLAUDE.md`: una sola rama, `josue-development`; desaparecen la tabla de ramas por persona y la excepción de los testers. `CODEOWNERS`, `README.md`, `TODO.md` y `planning/README.md` dejan de mencionar los TODO de testers.
- `.gitignore`: `graphify-out/` (grafo local del código).

### Eliminado
- `TODO-rayko.md` y `TODO-edian.md`, que estaban vacíos.

## [0.10.42] - 2026-10-25

0.10-I (B13 cerrado, B14 en marcha): **ensayo del reinicio de lanzamiento en staging** y primer repaso jugado de `tests/features.md`.

### Añadido
- `planning/reinicio_lanzamiento.md`: el ensayo completo (`launch-reset` en seco, `backup`, `launch-reset --yes`, `restore`) hecho en staging contra una copia de la base local, con sus conteos; las 24 tablas coinciden tras la restauración. Queda solo el ensayo con una copia de producción real (B14).
- `tests/features.md`: marcadas las casillas comprobadas jugando con un Guerrero en inglés (creación de personaje, teclado fijo, escena, mapa, viaje, tienda, diálogo, combate, seis de las diez misiones del tutorial).

### Arreglado
- Dos pistas de misión en `content/quests.yaml` (ES/EN, *Bloodroot* e *Iron for the Guard*) decían que recolectar o minar en el tutorial «termina al momento»; desde B08 esos tiempos son reales (4 min). El texto ahora dice la duración correcta.

### Cambiado
- `planning/plan_implementacion_0.10.md`: B13 pasa a "ensayado en staging con una copia de la base local; falta solo con datos de producción reales".

## [0.10.41] - 2026-10-25

0.10-I (B13): **se retira la cripta y se prepara el reinicio de lanzamiento.** El juego ya no tiene mazmorra ni el hilo del relicario; la campaña es la de Tamsin y el valle. El reinicio que conserva a las personas está implementado y ensayado en pruebas, pero **no se ha ejecutado**.

### Eliminado
- La **Cripta Hundida** entera (cinco salas), el Esqueleto de la cripta, el Guardián de la Cripta (Ser Aldren), el relicario sellado, las misiones *El relicario sellado* y *Huesos inquietos*, los escalones ocultos del Bosque de los Susurros y la bandera `crypt_unlocked`.
- Los logros del relicario y de la cripta se sustituyen por los de la nueva edición: **El valle se abre** (abrir el valle), **Cobrador cobrado** (derrotar al Recaudador, con título), **Los hechos primero**, **Un cuento de fantasmas** y **Un trato callado** (decisiones escritas del rumor y del agua). El metalogro *Guardián de Crownreach* y *Volví por ti* pasan al Recaudador.
- Del reglamento, de las guías y de los textos de los PNJ, toda mención a la cripta y al relicario (Mira, Holt, Ysolde, Tessa, Pell y Bram hablan ahora de las órdenes falsas).

### Añadido
- **`oath launch-reset`** (`oathforge/services/launch.py`): borra la partida y conserva cuentas con sus ajustes generales, el presupuesto de IA, las imágenes y la auditoría. En seco por defecto; con `--yes` escribe una copia, borra, comprueba que no queda ninguna referencia colgando y confirma.
- **`oath backup` y `oath restore`**: volcado lógico de toda la base en un archivo JSON y su restauración exacta (ids, fechas y secuencias de PostgreSQL).
- `planning/reinicio_lanzamiento.md`: qué se borra, qué se queda, el procedimiento, el plan de vuelta atrás y el ensayo hecho.
- Una **mazmorra de pruebas** (`tests/ruins.py`) para las pruebas del motor (salas con combate fijo, ruta oculta, cama gratis, jefe y descubrimientos), que antes usaban la cripta.
- Cinco pruebas del reinicio y la copia (en PostgreSQL cuando hay base de pruebas).

### Cambiado
- Las decisiones escritas de la campaña emiten su logro por la bandera que dejan (`DECISION_FLAGS`), no por un nombre de misión.
- La conducta de los PNJ de la ciudad y la clase de clérigo ya no hablan de la cripta.

### Pendiente
- El **ensayo en staging con una copia de producción** (hace falta una base real); el README raíz sigue nombrando la cripta (se rehace al final, B14).

## [0.10.40] - 2026-10-25

0.10-I (B12): **balance integral.** Se mide la campaña, no un jabalí: clases y ramas contra encuentros de su nivel, dos políticas, un equipo razonable, secuencias y un modelo de ritmo. El informe está en `planning/informe_balance_0.10.md`.

### Añadido
- **`oath balance`** (`oathforge/tools/balance.py`): matriz de 14 clases (niveles 1, 3, 5 y 9) y 41 ramas (10, 13, 17 y 20) contra rival débil, estándar, élite, pareja y jefe; política básica frente a informada; intervalos de Wilson al 95 %; secuencias de combates con descansos cortos; duración por rol; defectos con suelos; modelo de ritmo con dos sesiones diarias; informe con versión, commit, semilla y limitaciones. Usa todos los núcleos.
- **Simulador**: `--policy basic|informed` (la informada se defiende al aviso del jefe, bebe pociones, guarda el recurso para la ventana expuesta), `--kit t1` (la pieza de nivel 10 del gremio), pociones mayores desde el nivel 10 y secuencias que arrastran vida y recurso.
- **Tres criaturas** para los niveles 6–9 (sabueso de ceniza, cobrador del peaje, sargento del peaje) en el Puesto de Peaje Abandonado: no había nada entre el Viejo Colmillo y el nivel 11.
- Pruebas de la herramienta (intervalos, celdas reproducibles, kit, secuencias, informe y modelo de ritmo).

### Cambiado
- Custodio de las Balizas: 200 PV (antes 230) y menos daño, porque las ramas de lanzador ganaban 0 %; el Recaudador de Ceniza descarga más fuerte (4d6+5) para que ignorar la señal duela.
- XP de las misiones del valle al 70 %: antes casi todo el camino al nivel 20 salía de las misiones.

### Hallazgos (ver el informe)
- El ritmo es unas seis veces más corto que la meta: unas 6 horas de juego dirigido, ≈ 2,4 días a dos sesiones de 75 min, frente a 15–20 días. Hay que ampliar contenido, alargar tiempos o bajar la meta.
- Luz, Pirómano, Tirador y Tejemareas no llegan al 35 % contra el Custodio, y 35 parejas del mismo nivel quedan por debajo del 55 %, sobre todo lanzadores. No se tocó su diseño.

## [0.10.39] - 2026-10-25

0.10-I (B11): **el Valle de la Fragua Gris, de los niveles 11 al 20.** Región provisional (nombre y lore pendientes de que Josue los apruebe) con ocho lugares, doce criaturas, tres PNJ y once misiones hasta la prueba final.

### Añadido
- **Región** `greyforge_vale`: Cruce de los Carreteros, Puesto del Vado (refugio: descanso, curandera y tienda; no sustituye a Crownreach), Cantera de Ceniza, Bosque de las Astas, Aserradero Silencioso, Ribera del Vidrio, Taller del Regulador y Alto de las Balizas. La puerta es la entrega del Ciervo (`valley_open`) y todo el grafo tiene camino de vuelta a Crownreach. Recursos de T1 (hierro profundo, corazón de roble, seda, piedra en bruto, hojas de luna, musgo de reposo) en la cantera, el bosque y la ribera.
- **Doce criaturas** de los niveles 11 a 20 (contrabandista y ballestero de ceniza, reptante de cantera, lobo astado, cervato de hierro, leñador desbocado, autómata de sierra, anguila de vidrio, acechador de esquirlas, centinela del regulador, guardián de baliza y **el Custodio de las Balizas**). Centinela, guardián y Custodio usan patrón de jefe (placa, aviso, recarga); el Custodio se endurece de nuevo a media vida.
- **Tres PNJ** con respaldos de diálogo ES/EN: Orsa Vael (refugio y tienda), Kellan Brack (cantera) e Iwen Sorrel (balizas).
- **Once misiones** en cuatro actos: *Seguir la carga* (llegar al valle, cargamento sin papeles, la cantera), *Lo que sostiene el valle* (el agua de la cantera con decisión y reputación, las astas, el aserradero, hierbas y vidrio), *Las balizas rotas* (los centinelas del taller, encender la primera baliza en tres pasos, los guardianes de la loma) y *Culminación* (la prueba de las balizas, a nivel 20, con entrega a Iwen).
- Núcleo de regulador (objeto de misión): lo sueltan siempre los centinelas.
- Pruebas: grafo conectado con ida y vuelta, puerta cerrada sin la bandera, refugio, cadena de misiones, objetivos alcanzables donde dice el texto, núcleos suficientes para la reparación y la decisión del agua.

### Cambiado
- El Ciervo de Hierro ahora abre el valle (`valley_open`).
- La prueba del simulador de «daño por ronda mayor que cero» sólo vale para criaturas de hasta 40 PV.

### Pendiente
- El nombre y la historia del valle son provisionales (N02); falta tu aprobación.
- Once misiones regionales, no las 18–24 de la semilla; no hay contratos repetibles ni misiones secundarias.
- Los contextos de los modificadores 13 y 17 son los combates normales del valle; no hay encuentros hechos a medida.
- Retratos reales (doce marcadores de posición) y de Orsa, Kellan e Iwen.
- Balance de las criaturas con el simulador (los pares de centinelas y guardianes son duros); se ajusta en B12.

## [0.10.38] - 2026-10-25

0.10-I (B10): **el Ciervo de Hierro y la graduación.** Del nivel 10 al hito `iron_stag` (tope 20): elegir rama, recibir una pieza de nivel 10, leer las señales y vencer al jefe con lo que has escogido.

### Añadido
- **El Ciervo de Hierro** y la **Hondonada del Ciervo** (al fondo de la Arboleda Antigua): coraza que absorbe daño, **carga anunciada** (baja la cabeza un turno antes), ventana de **vulnerabilidad** tras cargar y, a media vida, **se endurece una vez más** (`rearm`). Defenderse debilita la carga.
- **💡 ¿Qué hago?** en el panel de combate: reglas y plantillas, sin IA. Lee el combate (avisa, recarga, placa, poca vida) y nombra las habilidades de **tu** clase que sirven (curar, protegerse, golpear). Un popup, sin gastar acción.
- Acto VII: **Tu camino** (elegir rama en el gremio, nivel 10), **Equipo para la hondonada** (Tamsin ofrece una pieza de nivel 10 a elegir, sin exigir conjunto completo), **Señales en la arboleda** (examinar los troncos) y **El Ciervo de Hierro** (entrega a Tamsin: hito `iron_stag`, XP, poción mayor).
- El simulador bebe pociones por debajo del 40 % de vida (2 de preparación) y se defiende cuando el jefe avisa.
- Pruebas: mecánica del Ciervo, reglas de la ayuda en ES/EN, cadena de la graduación, piezas del equipo y un suelo del 20 % para las **41 ramas** al nivel 10.

### Pendiente
- Retrato real del Ciervo (marcador de posición).
- Las ramas de lanzador de fuego, hielo y arcano rondan el 40–50 % contra el Ciervo en el simulador; se ajusta en B12.
- La región cercana a la que apunta la entrega («el valle») es el B11.

## [0.10.37] - 2026-10-25

0.10-I (B09, cierre): **la campaña común hasta el Recaudador de Ceniza.** Del tutorial al nivel 10 sin callejones: 21 misiones nuevas, el mentor y un jefe que avisa sus golpes. Las decisiones de mentor y trama las tomé yo como provisionales (Josue las revisará, y el refactor de Vale e instructor queda para después).

### Añadido
- **Tamsin Harrow, «la Linterna»**, exploradora del Gremio (de día en el Gremio, de noche en la taberna), con persona, saludos y doce respaldos de diálogo ES/EN.
- **Actos I–VI** (`quests.yaml`): Una entrega sospechosa → Lo que se lleva puesto → Lo que se guarda → Elige tu mano → ocho encargos de oficio (uno por oficio, con el material y las primeras lecciones que da su maestro) → Rastros en el barro → Hierbas para el camino → Una caña y una sartén → Rumor o hecho (decisión con reputación) → Pociones para el camino → Volver también es vencer (libro de cargas, humo, curación) → La mesa de Tamsin (tres pistas con botones) → El Recaudador de Ceniza.
- **El Recaudador de Ceniza** y el **Puesto de Peaje Abandonado** (nuevo lugar del Camino del Viejo Rey). El jefe lleva una **placa** que se desgasta con cualquier daño, **avisa** su disparo fuerte un turno antes, descarga y **recarga expuesto**; al romperse la placa avisa más a menudo. Defenderse debilita el disparo. El panel muestra la placa y su intención. Entrega a Tamsin: hito `ash_collector` (tope de nivel 10), 600 de XP.
- Motor: mecánica de jefe con patrón (`pattern` en el monstruo), efecto `profession_xp`, `unlock_profession` en las misiones y el objetivo `short_rest` (los de 0.10.36 ya estaban).
- Objetos de misión: libro de cargas del peaje y prueba de falsificación. La bomba de humo se vende en la forja de Tessa (fuente siempre recuperable).
- Pruebas del jefe (aviso, descarga, recarga, placa) y de la campaña (cadena entera, llegada al jefe, material suficiente en cada oficio, decisión con reputación a ambos lados, humo siempre disponible).

### Cambiado
- El Viejo Colmillo ya no paga 80 de oro: queda como caza opcional con su botín y su XP.
- El simulador cuenta el daño a la placa como daño al jefe.

### Pendiente
- Retratos reales del Recaudador y de Tamsin (hay un marcador de posición, `TODO-images.md`).
- Los casters siguen flojos contra el jefe en el simulador (Chamán 60 % al nivel 9): se ajusta en B12.
- Las tres tareas de cada oficio son una misión con tres objetivos, no tres misiones; son ≈ 33 misiones entre tutorial y campaña.

## [0.10.36] - 2026-10-25

0.10-I (B09, 1.ª parte): **objetivos de misión que nacen de los servicios.** Es el motor de la campaña hasta el Recaudador; el texto del mentor y de los actos queda a la espera de la aprobación de `planning/mundus.md`.

### Añadido
- Nueve tipos de objetivo: `equip`, `buy`, `sell`, `stash` (guardar en el cofre), `take` (sacar), `learn_profession`, `blueprint`, `smoke` (salir de un combate con una bomba de humo) y `branch` (elegir rama). Cada uno lo emite el servicio correspondiente, nunca una frase de la IA; `equip`, `buy`, `sell`, `stash`, `take`, `smoke` y `branch` aceptan `any`.
- El cargador valida sus objetivos (objeto, oficio o rama existentes) y hay textos ES/EN para el diario.
- Prueba de que equipar, comprar, vender, guardar y sacar avanzan una misión.
- Propuesta provisional del mentor (Tamsin Harrow) y de la trama «Los nombres que faltan» en `planning/mundus.md`, para aprobar antes del texto final.

## [0.10.35] - 2026-10-25

0.10-I (B08): **tiempos reales, descanso corto y derrota con tope.** Se acaban las ayudas de beta: el descanso y el tutorial llevan su tiempo y las pociones cuestan lo que valen.

### Añadido
- **Tabla de tiempos en un solo sitio** (`engine/timings.py`): recolección 4 min, expedición 15, rastreo 3, descanso largo 15, descanso corto 3. El reglamento y el panel de Actividades leen esa misma tabla.
- **Descanso corto** (💤 en Actividades, en cualquier sitio, gratis): al terminar da un 30 % de la vida (sin pasar del tope de las heridas graves) y parte de la barra o un uso gastado; no cura heridas graves. Solo dos entre dos descansos largos, que los devuelven. Abandonarlo no da nada.
- La actividad guarda la herramienta con la que empezó: **no se puede vender la única que estás usando**.
- Pruebas: descanso largo con su tiempo, descanso cancelado, doble cobro, descansos cortos limitados, venta de la herramienta en uso y tope de la derrota.

### Cambiado
- **Derrota**: el 10 % del oro con un tope de 15 por nivel (y nunca deuda). Sigue sin quitar equipo ni compañeros.
- «Curar heridas» de la Capilla cuesta 3 de oro; quien lleva menos paga lo que tenga, así que nadie se queda atascado sin oro.
- Pociones de curación (20) y de maná (60) a su precio normal.
- Textos del reglamento, de las misiones del tutorial y de Actividades sin referencias a la beta ni a «ocho horas de sueño».

### Eliminado
- `beta_instant_rest` y `beta_instant_tutorial` (config), el atajo `tutorial_boost` de las misiones y los textos y pruebas que los acompañaban.

### Pendiente de B08
- Stock crítico y cobertura T0/T1 de herramientas para todas las clases (se revisa con la campaña, B09).

## [0.10.34] - 2026-10-25

0.10-I (B07, lote C): **las 41 ramas ya se pueden elegir.** Este lote cierra B07 con las nueve de entidades, formas, tótems y tiempo.

### Añadido
- **Nueve ramas listas**, con su recorrido del 10 al 20: Invocador, Cronomante, Cambiaformas, Demonólogo, Nigromante, Señor de Bestias, Artillero, Maestro de Constructos y Guardián Ancestral.
- Seis entidades nuevas (Siervo exhumado, Horda de huesos, Espíritu de la tormenta, Autómata de arco, Autómata titán, Tótem protector) y dos formas (ent y bestia primigenia).
- Cronomante: adelantar los enfriamientos propios (`reduces_cooldowns`) y trabar o aturdir al rival.
- Constructos y tótems son una elección: solo cabe uno a la vez (guardián o autómata de arco; tótem que asusta o que protege).
- Prueba de que no queda ninguna rama sin terminar.

## [0.10.33] - 2026-10-25

0.10-I (B07, lote B): **doce ramas más.** Con las veinte del lote A son 32 de las 41 las que ya se pueden elegir; este lote reúne la curación, la regeneración, las melodías, las reacciones y el control.

### Añadido
- **Doce ramas listas**, con su recorrido entero del 10 al 20: Redentor (Paladín), Dominio de la Vida, de la Luz y de la Guerra (Clérigo), Guardián del Bosque y Círculo de las Esporas (Druida), Cantor de Guerra e Ilusionista (Bardo), Armero Rúnico y Catalizador (Artífice), Elementalista y Tejemareas (Chamán).
- Curar de verdad es una decisión: barreras de PV temporales tras la curación, robo de vida acotado, curación como acción adicional y una Absolución o Santuario al 20.
- Controlar y aprovechar el control: aplicar miedo, deslumbre, esporas o trabas y gastarlos después por daño extra, como ya hacían las marcas.
- Los lanzadores heridos recuperan recurso (`resource_on_hurt` también en Dominio de la Guerra, Esporas, Elementalista y Tejemareas): sin ello se quedaban sin barra a los dos turnos.

### Cambiado
- El simulador cura con la acción principal cuando va por debajo de un tercio de PV (antes solo usaba las curaciones de acción adicional).

## [0.10.32] - 2026-10-25

0.10-I (B07, lote A): **por fin se puede elegir una rama de clase.** Veinte de las 41, las de daño, marcas, defensa y maniobras, ya tienen su recorrido entero del nivel 10 al 20.

### Añadido
- **Veinte ramas listas**, cada una con una pasiva y una técnica al 10, un desarrollo fijo al 15, dos modificadores a elegir en el 13 y otros dos en el 17, y una técnica culminante al 20: Vengador, Custodio Sagrado e Inquisidor (Paladín); Maestro de Batalla y Baluarte (Guerrero); Berserker y Coloso (Bárbaro); Asesino, Duelista y Saboteador (Pícaro); Puño de Hierro y Danzante de Sombras (Monje); Piromante, Criomante, Arcanista y Tempestario (Hechicero); Tirador (Explorador); Filo Maldito (Brujo); Sangre y Escarcha (Caballero de la Muerte). Las 21 restantes siguen sin poder elegirse y `/path` lo dice.
- **Gastar un estado** (`consumes`): una técnica puede gastar una marca, una quemadura, una traba o un sello del objetivo a cambio de daño extra. Dejar que siga corriendo o gastarlo es la decisión del Vengador, el Piromante, el Criomante, el Maestro de Batalla, el Tirador o el Caballero de Escarcha.
- **Represalia** (`thorns`, `resource_on_hurt`): una pasiva que responde a una herida real —el atacante recibe daño, la barra se llena—. Una vez por ataque, solo si el golpe hirió de verdad y sin que la respuesta se responda a sí misma. Para el Custodio, el Baluarte, el Coloso, la Sangre y el Tempestario.
- **Robo de vida acotado** (`leech_pct`): cura una parte del daño real que hizo la técnica, nunca más de la vida máxima ni de un golpe fallado. Para la Sangre.
- **Reducir enfriamientos** (`reduces_cooldowns`) y **barrera al curar** (un `temp_hp` en una curación solo si curó de verdad).
- **Los modificadores pueden cambiar dados**, no solo costes y duraciones: «Veredicto pesado» cambia 3d8 por 5d8. Un parche solo sustituye lo que la habilidad ya tenía: no inventa una mecánica.
- **Los trucos de los lanzadores escalan con el nivel** (`damage_tiers`): el Rayo de Fuego, la Llama Sagrada, el Látigo de Espinas, el Estallido, la Burla, la Descarga y la Chispa pasan a 2, 3 y 4 dados en los niveles 5, 11 y 17. Sin esto los lanzadores se quedaban sin nada que hacer al agotar el Maná.
- **El Filo Maldito pelea con CAR** (`attack_with`), como pedía su identidad.
- El **simulador** juega con rama, entrenamientos y modificadores (`oath simulate --branch avenger --level 10-20`) y sabe invocar, ordenar, converger y transformarse.
- Más estados que una técnica puede aplicar: vulnerable, envenenado, ardiendo y sangrando.

### Cambiado
- `/path` ofrece de verdad las ramas listas de tu clase y deja las otras bloqueadas.
- Las pruebas de ramas ya no dan por hecho que ninguna esté lista: usan ramas sintéticas.

## [0.10.31] - 2026-10-25

0.10-I (B06, 3.ª parte): cierre de las clases base. Llegan el Explorador, el Artífice, el Chamán y el Caballero de la Muerte, y el Brujo pasa a su barra. **Ya son catorce, todas con su recurso y habilidades de nivel 1 a 9.**

### Añadido
- **Explorador** (Foco): dispara con el arco. *Disparo certero*, *Marca de presa* (cada golpe suma un dado perforante), *Paso del bosque*, *Lluvia de flechas*, *Bálsamo del bosque*, *Disparo doble*, *Flecha envenenada*, *Ojo de halcón* y *Tormenta de flechas*.
- **Artífice** (Carga): un aparato que carga y descarga, sin pociones ni oficio de Alquimia. *Descarga del aparato*, *Pulso restaurador*, *Reactivo corrosivo*, *Espuma protectora*, *Sobrecarga*, *Armamento arcano*, *Reacción en cadena*, *Blindaje reforzado* y *Gran descarga*.
- **Chamán** (Maná): *Chispa elemental*, *Piel de piedra*, *Marea sanadora*, *Agarre de tierra*, *Latigazo de escarcha*, *Resguardo de los espíritus*, *Cadena de tormenta*, *Cuero de tierra* y *Llamada de la tempestad*.
- **Caballero de la Muerte** (Poder rúnico): sus golpes cargan el poder que luego descarga. *Golpe de muerte*, *Runa protectora*, *Sorber vitalidad*, *Cadenas de escarcha*, *Hoja rúnica*, *Aniquilar*, *Voluntad impía*, *Despiadado* y *Ráfaga aullante*.
- **Brujo** (Esencia) con *Drenar vida*, *Piel de sombra*, *Hambre del vacío* y *Desgarro de alma*.
- Los prompts de los seis retratos pendientes en `TODO-images.md`.

### Cambiado
- El **reglamento** explica la barra de clase, nombra las catorce clases y manda a `/path`; ya no habla de usos por descanso ni de que las especializaciones «llegarán más adelante».
- `planning/ordines.md` recoge la tabla de las catorce clases con su recurso y su identidad de los niveles 1 a 9.
- El **Poder rúnico** parte de una base de 2, como la Convicción, para que el primer golpe sea posible.
- Ya no hay clases «futuras» en `progression.yaml`: la lista queda vacía.
- La prueba de las clases (`test_class_roster.py`) ya no tiene lista de pendientes: exige lo mismo a las catorce.

## [0.10.30] - 2026-10-25

0.10-I (B06, 2.ª parte): los lanzadores. El Clérigo, el Hechicero, el Druida y el Bardo dejan los usos por descanso y pasan a su barra, con habilidades de nivel 1 a 9.

### Añadido
- **Clérigo, Hechicero y Druida (Maná)**, y **Bardo (Resonancia)**, con cuatro o cinco habilidades nuevas cada uno: *Plegaria sanadora*, *Rayo guía*, *Resguardo sagrado* y *Columna de luz*; *Lanza de hielo*, *Maestría arcana*, *Nova gélida*, *Resguardo arcano* y *Cono de frío*; *Piel de corteza*, *Enjambre punzante*, *Rebrote* y *Tormenta de espinas*; *Susurros disonantes*, *Acorde estremecedor*, *Bis* y *Virtuoso*.
- La **Resonancia** del Bardo empieza vacía y se construye con su burla, su ataque y cada turno; su estribillo la gasta de golpe.

### Cambiado
- Los textos de estas cuatro clases hablan del Maná y la Resonancia en lugar de «dos usos por descanso» o «ilimitado».
- Los nombres de habilidad nuevos llevan las mismas mayúsculas que los antiguos.
- Quedan solo el Brujo con usos por descanso: es el último de la lista, y se rehace con el siguiente grupo.

## [0.10.29] - 2026-10-25

0.10-I (B06, 1.ª parte): las clases marciales. Llegan el Bárbaro y el Monje y se rehacen el Guerrero, el Paladín y el Pícaro, todos con su propia barra y habilidades de nivel 1 a 9.

### Añadido
- **Bárbaro** (Furia): se enciende atacando y empieza cada combate en cero. *Defensa sin armadura*, *Golpe temerario*, *Furia* (bendición y PV temporales), *Golpe de barrido*, *Asalto implacable*, *Instinto brutal*, *Golpe salvaje* y *Pisotón atronador*.
- **Monje** (Foco): golpea con DES y se viste de disciplina, sin armadura (CA 10 + DES + 3). *Ráfaga de golpes*, *Golpe aturdidor*, *Desviar golpes*, *Respiración serena*, *Mil puños*, *Cuerpo de hierro*, *Ola arrolladora* y *Foco perfecto*. Estrena las **vendas de combate**, su única arma.
- **Guerrero (Foco), Paladín (Convicción) y Pícaro (Energía)** pasan a barra y ganan hasta cinco habilidades nuevas cada uno entre los niveles 1 y 9: *Golpe poderoso*, *Embestida de escudo*, *Golpe de gracia*; *Favor divino*, *Cólera sagrada*, *Luz purificadora*; *Golpe bajo*, *Zancadilla*, *Acción astuta*, *Filo mortal*…
- **El golpe base del Paladín es ahora el *Castigo divino***, como pedía el TODO, y gasta Convicción en lugar de usos.
- **Ataques a distancia con técnica** (`ranged` en un `strike`, para quien dispara) y el estado **presa marcada**, que añade un dado perforante a cada golpe de quien la marcó.
- Una prueba que recorre **todas las clases** y exige lo mismo de cada una: barra propia, técnica distintiva y algo que pagar desde el nivel 1, nada que dependa de una rama, un aliado o un oficio, un calendario sin un botón nuevo cada nivel, victoria sobre un bandido en los niveles 1, 3, 5 y 9 y sobre una pareja de goblins desde el 5, y tres combates seguidos sin que la barra se salga de su rango.
- Las etiquetas de habilidad muestran su coste de barra («🔹 4») en vez de «ilimitado».

### Cambiado
- La **Convicción** parte de una base de 2, para que el primer Castigo divino sea posible.
- El simulador ya no sube un atributo en el nivel 4 (los entrenamientos lo sustituyeron) y entiende los ataques a distancia con técnica.
- Los retratos de las clases nuevas están pendientes (`TODO-images.md`): la ficha se muestra sin foto, como el juego ya hacía con cualquier cosa sin arte, y no se inventa ninguno.

## [0.10.28] - 2026-10-25

0.10-I (B05): aliados que combaten solos, formas y compañeros permanentes. La base técnica de las ramas complejas, todavía sin ninguna rama que la use.

### Añadido
- **Entidades** (`content/entities.yaml`): invocaciones, servidores, bestias, constructos, torretas y tótems. Actúan solas, de forma determinista, **una vez por turno de su dueño**, y nada —acción adicional, menú, reintento— las hace actuar dos veces. Cuatro roles: atacan a la presa marcada o a la más débil, golpean a toda una fila sin tirada, **absorben el daño en lugar del héroe** o acosan con un estado. Una entidad nunca es un objeto: no se compra, no se vende ni se duplica.
- **Invocar, ordenar, converger**: *invocar* trae a un aliado (como mucho **dos** a la vez, y lo ya llamado en un combate no se vuelve a llamar, ni caído: reinvocar no cura); *ordenar* lo hace actuar ahora, nombra la presa y le cuesta el turno; **Convergencia** potencia lo que hay durante unos turnos, sin añadir una tercera entidad ni un turno.
- **Formas** (`content/forms.yaml`): el Cambiaformas sustituye sus ataques por los de la forma, con una reserva acotada de PV temporales **solo la primera vez** en un combate. Alternar no cura, no apila reservas y devuelve ataques y CA al salir. Oso y pantera de arranque.
- **Compañero permanente** (`services/companions.py`): el servidor del pacto o la bestia es siempre el mismo ser, con **el nombre que le pone el jugador** (validado como dato, nunca como instrucción para la IA). Si cae, vuelve en el siguiente combate a la mitad de su vida; herido, sigue herido hasta un descanso largo.
- El panel de combate muestra **una línea por aliado** y la forma del héroe; la ficha de habilidad explica las cuatro habilidades nuevas, su coste y su enfriamiento.
- El loader valida que una invocación, una orden o una forma apunten a algo que existe, que una invocación tenga duración y que un ser permanente no caduque.

### Arreglado
- Los aliados ya no actúan si su dueño cayó o el combate acabó.

## [0.10.27] - 2026-10-25

0.10-I (B04): el camino de clase. La rama, los entrenamientos y los modificadores ya se eligen y cambian lo que el héroe puede hacer.

### Añadido
- **El catálogo efectivo único**: `characters.effective()` junta clase, rama, modificadores y entrenamientos, y es lo que leen el motor, la ficha, el descanso, las pociones, `/skill_<clave>` y la tarjeta de subida. Ya no hay listas paralelas.
- **`/path` (🧭 Tu camino)**, también desde la ficha: tu rama, las elecciones pendientes, la ficha de cada opción con lo que de verdad hace y una **confirmación definitiva** («⚠️ No se puede deshacer»). La rama se elige al **nivel 10 en el Gremio**; los entrenamientos y los modificadores, en cualquier sitio.
- **Entrenamientos en los niveles 5, 12 y 18**: dos paquetes, *Instinto afilado* (+1 a atacar y a la CD) y *Temple* (+8 PV y +2 de barra). Los PV nuevos son reales y no curan el resto; la barra no se rellena.
- **Modificadores** (13 y 17): dos opciones fijas por nivel que afinan una habilidad (coste, enfriamiento, duración) o conceden otra nueva.
- **Segunda elección gratuita**, una sola vez, si una actualización cambia de forma sustancial cómo juega tu rama (`revision`). Deshace los modificadores y conserva los entrenamientos.
- El loader exige que una rama esté **completa para estar lista**: pasiva y técnica del 10, técnica culminante del 20 y exactamente dos modificadores en cada nivel de elección. Y que ninguna rama reutilice la clave de otra habilidad.

### Cambiado
- **Se retira la mejora de atributo del nivel 4** y el aviso de «pronto podrás elegir una especialización» del 5: los sustituyen los entrenamientos y el aviso del 10. El reglamento lo explica con las cifras del motor.
- Las elecciones pendientes se encolan: saltar niveles de golpe no pierde ninguna.
- Se quita el campo `specializations` de cada clase en `classes.yaml`, que eran solo nombres y contradecían el catálogo de 41 ramas.
- Ninguna rama es elegible todavía (B07 les escribe el recorrido de 10 a 20), y `/path` lo dice en vez de ofrecer algo a medias.

## [0.10.26] - 2026-10-21

### Añadido
- **Guía canónica de Aetherfall** en content/world/guide.yaml: resume en español e inglés la ambientación, sociedad, tecnología, magia y límites de lo que un trasfondo puede declarar. Se valida al cargar el contenido y se muestra resumida al escribir un trasfondo propio.
- **Propuestas adaptadas**: si la idea del jugador contiene una plataforma, marca o anacronismo, Gemini conserva su identidad, oficio y motivación y propone un equivalente de Aetherfall. El jugador puede aceptarlo, editarlo o volver a la lista; propuestas y botones antiguos no se pueden reutilizar.

### Cambiado
- El trabajo sexual entre adultos y otros pasados oscuros se aceptan cuando se describen sin detalles explícitos. Solo se rechaza cuando una reformulación segura no puede conservar la idea central o cuando se intentan imponer ventajas, autoridad o hechos canónicos.
- La revisión de trasfondos devuelve accepted, adapted o rejected, recibe la guía del mundo y el linaje como contexto fiable, respeta los límites de longitud y registra el resultado sin guardar el texto del jugador en action_logs.

## [0.10.25] - 2026-10-21

0.10-I (B03): las clases estrenan su propia barra, en vez de usos por descanso.

### Añadido
- **La barra de clase en el motor**: generación, coste, recuperación por turno y **enfriamientos contados en turnos de combate**, nunca en segundos reales. El **ataque básico es gratis y siempre útil**, y en las clases que lo construyen atacando alimenta la barra —una vez por acción, no por golpe, así que un Ataque Extra no la llena el doble—. Nada pasa del máximo ni baja de cero.
- **Guerrero (Foco) y Hechicero (Maná) como pilotos**: Segundo Aliento y Oleada de Acción se pagan con Foco; Dormir, Bola de Fuego y Proyectil Mágico, con Maná. El Rayo de Fuego sigue siendo gratis, que es el sentido de la acción básica. Las otras doce clases llegan en B06.
- **Los jefes no se encadenan**: el control duro les dura un turno y lo que sobra los deja **vulnerables**, dicho en el registro. Nunca una inmunidad callada que anule una rama entera. El Viejo Colmillo y el Guardián de la Cripta ya son jefes.
- La poción de maná y el tónico del reposo devuelven **barra** a quien tiene barra y **usos** a quien tiene usos; lo decide la clase de quien bebe, no el objeto. Ganar un combate devuelve su parte del Maná: huir no recarga nada.
- 🔹 La barra en la cabecera del panel de combate y en `/sheet`, y el coste en el propio botón del poder («🌟 Segundo Aliento (4)»). Un poder que no puedes pagar no se ofrece, y el registro dice «−4 Foco (0 restante)».
- El simulador gasta la barra y prioriza lo que cuesta; con eso mide a los dos pilotos.

### Cambiado
- Un estado **se refresca y no se acumula**: al repetirlo gana la duración más larga. Estaba así, ahora está escrito y probado.
- `content/classes.yaml` acepta `cost`, `generates` y `cooldown` por habilidad, y `resource` y `resource_on_attack` por clase; el loader rechaza una pasiva que cueste, un coste que no quepa en la barra del nivel y una clase que mezcle usos con barra.
- **Migración 0014**: `characters.pools`, la barra entre sesiones. Vacío significa barra llena: nadie pierde lo que no gastó.

## [0.10.24] - 2026-10-21

0.10-I (B02): la XP ya no basta para subir de nivel, y las misiones se cobran en persona.

### Añadido
- **Entregar la misión a quien la dio**: al cumplir los objetivos, una misión con `turn_in_stage` queda **lista para entregar** y no paga nada. Vuelves a su dador, pulsas «📜 Entregar: …» —en la escena y en el panel del PNJ— y entonces cobras: recompensa, hito y la misión siguiente, todo en la misma transacción. Pulsar dos veces, o desde un menú viejo, nunca paga dos veces. El diario y `/quests` la muestran ✅ con el nombre de quien te la debe, y la ruta del objetivo te lleva hasta él.
- **El nivel necesita XP y un hito narrativo.** La XP demuestra experiencia; el hito abre una frontera. Con la XP del nivel 12 y sin el hito del Recaudador el héroe se queda en 9, **sin perder un punto**: en cuanto el hito llega, sube solo. La ficha lo dice: la barra de XP se llena y debajo aparece «🔒 Tienes la XP del siguiente nivel; te falta: …».
- Efecto de contenido **`milestone`**, para que la recompensa de una misión conceda su puerta, y `characters.grant_milestone`, que la concede una sola vez.
- `El Viejo Colmillo` se entrega a Bram: la primera misión del juego que se cobra en persona, y el molde de lo que hará el Recaudador.

### Cambiado
- **El techo deja de ser el nivel 5**: la tabla de XP de veinte niveles de `content/progression.yaml` es ya la que manda. `engine/progression.py` se queda con los PV y las competencias; los niveles los calcula `engine/class_build.py`.
- `characters.grant_xp` solo suma experiencia; aplicar niveles es `apply_levels`, que se vuelve a ejecutar también al cumplir un hito.
- La barra de XP de la ficha no se pasa de su propio total mientras esperas en una puerta.

## [0.10.23] - 2026-10-21

0.10-I: Sacerdote pasa a **Clérigo** y Mago a **Hechicero**, id incluido.

### Cambiado
- **Los ids de clase se renombran**: `priest` → `cleric` y `mage` → `sorcerer`, en el contenido, el código, las pruebas y las carpetas de retratos. El contrato recomendaba conservarlos para no romper nada; como se arranca de cero y no hay partidas que proteger, no vale la pena cargar con dos nombres para lo mismo.
- Los nombres visibles pasan a **Clérigo / Cleric** y **Hechicero / Sorcerer**, y con ellos las descripciones de clase, las de SAB e INT en `abilities.yaml` y las dos menciones del reglamento. El conjuro «Armadura de Mago» conserva su nombre: es el nombre del hechizo, no el de la clase.

## [0.10.22] - 2026-10-21

0.10-I (B01): los contratos de las ramas de clase, la progresión y los recursos. Todavía no cambia el juego.

### Añadido
- **`content/class_specializations.yaml`**: el catálogo de las **41 ramas de clase** de las catorce clases, con su nombre ES/EN, su bucle y sus roles (daño, defensa, recuperación y control). Ninguna es elegible aún: van marcadas `ready: false` hasta que tengan su recorrido entero de 10 a 20. No se confunde con `content/specializations.yaml`, que son las ramas de maestría de campo.
- **`content/progression.yaml`**: la tabla de XP de los **veinte niveles**, las dos puertas narrativas (el Recaudador abre el 10, el Ciervo abre el resto), los niveles de entrenamiento (5, 12 y 18) y de modificador (13 y 17), y las **nueve barras de clase** —Convicción, Foco, Furia, Energía, Maná, Resonancia, Esencia, Carga y Poder rúnico— con cómo se recuperan. Son cifras semilla, para medirlas.
- **`oathforge/engine/class_build.py`**: el catálogo efectivo y la progresión híbrida, puros y sin leer contenido por su cuenta. El nivel es el menor de tres: el que da la XP, el que permiten los hitos y el tope. La XP no se pierde esperando en una puerta, y las elecciones pendientes se encolan, así que saltar de golpe del 4 al 13 no pierde el entrenamiento del 5.
- **Validación cruzada** en el loader: una rama tiene que ser de una clase real o de una que el contrato todavía debe (y entonces no puede estar lista), ninguna clase se queda sin rama, un id no puede estar en las dos familias y un recurso de clase tiene que existir. Con sus pruebas, más las del motor para los casos de §4.2 que no necesitan base de datos.
- **Migración 0013**: `characters.build`, un bloque JSON versionado con los hitos cumplidos y las elecciones de entrenamiento y modificador.

### Arreglado
- La suite ya no depende del `.env` de cada máquina: `tests/conftest.py` fija el idioma por defecto y las pruebas del cliente de Gemini fijan su cadena de modelos. Eran los cinco fallos de la línea base de 0.10.21.

## [0.10.21] - 2026-10-21

0.10-I (B00): el contrato de la revisión más grande del proyecto y la auditoría de la base. Solo documentación.

### Añadido
- **`planning/roadmap_balance.md`**: el contrato de **0.10-I**, la revisión de clases, progresión y campaña. Catorce clases (Mago y Hechicero se fusionan, Sacerdote pasa a Clérigo y entran seis nuevas), **41 ramas que se eligen al nivel 10**, progresión híbrida de **XP más hitos hasta el nivel 20**, entrega de las misiones a quien las dio, una campaña inicial nueva con el Recaudador de Ceniza y el Ciervo de Hierro, una región cercana a Crownreach para los niveles 11–20, tiempos normales sin atajos de beta, la retirada de la Cripta Hundida y el reinicio limpio antes de abrir. Se trabaja en quince fases (B00–B14), una o varias por parche.
- **Auditoría de la base 0.10.20** dentro de ese documento: línea base de la suite (410 pasan; los 5 fallos que quedan son del `.env` local, no del código) e inventario de todo lo que la entrega tendrá que tocar —ids `priest` y `mage`, el aviso de rama al nivel 5, el techo de nivel 5, la mejora de atributo del 4, los usos por descanso, los atajos de beta y las 31 referencias a la cripta—.

### Cambiado
- **`TODO.md`**: la especialización pasa del nivel 5 al **10**, «siguientes clases» pasa a las catorce con su recurso propio, «más misiones después del nivel 5» y «segunda región» pasan a la campaña 1–20 y a la región cercana, y el campamento de entrenamiento baja a idea.
- **`planning/roadmap.md`** estrena el hito **0.10-I** y marca como sustituidas las fichas F07, F10, F12, F13, F14 y F19, que se conservan como historia. Lo entregado en F15 no se rehace.
- `planning/README.md` enlaza el contrato nuevo.

## [0.10.20] - 2026-10-20

Marcado lo que F15 deja hecho. Solo documentación.

### Cambiado
- **`TODO.md`**: «Profesiones y recolección» recoge lo entregado en 0.10.9–0.10.19 y deja a la vista lo que falta (la partida de prueba y el balance con la beta). Las «afinidades de maestría» quedan a medias —las ramas sí, la durabilidad y las vetas no— y se marcan hechas las **«recetas por tier»**, resueltas como T0 = rango 0–2 y T1 = rango 3–5, y el **«cofre o almacén»**, que es el de tu cuarto.
- **`planning/roadmap.md`**: F15 estrena su «Estado (0.10.19)», la puerta de salida ya habla de **ocho** oficios y la tabla de trazabilidad dice en qué versión se resolvió cada pendiente del TODO.

## [0.10.19] - 2026-10-20

Profesiones (F15, cierre): la ficha queda cerrada salvo la partida de prueba.

### Añadido
- **`tests/features.md`** recoge el recorrido de F15: el mundo nuevo, refinar y fabricar, Sastrería, técnicas y planos, la habitación, ramas y herramientas, T1 y economía, y las tres carreras que hay que probar con PostgreSQL. Lo que la suite ya demuestra va marcado; lo que pide jugar, no.

### Cambiado
- **`planning/opificia.md`** describe el sistema tal y como quedó: ocho oficios con su maestro y su puesto, el refinado de las maestrías, las ramas, el conocimiento, la instantánea de cada actividad, el hallazgo raro, las herramientas, el cuarto y las 60 recetas con sus tiers.
- `planning/facies.md` lista los comandos nuevos, y `planning/roadmap.md` cierra las diez fases de F15.

### Pendiente
- La **partida de punta a punta con `tgtest` en español y en inglés** y las pruebas de concurrencia con PostgreSQL: necesitan el bot en marcha y la base migrada (`alembic upgrade head` trae las migraciones 0011 y 0012).

## [0.10.18] - 2026-10-20

Profesiones (F15, 10.ª parte): el catálogo T1.

### Añadido
- **Tres materiales T1 en los lugares de siempre**, detrás del rango 4: **mena de hierro profundo** en la Mina del Paso Viejo, **tronco de corazón** en la Arboleda Antigua y **fibra sedosa** en el Claro de la Raíz Roja. El rango de la maestría es lo que abre la veta buena, no un mapa nuevo.
- **El acero**: hierro profundo + carbón → **lingote de acero** en el horno (Minería, rango 4).
- **Ocho recetas T1** (rango 3–5), una por oficio donde tenía sentido: espada y coraza de acero, cuero endurecido, bastón de corazón de roble, poción de curación mayor, anillo guardado y tela de seda. El **equipo de combate pide nivel 10** para equiparse o beberse: se forja, se vende y se guarda desde ya, y la ficha lo dice.
- **Los maestros venden los componentes de su oficio**: Hedda hilo, tela y sedal; Garrick tablones de roble y de fresno; Oda cuero curtido. Nadie se queda esperando a otro jugador.
- **Una prueba recorre todo el catálogo** y exige que ningún ingrediente carezca de origen, que ninguna receta pida lo que produce, que una receta T0 no dependa de otro oficio sin salida y que **comprar los ingredientes y vender el resultado nunca dé beneficio**. Ese examen ajustó el precio del sedal y del cuero endurecido.

## [0.10.17] - 2026-10-20

Profesiones (F15, 9.ª parte): las herramientas especializadas.

### Añadido
- **Quince herramientas**, tres diseños por disciplina: **rápido** (−10 % de tiempo), **selectivo** (raro ×1,05) y **productivo** (5 % de una unidad extra por actividad completa). Pico, hacha, hoz y cuchillo los forja la **Herrería** (técnica nueva «Herramientas especializadas», rango 2) y las cañas las hace la **Carpintería** (técnica «Cañas de pescar»). Las mejores piden una pieza de otro oficio: tela, hilo, cuero o un tablón de fresno.
- **Una herramienta por disciplina**: se elige en 🛠️ Oficios → Maestrías → 🧰 Herramientas, pide tenerla y el rango que marque, y **llevar tres no suma**. La elegida sustituye a la de siempre: con ella puestas, minar sigue pidiendo un pico, pero cuenta el tuyo.
- **La rama y la herramienta se suman una sola vez** y quedan **fijadas al empezar** el trabajo, dentro de su instantánea: ponerse otra a mitad no cambia el premio, y con un trabajo en marcha el cambio se rechaza.
- El desuello también se acorta con el cuchillo que corresponde, sin bajar nunca del suelo de 30 segundos.
- El reglamento explica los tres diseños y, con un ejemplo, la diferencia entre un **+5 % relativo** (10 % → 10,5 %) y **+5 puntos** (10 % → 15 %): aquí siempre es lo primero.
- Comentarios `DESIGN-N04` y `DESIGN-N06` donde se leen las herramientas: diseños fijos, sin desgaste ni piedra de afilar.

## [0.10.16] - 2026-10-20

Profesiones (F15, 8.ª parte): las ramas de cada maestría.

### Añadido
- **Doce ramas**, dos por cada maestría y dos para la Pesca (`content/specializations.yaml`): Extracción o Prospección en Minería, Producción o Selección forestal en Tala, Cosecha abundante o Botánica selectiva en Herboristería, Aprovechamiento o Extracción cuidadosa en Desuello, Rastro seguro o Rastro selectivo en Rastreo, y Pesca abundante o selectiva.
- **🌿 Especializaciones** en el Gremio de Aventureros: a **rango 2** eliges una rama por disciplina. La primera es gratis; cambiarla cuesta **50 de oro** (`SPEC_SWITCH_COST`), con una confirmación que dice el precio y qué queda pausado. La rama que dejas **no se borra**: queda aprendida y pausada, y volver a ella cuesta lo mismo.
- **Las disciplinas no comparten plaza**: puedes llevar Minería y Tala especializadas a la vez, y solo la rama activa de cada una cuenta.
- **La rama queda fijada al empezar la actividad**, dentro de su instantánea: cambiarla a mitad no cambia el premio, y con un trabajo en marcha el cambio se rechaza.
- **Piloto de Rastreo**: «Rastro seguro» acorta la espera un 15 % y «Rastro selectivo» inclina el rastro hacia la presa más escasa del lugar, sin tocar nunca al jefe de una misión. Lleva sus comentarios `DESIGN-N01` y `DESIGN-N02` para decidir más adelante si Rastreo sigue siendo maestría.
- Sección **🌿 Ramas de maestría** en `/rulebook`, con el rango, el precio y el ejemplo de 10 % → 10,5 %.

## [0.10.15] - 2026-10-20

Profesiones (F15, 7.ª parte): cada actividad se paga con las reglas con las que empezó, y el hallazgo raro se tira una vez.

### Añadido
- **Instantánea de reglas al empezar** (la casilla pendiente de F08): una recolección o una expedición guardan su tabla de recursos, su rango y sus modificadores, y al cobrarla se resuelven con eso, no con el contenido de ese momento. Reiniciar el bot o publicar un cambio de catálogo ya no puede alterar un premio en marcha. Las actividades anteriores a la instantánea se siguen pagando como antes.
- **El hallazgo raro es de la actividad, no de cada unidad**: los recursos de rango 3 o más salen de una sola tirada por trabajo, con la probabilidad que el catálogo tenía de dar al menos uno, y sustituyen una unidad común en vez de añadirse. Así la cantidad no cambia y el porcentaje que se anuncia es el que se cumple.
- **`Mods`**, el perfil de lo que una herramienta o una rama cambian: tiempo (`300 s` con −10 % son 270 s, con un suelo de 30 s), raro **relativo** (10 % × 1,05 = 10,5 %, nunca 15 %) y una unidad extra con **una sola oportunidad por actividad completa**, sin XP. Las dos cosas que lo rellenarán —rama y herramienta— llegan en sus fases.
- Pruebas de distribución con semilla que comparan la economía nueva con la vieja: las mismas unidades por trabajo y las gemas en el mismo orden de magnitud.

## [0.10.14] - 2026-10-20

Profesiones (F15, 6.ª parte): tu cuarto en el gremio, con cama y cofre.

### Añadido
- **Un cuarto propio**, misión nueva del tutorial (la 8, tras «Hierro para la Guardia», que ahora paga con un **hacha** en vez de con oro): talas robles, asierras los troncos en el gremio, montas el **cofre** con cuatro tablones y, con la **tela** que te da Vale y dos tablones más, la **cama**. Las dos son **recetas de iniciación**: no piden oficio ni plaza y solo existen mientras esa misión dura.
- **Dormir en tu cama** es el descanso largo de siempre —lo mismo que recupera, lo mismo que tarda— pero **no cuesta oro**.
- **El cofre**, con 20 huecos (`CHEST_SLOTS`). Lo guardado **no se lleva encima**: no se vende, no se gasta ni se fabrica con ello hasta sacarlo, y cada pieza conserva su identidad y quién la hizo, porque se mueve la fila, no una copia. Depositar y retirar son atómicos y bloquean las filas.
- **`/room`** (alias `/stash`) abre el cuarto: la cama, el cofre con lo que hay dentro y lo que llevas en la mochila. Con **`/stash_<objeto> 5`** y **`/take_<objeto> 5`** se mueve cualquier cosa sin abrir menús; repetir el mismo mensaje no lo mueve dos veces.
- **Mejora del cofre**, una receta de Carpintería (rango 1): seis tablones y un lingote por 10 huecos más, sin tocar lo guardado. El carpintero se la hace; los demás se la comprarán.
- La tela del gremio es **material de misión, no vendible**, y Vale la repone mientras no tengas la cama montada ni la tela encima: ni se pierde la misión ni se puede pedir una y otra vez.
- Sección **🏠 Tu cuarto y el cofre** en `/rulebook`, con las cifras del motor.
- Migración **0012**: `item_instances.container` (la mochila o el cofre) y `characters.home`.

## [0.10.13] - 2026-10-20

Profesiones (F15, 5.ª parte): Sastrería, las técnicas y los planos.

### Añadido
- **Sastrería**, el octavo oficio, con su puesto: el **Telar de Hedda**, maestra sastra. La cadena es fibra vegetal → fibra limpia (Herboristería, en el gremio) → **hilo** → **tela** → **jubón acolchado** (CA 11) y, a rango 2, el **sedal** que la carpintería necesitará para sus cañas.
- **Técnicas**: cada rango nuevo enseña de golpe una técnica entera con todas sus recetas comunes, y lo dice en una línea («📘 Técnica aprendida: Forja de armas · Espada de hierro»). Dieciséis técnicas repartidas entre los ocho oficios y las dos aficiones.
- **Planos** (`type: blueprint`): un pliego que enseña una receta especial. Leerlo gasta ese ejemplar y el conocimiento ya no se pierde, tampoco al cambiar de oficio; si ya la conoces, no se gasta y puedes vender el plano. La ficha `/item_` de un plano dice qué enseña y trae el botón «📘 Aprender la receta».
- La primera receta especial: la **daga de colmillo** (1d6 perforante, sutil), que se forja con un lingote, dos colmillos y cuero. Su plano lo suelta **el Viejo Colmillo**, el jefe del tutorial.
- Migración **0011**: `characters.crafting` guarda lo aprendido de los planos (y, más adelante, la rama y la herramienta elegidas de cada disciplina).

### Cambiado
- El reglamento cuenta los ocho oficios, las técnicas por rango y los planos.

## [0.10.12] - 2026-10-20

Profesiones (F15, 4.ª parte): el refinado pertenece a las maestrías, y las recetas tienen panel y comandos.

### Añadido
- **Refinar es cosa de la maestría, no del oficio.** En el Gremio de Aventureros, cualquiera funde **lingotes de hierro** y **de cobre** en el horno (XP de Minería), asierra **tablones de roble** y **de fresno** (Tala), cura **cuero** en el secadero (Desuello) y limpia **fibra** en la mesa de preparación (Herboristería). Sin oficio, sin plaza y con el rango de esa maestría.
- **Tres materiales nuevos**: lingote de cobre, tablón de fresno y fibra limpia.
- **`/recipes`**: todas las recetas de tus disciplinas por pestañas —✅ Puedo fabricar · ❌ Faltan materiales · 🔒 Por aprender · T0 · T1—, de 8 en 8, cada una con su `/r_<receta>`.
- **`/r_<receta>`**, la ficha: qué hace y cuánto da, su disciplina y su rango, dónde está su estación, los ingredientes con `tengo/necesito` y, de lo que falta, **de dónde sale** (el lugar donde se recoge, la maestría que lo refina, la criatura que lo suelta o quién lo vende), la XP que paga y el nivel que pide para equiparse. Abajo, botones **🔨 ×1 · ×5 · ×máx**, limitados por los materiales y por `CRAFT_BATCH_MAX`.
- **`/craft_<receta> n`**: fabricar escribiendo, sin abrir un menú; sin número, abre la ficha. Repetir el mismo mensaje no fabrica dos veces.
- El reglamento explica el refinado y los lotes, con la cifra del motor.

### Cambiado
- **Las recetas de refinado cambian de disciplina y de estación**, conservando sus ids: `iron_ingot` y `copper_ingot` a Minería, `oak_plank` y `ash_plank` a Tala, `treated_leather` y `wolf_leather` a Desuello y `clean_fiber` a Herboristería. Los objetos ya fabricados no se tocan.
- El **anillo de cobre** se hace con un lingote de cobre (antes, con mena cruda) y el **bastón de roble**, con fibra limpia. El mismo material de partida, un paso más de oficio.
- Las guías de **Herrería**, **Carpintería** y **Peletería** cuentan lo que hacen ahora: forjar, trabajar la madera y coser, con el refinado hecho en el gremio.
- El panel de fabricar enlaza cada receta con su ficha y lleva un botón «📜 Recetas».

## [0.10.11] - 2026-10-20

Profesiones (F15, 3.ª parte): el Gremio de Aventureros y una calle con un puesto por oficio.

### Añadido
- **Gremio de Aventureros** (`adventurers_guild`), un lugar nuevo al este de la plaza. Dentro están el **horno de fundición**, el **puesto de aserrado**, el **secadero** y la **mesa de preparación** —las estaciones del refinado de las maestrías, abiertas a cualquiera— y un fogón. Es también donde la sargenta **Vale** alista ahora a los reclutas: pasa de la plaza al gremio y deja de hablar en nombre de la Guardia para hacerlo en nombre del gremio.
- **Siete puestos de oficio**, cada uno un lugar del mapa con su estación, su descripción de día y de noche y su maestro: la **Forja de Tessa** (herrería), la **Botica del Alquimista** de Ilva, el **Taller del Carpintero** de Garrick, la **Curtiduría** de Oda, el **Banco del Joyero** de Pell, el **Escritorio del Escriba** de Lorent y el **Taller del Ingeniero** de Dunn. Seis PNJ nuevos con su carácter, su horario y sus textos de respaldo; Tessa trabaja de día en su forja y sigue vendiendo lo que vendía. El telar de Sastrería llegará con su oficio.
- **Cada oficio se aprende en su puesto** (`teaches` en el lugar): con el maestro que lo practica, no con un botón en cualquier parte. Quien lo intente donde no toca recibe el nombre del lugar al que ir.
- **El mapa agrupa los puestos**: salen nombrados bajo su calle y un botón «🛠️ Puestos (7)» los abre, así que la ciudad sigue cabiendo en una pantalla aunque tenga trece lugares.
- Los prompts del gremio y de los siete puestos, en `TODO-images.md`.

### Cambiado
- **El Barrio de Oficios conserva su id y se queda sin estaciones**: ahora es la calle de la que cuelgan los puestos. Las misiones, los logros y los textos que lo nombran siguen funcionando.
- **El tutorial se adapta**: «Alistamiento» empieza en el gremio (la plaza enseña por dónde se va), «Calles de Crownreach» habla de los puestos y «El mercado» manda a Tessa a su forja. El botón «🛒 Pico · ir a…» lleva ahora a la forja.
- El reglamento, las guías y la ficha del héroe dicen que cada oficio se aprende con su maestro, en su puesto.

## [0.10.10] - 2026-10-20

Profesiones (F15, 2.ª parte): el contrato de las recetas. Nada cambia todavía para el jugador; cambia lo que una receta puede decir de sí misma.

### Añadido
- **Estación por receta**: una receta puede traer su propia `station` en vez de heredar la de su oficio. Es lo que permitirá fundir en el horno sin ser herrero, y lo que hacía falta para separar el refinado del oficio.
- **La disciplina de una receta puede ser una maestría** (minería, tala, herboristería, desuello): entonces no ocupa plaza, cualquiera la trabaja y su XP va a esa maestría, nunca a un oficio. El rango exigido también es el de la maestría.
- **Cinco estaciones nuevas** con sus nombres ES/EN: telar, horno de fundición, puesto de aserrado, secadero y mesa de preparación.
- **Fabricar por lotes**: `craft` acepta una cantidad (hasta `CRAFT_BATCH_MAX`, 10 por defecto). Comprueba todos los materiales antes de gastar uno y produce el lote entero o ninguno; la XP se multiplica por lo fabricado. El botón `craft` acepta `receta:cantidad`.
- **Requisito de nivel para equipar y usar** (`min_level`): un objeto T1 se fabrica por rango y se lleva por nivel, así que un artesano de nivel bajo puede forjarlo y no equiparlo. Desequipar nunca se bloquea.
- **Planos** (`type: blueprint`, campo `teaches`) y recetas `special`, `technique` y de misión (`quest`): el esquema ya las admite y el cargador las valida; el aprendizaje llega en su fase.
- **Validaciones del cargador**: la disciplina existe como oficio o maestría, una receta de maestría trae su estación, la estación existe en algún lugar, las cantidades son positivas, la misión de una receta existe, un plano enseña una receta que de verdad es especial y una receta especial tiene quien la enseñe.

### Cambiado
- Las fichas `/item_` y el panel de fabricar hablan de «disciplina», no de «oficio»: el icono y el nombre salen del oficio o de la maestría, según cuál sea.

## [0.10.9] - 2026-10-20

Profesiones, maestrías y aficiones (F15, 1.ª parte): el contrato. Solo documentación; el juego no cambia.

### Añadido
- **`planning/roadmap-profesiones.md`**, el contrato de F15 auditado sobre 0.10.8: veinticinco decisiones (D01–D25), la cadena de refinado de cada maestría, las dos ramas por disciplina, las herramientas con sus porcentajes, los ocho oficios con Sastrería, las técnicas y los planos, el Gremio de Aventureros, la calle con un puesto por oficio, la habitación con cama y cofre, los contratos técnicos, la interfaz y once fases de entrega con su puerta de salida. Las trece notas de experimentos y balance (N01–N13) quedan al final, sin recortar.
- Decisiones nuevas de esta revisión: **T0 son las recetas de rango 0–2 y T1 las de rango 3–5**, así que el tier no es un campo que mantener a mano; el catálogo T1 se publica entero y su equipo de combate pide nivel 10 para equiparse; el **Barrio de Oficios conserva su id** y pasa a ser una calle de la que cuelgan ocho puestos, cada uno un lugar con su estación y su **maestro**; **Tessa** se convierte en la maestra de Herrería en su Forja; el **Gremio de Aventureros** reúne a Vale, el refinado, un fogón, las especializaciones y la habitación; y la habitación entra **dentro del tutorial**.

### Cambiado
- **F15 en `planning/roadmap.md`** deja de ser una lista de auditorías y pasa a ser once fases con su versión (0.10.9–0.10.19), enlazadas al contrato. El hito 0.10-F abarca ese tramo.
- El **cofre personal** de F06 y la **instantánea de reglas** que le falta a F08 se entregan dentro de F15 (fases 5 y 6); sus casillas lo dicen.
- `planning/opificia.md` recoge lo decidido y lo que queda futuro, y advierte de dos trampas del código: las maestrías están fijas en `engine/gathering.py`, no en el contenido, y la estación de una receta sale de su oficio, no de la receta.
- `planning/mundus.md`, `mercatura.md`, `facies.md`, `README.md` e `iter.md` apuntan al contrato con lo que les toca.

## [0.10.8] - 2026-10-19

Logros (F04): auditoría, un solo nombre y el título donde se ve.

### Añadido
- **Cuatro logros** sobre lo que ya existe: «Héroe de Crownreach» (nivel 5, con el título *de Crownreach*), «Oficial del gremio» (rango 2 en un oficio) y dos **ocultos**, que no se ven hasta conseguirlos: «Volví por ti» (huir de un combate y luego acabar con el Guardián de la Cripta) y «Lo que caza de noche» (ganar después del anochecer). Son 36 logros y 5 títulos.
- **El título se ve fuera de `/hero`**: junto al nombre en `/sheet`, en la cabecera del Libro del Héroe («de Morgana, *Rompecriptas*») y como dato en el contexto del narrador y de los PNJ, que pueden saludarte por él. La IA lo recibe; concederlo sigue siendo solo del motor.

### Cambiado
- **Un solo nombre, «Logros»**: desaparecen «Ver hazañas», «puntos de hazaña» y «Tu historia recuerda esta hazaña». Los ids, el comando `/achievements` y las tablas no cambian.

### Arreglado
- Una expedición o un rastreo que acaba en derrota ya no cuenta como actividad completada para «Vida de campo» ni «Herramientas del oficio».
- Los desafíos decían «nivel 3–5»: la pareja de lobos pide nivel 4 y la de murciélagos nivel 3, y el límite es empezar a nivel 5 o antes.
- Destacar o seguir un logro con la clave «-» (que solo significa «quitar el título») se rechaza en vez de añadir un hueco a la lista.

## [0.10.7] - 2026-10-19

Diario y reglamento (F03): el Libro del Héroe.

### Añadido
- **Crónica de hechos** (`hero_facts`, migración 0010): el registro que ya deduplicaba los logros ahora guarda también el tipo de hecho, sus datos y el día de juego, y marca los que merecen una entrada. Sustituye a `achievement_event_receipts`, cuyas filas se conservan. Hechos nuevos: nivel alcanzado, rango de oficio y misión aceptada.
- **🕯️ Crónica** en el diario: lo que has hecho, de lo más reciente a lo más antiguo, agrupado por día y de 8 en 8 con ◀ ▶. Siempre misión terminada, decisión, logro, nivel, derrota, secreto y descubrimiento; la primera vez que pisas un lugar, fabricas una receta, ves una criatura o subes un rango; nunca lo repetido. Lo reconocido del progreso anterior va bajo «Antes de este libro». No gasta IA.
- **📖 Ahora**, la portada del diario: la actividad en marcha con lo que le queda, el viaje que dejaste a medias, el objetivo de cada misión en curso y los objetivos seguidos, cada uno con su botón para continuar. Sin misiones, un botón hacia quien las da: el diario ya no es un callejón sin salida.
- **Estadísticas verificables**: misiones terminadas, fabricaciones y recetas distintas, secretos, criaturas conocidas y especies abatidas, niveles y logros, contados desde la crónica. Las antiguas siguen, y cada bloque dice desde cuándo cuenta.
- Sección **🏆 Logros y títulos** en `/rulebook`: qué reconocen, que no dan poder y cómo se equipa un título.
- Una prueba de contenido exige que cada `{marcador}` del reglamento y de las guías de oficio tenga valor en el motor, en español y en inglés.

### Cambiado
- **Diario por pestañas**: 📖 Ahora · 📜 Misiones · 🕯️ Crónica · 🏆 Logros · 🐉 Bestiario · 🗣️ Rumores · 📈 Estadísticas, en un solo mensaje que se edita, con la activa entre «• … •». Las misiones terminadas pasan de «📚 Registro» a la pestaña de Misiones; el botón «Registro» de menús viejos abre la Crónica.
- **El reglamento lee el motor**: coste y duración del descanso, CD de huida, puntos de creación, nivel de la subida de atributo, nivel máximo, oro que cuesta una derrota, segundos de desuello y las CD por dificultad ya no están escritos a mano. Las frases de beta (descanso y tutorial instantáneos) aparecen según el flag.

### Arreglado
- El reglamento decía que un tramo ⚠️⚠️ tiene un 15 % de emboscada: son el 15 % por cada ⚠️ del peor tramo (30 %), más un 5 % por cada tramo peligroso de más, hasta un 45 %.
- Prometía una especialización a nivel 5, que todavía no existe: ahora dice que llegará más adelante.
- No mencionaba el descanso gratis en la Cripta Hundida, el crítico con 19 de algunas habilidades, que subir de nivel permite repetir una prueba, el enfriamiento del tónico del reposo ni que en el tutorial las actividades terminan al instante.
- El backfill de logros daba por hecho que ningún lugar estaba fuera de la ciudad, así que «Más allá de las puertas» no se reconocía nunca. Ahora también reconoce los niveles alcanzados.

## [0.10.6] - 2026-10-19

### Cambiado
- **Un solo botón, 🖼️ Ver lugar**: «🏙️ Ver ciudad» desaparece. En la plaza de una ciudad (lugar `hub`) sin imagen propia, «Ver lugar» enseña la panorámica de la ciudad; los botones «Ver ciudad» de menús viejos siguen funcionando igual.

### Arreglado
- En la Plaza de Crownreach salían «Ver ciudad» y «Ver lugar» a la vez, y «Ver lugar» decía que no había imagen.

## [0.10.5] - 2026-10-18

Audiovisual (F02, 2.ª parte): «Ver lugar».

### Añadido
- **🖼️ Ver lugar** en cada escena: envía la imagen del lugar (la nocturna de noche, si la hay) con su nombre y descripción, y la escena debajo. Si el lugar aún no tiene imagen, una ventanita: «🎨 Ningún pintor ha plantado aún su caballete en la Plaza de Crownreach. Por ahora, tendrás que imaginarlo.»

## [0.10.4] - 2026-10-18

Audiovisual (F02, 1.ª parte): estilo visual y Crownreach de día y de noche.

### Añadido
- **Crownreach de noche** (`panorama.night.jpg`): «🏙️ Ver ciudad» la enseña cuando es de noche en el juego.
- `TODO-images.md` en la raíz: las imágenes que faltan (zonas, mapa, los 17 lugares, PNJ, linajes, eventos, avatar y emblema) con su ruta y su prompt sugerido, más cómo hacer la versión de noche desde la de día.

### Cambiado
- **Estilo visual decidido**: ilustración de libro de rol en gouache, con un sufijo común para todos los prompts (`planning/ars.md` §5).
- Nueva panorámica de Crownreach de día en ese estilo.

## [0.10.3] - 2026-10-18

Solo documentación: no cambia el juego.

### Añadido
- `planning/facies.md`: notas de jugar en vivo con la cuenta de prueba en Chat Wars (castillo Moonlight) y AshWars — menú principal, perfil corto con estado actual, contenedores de inventario, el crafteo por estaciones móviles (probado montando una Tienda de campaña: botón solo con materiales completos, mejora medible al instante, contador de pendientes, coste visible aunque esté bloqueada) y el combate de incursión (enemigo oculto hasta identificarlo, confirmación al huir). Candidatas para revisar en F01/F08/F15; nada implementado todavía.

## [0.10.2] - 2026-10-18

Interfaz (F01, 3.ª parte): inventario ordenado y un icono para cada cosa.

### Añadido
- **Icono por objeto** (`icon` en `content/items.yaml`, los 62): 🪨 menas, 🪵 maderas, 🌺🍃🌿 hierbas, 🐗🐺 pieles, 🥩 carne, 🐟 pescado, ⛏️🪓🌾🔪🎣 herramientas… Siempre junto al nombre, nunca en su lugar (`Item.label`); sin icono propio, el de su tipo. Se ve en el inventario, el botín, las crónicas, las recetas, las tiendas, el combate y `/item_`. Una prueba de contenido exige que todos lo tengan.
- `/item_<clave>` de algo que llevas trae su botón de equipar o usar.

### Cambiado
- **Inventario con pestañas**: el resumen dice qué llevas puesto y cuántos objetos hay de cada tipo; las pestañas ⚔️ Equipo · 🧪 Consumibles · 🧱 Materiales · 🧰 Herramientas listan cada objeto en una línea («🪨 Mena de hierro ×3 · /item_iron_ore»), sin la descripción entera, con la pestaña activa marcada «• … •». Equipar está en Equipo y usar en Consumibles; Volver lleva al resumen.

## [0.10.1] - 2026-10-18

Interfaz (F01, 2.ª parte): textos claros.

### Cambiado
- **Pruebas de habilidad legibles**: «🎲 Supervivencia: 2 + 1 = 3 vs CD 13 · ❌ Fallo» (el d20, el bono, el total, la CD y el veredicto) en vez de «2 → 3 contra CD 13 ❌». Una sola función (`characters.add_check`) para investigar, acciones de misión, robar y texto libre.
- **Artículos**: cada lugar lleva el suyo (`article` en `place.yaml`) y el texto dice «Llegas al Mercado», «a la Taberna», «por el Camino del Viejo Rey», «Rastreo en el Prado», «Ve a la Capilla del Alba». El traductor contrae «a el» y «de el». En inglés, «the Old Pass Mine»; la taberna se llama «Broken Crown Tavern».
- **Singular**: «1 ronda», «1 turno», «1 terminada», «1 punto», «1 logro»… El traductor elige `<clave>_one` cuando la cuenta es 1.
- La pista de la misión de cocina dice dónde está ahora «🔨 Fabricar».

### Añadido
- Leyenda de las competencias en `/sheet`: «● competente · ○ practicada · · sin entrenar · ★ rango de práctica».

## [0.10.0] - 2026-10-18

Empieza la consolidación (0.10.x) con la interfaz (F01, 1.ª parte): menos mensajes, menos botones y siempre a mano lo que puedes hacer.

### Añadido
- **⚒ Actividades** en el teclado fijo, en la escena (con cuántas hay) y como `/activities`: cazar, recolectar, expedición larga, rastrear, desollar, descansar, fabricar y curar, cada una con su duración y lo que te falta. Sin herramienta no sale el botón: sale «🛒 Pico · ir a Mercado», que te lleva a quien la vende. La disponibilidad usa la misma regla que el servicio (`activities.check`), así que un botón nunca promete lo que luego se rechaza.
- **🛠️ Oficios** desde Héroe y desde Actividades, con las pestañas de oficios, maestrías y aficiones. `/activities`, `/masteries` y `/hobbies` en el menú de comandos.
- Pista «Escribe lo que haces…» en el campo de texto.

### Cambiado
- Teclado fijo de 3 + 3: 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario (`KEYBOARD_VERSION = 3`: los jugadores existentes lo reciben solo).
- La escena se queda con lo social: Viajar, Investigar, Hablar, Comerciar y ⚒ Actividades, más «Seguir viaje», las acciones de misión y «Ver ciudad».
- **Un mensaje por acción**: investigar, cazar, abandonar o un texto libre dejan un solo mensaje con el resultado y la cabecera del lugar con sus botones, y el panel pulsado se queda sin botones. Subidas de nivel, crónicas y combates siguen en mensajes propios. Una actividad que termina sola trae los botones del lugar en el mismo mensaje.
- Comprar, vender, equipar, usar, aprender un oficio y fabricar ponen el resultado encima del mismo menú, sin mensaje nuevo. Empezar una actividad convierte el mensaje en su panel; «🔄 Actualizar» lo refresca en el sitio.
- **Rechazos en ventanita**: «Necesitas un pico», sin oro, un menú viejo, un doble toque o un error de combate salen como aviso emergente de Telegram, sin escribir en el chat, y el mensaje pulsado pasa a la vista actual. Nada se gasta dos veces.
- Las pistas del tutorial y el `/rulebook` dicen dónde están ahora cazar, recolectar, minar, curar y descansar.
- Hoja de ruta renumerada: la consolidación son parches **0.10.x** (la serie 0.9 terminó en 0.9.1), empieza por F01 y el hito A va justo después (`planning/roadmap.md`, `planning/iter.md`).

### Arreglado
- Pulsar dos veces la misma vista ya no manda un mensaje repetido («Message is not modified»).
- Un conflicto de versión al pulsar un botón ya no deja «Aquí tienes el actual:» sin la vista detrás.


---

Las series 0.1 a 0.9 están en [`planning/archivum/CHANGELOG-0.1-0.9.md`](planning/archivum/CHANGELOG-0.1-0.9.md) (archivo: no se lee salvo que se pida).
