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
- **v0.7.0**: `/settings` (⚙️ Ajustes) reúne idioma y tiradas manuales; `/roll` sale del menú. Las tiradas manuales están desactivadas por defecto y, al activarlas, un aviso explica que el dado de Telegram es un d6 decorativo y que la tirada real es el d20 del motor. La tirada pendiente se lanza con el botón «🎲 Tirar el dado». `/prof_<oficio>` abre la guía de cada oficio y afición.
- **v0.7.7–0.7.8**: creación de personaje con emojis (linajes, trasfondos, clases, atributos y confirmación) y ayuda a mitad de la creación: `/lineage` (alias `/race`) y `/background` responden sin personaje y sin romper el asistente. El paso de trasfondo muestra los 4 básicos (`basic: true` en `content/backgrounds.yaml`) y «📜 Más trasfondos…» abre los 12. No están en el menú de Telegram: se llegará a ellos desde `/rulebook`.
- **v0.7.9**: trasfondo propio. «✍️ Escribir mi propio trasfondo» pide nombre (primera línea) e historia (20–300 caracteres) en un mensaje; Gemini lo revisa (`oathforge/ai/moderation.py`) y, si lo acepta, el jugador elige 2 habilidades. Se guarda en `characters.custom_background` y sale en `/sheet` y en el contexto del narrador.
- **v0.7.10**: `/rulebook` (alias `/rules`, en el menú): índice de secciones con botones y una página por sección con ◀ ▶ (tiradas y CD, atributos, CA, PV y dado de golpe, combate, descanso, linajes, trasfondos, clases, oficios, viajar). Los textos están en `content/rulebook.yaml`: una sección nueva es una entrada más. El mensaje de bienvenida de `/start` lo menciona y trae el botón «📖 Reglamento»; funciona sin personaje.
- **v0.7.11**: `/skill_<clave>` (por ejemplo `/skill_lay_on_hands`): una habilidad de clase en detalle. Muestra la clase y el nivel, el tipo de acción y los usos, una explicación larga (campo opcional `details` en `content/classes.yaml`; si falta, la descripción corta) y «⚙️ Cómo funciona», que se genera con los datos que usa el motor (daño, salvación, área, curación, estados, CA…). Se enlaza desde `/class_<clase>`, la tarjeta de subida de nivel y `/sheet`.
- **v0.7.17**: teclado fijo de Telegram (`ReplyKeyboardMarkup` persistente) con 🧝 Héroe · 🗺 Mapa · 🎒 Inventario · 📖 Diario. Llega al crear el personaje, con `/start` y, a quien ya jugaba, en su siguiente vista (una vez por idioma, `users.settings.keyboard`). Sus etiquetas, en cualquier idioma, abren la vista de su comando y nunca llegan a la IA como texto libre. El reglamento pasa a 📘 y el bestiario a 🐉 para no repetir el 📖 del diario.
- **v0.7.18**: la escena muestra la hora del juego y cuánto falta para que anochezca o amanezca (`exploration.clock`, `until_switch`), y «👥 Aquí:» como lista. `/quests` solo con lo que está en curso; las misiones terminadas pasan a «📚 Registro» en el diario (verbo `jrl`).
- **v0.7.19**: fichas de consulta. `/item_<clave>` (qué es, para qué sirve, ingrediente de, dónde se consigue, valor), enlazada en cada «Obtienes…» y en el inventario; `/monster_<clave>` con solo la imagen, enlazada al empezar un combate; `/masteries` y `/hobbies` con pestañas entre ellas y `/professions`. El `/rulebook` admite `{marcadores}` que se rellenan con las cifras del motor (`render.rule_numbers`).
- Canales de anuncios: https://t.me/OathForge (inglés) y https://t.me/OathForge_es (español).

## Ideas

### Principios (GDD §2.1)

- **Escena compacta**: lugar, hora y clima, descripción, actores visibles, sucesos importantes y opciones, todo en un mensaje.
- **Interfaz progresiva**: al principio pocas opciones claras; aparecen más botones cuando el personaje desbloquea sistemas.
- **Un mensaje de estado que se edita** (turno, PV, decisiones) en lugar de diez mensajes por acción; los mensajes nuevos, solo para cambios narrativos.
- Comandos que faltan: `/party`, `/rest`. `/map` existe desde la v0.7.6 (ver `mundo-y-misiones.md`).

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
