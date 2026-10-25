# Plan de implementación 0.10-I (clases, progresión 1–20 y campaña)

> **Para qué sirve.** Es el plan de trabajo de la serie 0.10.x, escrito para que cualquier sesión de Claude lo siga **fase a fase sin cargar todo el contexto**. El *qué* y el *por qué* están en [roadmap_balance.md](roadmap_balance.md) (el contrato); este archivo dice *en qué orden*, *cómo se cierra cada parche* y *qué se aprendió por el camino*.
>
> **Cómo usarlo en una sesión nueva:** lee este archivo, la tabla de §0 de `roadmap_balance.md` y la sección de la fase que toca (Grep por `### B08 ·`, etc.; el documento es grande, léelo por rangos). No releas las fases ya hechas: su estado está en el CHANGELOG (primeras entradas) y en `tests/features.md`.

## Estado (al cerrar 0.10.34)

| Fase | Estado | Versión |
|---|---|---|
| B00 Base y auditoría | ✅ | 0.10.21 |
| B01 Contratos de contenido y estado | ✅ | 0.10.22 |
| B02 XP híbrida y entrega al PNJ | ✅ | 0.10.24 |
| B03 Motor de recursos y efectos | ✅ | 0.10.25 |
| B04 Catálogo efectivo, selección y elecciones | ✅ | 0.10.27 |
| B05 Compañeros, formas y dispositivos | ✅ | 0.10.28 |
| B06 Catorce clases base, niveles 1–9 | ✅ | 0.10.29–31 |
| B07 Las 41 ramas | ✅ | 0.10.32–34 |
| **B08 Tiempos, descanso, derrota y economía** | ⏳ **siguiente** | |
| B09 Campaña común hasta el Recaudador | ⏳ | |
| B10 Ciervo de Hierro y graduación | ⏳ | |
| B11 Región cercana 11–20 | ⏳ | |
| B12 Balance integral | ⏳ | |
| B13 Retirar cripta, documentación y reinicio que conserva preferencias | ⏳ | |
| B14 Candidato de lanzamiento | ⏳ | |

Decisiones de Josue que siguen vigentes:
- **Avanzar fase a fase y parar al final de cada una** con el resumen y lo que conviene probar a mano.
- **Mentor y región son provisionales**: propón el texto en `planning/` (p. ej. `mundus.md`) y espera su aprobación antes del texto final de B09 y B11.
- No hay jugadores que conservar: se arranca de cero y las migraciones de datos viejos se tratan al final. (`oath reset-players --yes` al empezar una ronda de pruebas.)
- Los ids `priest` y `mage` ya se cambiaron a `cleric` y `sorcerer`.

## Reglas de cada parche (no se saltan)

1. Rama `josue-development`; `git fetch` y `git merge origin/main` al empezar. Nada de commits en `main`.
2. Sube la versión en `oathforge/__init__.py` (un parche 0.10.N por incremento comprobable).
3. En el mismo commit: entrada en `CHANGELOG.md`, fila en `planning/iter.md`, casillas de `tests/features.md`, y el **Estado actual** del resumen latino afectado (`ordines`, `progressio`, `pugna`, `mundus`, `mercatura`, `facies`, `narratio`, `bestiarium`, `ars`).
4. **Marcado al cerrar la fase:** `[x]` con versión en `planning/roadmap_balance.md` (casillas y tabla de §0), en `planning/roadmap.md` (hito 0.10-I y las fichas que sustituye) y en `TODO.md` (cerrar solo lo demostrado, reescribir lo que cambia de criterio).
5. Asunto `vX.Y.Z: resumen corto`; cuerpo con la misma lista que el CHANGELOG. **Sin `Co-Authored-By` ni atribución a Claude.**
6. Pruebas: `pytest tests/<área> -q` mientras trabajas, `tests/test_content.py` si tocas `content/`, **suite completa antes del commit**, `oath simulate` si tocas combate, `tgtest` en ES y EN para lo que ve el jugador.

## Lo que queda por hacer

### B08 · Tiempos, descanso, derrota y economía
- Tabla de tiempos de §12 centralizada (un solo sitio, no números sueltos).
- Apagar `beta_instant_rest` y `beta_instant_tutorial` en `config.py` y retirar `quests.tutorial_boost`: tiempos reales, sin atajos de beta.
- Descanso corto limitado; matriz de acciones en `busy`; derrota con coste pequeño y tope; precios normales.
- Servicios implicados: `activities`, `exploration`, `world_map`, `characters` (descanso), `combat_service` (derrota). Cualquier cambio de economía, permisos o concurrencia lleva test.

### B09 · Campaña común hasta el Recaudador
1. Primero `planning/mundus.md`: mentor y trama **provisionales** para que Josue los apruebe.
2. Luego los actos I–VI en `quests.yaml`, `npcs.yaml`, `monsters.yaml`; nuevos tipos de objetivo (equipar, aprender oficio, abrir cofre, humo, elegir rama…); el Recaudador de Ceniza y su entrega (hito `ash_collector`, tope de nivel 10).
- `content/quests.yaml` es grande: léelo por rangos.

