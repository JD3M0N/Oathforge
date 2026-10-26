# ADR 001 — El motor decide, la IA narra

**Estado:** vigente

## Contexto

Un narrador de IA que decidiera resultados daría oro, XP u objetos distintos cada vez y sería manipulable por el jugador.

## Decisión

Un motor d20 determinista (`oathforge/engine/`, RNG inyectable, todo azar por `engine/dice.py`) valida, tira y guarda. La IA solo interpreta el texto libre a una intención estructurada y narra lo que ya pasó.

## Consecuencias

El texto del jugador va como datos (`<player_text>`); los ids propuestos por la IA deben existir en el contexto; sus dificultades se limitan a un rango; si falla o se agota el presupuesto, el juego sigue con `content/fallbacks/`. Detalle: `AGENTS.md`, `narratio.md`.
