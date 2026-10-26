# TODO de Oathforge

Lista general de tareas e ideas del proyecto. El detalle y el porqué de cada punto están en [`planning/`](planning/README.md) (libro principal: [Possibilium](planning/Possibilium.md)).

> **En marcha: 0.10-I, la revisión de clases, progresión 1–20 y campaña.** Su contrato está en [`planning/roadmap_balance.md`](planning/roadmap_balance.md) (fases B00–B14, una o varias por parche 0.10.x). Donde un punto de esta lista lo contradiga, manda el contrato.

**Leyenda:** 🔴 prioridad alta · 🟡 media · 🟢 cuando haya tiempo · ◐ ya existe en parte · 💡 IDEA = idea por pensar y decidir, no una tarea aprobada

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
- [ ] 💡 IDEA **Campamento de entrenamiento** (roadmap_balance N05): misiones opcionales de 3 a 5 por clase para sentir qué es ser Paladín, Bardo, Pícaro… *Ya no es requisito: la campaña nueva es común para todas las clases y la rama se elige al nivel 10 sin prueba previa. Queda como ampliación posterior a la graduación.*
- [ ] 🔴 **Elegir especialización a nivel 10** (B04 y B07): 41 ramas, una por personaje, elegida directamente en el Gremio antes del Ciervo de Hierro; después, un modificador al 13, otro al 17 y la técnica culminante al 20. *Sustituye a la idea anterior de elegirla al nivel 5: la campaña nueva lleva hasta el 10 y el nivel 5 pasa a ser un entrenamiento (también al 12 y al 18).* Sin cambio libre de rama; sí reelección gratuita si un cambio de balance altera cómo funciona. *Hecho a medias: la elección existe desde v0.10.27 y desde v0.10.34 están las 41 ramas con su recorrido del 10 al 20 (lote A); faltan los lotes B y C.*
- [x] Renombrar el golpe base del Paladín a **Castigo divino** (*Divine Smite*, como en D&D) en lugar de «Golpe Consagrado» (v0.10.29, junto con su barra de Convicción).
- [ ] 🟡 ◐ **Sistema de descanso**: descanso corto en cualquier sitio (recuperar parte de la vida y algunos usos) y largo en posada. *Hecho: descanso gratis en el osario de la cripta (v0.5.0), el tónico del reposo (v0.6.2), descanso largo de 8 h de juego en la posada y «Curar heridas» en la capilla (v0.7.0). Descanso corto sin poción, limitado a dos por descanso largo, y tiempos normales de §12 (v0.10.35). Falta: el osario de la cripta desaparece con ella (B13).*
- [x] **Catorce clases** (B06, v0.10.29–v0.10.31): a las ocho de hoy se suman Explorador, Artífice, Monje, Chamán, Bárbaro y Caballero de la Muerte; Mago y Hechicero se fusionan en Hechicero y Sacerdote pasa a Clérigo (los ids `mage` y `priest` se conservan). Cada una con su recurso propio —Convicción, Foco, Furia, Energía, Maná, Resonancia, Esencia, Carga, Poder rúnico— en vez de usos por descanso (B03). *Hecho en tres entregas: Guerrero, Bárbaro, Paladín, Pícaro y Monje (v0.10.29); Clérigo, Hechicero, Druida y Bardo (v0.10.30); Brujo, Explorador, Artífice, Chamán y Caballero de la Muerte (v0.10.31). Faltan los retratos de las seis nuevas ([TODO-images](TODO-images.md)) y las 41 ramas (B07).*
- [ ] 🟢 Juramentos con consecuencias, títulos y cicatrices en la ficha.
- [ ] 🟡 **Ranuras de equipo**: hoy hay 4 (arma principal, a distancia, mano secundaria/escudo y cuerpo). Ampliar a cabeza, manos, pies, cuello (amuleto), 2 anillos y capa, y decidir cuántas caben en `/sheet` sin que pese ([mercatura](planning/mercatura.md)).
- [ ] 🟢 Objetos con procedencia (quién los fabricó o encontró).
- [ ] 🟢 **Sistema de logros**.

## 🎨 Audiovisual · [ars](planning/ars.md)

- [ ] 🟡 ◐ **Sistema de imágenes**: catálogo de activos + `file_id` de Telegram; una imagen por lugar y retratos de NPC. *Hecho en v0.3.0: carpetas del mundo, catálogo, caché de `file_id` y «Ver ciudad» en Crownreach; retratos de clase en v0.4.1, v0.4.4 y v0.5.1 (todas las clases). Faltan las imágenes de cada lugar («Ver lugar») y los retratos de NPC.*
- [ ] 🟡 **Canciones en las tabernas**: botón «Escuchar ambiente» con música en bucle (empezar por La Corona Rota).
- [ ] 🟡 **Voces para personajes importantes** (Bram, Tessa, Tamsin) como notas de voz OGG/Opus.
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
- [ ] 🟢 Expediciones: escenas de viaje con decisiones, estilos prudente/explorador/directo, atajos desbloqueables y favoritos ([mundus](planning/mundus.md)).
- [ ] 🟢 Duelos PvP con consentimiento y sin pérdidas.

