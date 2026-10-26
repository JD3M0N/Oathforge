# ADR 007 — Proyecto de una sola persona

**Estado:** vigente

## Contexto

Hubo ramas por tester y TODO sincronizados a `main`, sin uso real.

## Decisión

Josue (JD3M0N) trabaja solo en `josue-development`; sin PR, sin testers y sin ramas por persona. `main` solo recibe trabajo cuando Josue lo pide, y con la CI en verde.

## Consecuencias

Cada commit sube la versión y lleva su entrada de CHANGELOG (`vX.Y.Z: resumen`). Reglas en `CLAUDE.md` y `AGENTS.md`.
