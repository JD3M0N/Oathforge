# Facies — interfaz en Telegram

Resumen de [Possibilium §4](Possibilium.md#s04). Cómo se ve el juego en el chat.

## Estado actual (0.8.2)

- **Teclado fijo** (`ReplyKeyboardMarkup` persistente, `KEYBOARD_VERSION`): 📍 Lugar · 🧝 Héroe · 🗺 Mapa / 🎒 Inventario · 📖 Diario. Sus etiquetas nunca llegan a la IA como texto libre.
- **Escena**: lugar, hora del juego y cuánto falta para el cambio («☀️ 14:30 · anochece en 55 min»), «👥 Aquí:» en lista, acciones con botones y texto libre que interpreta Gemini.
- **Comandos** (menú y `/help`): `/start`, `/look`, `/hero` (resumen), `/sheet` (ficha completa con retrato), `/inventory`, `/journal`, `/quests`, `/map`, `/report`, `/professions`, `/classes`, `/rulebook` (alias `/rules`), `/settings`, `/language`, `/cancel`.
- **Comandos de consulta** enlazados desde los mensajes: `/class_<clase>`, `/skill_<clave>`, `/prof_<clave>`, `/item_<clave>`, `/monster_<clave>`, `/masteries`, `/hobbies`, `/lineage` (alias `/race`), `/background`, `/skin`. Funcionan sin personaje cuando tienen sentido.
- **Diario**: misiones en curso con avance, 📚 Registro de terminadas, 🐉 Bestiario, 🗣️ Rumores y 📈 Estadísticas.
- **`/rulebook`**: índice con botones y páginas ◀ ▶ desde `content/rulebook.yaml`, con `{marcadores}` rellenados por el motor (`render.rule_numbers`).
- **`/settings`**: idioma y tiradas manuales (desactivadas por defecto; el dado de Telegram es un d6 decorativo y la tirada real es el d20 del motor; la tirada se lanza con «🎲 Tirar el dado»).
- **Mapa**: dónde estás, 📜 objetivo, esta zona, otras zonas conocidas y 🌫️ sin explorar; al llegar sin nada más, el mensaje del mapa se convierte en la escena.
- Avisos: subida de nivel en mensaje propio, poca vida al cazar, «lo siguiente» de cada misión, resultado de actividades aunque estés desconectado.
- Solo chat privado.

## Decidido

- Interfaz progresiva: pocas opciones claras al principio.
- Un mensaje que se edita para estado (combate, mapa) en lugar de diez mensajes por acción.
- Los iconos acompañan palabras; todo audio tendrá texto.

## Próximo

- **UX-04** estados explícitos de acción (pendiente, interpretando, requiere tirada, resuelta, rechazada).
- **UX-05** `/resume`, `/unstuck`, `/party`, `/rest`.
- Pruebas de habilidad más claras (hoy «🎲 Survival: 2 → 3 vs DC 13 ❌»), nombres traducidos y leyenda ●/○/· en `/sheet`.
- Gramática: «Llegas al Mercado / a la Taberna» (artículo por lugar) y «1 ronda» en singular.
- Inventario comparativo; mensajes de estado editables en más vistas.
- Modo silencioso cuando haya audio ([ars](ars.md)); Mini App más adelante.

## Preguntas abiertas

- ¿Cuántos botones por pantalla antes de que sea incómodo en el móvil?
- ¿Editar la escena o enviar una nueva al cambiar de lugar?
- ¿Comandos también en español (`/ficha`, `/mapa`)?
