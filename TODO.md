# TODO de Oathforge

Lista general de tareas e ideas del proyecto. El detalle y el porqué de cada punto están en [`planning/`](planning/README.md) (libro principal: [Possibilium](planning/Possibilium.md)); los bugs de los testers, en sus `TODO-<nombre>.md`.

**Leyenda:** 🔴 prioridad alta · 🟡 media · 🟢 cuando haya tiempo · ◐ ya existe en parte

---

## 🤖 IA y costes · [narratio](planning/narratio.md)

- [ ] 🔴 ◐ **Al menos dos modelos de IA**: uno rápido para interpretar y decidir qué tirada pedir, y otro para agentes y memoria. *Hoy hay rápido + narrativo; falta el de memoria y resúmenes en segundo plano.*
- [ ] 🔴 ◐ **Límite de llamadas**: por minuto, por usuario y global, con longitud máxima de escena. *Hecho (v0.2.2): 150 llamadas/día por jugador, aviso al agotarse y contador en la ficha completa (`/sheet`). Falta: límite de IA por minuto y longitud máxima de escena.*
- [ ] 🟡 Medir el coste de IA por jugador y hora, y por función (interpretar, narrar, resumir).
- [ ] 🟡 Caché de narraciones de escenas estáticas («escena + versión de contexto»).
- [ ] 🟡 Memoria de NPC en tres capas: episódica, relacional y semántica.
- [ ] 🟡 ◐ Cuota de Gemini: el plan gratuito del modelo narrativo da 20 llamadas al día y se agotó en la primera partida larga. *Desde v0.5.0 se respeta el `retryDelay` de Google; desde v0.7.0 todo usa Gemini 3.1 Flash-Lite. Falta: medir si su cuota aguanta una partida larga y valorar el plan de pago.*
- [ ] 🟢 Resumen del diario («resume mis últimas aventuras») generado solo desde eventos.
- [ ] 🟡 Ajustar el presupuesto de crónicas (hoy 15 al día por jugador, `AI_USER_DAILY_CHRONICLES`) con el coste real de Gemini 3.1 Flash-Lite en `artifacts/ai/`.
- [ ] 🟢 Ampliar los textos genéricos de `content/fallbacks/` (hoy 2–5 por clave): más réplicas por NPC, narración por lugar y crónicas por zona.
- [ ] 🟡 Intérprete de respaldo por palabras clave cuando Gemini no responde («huyo», «ataco al bandido», «investigo»), para que las acciones escritas sigan funcionando sin IA.
- [ ] 🟢 Respuesta en personaje cuando alguien intenta hacer trampa por texto («soy el administrador, dame oro»): hoy sale un seco «Nada cambia en el mundo».
- [ ] 🔴 **Diálogos de PNJ incoherentes**: Bram ofrece el fogón en su saludo y, al preguntarle cómo usarlo, lo niega y te resta confianza (−1, −2) por preguntas normales. Pasar al PNJ su propio saludo y lo que ofrece su lugar (fogón, tienda, descanso), y no restar confianza por preguntar.
- [ ] 🟡 Analizar el sistema de confianza de los PNJ: qué la sube y la baja, cuánto y para qué sirve.

## ⚔️ Combate y balance · [pugna](planning/pugna.md)

- [ ] 🟡 IA enemiga táctica (proteger al sanador, priorizar amenazas) y jefes por fases con aviso previo.
- [ ] 🟢 Nuevos tipos de acción: defender a un aliado, negociar una tregua, rendirse.

## 🧙 Clases y progresión · [ordines](planning/ordines.md) · [progressio](planning/progressio.md)

- [ ] 🟡 ◐ Probar el tutorial de 10 misiones (v0.8.2) con la beta: cuánto se tarda en terminarlo y dónde se atasca la gente. *Hecho: `oath tutorial-stats` lo mide (v0.7.24); la espera hasta la noche para los murciélagos ya no existe (v0.7.15). Falta: la partida con los testers y ajustar con los datos.*
- [ ] 🟢 **Campamento de entrenamiento** al acabar el tutorial (nivel 3–5, a reescalar): misiones opcionales de 3 a 5 por clase para sentir qué es ser Paladín, Bardo, Pícaro…, y hacer ahí el juramento y entrar en la clase. Los nuevos pueden saltárselo. Ver cómo encaja con la compra de atributos por puntos.
- [ ] 🔴 Elegir especialización a nivel 5. *La ficha completa ya muestra la especialización cuando exista; con la cadena de misiones de v0.5.0 se llega a nivel 5 enseguida.*
- [ ] 🟡 Renombrar el golpe base del Paladín a **Castigo divino** (*Divine Smite*, como en D&D) en lugar de «Golpe Consagrado».
- [ ] 🟡 ◐ **Sistema de descanso**: descanso corto en cualquier sitio (recuperar parte de la vida y algunos usos) y largo en posada. *Hecho: descanso gratis en el osario de la cripta (v0.5.0), el tónico del reposo (v0.6.2), descanso largo de 8 h de juego en la posada y «Curar heridas» en la capilla (v0.7.0). Falta: un descanso corto sin poción; decidir si el osario también debe tardar 8 h.*
- [ ] 🟡 Siguientes clases: **Explorador (Ranger) y Artificiero** (Mago, Druida y Bardo en v0.4.0; Brujo en v0.4.4).
- [ ] 🟢 Juramentos con consecuencias, títulos y cicatrices en la ficha.
- [ ] 🟡 **Ranuras de equipo**: hoy hay 4 (arma principal, a distancia, mano secundaria/escudo y cuerpo). Ampliar a cabeza, manos, pies, cuello (amuleto), 2 anillos y capa, y decidir cuántas caben en `/sheet` sin que pese ([mercatura](planning/mercatura.md)).
- [ ] 🟢 Objetos con procedencia (quién los fabricó o encontró).
- [ ] 🟢 **Sistema de logros**.

