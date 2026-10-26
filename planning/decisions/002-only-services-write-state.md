# ADR 002 — Solo los servicios escriben estado

**Estado:** vigente

## Contexto

Si los handlers de Telegram escribieran modelos, las reglas se duplicarían y no se podrían probar sin el bot.

## Decisión

Solo `oathforge/services/` escribe estado; los handlers seleccionan, llaman a un servicio y pintan. `engine/` no conoce BD, Telegram ni IA.

## Consecuencias

Lo comprueban import-linter (capas) y `tests/test_layers.py` (el bot no escribe modelos). Cada botón lleva nonce y el combate usa `<encounter.version>.<turn_index>.<nonce>`, para que un doble clic o un menú viejo no ejecute dos veces.
