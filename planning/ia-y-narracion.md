# IA y narración

## Estado actual

- Gemini (`google-genai`): modelo rápido para interpretar intenciones y modelo narrativo para narrar. Si el narrativo falla, se usa el rápido con un enfriamiento.
- **Regla de oro: la IA nunca decide resultados.** Interpreta → el motor valida y tira → la IA narra los hechos.
- El texto del jugador va delimitado como datos; los ids se validan contra el contexto; las dificultades están acotadas.
- Presupuesto diario por usuario y global; si se agota, se usan plantillas.
- NPC con persona, objetivos, secretos y memoria.
- v0.1.1: cada llamada se guarda en `artifacts/ai/` (prompt, respuesta, modelo, tokens, latencia).

## Ideas

- Revisar en `artifacts/ai/` las interpretaciones erróneas y añadir ejemplos al prompt.
- Narración de combate al final de cada ronda (resumen de los hechos), opcional.
- Resúmenes del diario generados a partir de los eventos.
- Medir el coste medio por jugador y hora con `artifacts/events/`.
- Voz (TTS) para los NPC importantes.

## Preguntas abiertas

- ¿Cuánto texto de IA por acción resulta agradable en Telegram? Hoy, 2–4 frases.
- ¿Merece la pena cachear narraciones de situaciones repetidas?
