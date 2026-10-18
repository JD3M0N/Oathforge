# Facies — interfaz en Telegram

Resumen de [Possibilium §4](Possibilium.md#s04). Cómo se ve el juego en el chat.

## Estado actual (0.10.2)

- **Teclado fijo** (`ReplyKeyboardMarkup` persistente, `KEYBOARD_VERSION = 3`): 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario, con la pista «Escribe lo que haces…» en el campo de texto. Sus etiquetas nunca llegan a la IA como texto libre.
- **Escena** (lo social): lugar, hora del juego y cuánto falta para el cambio («☀️ 14:30 · anochece en 55 min»), «👥 Aquí:» en lista y los botones 🧭 Viajar · 🔎 Investigar · 💬 Hablar · 🛒 Comerciar · ⚒ Actividades (n), más «Seguir viaje», acciones de misión y «Ver ciudad». Texto libre que interpreta Gemini.
- **⚒ Actividades** (lo que se hace con las manos, `render.activities_view`): cazar, recolectar, expedición, rastrear, desollar, descansar, fabricar y curar, cada una con duración y qué falta. La disponibilidad sale de `activities.check`, la misma regla que usa `start`: sin herramienta no hay botón, sino «🛒 Pico · ir a Mercado» hacia quien la vende. Desde ahí, 🛠️ Oficios (también desde Héroe).
- **Mensajes**: la navegación (menús, pestañas, Volver, Actividades) edita el mismo mensaje. Cada acción deja **un** mensaje con el resultado y la cabecera del lugar con sus botones, y el panel pulsado pierde los suyos. Subidas de nivel, crónicas y combates siguen en mensajes propios. Las compras, equipar, aprender y fabricar ponen el resultado encima del mismo menú.
- **Textos** (0.10.1): pruebas «🎲 Supervivencia: 2 + 1 = 3 vs CD 13 · ❌ Fallo»; leyenda ●/○/· en `/sheet`; cada lugar con su artículo (`article`, `Location.phrase()`), con «al»/«del» contraídos por el traductor; `<clave>_one` cuando una cuenta (`n`, `count`, `turns`, `left`) vale 1.
- **Inventario** (0.10.2): resumen (puesto y cuántos de cada tipo) y pestañas ⚔️ Equipo · 🧪 Consumibles · 🧱 Materiales · 🧰 Herramientas, una línea por objeto con su icono y `/item_`. Cada objeto tiene `icon` (`Item.label`), visible en botín, recetas, tiendas y combate.
- **Rechazos en ventanita** (`answerCallbackQuery`): «Necesitas un pico», un menú viejo o un doble toque no escriben en el chat; el mensaje pulsado pasa a la vista actual y nada se gasta dos veces.
- **Comandos** (menú y `/help`), siempre en inglés y sin alias en español: `/start`, `/look`, `/hero` (resumen), `/sheet` (ficha completa con retrato), `/inventory`, `/journal`, `/achievements`, `/quests`, `/map`, `/report`, `/professions`, `/classes`, `/rulebook` (alias `/rules`), `/settings`, `/language`, `/cancel`.
- **Comandos de consulta** enlazados desde los mensajes: `/class_<clase>`, `/skill_<clave>`, `/prof_<clave>`, `/item_<clave>`, `/monster_<clave>`, `/masteries`, `/hobbies`, `/lineage` (alias `/race`), `/background`, `/skin`. Funcionan sin personaje cuando tienen sentido.
- **Logros**: /achievements; acceso desde héroe y diario, seis entradas por página, detalle, categorías, pendientes, obtenidos y destacados. Las pistas pueden revelarse. Sin porcentaje global que penalice decisiones alternativas.
- **Identidad y avisos**: un título y tres destacados en el héroe; tres objetivos en el diario. Anuncios privados agrupados tras el commit, recuperables tras reinicio.
- **Diario**: misiones en curso con avance, 📚 Registro de terminadas, 🐉 Bestiario, 🗣️ Rumores y 📈 Estadísticas.
- **`/rulebook`**: índice con botones y páginas ◀ ▶ desde `content/rulebook.yaml`, con `{marcadores}` rellenados por el motor (`render.rule_numbers`).
- **`/settings`**: idioma y tiradas manuales (desactivadas por defecto; el dado de Telegram es un d6 decorativo y la tirada real es el d20 del motor; la tirada se lanza con «🎲 Tirar el dado»).
- **Mapa**: dónde estás, 📜 objetivo, esta zona, otras zonas conocidas y 🌫️ sin explorar; al llegar sin nada más, el mensaje del mapa se convierte en la escena.
- Avisos: subida de nivel en mensaje propio, poca vida al cazar, «lo siguiente» de cada misión, resultado de actividades aunque estés desconectado.
- Solo chat privado.

## Referencias (partidas de prueba, 18-10-2026)

- **Chat Wars** (`@chtwrsbot`): teclado fijo de 5 botones con emoji y 1–2 palabras, menús de 3 niveles como mucho y ⬅️ Volver siempre; las listas largas usan `/comandos` en el texto; las actividades con tiempo avisan al terminar con un mensaje corto con botín.
- **AshWars** (`@AshWarsBot`, «Threnor»): cabeceras en MAYÚSCULAS con emoji y separador ━━━; barras ▰▱ para vida, maná y experiencia; atributos en dos columnas; línea «[ Estado: ⛺ Campamento ]»; pestañas inline con la activa marcada («·🎒Mochila·»); el mensaje pulsado se queda sin botones y el siguiente paso llega en uno nuevo; ventanita con el nombre del botón pulsado.

## Decidido

- Interfaz progresiva: pocas opciones claras al principio.
- Un mensaje que se edita para estado (combate, mapa) en lugar de diez mensajes por acción.
- Navegación editada, hitos en mensaje nuevo; un mensaje por acción; rechazos en ventanita (0.10.0).
- Los iconos acompañan palabras; todo audio tendrá texto.

## Próximo

- **UX-04** estados explícitos de acción (pendiente, interpretando, requiere tirada, resuelta, rechazada).
- **UX-05** `/resume`, `/unstuck`, `/party`, `/rest`.
- Inventario comparativo.
- Modo silencioso cuando haya audio ([ars](ars.md)); Mini App más adelante.

## Preguntas abiertas

- ¿Cuántos botones por pantalla antes de que sea incómodo en el móvil?
- ¿Editar la escena o enviar una nueva al cambiar de lugar?
- ¿Comandos también en español (`/ficha`, `/mapa`)?
