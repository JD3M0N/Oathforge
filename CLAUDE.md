# Oathforge — instrucciones para Claude

RPG narrativo para Telegram: un motor d20 determinista decide y Gemini narra. Las reglas de trabajo comunes (invariantes, mapa del repo, cómo leer gastando pocos tokens, pruebas y versionado) están en `AGENTS.md`:

@AGENTS.md

## Ramas (obligatorio)

Josue (JD3M0N) es el único desarrollador. Se trabaja en `josue-development`; compruébalo con `git branch --show-current` antes de editar.

- Si no estás en esa rama, cámbiate (`git switch josue-development`). Si hay cambios sin commitear, llévalos contigo.
- Nunca hagas commit directamente en `main`. Solo se lleva trabajo a `main` cuando Josue lo pide.
- Después de cada merge a `main`, regenera el grafo del código con `/graphify . --update` (sale del AST, no gasta tokens de IA).
- Antes de empezar, trae lo nuevo: `git fetch` y `git merge origin/main`.

## Commits

- No añadas `Co-Authored-By` ni ninguna atribución a Claude en los commits.
- Versionado obligatorio en cada commit (ver `AGENTS.md`).

## Cerca de lo que tocas

Cada zona tiene su `CLAUDE.md` con sus reglas, que se carga al trabajar allí: `content/`, `oathforge/engine/`, `oathforge/services/`, `oathforge/bot/` y `tests/`. Para encontrar un id de contenido, lee `content/INDEX.md` (una línea por id) antes de abrir los YAML. Al editar `content/*.yaml`, un hook ejecuta `oath validate` y actualiza el índice; si devuelve errores, arréglalos antes de seguir.

## Serie 0.10-I (clases, progresión 1–20 y campaña)

Si la tarea es seguir esta serie, empieza por `planning/plan_implementacion_0.10.md` (estado, siguiente fase y reglas de cierre) y lee solo la fase que toca en `planning/roadmap_balance.md`, por rangos. Avanza una fase y para.

## Structura (orden del proyecto)

Si la tarea es ordenar el proyecto («sigue con structura», «la siguiente fase», ruff, CI, mover el contenido a carpetas, partir archivos grandes, skills de protocolo…), empieza por `planning/structura.md`: el **Estado actual** dice qué está hecho y cuál es la siguiente fase, y la sección «Cómo continuar» explica cómo cerrarla. Avanza una fase y para.

## Josue

- Suele poner ejemplos con el Paladín porque es la clase que prueba: salvo que diga lo contrario, el ejemplo vale para todas las clases.
- `content/officina/` es su laboratorio de imágenes y prompts: no lo toques ni lo leas salvo que lo pida.

## Comandos

```powershell
.venv\Scripts\python -m pytest          # tests (Postgres si TEST_DATABASE_URL conecta; si no, SQLite)
.venv\Scripts\oath bot                 # arrancar el bot
.venv\Scripts\oath restart             # reiniciar el bot en marcha (lo arranca en segundo plano); oath stop lo para
.venv\Scripts\oath reset-players       # borrar todos los jugadores (--yes para confirmar)
.venv\Scripts\oath delete-player Aldric # borrar un jugador por nombre o id de Telegram (--yes para confirmar)
.venv\Scripts\alembic upgrade head      # migraciones
.venv\Scripts\oath validate             # comprobar content/ sin arrancar el bot
.venv\Scripts\oath content-index        # reescribir content/INDEX.md
.venv\Scripts\oath simulate --level 1-5   # simulador de combates para el balance
.venv\Scripts\oath tutorial-stats        # minutos por misión del tutorial y dónde se atasca cada jugador
.venv\Scripts\oath tgtest send "/start"   # jugar con el bot desde la cuenta de prueba (también press, show)
```

`oath help` lista los comandos de consola (`oathforge/cli.py`; `oathforge` es el nombre largo); si añades uno, añádelo a su grupo en `COMMANDS`.
