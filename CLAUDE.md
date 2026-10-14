# Oathforge — instrucciones para Claude

RPG narrativo para Telegram: un motor d20 determinista decide y Gemini narra. Ver `README.md` para la arquitectura.

## Ramas (obligatorio)

Antes de editar nada, comprueba la rama (`git branch --show-current`) y el usuario (`git config user.name`, `git config user.email`). Cada persona trabaja **solo** en su rama:

| Usuario de git | Rama |
|---|---|
| JD3M0N / josuedeki21@gmail.com (Josue) | `josue-development` |
| Rayko | `rayko-development` |
| Edian | `edian-development` |

- Si no estás en esa rama, cámbiate (`git switch <rama>`; si no existe, créala desde `origin/main`). Si hay cambios sin commitear, llévalos contigo.
- Nunca hagas commit de código directamente en `main`. Solo se lleva trabajo a `main` cuando Josue lo pide.
- Antes de empezar, trae lo nuevo: `git fetch` y `git merge origin/main`.
- Los testers apuntan bugs e ideas en su `TODO-<nombre>.md` y lo editan y empujan **directamente en `main`**: el ruleset deja pasar a quien tiene permiso de escritura. Es la única excepción.

## Commits y PR

- No añadas `Co-Authored-By` ni ninguna atribución a Claude en commits ni en PR.

## Versionado (obligatorio en cada commit)

- La versión vive solo en `oathforge/__init__.py` (`__version__`); `pyproject.toml` la lee de ahí.
- Cada commit con cambios sube la versión: **parche** `0.1.1 → 0.1.2` para arreglos y cambios pequeños; **menor** `0.1.x → 0.2.0` para una feature grande. `1.0.0` queda reservado para la primera versión pública estable.
- En el mismo commit, añade la entrada en `CHANGELOG.md` (Añadido / Cambiado / Arreglado) y, si cambia el plan, `planning/roadmap.md`.
- Asunto del commit: `vX.Y.Z: resumen corto`. Cuerpo: la misma lista de cambios que el CHANGELOG.
- Los commits automáticos de la Action de TODO no suben versión.
- `CHANGELOG.md` sirve de contexto: léelo para saber qué cambió y cuándo.

## planning/ y artifacts/

- `planning/`: ideas y decisiones de diseño por tema (clases, combate, comercio…). Actualízala cuando una idea se implemente o se decida algo.
- `artifacts/` (ignorada por git): registro local de partidas para depurar y analizar: conversaciones, eventos, combates, llamadas a Gemini y errores (`oathforge/recorder.py`). **No la leas salvo que la tarea lo requiera** (depurar un bug concreto, analizar una partida o el balance). Si hace falta, localiza el archivo concreto por fecha, `telegram_id` o id de combate y lee solo ese; nunca la recorras entera.

## Reglas del proyecto

- **La IA nunca decide resultados.** Interpreta texto → intención; el motor valida, tira dados y guarda; la IA narra lo que pasó.
- Solo escriben estado los módulos de `oathforge/services/`.
- Todo texto visible para el jugador existe en español e inglés (`oathforge/i18n/locales/`, o `{es, en}` en `content/*.yaml`).
- Proveedor de IA: Gemini (`google-genai`). No cambiar de proveedor sin que Josue lo pida.

## Comandos

```powershell
.venv\Scripts\python -m pytest          # tests (Postgres si TEST_DATABASE_URL conecta; si no, SQLite)
.venv\Scripts\oath bot                 # arrancar el bot
.venv\Scripts\oath reset-players       # borrar todos los jugadores (--yes para confirmar)
.venv\Scripts\oath delete-player Aldric # borrar un jugador por nombre o id de Telegram (--yes para confirmar)
.venv\Scripts\alembic upgrade head      # migraciones
.venv\Scripts\oath simulate --level 1-5   # simulador de combates para el balance
.venv\Scripts\oath tgtest send "/start"   # jugar con el bot desde la cuenta de prueba (también press, show)
```

`oath help` lista los comandos de consola (`oathforge/cli.py`; `oathforge` es el nombre largo); si añades uno, añádelo a su grupo en `COMMANDS`.
