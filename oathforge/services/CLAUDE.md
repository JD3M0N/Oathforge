# services/ — el único sitio que escribe estado

- Cada función recibe la `AsyncSession` abierta por quien llama (`database/session.py: session_scope`). Aquí no se hace commit a mitad de una acción.
- **Bloquea antes de cambiar**: lee la fila con `with_for_update()` (por ejemplo, `active_encounter(..., lock=True)`), revalida y después escribe. Las tablas con columna `version` (`version_id_col` de SQLAlchemy) detectan solas una escritura concurrente.
- **Idempotencia**: toda acción de un botón reclama su nonce con `audit.claim(...)`. Si devuelve `None`, es un replay: no hagas nada.
- **Nada lento dentro de la transacción**: ni Gemini ni Telegram con filas bloqueadas. Primero se lee el contexto, luego se llama a la IA y después se bloquea y se resuelve.
- La economía (oro, XP, objetos, confianza) solo cambia aquí, con reglas del motor, nunca con lo que diga la IA.
- Un cambio de economía, permisos o concurrencia lleva su test en `tests/services/`. Las pruebas de concurrencia necesitan Postgres (`TEST_DATABASE_URL`).
