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
- Nunca hagas commit directamente en `main`. Solo se lleva trabajo a `main` cuando Josue lo pide.
- Antes de empezar, trae lo nuevo: `git fetch` y `git merge origin/main`.
- Los testers apuntan bugs e ideas en su `TODO-<nombre>.md`; al hacer push a su rama, una GitHub Action lo copia a `main`.

## Commits y PR

- No añadas `Co-Authored-By` ni ninguna atribución a Claude en commits ni en PR.

## Reglas del proyecto

- **La IA nunca decide resultados.** Interpreta texto → intención; el motor valida, tira dados y guarda; la IA narra lo que pasó.
- Solo escriben estado los módulos de `oathforge/services/`.
- Todo texto visible para el jugador existe en español e inglés (`oathforge/i18n/locales/`, o `{es, en}` en `content/*.yaml`).
- Proveedor de IA: Gemini (`google-genai`). No cambiar de proveedor sin que Josue lo pida.

## Comandos

```powershell
.venv\Scripts\python -m pytest          # tests (Postgres si TEST_DATABASE_URL conecta; si no, SQLite)
.venv\Scripts\python -m oathforge.main  # arrancar el bot
.venv\Scripts\alembic upgrade head      # migraciones
```
