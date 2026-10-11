# Interfaz en Telegram

Cómo se ve y se siente el juego dentro del chat. Fuente: [GDD](referencias/gdd-aetherfall-chronicles.pdf) §2.

## Estado actual

- Comandos: `/start` (crear personaje), `/look`, `/sheet`, `/inventory`, `/journal`, `/language`, `/help` y `/cancel` (`oathforge/bot/handlers/commands.py`, `creation.py`).
- Escenas con botones inline y texto libre que interpreta Gemini; el panel de combate es un mensaje con botones.
- Solo chat privado.

## Ideas

### Principios (GDD §2.1)

- **Escena compacta**: lugar, hora y clima, descripción, actores visibles, sucesos importantes y opciones, todo en un mensaje.
- **Interfaz progresiva**: al principio pocas opciones claras; aparecen más botones cuando el personaje desbloquea sistemas.
- **Un mensaje de estado que se edita** (turno, PV, decisiones) en lugar de diez mensajes por acción; los mensajes nuevos, solo para cambios narrativos.
- Comandos que faltan: `/map`, `/quests`, `/party`, `/rest`.

### Acción rápida y acción libre (GDD §2.3)

- Botones para lo frecuente (Acercarse, Inspeccionar, Hablar, Desenvainar, Retirarse) y debajo «Describe cualquier otra acción».
- Intenciones compuestas: «me acerco como médico mientras oculto la daga» → acercamiento social + Engaño + ocultación; el motor comprueba si tienes la daga y si el guardia puede verla.
- **Estado explícito de cada acción**: pendiente, requiere tirada, resuelta, interrumpida o fallida. Mientras la IA piensa, un indicador breve y los botones bloqueados para no duplicar recompensas.

### Sesiones de distinta duración (GDD §2.4)

- Microaventura (1–3 min): un encargo, recolectar, mirar el mercado.
- Sesión normal (10–25 min): taberna, conversación, combate, misión local.
- Expedición (30–90 min o varios días): mazmorra, asedio, viaje.
- Juego pasivo: caravanas, fabricación con temporizador, rutinas de NPC.
- Tolerar desconexiones: el juego se reanuda donde quedó.

### Audio (GDD §2.5)

Todo audio tiene su texto equivalente. **Modo silencioso** en la configuración; nunca enviar audio automático en cada interacción. Detalle en [audiovisual.md](audiovisual.md).

### Mini App (más adelante)

Mapa visual, árboles de talentos y mercado. Validar siempre `initData` en el servidor.

## Preguntas abiertas

- ¿Cuántos botones por pantalla antes de que resulte incómodo en el móvil?
- ¿Editar el mensaje de escena o enviar uno nuevo al cambiar de lugar? (afecta al historial del chat)
- ¿Comandos en español además de en inglés (`/ficha`, `/mapa`)?
