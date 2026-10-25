# Oathforge — instrucciones para Claude

RPG narrativo para Telegram: un motor d20 determinista decide y Gemini narra. Las reglas de trabajo comunes (invariantes, mapa del repo, cómo leer gastando pocos tokens, pruebas y versionado) están en `AGENTS.md`:

@AGENTS.md

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
- Versionado obligatorio en cada commit (ver `AGENTS.md`). Los commits automáticos de la Action de TODO no suben versión.

## Serie 0.10-I (clases, progresión 1–20 y campaña)

Si la tarea es seguir esta serie, empieza por `planning/plan_implementacion_0.10.md` (estado, siguiente fase y reglas de cierre) y lee solo la fase que toca en `planning/roadmap_balance.md`, por rangos. Avanza una fase y para.

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
.venv\Scripts\oath simulate --level 1-5   # simulador de combates para el balance
.venv\Scripts\oath tutorial-stats        # minutos por misión del tutorial y dónde se atasca cada jugador
.venv\Scripts\oath tgtest send "/start"   # jugar con el bot desde la cuenta de prueba (también press, show)
```

`oath help` lista los comandos de consola (`oathforge/cli.py`; `oathforge` es el nombre largo); si añades uno, añádelo a su grupo en `COMMANDS`.
