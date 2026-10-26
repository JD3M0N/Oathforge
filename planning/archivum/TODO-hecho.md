# TODO — lo hecho (archivo)

Casillas `[x]` de [`TODO.md`](../../TODO.md), por sección, y su antigua sección «Hecho». Se mueve aquí al cerrarse.

## 🧙 Clases y progresión · [ordines](planning/ordines.md) · [progressio](planning/progressio.md)

- [x] Renombrar el golpe base del Paladín a **Castigo divino** (*Divine Smite*, como en D&D) en lugar de «Golpe Consagrado» (v0.10.29, junto con su barra de Convicción).
- [x] **Catorce clases** (B06, v0.10.29–v0.10.31): a las ocho de hoy se suman Explorador, Artífice, Monje, Chamán, Bárbaro y Caballero de la Muerte; Mago y Hechicero se fusionan en Hechicero y Sacerdote pasa a Clérigo (los ids `mage` y `priest` se conservan). Cada una con su recurso propio —Convicción, Foco, Furia, Energía, Maná, Resonancia, Esencia, Carga, Poder rúnico— en vez de usos por descanso (B03). *Hecho en tres entregas: Guerrero, Bárbaro, Paladín, Pícaro y Monje (v0.10.29); Clérigo, Hechicero, Druida y Bardo (v0.10.30); Brujo, Explorador, Artífice, Chamán y Caballero de la Muerte (v0.10.31). Faltan los retratos de las seis nuevas ([TODO-images](TODO-images.md)) y las 41 ramas (B07).*

## 🌍 Mundo, misiones y economía · [mundus](planning/mundus.md) · [mercatura](planning/mercatura.md)

- [x] **Entregar las misiones a quien las dio** (B02, v0.10.24): al cumplir los objetivos la misión queda «lista para entregar»; vuelves a su dador, pulsas «📜 Entregar» y cobras recompensa, hito y la misión siguiente en la misma transacción, una sola vez. El nivel pide además **XP e hito**: con la XP de sobra y sin el hito, el héroe espera sin perder un punto. *Falta: las misiones de la campaña que conceden los hitos (B09) y la carrera de dos entregas con PostgreSQL.*
- [x] **Recetas por tier**, resuelto de otra forma (v0.10.10–v0.10.18): **T0 son las recetas de rango 0–2 y T1 las de 3–5**, así que el tier no es un campo que mantener a mano. La básica de cada oficio es autónoma y la avanzada pide una pieza de otro oficio, que su maestro vende. El equipo de combate T1 se fabrica por rango y pide nivel 10 para llevarse.
- [x] **Inventario y almacenamiento**: el cofre de tu cuarto en el Gremio, 20 huecos ampliables con Carpintería, con `/room`, `/stash_<objeto> n` y `/take_<objeto> n` (v0.10.14).

## ✅ Hecho (por versión)