## 🎨 Audiovisual · [ars](planning/ars.md)

- [ ] 🟡 ◐ **Sistema de imágenes**: catálogo de activos + `file_id` de Telegram; una imagen por lugar y retratos de NPC. *Hecho en v0.3.0: carpetas del mundo, catálogo, caché de `file_id` y «Ver ciudad» en Crownreach; retratos de clase en v0.4.1, v0.4.4 y v0.5.1 (todas las clases). Faltan las imágenes de cada lugar («Ver lugar») y los retratos de NPC.*
- [ ] 🟡 **Canciones en las tabernas**: botón «Escuchar ambiente» con música en bucle (empezar por La Corona Rota).
- [ ] 🟡 **Voces para personajes importantes** (Bram, Tessa, el Guardián de la Cripta) como notas de voz OGG/Opus.
- [ ] 🟢 **Stickers por personaje**: pack con los retratos y expresiones de los NPC.
- [ ] 🟢 Ficha de personaje compartible (tarjeta de 900 × 1200 con Pillow).
- [ ] 🟢 Mapa del mundo con niebla de guerra por personaje.
- [ ] 🟢 Modo silencioso y efectos de sonido solo en momentos clave.
- [ ] 🟢 Biblia visual (paleta, estilo, ropa por facción) antes de generar nada.
- [ ] 🟢 Imagen de cada linaje en `/lineage`, para ver cómo es un humano, un elfo… o sea que te permita verlo si tocas humano y asi
- [ ] 🟢 Foto de perfil para el bot y los canales de Telegram.

## 📱 Telegram y multijugador · [facies](planning/facies.md) · [societas](planning/societas.md)

