# ADR 003 — Ninguna E/S lenta con un lock abierto

**Estado:** vigente

## Contexto

Gemini y Telegram tardan segundos; con filas bloqueadas (`SELECT … FOR UPDATE`) frenarían a todos los demás.

## Decisión

El flujo es leer contexto (transacción corta) → interpretar → bloquear, revalidar y resolver (transacción) → commit → enviar o narrar.

## Consecuencias

Hay que revalidar tras bloquear, porque el estado pudo cambiar mientras la IA pensaba. Las pruebas de concurrencia solo corren con Postgres.