### B10 · Ciervo de Hierro y graduación
Jefe y entrega del hito `iron_stag` (abre el tope 20). Depende de B07 y B09.

### B11 · Región cercana 11–20
Región provisional («Greyforge Vale»), criaturas de los niveles 11–20 (hoy no existen; el simulador usa un jefe sintético) y lugares. Texto final tras la aprobación de Josue.

### B12 · Balance integral
Las cifras de clases, ramas y entidades son **semillas**. Aquí se miden con `oath simulate --level 1-20 [--branch …]` y se ajustan. Casos conocidos: lanzadores flojos contra jefes, Tirador de nivel 20, Filo Maldito y Piromante marginales. El simulador aún no modela bien la política de B12 (cuándo curar, cuándo ordenar al servidor).

### B13 · Retirar la cripta y reinicio de lanzamiento
Quitar la cripta (`crypt`, `reliquary`, Holt, Aldren, títulos) y el procedimiento de reinicio que **conserva preferencias** (distinto de `oath reset-players`). Aquí entran también las migraciones de datos viejos.

### B14 · Candidato de lanzamiento
Cierre: revisión de `tests/features.md` entera jugando con la cuenta de prueba, README raíz (solo si Josue lo pide), anuncio en los dos canales.

## Pendientes pequeños (no bloquean ninguna fase)
- Seis retratos de las clases nuevas (prompts en `TODO-images.md`).
- Comprobar en Telegram, en ES y EN, las pantallas de las clases y ramas nuevas.
- Un botón para poner nombre al servidor o a la bestia (`companions.rename` existe, sin interfaz).
- Pruebas de concurrencia con Postgres y de `downgrade` de las migraciones 0013/0014.
- `tests/services/test_activities.py::test_an_activity_is_paid_by_the_rules_it_started_under` es inestable (azar sin semilla; pasa sola).

## Cómo está construido (para no releer el código)

- **Nivel híbrido:** `eligible_level = min(level_for_xp, cap_for(hitos), máximo)`; hitos `ash_collector` (tope 10) e `iron_stag` (tope 20); `base_cap: 9`. La XP nunca se pierde en una puerta. `grant_xp` solo suma; `apply_levels` sube. Contenido en `content/progression.yaml`; reglas puras en `oathforge/engine/class_build.py`.
- **Entrega de misiones:** estado `ready`, `turn_in_stage`, `quests.turn_in`, callback `qturn`, efecto `milestone`.
- **Catálogo efectivo (única fuente):** `characters.effective(char)` / `class_build.build_for` (clase + rama + modificadores + entrenamientos); `abilities_of`, `find_ability`, `bonus_of`. Entrenamientos en 5/12/18, modificadores en 13/17, rama en 10 (`/path`, `services/class_specializations.py`).
- **Recursos por clase:** nueve barras en `progression.yaml`; las habilidades llevan `cost`, `cooldown` (en turnos) y `generates`; `characters.pools` guarda el estado. Control de jefes acotado (`BOSS_CONTROL_TURNS`).
- **Entidades y formas:** `engine/combat.py` (`Entity`, `Shape`, `summon/command/converge/shift`), `content/entities.yaml`, `content/forms.yaml`, `services/companions.py` para el compañero permanente. Máximo: 2 invocaciones, 1 de cada otro tipo. Los permanentes (servidor, bestia) los trae una pasiva con `entity`.
- **Ramas:** `content/class_specializations.yaml` (41, todas `ready: true`). El cargador exige pasiva y técnica al 10, técnica al 20, exactamente dos modificadores en cada nivel de modificador, claves de habilidad únicas entre ramas y costes que quepan en la barra. `tests/engine/test_branches.py` exige decisiones distintas entre ramas hermanas y un suelo de victorias contra un jefe sintético.
- **Simulador:** `oathforge/tools/simulate.py` (`--branch`, entrenamientos y modificadores por defecto, política de invocar/ordenar/curar).

## Trampas ya encontradas
- **Windows/pytest:** usa `--basetemp` dentro del scratchpad y `-p no:cacheprovider` si da `PermissionError`.
- **Scripts desde Bash:** un heredoc con `\n` dentro de Python corrompe cadenas; escribe los scripts en archivos o edita con las herramientas Edit/Write.
- **Mensajes de commit:** usa un archivo con `git commit -F` (PowerShell no admite `-F -`, y algunos filtros bloquean ciertas palabras).
- **`.env` local** (`DEFAULT_LANGUAGE=en`, `GEMINI_MODEL_FALLBACK`) rompía tests; `tests/conftest.py` ya lo aísla.
- **Claves de habilidad:** deben ser únicas entre ramas (el cargador lo comprueba); las de clases base pueden repetirse con las de una rama solo si ya existían.
- **tgtest:** `PYTHONIOENCODING=utf-8`, `MSYS_NO_PATHCONV=1` en Git Bash y un `sleep` entre pulsaciones consecutivas.
- Los fines de línea del repo son CRLF: al reescribir archivos desde scripts conserva el existente (`newline=""`) para no producir diffs de archivo entero.