- [x] Registro de partidas en `artifacts/` para depurar y analizar (v0.1.1).
- [x] Guerrero y Sacerdote; tipos de daño y de criatura (v0.2.0).
- [x] Documentos de diseño en `planning/referencias/` y planning ampliado (v0.2.1).
- [x] Hoja de héroe (`/hero`) y límite de 150 llamadas de IA al día por jugador (v0.2.2).
- [x] Mundo en carpetas, catálogo de imágenes con caché de `file_id` y «Ver ciudad» en Crownreach (v0.3.0).
- [x] Mago, Druida y Bardo; tiradas de salvación y CD de conjuro, área y control (v0.4.0).
- [x] Retratos de 4 clases; `/hero` como resumen y `/sheet` como ficha completa con retrato (v0.4.1).
- [x] Brujo jugable (Maleficio, `kind: curse`) con retrato de hombre y mujer, elección de sexo al crear y `/sheet` en el menú de comandos de Telegram (v0.4.4).
- [x] **Sistema de misiones**: cadena de 6 misiones hasta nivel 5, diario con Misiones (avance de cada una), Bestiario y Rumores, y `/quests` (v0.5.0).
- [x] Zona de caza: Prado de los Colmillos, con jabalíes de día, murciélagos de noche y el Viejo Colmillo (v0.5.0).
- [x] Cripta Hundida más fácil (esqueletos y guardián más débiles, descanso gratis en el osario) y curva de XP más corta (v0.5.0).
- [x] Botones de combate con `encounter.version` + `turn_index`: un doble clic no ataca dos veces (v0.5.0).
- [x] Mejorar la creación de personaje: compra de atributos por puntos (27, como en D&D) con explicación de cada atributo (v0.5.0).
- [x] Emojis en la XP, el oro, las subidas de nivel y las habilidades nuevas (v0.5.0).
- [x] Canales de Telegram creados (v0.5.0).
- [x] Arreglados los `TimedOut` al subir retratos y los reintentos a Gemini con la cuota diaria agotada (v0.5.0).
- [x] `/roll`: tiradas manuales opcionales con el dado animado de Telegram para las pruebas de habilidad (v0.5.1).
- [x] Retratos de hombre y mujer para todas las clases, salvo la barda (v0.5.1).
- [x] Una tirada por habilidad y lugar al día: no se puede repetir hasta que salga (v0.5.2).
- [x] Probar que el d20 es justo: test estadístico de la distribución de las tiradas (v0.5.3, `tests/engine/test_dice_fairness.py`).
- [x] Simulación de batallas para el balance: `oathforge simulate`, estadísticas en `artifacts/simulations/` (v0.5.4).
- [x] `oathforge tgtest`: probar el bot de punta a punta desde una cuenta de Telegram (v0.5.5).
- [x] Subida de nivel en un mensaje propio: PV antes → después, mejora de atributo y cada habilidad nueva con su descripción (v0.5.6).
- [x] Ver cada clase y sus habilidades: `/classes` y `/class_<clase>`, enlazado desde la subida de nivel y `/sheet` (v0.5.7).
- [x] Panel de combate más bonito: 🛡️ CA de cada combatiente, 💥 críticos, golpe y daño en un bloque y separador por ronda (v0.5.8).
- [x] Informe de batalla: botón «📜 Informe» al acabar y `/report`, con resumen (daño, aciertos, críticos, recompensas) y cada ronda tirada a tirada (v0.5.9).
- [x] **Actividades de campo** (minar, talar, hierbas, pescar; expedición larga con emboscada; rastrear), 6 maestrías, desuello y **presupuesto de misiones**: crónica personal con Gemini 3.1 Flash-Lite, 15 al día por jugador, y textos genéricos cuando se acaba (v0.6.0).
- [x] **Oficios**: 2 activos de 6, Barrio de Oficios con estaciones, 12 recetas, fabricación atómica y `/professions` (v0.6.1).
- [x] **Pociones nuevas**: poción de maná (+1 uso de conjuro) y tónico del reposo (descanso corto, enfriamiento de 4 h), con efectos tipados (v0.6.2).
- [x] **Aficiones y oficios nuevos**: Cocina y Pesca sin plaza; Escribanía y Artificiería con pergaminos y bombas («🎒 Objetos» en combate); guía `/prof_<oficio>`; cambiar de oficio pide confirmación (v0.7.0).
- [x] **Textos genéricos de respaldo** para todo lo que escribe Gemini, organizados en `content/fallbacks/`, y crónicas con 503 → texto genérico al momento; Gemini 3.1 Flash-Lite para todo (v0.7.0).
- [x] **Dado decorativo**: tiradas manuales desactivadas por defecto, aviso al activarlas y `/settings` en lugar de `/roll` (v0.7.0).
- [x] **Capilla del Alba** con «Curar heridas» por 3 de oro y **descanso largo** de 8 h de juego (80 min) acostado en la posada (v0.7.0).
- [x] Arreglos de la partida de prueba del 13-10: barra de XP del nivel, «Jabalí A/B», 🧪 solo con pociones, tienda con estadísticas, la antorcha se vende por 1, «pensativo» en NPC femeninas (v0.7.0).
- [x] Ilustraciones e icono propio para cada criatura del bestiario, retrato de la barda y archivo de prompt junto a cada imagen (v0.7.3).
- [x] Emojis en la creación de personaje (linajes, trasfondos, «⚔️ Elige tu clase (ℹ️ /classes)», confirmación) y en los atributos: 💪 FUE, 🏹 DES, 🫀 CON, 🧠 INT, 🦉 SAB, 🎭 CAR (v0.7.7).
- [x] `/lineage` (o `/race`) y `/background` para consultar las opciones a mitad de la creación, y 12 trasfondos: los 4 básicos como botón y «📜 Más trasfondos…» para el resto (v0.7.8).
- [x] **Trasfondo propio**: nombre e historia escritos por el jugador, revisados por Gemini (sin insultos, contenido inapropiado ni trampas) y 2 habilidades a elegir (v0.7.9).
- [x] **`/rulebook`** en el menú y en la bienvenida: tiradas, atributos, CA, PV y dado de golpe, combate, descanso, linajes, trasfondos, clases, oficios y viajes (v0.7.10).
- [x] Página de cada habilidad de clase, `/skill_<clave>`, con su explicación y «⚙️ Cómo funciona» sacado de los datos del motor, y enlazada desde `/class_<clase>`, la subida de nivel y `/sheet` (v0.7.11).
- [x] **Tutorial de la sargenta Vale**: 8 misiones de nivel 1 a 3, una actividad por misión (hablar, moverse por la ciudad, cazar y desollar, recolectar, cocinar, minar, cazar de noche, curarse); sustituye a las misiones 1–3 (v0.7.13).
- [x] Bram ya no habla de «problemas al norte»: manda a los nuevos con la sargenta Vale y les ofrece el fogón (v0.7.13).
- [x] Arreglado «📜 Más trasfondos…»: volvía siempre a los 4 básicos y no se podía elegir, por ejemplo, Noble (v0.7.14).
- [x] `GAME_CLOCK_OFFSET_HOURS` en `.env` adelanta el reloj del juego para hacer pruebas, por ejemplo de noche a día (v0.7.14).
- [x] **Tutorial sin depender de la hora**: murciélagos en la mina de día y de noche; «Calles de Crownreach» manda también a la taberna; «Alistamiento» enseña el `/rulebook` y su sección nueva «🧺 Actividades» (v0.7.15).
- [x] **Tutorial acelerado**: la primera recolección o desuello que pide la misión activa termina al momento y da justo lo que falta, una vez por misión (v0.7.16).
- [x] **Teclado fijo** de Telegram: 🧝 Héroe · 🗺 Mapa · 🎒 Inventario · 📖 Diario (v0.7.17).
- [x] Hora del juego en la escena y cuánto falta para el cambio; «👥 Aquí» en lista; `/quests` solo con lo que está en curso y «📚 Registro» en el diario; «Nueva misión» enlaza a `/quests` (v0.7.18).
- [x] Fichas `/item_<clave>` (enlazadas al recibir un objeto y en el inventario) y `/monster_<clave>` (solo la imagen, enlazada al empezar un combate); `/masteries` y `/hobbies`; `/rulebook` con cada actividad en detalle y las cifras del motor (v0.7.19).
- [x] **Artificiería → Ingeniería** y la **Pesca como afición** de verdad, con la migración 0008 (v0.7.20).
- [x] **Actividades que terminan solas** aunque estés desconectado, sin «Recoger»; crónica y botín en un mensaje; desuello con `/skin` y duración por presa (v0.7.21).
- [x] **Combate**: ronda 0 con la iniciativa, los dos d20 con ventaja o desventaja, «📊 Resumen» y «📜 Informe» completo, y botones por clase con habilidad destacada 🌟 y «✨ Acciones» (v0.7.22).
- [x] «📈 Estadísticas» en el diario y texto largo de todas las habilidades en `/skill_<clave>` (v0.7.23).
- [x] `oath tutorial-stats`: minutos por misión del tutorial y dónde se atasca cada jugador (v0.7.24).
- [x] Arreglos de la partida de prueba con Brannoc: Ysolde cura gratis y cierra heridas graves en la beta (nadie se queda atascado herido y sin oro), jabalíes también de noche, respaldo de PNJ con la pista de la misión, aviso de poca vida y «lo siguiente» de cada misión (v0.7.25).
- [x] Informe sin el resultado repetido y con la ronda real en los botones, crónica y botín juntos tras emboscadas y rastreos, criaturas con artículo en las crónicas, `/map` ocupado sin caminos, tiendas por categorías, poción a 20 de oro, el ala de murciélago para la poción de maná y la escena sin botones repetidos (v0.7.26).
- [x] «📍 Lugar» en el teclado fijo y `oath restart` / `oath stop` (v0.7.27).
- [x] Moverse por el mundo sin que sea tedioso: a cualquier lugar conocido en un toque (de la cripta despejada a la plaza), una tirada de emboscada por viaje, «▶️ Seguir» tras una emboscada y botón 📜 al objetivo de la misión (v0.8.0).
- [x] Tutorial de 10 misiones sin mazmorras, objetivo `hunt` y beta instantánea (v0.8.2).
- [x] Planning reorganizado: Possibilium como libro principal, resúmenes en latín, `ars.md`, PDF retirados, `AGENTS.md` y laboratorio `content/officina/` (v0.8.3).
- [x] README raíz simple y motivador; flujo, seguridad y `artifacts/` en `AGENTS.md` (v0.8.4–0.8.5).
- [x] **Interfaz más cómoda**: ⚒ Actividades en el teclado fijo y en la escena (con lo que falta y dónde comprarlo), 🛠️ Oficios que reúne oficios, maestrías y aficiones, un solo mensaje por acción y rechazos en ventanita (v0.10.0).
- [x] **Textos claros**: tiradas «2 + 1 = 3 vs CD 13 · ❌ Fallo», leyenda ●/○/· en `/sheet`, «Llegas al Mercado / a la Taberna» y «1 ronda» en singular (v0.10.1).
- [x] **Inventario por pestañas** (equipo, consumibles, materiales, herramientas) y un icono para cada objeto en el inventario, el botín, las recetas y las tiendas (v0.10.2).
- [x] **Diario y reglamento**: el Libro del Héroe por pestañas, la Crónica desde los hechos del motor y el reglamento con las cifras reales (v0.10.7); logros auditados, un solo nombre y el título visible (v0.10.8).
- [x] **Oficios, maestrías y aficiones** (F15, v0.10.9–v0.10.19): el Gremio de Aventureros con el refinado de las maestrías, el Barrio de Oficios convertido en una calle con un puesto y un maestro por oficio, Sastrería como octavo oficio, técnicas por rango y planos, el cuarto propio con cama y cofre dentro del tutorial, doce ramas de maestría, quince herramientas especializadas, la instantánea de reglas de cada actividad y el catálogo T0/T1 con sus precios auditados.
