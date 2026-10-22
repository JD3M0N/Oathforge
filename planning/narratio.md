# Narratio — IA y narración

Resumen de [Possibilium §25](Possibilium.md#s25).

**Regla de oro: la IA nunca decide resultados.** Interpreta → el motor valida, tira y guarda → la IA narra los hechos.

## Estado actual (0.10.26)

- Gemini (`google-genai`), con tres tipos de llamada: rápida (interpretar, revisar trasfondos), narrativa (narrar, diálogo de NPC) y crónica. **Los tres usan Gemini 3.1 Flash-Lite** (`GEMINI_MODEL_*` en `.env`).
- **Presupuesto**: 150 llamadas al día por jugador (`AI_USER_DAILY_CALLS`) y 15 crónicas (`AI_USER_DAILY_CHRONICLES`), comprobado antes de cada llamada (`ai_usage`). Si se agota, se avisa y se juega con botones y plantillas; `/hero` y `/sheet` muestran el uso.
- **Resiliencia** (0.7.29): cada modelo que falla se salta durante su cooldown (20 s; con 429 y `retryDelay`, lo que diga Google). Candidatos: modelo del tipo → rápido (solo narrativa) → `GEMINI_MODEL_FALLBACK` (opcional). Solo el último se reintenta una vez, y solo ante 500/502/503/504. Timeout de 10 s (8 s en crónicas), directo al respaldo.
- **Textos de respaldo** en `content/fallbacks/`:
  - `chronicles.yaml`: por desenlace y, en recolección, por oficio (`gather.mining`…);
  - `dialogue.yaml`: réplica neutral por NPC, sin género; si el NPC dio la misión activa, recuerda su pista;
  - `narration.yaml`: por desenlace (el final de combate manda);
  - `freetext.yaml`: aviso del DM (`budget_exhausted` solo si se agotó el presupuesto; `unavailable` en otro caso, sin prometer hora).

  Al menos 12 variantes por caso en es y en, con los mismos marcadores; se validan al arrancar y se eligen con `ai/fallbacks.pick` (`clave.contexto` → `clave` → `default`).
- **Cómo escribirlos**: segunda persona y fantasía oscura sobria; solo narran, nunca conceden objetos, oro, XP, curación ni confianza; no inventan armas, heridas, clima ni botín; el descanso empieza, no cura; la derrota se cuenta con dignidad; si no hay materiales, `{loot}` lo dice. Un NPC nuevo necesita su lista en `dialogue.yaml`.
- **Seguridad**: texto del jugador delimitado (`<player_text>`); ids de la IA validados contra el contexto (si no, `narrate_only`); dificultades acotadas.
- **Trasfondo propio**: `moderation.review_background` devuelve `accepted`, `adapted` o `rejected` con la guía canónica y el linaje como contexto. Acepta oficios adultos sin detalles explícitos, adapta plataformas y anacronismos conservando la idea y pide confirmación antes de guardar la propuesta. Sigue rechazando ventajas, autoridad, hechos canónicos y contenido que no admite una reformulación segura; sin Gemini no se acepta.
- NPC con persona, objetivos, secretos y memoria básica; cada llamada se guarda en `artifacts/ai/`.

## Decidido

- Gemini es el proveedor; no cambiarlo sin que Josue lo pida.
- Las crónicas no caen al modelo rápido.
- Contexto mínimo por llamada: escena, ficha mínima, actores pertinentes, 3–8 recuerdos y reglas del DM.

## Próximo

- **Diálogos incoherentes** (prioridad alta): Bram ofrece el fogón y luego lo niega y resta confianza por preguntas normales. Pasar al PNJ su saludo y lo que ofrece su lugar; no restar confianza por preguntar.
- Revisar la autoridad de `trust_delta` desde la respuesta IA (ticket AI-01); analizar el sistema de confianza.
- **IA-06** reserva atómica del presupuesto antes de llamar (AI-02); **IA-07** crónica single-flight (AI-03).
- **IA-01..05** memoria en capas: episódica con `event_id`, relacional por reglas, semántica con fuente y certeza, declaraciones separadas de hechos.
- Intérprete de respaldo por palabras clave sin IA; respuesta en personaje ante trampas por texto.
- Tercer uso de modelo para resúmenes en segundo plano; límite por minuto y longitud máxima de escena; coste por función.
- Banco de pruebas de abuso como tests con respuestas simuladas.

## Preguntas abiertas

- ¿Cuánto texto de IA por acción resulta agradable? Hoy 2–4 frases.
- ¿Cachear narraciones de escenas repetidas?
- ¿Aguanta la cuota de Flash-Lite una partida larga o hace falta plan de pago?