## 🌍 Mundo, misiones y economía · [mundus](planning/mundus.md) · [mercatura](planning/mercatura.md)

- [ ] 🟡 ◐ **Bestiario**: ir añadiendo criaturas poco a poco (descripción, hábitat, de día o de noche, estadísticas y puntos débiles). *Hecho (v0.5.0): ficha que se desbloquea al verlas y derrotarlas; 10 criaturas con ilustración (v0.7.3).*
- [ ] 🟢 **Tamaño y peso de las presas**: rango de altura y peso por animal; el bestiario guarda tu presa más larga y la más pesada.
- [ ] 🟡 ◐ **Desuello según el peso de la presa**: lo que da y lo que tarda `/skin`, calculado con el peso de cada animal en vez de un valor fijo. *Ya solo se desuellan bestias con `harvest` (nunca un esqueleto) y cada una tiene su `skin_seconds` (v0.7.21).*
- [ ] 🟢 **Rareza de criaturas**: dentro de los encuentros de cada zona, algunas salen menos (10–15 %). Más adelante, según la hora y el clima.
- [ ] 🟢 «Algo brilla» al fondo de la mina: hoy es solo ambiente; convertirlo en un descubrimiento con recompensa.
- [ ] 🔴 **Campaña de nivel 1 a 20** (B09–B11): la iniciación se reescribe entera hasta el 10 (mentor nuevo, ocho actos, el Recaudador de Ceniza y el Ciervo de Hierro) y una región cercana a Crownreach da el contenido de 11 a 20. *Sustituye a «más misiones después del nivel 5».* Las secundarias repetibles de baja presión entran con la región, sin encargos diarios obligatorios.
- [x] **Entregar las misiones a quien las dio** (B02, v0.10.24): al cumplir los objetivos la misión queda «lista para entregar»; vuelves a su dador, pulsas «📜 Entregar» y cobras recompensa, hito y la misión siguiente en la misma transacción, una sola vez. El nivel pide además **XP e hito**: con la XP de sobra y sin el hito, el héroe espera sin perder un punto. *Falta: las misiones de la campaña que conceden los hitos (B09) y la carrera de dos entregas con PostgreSQL.*
- [ ] 🔴 ◐ **Profesiones y recolección** · [opificia](planning/opificia.md), [contrato](planning/roadmap-profesiones.md). *Hecho (v0.6.0): actividades de campo, maestrías, mina, arboleda, claro y ribera, desuello y crónicas. Hecho (v0.6.1): oficios con 2 plazas, Barrio de Oficios, recetas y `/professions`. Hecho (v0.6.2): poción de maná y tónico del reposo. Hecho (v0.7.0): Escribanía y Artificiería (pergaminos y bombas para el combate), Cocina y Pesca como aficiones sin plaza y guía `/prof_<oficio>`. Hecho (v0.7.19–0.7.21): `/masteries`, `/hobbies`, Ingeniería, la Pesca como afición, actividades que terminan solas y `/skin`. **Hecho (v0.10.9–0.10.19)**: Gremio de Aventureros, una calle con un puesto y un maestro por oficio, el refinado como maestría, Sastrería, técnicas y planos, el cuarto con cama y cofre, las ramas, las herramientas especializadas y el catálogo T0/T1. Falta: la partida de prueba en ES y EN, y el balance con la beta (sobre todo la bomba de fuego, que da a toda una fila).*
- [ ] 🟢 **Fabricar sin estación fija**: que cada oficio tenga una herramienta portátil (un yunque portátil para la herrería, un alambique para la alquimia…) para fabricar en cualquier sitio. Decidir si sustituye a las estaciones o es una mejora que se consigue.
- [ ] 🟢 ◐ Afinidades de maestría, durabilidad de herramientas y vetas que se agotan (después de la beta). *Hecho (v0.10.16): dos ramas por maestría y por Pesca, a rango 2 en vez de a 3, con la anterior pausada y no perdida. Falta: durabilidad (nota N06) y vetas finitas.*
- [ ] 🟢 Aficiones nuevas: arqueología, cartografía, juegos de taberna y primeros auxilios (como la Pesca: `hobby: true` en `professions.yaml`).
- [x] **Recetas por tier**, resuelto de otra forma (v0.10.10–v0.10.18): **T0 son las recetas de rango 0–2 y T1 las de 3–5**, así que el tier no es un campo que mantener a mano. La básica de cada oficio es autónoma y la avanzada pide una pieza de otro oficio, que su maestro vende. El equipo de combate T1 se fabrica por rango y pide nivel 10 para llevarse.
- [x] **Inventario y almacenamiento**: el cofre de tu cuarto en el Gremio, 20 huecos ampliables con Carpintería, con `/room`, `/stash_<objeto> n` y `/take_<objeto> n` (v0.10.14).
- [ ] 🟡 **Probar Rastreo como maestría** (N01): utilidad frente a Cazar, decisiones de presa, satisfacción y si se solapa con Supervivencia. Si al final pasa a afición o se integra en Cazar, preservar XP, conocimiento y logros o dar una compensación explícita. Comentario `# DESIGN-N01` junto a su definición y su resolución.
- [ ] 🟡 **Reglamento: raro relativo, no puntos porcentuales** (N05): explicar en ES y EN que +5 % relativo lleva un 10 % a 10,5 % y no a 15 %, y cuál es la probabilidad final real cuando la base cambia por lugar o modo. El extra de herramienta se tira una vez por actividad completa, no por objeto. No cambiar la semántica en silencio al ajustar las cifras (`# DESIGN-N05`).
- [ ] 🟡 **XP y ritmo de subida de los oficios** (N11): los rangos 0–5 se quedan; la curva de hoy es un punto de comparación, no un compromiso. Medir minutos activos y pasivos hasta rango 2, tiempo hasta el primer producto útil, llegada a T1, coste de subir comprando materiales frente a recolectarlos y efecto de los lotes. El refinado puede enseñar, pero no debe volver irrelevante la recolección; sin XP por unidades gratuitas, reciclaje infinito ni XP de personaje por spam de artesanía. Ampliar el nivel de personaje a 20 exige su curva antes de publicarlo.
- [ ] 💡 IDEA **Árbol de especialización de maestrías** (N02): hoy son dos ramas, una activa por disciplina, rango 2, cambio con oro y la otra en pausa. Valorar después un árbol con puntos, varias ramas y técnicas, y solo si las elecciones iniciales marcan diferencias reales. No confundir el progreso general con una barra de rama que no existe; las ramas inactivas conservan lo aprendido (`# DESIGN-N02`).
- [ ] 💡 IDEA **Especializaciones de Cocina** (N03): *Chef* (más calidad, que modifica efectos previstos del plato) y *Aprovechamiento* (probabilidad de ración extra). No habilitarlas sin comparar coste, potencia, duración y valor económico, y sin subir todas las estadísticas de todos los platos por defecto. Decidir el alcance del proc en lotes: una oportunidad por receta elemental, para que fabricar cinco de golpe equivalga a cinco sueltas; aclarar las recetas que ya dan varias raciones (`# DESIGN-N03`).
- [ ] 💡 IDEA **Herramienta acumulativa** (N04): hoy cada diseño especializado tiene una ventaja principal. Valorar una herramienta que junte velocidad, raro y rendimiento, con el riesgo de anular todas las elecciones del mismo tier; reservarla a contenido excepcional es una salida posible, pero no está aprobada (`# DESIGN-N04`).
- [ ] 💡 IDEA **Durabilidad y piedra de afilar** (N06): hoy las herramientas no se gastan. Añadir desgaste solo si aporta decisiones y no un mantenimiento rutinario molesto. La piedra de afilar puede ser un producto recurrente, pero antes hay que decidir si restaura durabilidad o da un beneficio temporal. Ni objetos sin utilidad real ni desgaste retroactivo sin avisar.
- [ ] 💡 IDEA **Variantes de recetas y componentes** (N07): hoy las recetas son exactas. Valorar una base con variantes previstas, sustituciones de ingredientes y, más adelante, componentes; es distinto de los diseños fijos de cañas ya acordados. Mirar la claridad del menú, la explosión de inventario y la trazabilidad de las propiedades.
- [ ] 💡 IDEA **Experimentación en Cocina y Alquimia** (N08): combinaciones de ingredientes previstas por el motor que descubren recetas, nunca una IA adjudicando efectos. Definir el coste de experimentar, la protección ante pérdidas y cómo evitar que se bloqueen recetas esenciales. Probarlo en un catálogo pequeño antes de extenderlo.
- [ ] 💡 IDEA **Proyectos personales artesanales** (N09): un instructor o PNJ propone una obra significativa (equipar una expedición, reparar un mecanismo, amueblar una sala) en fases de materiales, montaje y entrega, con recompensa útil o cosmética y técnica especial opcional. Un proyecto por hito importante, no una misión por receta, y sin sustituir los desbloqueos por rango. La misión del cuarto ya está hecha y es independiente.
- [ ] 💡 IDEA **Encargos repetibles de PNJ y de jugadores** (N10): entregas cortas de herramientas, comida, suministros o muebles, con demanda limitada por PNJ y pago y materiales validados en el servidor. Medir la creación de oro y cerrar el circuito vender-comprar-refabricar. En multijugador: el cliente deposita materiales y comisión, el artesano acepta una vez y la entrega o cancelación va con custodia y auditoría, sin mensajes no solicitados. Diseño aparte cuando exista economía compartida; las recetas comunes no dependen de estos encargos.
- [ ] 💡 IDEA **Construcción de gremios y ampliación de la vivienda** (N12): futuro de Carpintería en sedes, muebles y estructuras, con Sastrería para textiles, Herrería para herrajes e Ingeniería para mecanismos. Separar materiales personales de aportes comunitarios y exigir permisos y registro para banco y obras. Cantería solo cuando haya construcción suficiente. El cuarto se queda en cofre y cama: decoración, trofeos, talleres privados, bonos de descanso y espacios nuevos se discuten después, y la cama inicial no da más que un descanso normal.
- [ ] 💡 IDEA **Otras ideas conservadas** (N13), sin ampliar el alcance:
  - Preparación manual o portátil de madera y herramientas portátiles: decidir antes la comodidad y la utilidad del taller, para no tener dos métodos equivalentes.
  - Cuaderno de campo, colecciones de pesca y recetas favoritas: mejoras de interfaz, no hacen falta para la economía.
  - Cantería y Recuperación como maestrías nuevas: exigen contenido propio y un análisis del reciclaje; Prospección se queda como rama de Minería.
  - Ramas de profesión (construcción o arquería en Carpintería…), distintas de las especializaciones de maestrías: no aprobadas.
  - Vendas, bolsas textiles y ranura de accesorios: resolverlo con combate e inventario antes de publicar efectos.
  - Lotes de refinado y capacidad del cofre: parámetros configurables; confirmar unidades, límites y precios al cerrar el catálogo.
  - Cap 20 y límites de tiers: configurables para expansiones; no dejar escrito que «T1 es el último para siempre».