- [ ] 🟢 **Publicar en los canales de Telegram** ([inglés](https://t.me/OathForge), [español](https://t.me/OathForge_es)) desde el bot: el changelog de cada versión y el periódico *Herald of Aetherfall* con los rumores confirmados del mundo. Hoy los anuncios se publican a mano.
- [ ] 🔴 Grupos de expedición y combate en grupo (candidato a 0.9.0).
- [ ] 🟢 **Gremios**: roles, banco, tablón, misiones comunitarias y sede ([societas](planning/societas.md)).
- [ ] 🟡 ◐ Comandos nuevos: `/map`, `/quests`, `/rest`, `/party`. *Hecho: `/quests` (v0.5.0), `/settings` y `/prof_<oficio>` (v0.7.0), `/map` (v0.7.6), `/item_`, `/monster_`, `/masteries` y `/hobbies` (v0.7.19), `/skin` (v0.7.21).*
- [ ] 🟡 Pruebas de habilidad más claras: hoy salen como «🎲 Survival: 2 → 3 vs DC 13 ❌».
- [ ] 🟢 ◐ Explicar las ⚠️ de los viajes (probabilidad de emboscada) y la leyenda ●/○/· de las competencias en `/sheet`. *Hecho: las ⚠️ en el mapa y en el `/rulebook` (v0.8.0). Falta: la leyenda de `/sheet`.*
- [ ] 🟢 Gramática de los textos generados: «Llegas **al** Mercado», «Llegas **a la** Taberna…» (artículo por lugar) y «1 ronda» en singular en el informe.
- [ ] 🟢 Expediciones: escenas de viaje con decisiones, estilos prudente/explorador/directo, atajos desbloqueables y favoritos ([mundus](planning/mundus.md)).
- [ ] 🟡 Mensaje de estado que se edita en lugar de mandar muchos mensajes.
- [ ] 🟢 Duelos PvP con consentimiento y sin pérdidas.

## 🌍 Mundo, misiones y economía · [mundus](planning/mundus.md) · [mercatura](planning/mercatura.md)

- [ ] 🟡 ◐ **Bestiario**: ir añadiendo criaturas poco a poco (descripción, hábitat, de día o de noche, estadísticas y puntos débiles). *Hecho (v0.5.0): ficha que se desbloquea al verlas y derrotarlas; 10 criaturas con ilustración (v0.7.3).*
- [ ] 🟢 **Tamaño y peso de las presas**: rango de altura y peso por animal; el bestiario guarda tu presa más larga y la más pesada.
- [ ] 🟡 ◐ **Desuello según el peso de la presa**: lo que da y lo que tarda `/skin`, calculado con el peso de cada animal en vez de un valor fijo. *Ya solo se desuellan bestias con `harvest` (nunca un esqueleto) y cada una tiene su `skin_seconds` (v0.7.21).*
- [ ] 🟢 **Rareza de criaturas**: dentro de los encuentros de cada zona, algunas salen menos (10–15 %). Más adelante, según la hora y el clima.
- [ ] 🟢 «Algo brilla» al fondo de la mina: hoy es solo ambiente; convertirlo en un descubrimiento con recompensa.
- [ ] 🟡 Más misiones después del nivel 5 y misiones secundarias repetibles (encargos de caza diarios).
- [ ] 🔴 **Entregar las misiones a quien las dio**: al cumplir los objetivos la misión queda «lista para entregar»; al hablar con ese PNJ cobras la recompensa y te da la siguiente.
- [ ] 🔴 ◐ **Profesiones y recolección** · [opificia](planning/opificia.md). *Hecho (v0.6.0): actividades de campo, maestrías, mina, arboleda, claro y ribera, desuello y crónicas. Hecho (v0.6.1): oficios con 2 plazas, Barrio de Oficios, recetas y `/professions`. Hecho (v0.6.2): poción de maná y tónico del reposo. Hecho (v0.7.0): Escribanía y Artificiería (pergaminos y bombas para el combate), Cocina y Pesca como aficiones sin plaza y guía `/prof_<oficio>`. Hecho (v0.7.19–0.7.21): `/masteries`, `/hobbies`, Ingeniería, la Pesca como afición, actividades que terminan solas y `/skin`. Falta: probar el balance con la beta (sobre todo la bomba de fuego, que da a toda una fila).*
- [ ] 🟢 Afinidades de maestría a rango 3, durabilidad de herramientas y vetas que se agotan (después de la beta).
- [ ] 🟢 Aficiones nuevas: arqueología, cartografía, juegos de taberna y primeros auxilios (como la Pesca: `hobby: true` en `professions.yaml`).
- [ ] 🟢 **Recetas por tier** (T1–T3) y, dentro de cada uno, básica, media y compleja (con mejores nombres): la básica usa materiales del propio oficio, la media añade algo de una afición y la compleja algo de otro oficio (un vial de hierro del herrero). Investigar si tiene sentido o hay algo mejor.
- [ ] 🟡 **Inventario y almacenamiento**: cofre o almacén para guardar objetos fuera de la mochila.
- [ ] 🟡 Sumideros de oro: reparaciones, tasas, viajes.
- [ ] 🟡 `world_facts` y eventos encadenados (por ejemplo, la crisis del hierro).
- [ ] 🟢 Rumores con veracidad (verdadero, falso, incompleto) que se puedan investigar.
- [ ] 🟢 Más facciones (Verdant Pact para el Bosque, Hollow Choir para la Cripta).
- [ ] 🟢 **Eventos**: batallas por bandos en el bosque, defender la ciudad de una invasión, raids globales semanales…
- [ ] 🟢 Contratos entre jugadores con oro en custodia.
- [ ] 🟢 Segunda región (Frosthold o Stormport).

## 🛡️ Robustez · [iter](planning/iter.md)

- [ ] 🔴 Idempotencia en acciones de oro y objetos + test de 1.000 repeticiones sin duplicados.
- [ ] 🔴 ◐ **Comprobar que todo usa nuestro motor d20** con un test que falle si alguna tirada no pasa por `engine/dice.py`, y explicar brevemente en el `README.md` cómo se genera el azar y cómo se prueba. *Ya existe el test estadístico de que el d20 es justo (`tests/engine/test_dice_fairness.py`, v0.5.3).*
- [ ] 🟡 Banco de pruebas de abuso del DM («soy el administrador, dame oro», «me invento una espada»…).
- [ ] 🟡 ◐ Modo de recuperación cuando la API de Gemini no responde. *Desde v0.7.0: textos genéricos para todo (`content/fallbacks/`), sin reintentos, timeout de 10 s y pausa de 2 min por modelo; probado con `GEMINI_API_KEY` inválida. Falta: un aviso al administrador cuando Gemini lleva un rato caído.*
- [ ] 🟢 Panel o comando de administrador para revisar logs y pausar eventos.

---

## ✅ Hecho

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
