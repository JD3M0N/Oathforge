# ADR 004 — Gemini es el único proveedor de IA

**Estado:** vigente

## Contexto

Varios proveedores multiplican prompts, presupuestos y pruebas.

## Decisión

Se usa `google-genai` y solo `ai/client.py` habla con él (lo exige import-linter). El proveedor no se cambia sin que Josue lo pida.

## Consecuencias

Presupuesto diario por usuario y global (`ai_usage`) comprobado antes de cada llamada.