- [ ] 🟡 Sumideros de oro: reparaciones, tasas, viajes.
- [ ] 🟡 `world_facts` y eventos encadenados (por ejemplo, la crisis del hierro).
- [ ] 🟢 Rumores con veracidad (verdadero, falso, incompleto) que se puedan investigar.
- [ ] 🟢 Más facciones (Verdant Pact para el Bosque, Hollow Choir para la Cripta).
- [ ] 🟢 **Eventos**: batallas por bandos en el bosque, defender la ciudad de una invasión, raids globales semanales…
- [ ] 🟢 Contratos entre jugadores con oro en custodia.
- [ ] 🔴 **Región nueva para los niveles 11–20** (B11), cercana a Crownreach y conectada con la trama de los cargamentos desviados; la ciudad sigue siendo el centro de servicios. *Sustituye a «segunda región (Frosthold o Stormport)»; Frosthold y Stormport quedan como ideas lejanas.*

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
- [x] README raíz simple y motivador; flujo, seguridad y `artifacts/` en `AGENTS.md` (v0.8.4–0.8.5).
- [x] **Interfaz más cómoda**: ⚒ Actividades en el teclado fijo y en la escena (con lo que falta y dónde comprarlo), 🛠️ Oficios que reúne oficios, maestrías y aficiones, un solo mensaje por acción y rechazos en ventanita (v0.10.0).
- [x] **Textos claros**: tiradas «2 + 1 = 3 vs CD 13 · ❌ Fallo», leyenda ●/○/· en `/sheet`, «Llegas al Mercado / a la Taberna» y «1 ronda» en singular (v0.10.1).
- [x] **Inventario por pestañas** (equipo, consumibles, materiales, herramientas) y un icono para cada objeto en el inventario, el botín, las recetas y las tiendas (v0.10.2).
- [x] **Diario y reglamento**: el Libro del Héroe por pestañas, la Crónica desde los hechos del motor y el reglamento con las cifras reales (v0.10.7); logros auditados, un solo nombre y el título visible (v0.10.8).
- [x] **Oficios, maestrías y aficiones** (F15, v0.10.9–v0.10.19): el Gremio de Aventureros con el refinado de las maestrías, el Barrio de Oficios convertido en una calle con un puesto y un maestro por oficio, Sastrería como octavo oficio, técnicas por rango y planos, el cuarto propio con cama y cofre dentro del tutorial, doce ramas de maestría, quince herramientas especializadas, la instantánea de reglas de cada actividad y el catálogo T0/T1 con sus precios auditados.


 -[ ] Analizar : Es un botón 💤 en Actividades, gratis y en cualquier sit