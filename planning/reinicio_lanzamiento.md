# Reinicio de lanzamiento

> Procedimiento del reinicio que **conserva a las personas y borra la partida** (roadmap_balance §16). No es `oath reset-players` (que borra también las cuentas). Todo lo que está aquí está implementado en la versión 0.10.41 y ensayado en pruebas contra PostgreSQL; el ensayo con una copia de producción real está pendiente y se hace antes del lanzamiento (B14). **No se ha ejecutado contra datos reales**; sí se ensayó el 2026-10-25 con una copia de la base local.

## Qué se borra y qué se queda

| Se borra | Se queda |
|---|---|
| Personajes, habilidades, ramas, modificadores y compañeros | `users`: cuenta de Telegram, idioma y **ajustes generales** (tiradas manuales) |
| Mochila, cofre, propiedad artesanal y vivienda | `ai_usage`: el presupuesto diario de IA nunca se reinicia con la partida |
| Misiones, logros, títulos, reputación y memoria de los PNJ | `media_files`: ids de Telegram de las imágenes (ahorran subidas) |
| Encuentros, actividades en marcha y premios pendientes | `action_logs`: auditoría técnica, con sus enlaces a personaje y usuario puestos a `NULL` |
| Rumores y hechos del mundo (`world_facts`, `location_state`) | El contenido (`content/`), que no está en la base |
| Ajustes de usuario atados a la partida vieja (p. ej. `keyboard`) | |

La lista de lo que se queda es `launch.KEEP_TABLES` y `launch.KEEP_SETTINGS` (`oathforge/services/launch.py`).

## Comandos

```powershell
.venv\Scripts\oath launch-reset                 # ensayo: lista lo que se borra y lo que se queda; no cambia nada
.venv\Scripts\oath launch-reset --yes           # copia de seguridad, borrado, comprobación y commit
.venv\Scripts\oath backup copia.json            # volcado lógico de toda la base (sólo lectura)
.venv\Scripts\oath restore copia.json           # muestra los conteos
.venv\Scripts\oath restore copia.json --yes     # reemplaza TODA la base por la copia
```

`launch-reset --yes` escribe antes un volcado en `artifacts/backups/before-launch-<fecha>.json`, borra, comprueba que no queda ninguna clave foránea apuntando a una fila desaparecida y sólo entonces confirma. Si encuentra huérfanos, hace *rollback* y no cambia nada. Con PostgreSQL en producción, `pg_dump` sigue siendo la copia oficial; este volcado es el portátil y el del ensayo.

## Procedimiento

1. **Staging.** Restaurar una copia de producción en una base de ensayo (`pg_dump` → `pg_restore`) y apuntar `DATABASE_URL` a ella. Ejecutar `oath launch-reset` y guardar los conteos.
2. **Copia.** En producción: `pg_dump` completo y, además, `oath backup <archivo>`. Verificar la restauración en staging (`oath restore <archivo> --yes` y comparar conteos).
3. **Mantenimiento.** Parar el bot (`oath stop`): no puede haber acciones nuevas ni actividades que se cobren solas.
4. **Migraciones.** `alembic upgrade head`. Nunca borrar usuarios con `reset-players` (eliminaría las cuentas).
5. **Reinicio.** `oath launch-reset --yes`. Anotar los conteos de antes y de después.
6. **Época.** Los botones antiguos llevan un identificador que ya no existe: al no haber personaje, el bot ofrece crear uno. No hace falta invalidar nada más. El anuncio de la versión sale por los canales a mano.
7. **Arranque.** `oath bot`; crear un personaje de prueba y recorrer `tests/features.md` en ES y EN con `tgtest`.
8. **Abrir** el acceso.

## Si algo falla

- **Antes de abrir:** `oath restore <archivo del paso 5> --yes` devuelve la base exactamente como estaba (ids y secuencias incluidos). Es el único caso en que se restaura.
- **Después de abrir:** no se restaura en silencio, porque se perderían partidas nuevas. Se trata como incidencia aparte.

## Ensayo hecho

`tests/services/test_launch.py` (se ejecuta en PostgreSQL si hay una base de pruebas, y en SQLite si no): un ensayo en seco no cambia nada; el reinicio borra el juego y deja cuentas, presupuesto de IA, imágenes y auditoría; ningún orfanato queda tras el reinicio; una cuenta puede crear personaje de nuevo; un volcado pasado por JSON restaura la base exacta tras el reinicio (conteos, fechas y contenido), y una copia de otra versión se rechaza sin tocar nada.

Ensayo en staging (2026-10-25): `pg_dump` de la base local (1 personaje, 46 misiones) → `pg_restore` en `oathforge_staging` → `launch-reset` en seco, `backup`, `launch-reset --yes` (quedan 0 personajes y 0 misiones; se conservan `users`, `media_files` y `action_logs`) → `restore` de la copia previa: las 24 tablas coinciden con la copia.
