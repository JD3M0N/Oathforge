# Facies — interfaz en Telegram

Resumen de [Possibilium §4](Possibilium.md#s04). Cómo se ve el juego en el chat.

## Estado actual (0.10.8)

- **Teclado fijo** (`ReplyKeyboardMarkup` persistente, `KEYBOARD_VERSION = 3`): 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario, con la pista «Escribe lo que haces…» en el campo de texto. Sus etiquetas nunca llegan a la IA como texto libre.
- **Escena** (lo social): lugar, hora del juego y cuánto falta para el cambio («☀️ 14:30 · anochece en 55 min»), «👥 Aquí:» en lista y los botones 🧭 Viajar · 🔎 Investigar · 💬 Hablar · 🛒 Comerciar · ⚒ Actividades (n), más «Seguir viaje», acciones de misión y «🖼️ Ver lugar» (en la plaza, la ciudad). Texto libre que interpreta Gemini.
- **⚒ Actividades** (lo que se hace con las manos, `render.activities_view`): cazar, recolectar, expedición, rastrear, desollar, descansar, fabricar y curar, cada una con duración y qué falta. La disponibilidad sale de `activities.check`, la misma regla que usa `start`: sin herramienta no hay botón, sino «🛒 Pico · ir a Mercado» hacia quien la vende. Desde ahí, 🛠️ Oficios (también desde Héroe).
- **Mensajes**: la navegación (menús, pestañas, Volver, Actividades) edita el mismo mensaje. Cada acción deja **un** mensaje con el resultado y la cabecera del lugar con sus botones, y el panel pulsado pierde los suyos. Subidas de nivel, crónicas y combates siguen en mensajes propios. Las compras, equipar, aprender y fabricar ponen el resultado encima del mismo menú.
- **Textos** (0.10.1): pruebas «🎲 Supervivencia: 2 + 1 = 3 vs CD 13 · ❌ Fallo»; leyenda ●/○/· en `/sheet`; cada lugar con su artículo (`article`, `Location.phrase()`), con «al»/«del» contraídos por el traductor; `<clave>_one` cuando una cuenta (`n`, `count`, `turns`, `left`) vale 1.
- **Inventario** (0.10.2): resumen (puesto y cuántos de cada tipo) y pestañas ⚔️ Equipo · 🧪 Consumibles · 🧱 Materiales · 🧰 Herramientas, una línea por objeto con su icono y `/item_`. Cada objeto tiene `icon` (`Item.label`), visible en botín, recetas, tiendas y combate.
- **Rechazos en ventanita** (`answerCallbackQuery`): «Necesitas un pico», un menú viejo o un doble toque no escriben en el chat; el mensaje pulsado pasa a la vista actual y nada se gasta dos veces.
- **Comandos** (menú y `/help`), siempre en inglés y sin alias en español: `/start`, `/look`, `/hero` (resumen), `/sheet` (ficha completa con retrato), `/inventory`, `/journal`, `/achievements`, `/quests`, `/map`, `/report`, `/professions`, `/classes`, `/rulebook` (alias `/rules`), `/settings`, `/language`, `/cancel`.
- **Comandos de consulta** enlazados desde los mensajes: `/class_<clase>`, `/skill_<clave>`, `/prof_<clave>`, `/r_<receta>` (su ficha, con el origen de lo que falta), `/craft_<receta> n` (fabricar escribiendo), `/item_<clave>`, `/monster_<clave>`, `/masteries`, `/hobbies`, `/lineage` (alias `/race`), `/background`, `/skin`. Funcionan sin personaje cuando tienen sentido.
- **Logros**: /achievements; acceso desde héroe y diario, seis entradas por página, detalle, categorías, pendientes, obtenidos y destacados. Las pistas pueden revelarse y los ocultos no aparecen hasta conseguirlos. En la interfaz siempre «Logros» y «puntos de logro». Sin porcentaje global que penalice decisiones alternativas.
- **Identidad y avisos**: un título y tres destacados en el héroe, el título también en `/sheet` y en la cabecera del Libro del Héroe; tres objetivos en el diario. Anuncios privados agrupados tras el commit, recuperables tras reinicio.
- **Diario (El Libro del Héroe)**: siete pestañas que editan un mensaje, la activa entre «• … •»: 📖 Ahora (actividad en marcha, viaje a medias, objetivo de misión y objetivos seguidos, siempre con botón para continuar), 📜 Misiones (en curso y terminadas), 🕯️ Crónica (los hechos del motor, 8 por página, agrupados por día; los antiguos bajo «Antes de este libro»), 🏆 Logros, 🐉 Bestiario, 🗣️ Rumores y 📈 Estadísticas (las de siempre más los contadores de la crónica). Abrir el diario no gasta IA.
- **`/rulebook`**: índice con botones y páginas ◀ ▶ desde `content/rulebook.yaml`, con `{marcadores}` rellenados por el motor (`render.rule_numbers`): CD, nivel máximo, puntos de creación, CD de huida, coste y duración del descanso, pérdida de oro al caer, segundos de desuello, probabilidad de emboscada y las frases de beta. Una prueba de contenido exige que cada marcador tenga valor. Sección nueva 🏆 Logros y títulos.
- **`/settings`**: idioma y tiradas manuales (desactivadas por defecto; el dado de Telegram es un d6 decorativo y la tirada real es el d20 del motor; la tirada se lanza con «🎲 Tirar el dado»).
- **Mapa**: dónde estás, 📜 objetivo, esta zona, otras zonas conocidas y 🌫️ sin explorar; al llegar sin nada más, el mensaje del mapa se convierte en la escena. Los puestos de oficio no ocupan una línea cada uno: salen nombrados bajo su calle, con un botón «🛠️ Puestos (n)» que los abre.
- Avisos: subida de nivel en mensaje propio, poca vida al cazar, «lo siguiente» de cada misión, resultado de actividades aunque estés desconectado.
- Solo chat privado.

## Referencias (partidas de prueba, 18-10-2026)

- **Chat Wars** (`@chtwrsbot`): teclado fijo de 5 botones con emoji y 1–2 palabras, menús de 3 niveles como mucho y ⬅️ Volver siempre; las listas largas usan `/comandos` en el texto; las actividades con tiempo avisan al terminar con un mensaje corto con botín.
- **AshWars** (`@AshWarsBot`, «Threnor»): cabeceras en MAYÚSCULAS con emoji y separador ━━━; barras ▰▱ para vida, maná y experiencia; atributos en dos columnas; línea «[ Estado: ⛺ Campamento ]»; pestañas inline con la activa marcada («·🎒Mochila·»); el mensaje pulsado se queda sin botones y el siguiente paso llega en uno nuevo; ventanita con el nombre del botón pulsado.

### Ideas aprovechables (Chat Wars y AshWars, 18-10-2026)

**Chat Wars** (`@chtwrsbot`, castillo Moonlight)
- Menú principal de 4 botones en una cuadrícula 2×2 (🏅 Yo · 🗺 Misiones · 🏰 Castillo · 💬 Chat). Todo lo demás cuelga de ahí con ⬅ Volver.
- Cabecera del héroe en una línea por dato: nivel con %, ⚔️/🛡 emparejados, 🔥 exp, ❤️ vida, 🔋 aguante `7/7`, 💰 oro, **«Estado: 🛌 Descanso»** (qué estás haciendo ahora) y «Más: /hero». El perfil corto cabe en una pantalla.
- El perfil largo es una lista de atajos `/ach`, `/class`, `/stock`, `/settings`: los comandos clicables sustituyen a botones.
- Cada actividad con tiempo dice su duración en el propio botón («🌳 Bosque 3 min»).
- Un aviso de evento global en el menú («Batalla de los siete castillos en 2 h 2 min», «la taberna abre por la tarde»): da un porqué para volver.
- Contenedores en el inventario: 🎒 Mochila · 📦 Recursos · 🗃 Varios, con «0/15» de capacidad. Es lo que ahora hacen nuestras pestañas.
- Pega mucho el «esto va de hablar con otros»: el primer mensaje manda al chat de jugadores.

**AshWars** (`@AshWarsBot`, Threnor)
- Un solo `Hero` con pestañas inline: 🔎 Detalles · 🏅 Títulos / 👤 Héroe · 🎒 Mochila · 🗡 Equipo; la activa va entre puntos y se edita el mismo mensaje.
- **Crafteo** (⛺ Campamento → 🔨 Montaje / ⚒️ Forja / ⚗️ Alquimia / 🛠️ Reparar):
  - Las **estaciones se montan** con materiales (tienda de campaña 5 madera + 15 fibra; forja 5 carbón + 20 piedra + 5 hierro; caldero; fogón; altar rúnico) y son móviles.
  - Cada estación lista sus recetas con 🔒 hasta montarla, con el motivo («Monta el Forja para habilitar esta operación»).
  - Antes de montar, cada requisito sale como `▫️ 🪵 Madera 0/5` y una línea ⚠️ «te falta 0/5 🪵 Madera · 0/15 🌾 Fibra».
  - Selector de **fuente de recursos** (🎒 Mochila / 📦 Baúl) en la propia pantalla.
  - Lo que se gasta (consumibles) y lo que se queda (estaciones) se dice en la cabecera de cada taller.
  - Relaciona con el TODO «fabricar sin estación fija»: aquí la estación es un objeto que se construye una vez.
- **Salidas** (🍁 Quest → Cazar / Recolectar / Party): cada bioma con su descripción literaria y «20 s de marcha»; luego «⚔️ Incursión rápida» o «⛺ Asentar campamento». La incursión avisa de antemano de la fauna en la ruta y de qué se pierde si caes o huyes («se perderá todo el botín»), y deja un botón «🔄 Ver la incursión».
- Misiones en un tablón con pestañas 📖 Historia · ⚔️ Sendas · 🧭 Tablón, recompensa resumida arriba (🎖 XP · 🪙 oro · 🧠 aprendizaje) y objetivos con ✅/▫️.
- Los textos de arranque usan cabeceras en mayúsculas con emoji, y una barra ━━━.

- **Combate de AshWars** (emboscada en la incursión): una sola tarjeta que se edita por turno, con ambos bandos (❤️ barra, 🔵 maná, ⚔️/🛡) y debajo el registro del turno en 2–3 líneas; el enemigo desconocido se llama «❓ ???» y se revela al ganar («¡Nuevo espécimen registrado!»). Botones: 4 acciones en 2×2 más 🧪 Objeto y 🏃 Huir. Al ganar, el botín en líneas con emoji (🟤 Cuero ×2 · 🥩 Carne ×2 · 🪙 +5 · 🎖 XP · 🏹 XP de Caza) y el desgaste del equipo. «Retirarse» pide confirmación diciendo qué se pierde y qué se conserva.
- Una incursión larga se resuelve **dentro de la misma tarjeta**: tras el combate sigue «La extracción continúa» sin mensajes nuevos.

**Crafteo probado de verdad** (monté la Tienda de campaña: 3 incursiones de recolección, cada una con su emboscada, hasta juntar 5 madera + 15 fibra):
- El botón de montar solo aparece cuando los materiales están completos; no hay «intentar y fallar», el panel pasa de «materiales incompletos» a mostrar «🔧 Montar X» directamente.
- Al craftear, un mensaje propio de confirmación («✅ Tienda de campaña montada y operativa») además de refrescar el panel con la lista.
- La estación da una mejora medible de inmediato, no solo desbloquea recetas: la Tienda subió la curación del campamento de 25 %/h a 80 %/h. Se nota el resultado de haber invertido el material.
- El contador de pendientes en el menú («🔨 Montaje (5)» → «(4)») baja al completar una estación: progreso visible del campamento en conjunto, no solo de cada receta.
- Una estación bloqueada (sin Forja) igual muestra el coste de su receta («Coste: 0/1 Mineral de Hierro · 1 🪙»), para saber qué conseguir antes de poder usarla.
- El bestiario recuerda entre encuentros: la segunda vez que salió el Antílope Cantautor (ya identificado antes) apareció con su nombre, no «❓ ???».

**Para Oathforge (candidatas)**
- [ ] Enemigo desconocido como «❓ ???» hasta derrotarlo o descubrirlo (ya tenemos el bestiario por tiers; mostrarlo en el combate), coherente con que ya se nombre una vez identificado.
- [ ] Confirmación al abandonar/huir que diga qué se conserva y qué se pierde.
- [ ] El botón de fabricar un objeto solo aparece con los materiales completos, no deshabilitado: ya es así en `craft_menu`; revisar que el de `activities_view` (herramientas) siga la misma regla.
- [ ] Mostrar el coste de una receta aunque la estación esté bloqueada por otra regla (p. ej. una especialización no desbloqueada).
- [ ] Línea de **estado actual** en la cabecera («Estado: ⛏️ Minando, 3 min») ya la tenemos en el panel de actividad; llevarla también a `/hero`.
- [ ] Avisar **antes** de empezar de lo que se arriesga (como AshWars en la incursión: emboscada, qué se pierde). Ya hay un aviso en la expedición larga; unificarlo en la vista de Actividades.
- [ ] Mostrar los ingredientes de una receta con `have/need` y una línea de «te falta» (ya en `craft_menu`; revisar el formato con el de AshWars).
- [ ] Capacidad de la mochila `8/15` (decide con el cofre personal, F06).
- [ ] Un aviso de **evento del mundo** en la escena o en el teclado (llegada de caravana, cambio de hora) para dar motivo de volver.

## Decidido

- Interfaz progresiva: pocas opciones claras al principio.
- Un mensaje que se edita para estado (combate, mapa) en lugar de diez mensajes por acción.
- Navegación editada, hitos en mensaje nuevo; un mensaje por acción; rechazos en ventanita (0.10.0).
- Los iconos acompañan palabras; todo audio tendrá texto.

## Próximo

- **Oficios** ([F15](roadmap.md#F15), [contrato](roadmap-profesiones.md)): fabricar con ×1 · ×5 · máx y el coste total, ingredientes con `tengo/necesito` y de dónde sale lo que falta, selector 🎒 Mochila / 📦 Cofre, y comandos nuevos `/recipes`, `/r_<id>`, `/craft_<id> [n]`, `/guild`, `/room` y `/stash`.
- **UX-04** estados explícitos de acción (pendiente, interpretando, requiere tirada, resuelta, rechazada).
- **UX-05** `/resume`, `/unstuck`, `/party`, `/rest`.
- Inventario comparativo.
- Modo silencioso cuando haya audio ([ars](ars.md)); Mini App más adelante.

## Preguntas abiertas

- ¿Cuántos botones por pantalla antes de que sea incómodo en el móvil?
- ¿Editar la escena o enviar una nueva al cambiar de lugar?
- ¿Comandos también en español (`/ficha`, `/mapa`)?
