# Interfaz en Telegram

Cómo se ve y se siente el juego dentro del chat. Fuente: [GDD](referencias/gdd-aetherfall-chronicles.pdf) §2.

## Estado actual

- Comandos: `/start` (crear personaje), `/look`, `/hero` (alias `/sheet`: hoja de héroe con barras de PV y XP, atributos, equipo, habilidades bloqueadas por nivel, reputación y uso diario de IA, v0.2.2), `/inventory`, `/journal`, `/language`, `/help` y `/cancel` (`oathforge/bot/handlers/commands.py`, `creation.py`).
- Escenas con botones inline y texto libre que interpreta Gemini; el panel de combate es un mensaje con botones.
- Solo chat privado.
- **v0.5.0**: `/quests` (misiones y su avance) y diario con Misiones, Bestiario y Rumores.
- **v0.5.1**: `/roll`. Sin tirada pendiente, activa o desactiva las tiradas manuales (`users.settings.manual_rolls`). Con ellas activadas, investigar, las acciones de misión con prueba y las acciones escritas que piden tirada esperan a que el jugador haga `/roll` (o pulse «🎲 Tirar el dado»). Entonces sale el dado animado de Telegram y, al pararse, el resultado del motor (d20 + bonificador contra la CD). El dado de Telegram solo va de 1 a 6, así que es decorativo: el resultado lo calcula siempre el motor. El combate no espera a `/roll`.
- **v0.5.6**: la subida de nivel llega en un mensaje propio (tarjeta por nivel con PV, atributo y habilidades nuevas explicadas), separada del mensaje de XP y botín.
- **v0.5.7**: `/classes` (lista de clases) y `/class_<clase>` (por ejemplo `/class_paladin`): dado de golpe, atributo principal, magia, competencias, equipo inicial, habilidades por nivel con tipo, usos y descripción, y especializaciones. Los `/class_<clase>` que salen dentro de un mensaje se pueden tocar; los enlazan la tarjeta de nivel y `/sheet`. Con tu propia clase, ✅ en lo desbloqueado y 🔒 en lo que falta. Funciona sin personaje.
- **v0.5.9**: `/report` y botón «📜 Informe» en el panel final: informe de la última batalla, con resumen y una página por ronda (botones ◀ ▶ que editan el mismo mensaje).
- Canales de anuncios: https://t.me/OathForge (inglés) y https://t.me/OathForge_es (español).

## Ideas

### Principios (GDD §2.1)

- **Escena compacta**: lugar, hora y clima, descripción, actores visibles, sucesos importantes y opciones, todo en un mensaje.
- **Interfaz progresiva**: al principio pocas opciones claras; aparecen más botones cuando el personaje desbloquea sistemas.
- **Un mensaje de estado que se edita** (turno, PV, decisiones) en lugar de diez mensajes por acción; los mensajes nuevos, solo para cambios narrativos.
- Comandos que faltan: `/map`, `/party`, `/rest`.

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
