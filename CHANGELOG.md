# Changelog

Todos los cambios relevantes de Oathforge. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado `0.x.y` (ver `planning/iter.md`).

Cada versión corresponde a un commit cuyo asunto es `vX.Y.Z: resumen` y cuyo cuerpo repite esta lista.

## [0.10.17] - 2026-10-20

Profesiones (F15, 9.ª parte): las herramientas especializadas.

### Añadido
- **Quince herramientas**, tres diseños por disciplina: **rápido** (−10 % de tiempo), **selectivo** (raro ×1,05) y **productivo** (5 % de una unidad extra por actividad completa). Pico, hacha, hoz y cuchillo los forja la **Herrería** (técnica nueva «Herramientas especializadas», rango 2) y las cañas las hace la **Carpintería** (técnica «Cañas de pescar»). Las mejores piden una pieza de otro oficio: tela, hilo, cuero o un tablón de fresno.
- **Una herramienta por disciplina**: se elige en 🛠️ Oficios → Maestrías → 🧰 Herramientas, pide tenerla y el rango que marque, y **llevar tres no suma**. La elegida sustituye a la de siempre: con ella puestas, minar sigue pidiendo un pico, pero cuenta el tuyo.
- **La rama y la herramienta se suman una sola vez** y quedan **fijadas al empezar** el trabajo, dentro de su instantánea: ponerse otra a mitad no cambia el premio, y con un trabajo en marcha el cambio se rechaza.
- El desuello también se acorta con el cuchillo que corresponde, sin bajar nunca del suelo de 30 segundos.
- El reglamento explica los tres diseños y, con un ejemplo, la diferencia entre un **+5 % relativo** (10 % → 10,5 %) y **+5 puntos** (10 % → 15 %): aquí siempre es lo primero.
- Comentarios `DESIGN-N04` y `DESIGN-N06` donde se leen las herramientas: diseños fijos, sin desgaste ni piedra de afilar.

## [0.10.16] - 2026-10-20

Profesiones (F15, 8.ª parte): las ramas de cada maestría.

### Añadido
- **Doce ramas**, dos por cada maestría y dos para la Pesca (`content/specializations.yaml`): Extracción o Prospección en Minería, Producción o Selección forestal en Tala, Cosecha abundante o Botánica selectiva en Herboristería, Aprovechamiento o Extracción cuidadosa en Desuello, Rastro seguro o Rastro selectivo en Rastreo, y Pesca abundante o selectiva.
- **🌿 Especializaciones** en el Gremio de Aventureros: a **rango 2** eliges una rama por disciplina. La primera es gratis; cambiarla cuesta **50 de oro** (`SPEC_SWITCH_COST`), con una confirmación que dice el precio y qué queda pausado. La rama que dejas **no se borra**: queda aprendida y pausada, y volver a ella cuesta lo mismo.
- **Las disciplinas no comparten plaza**: puedes llevar Minería y Tala especializadas a la vez, y solo la rama activa de cada una cuenta.
- **La rama queda fijada al empezar la actividad**, dentro de su instantánea: cambiarla a mitad no cambia el premio, y con un trabajo en marcha el cambio se rechaza.
- **Piloto de Rastreo**: «Rastro seguro» acorta la espera un 15 % y «Rastro selectivo» inclina el rastro hacia la presa más escasa del lugar, sin tocar nunca al jefe de una misión. Lleva sus comentarios `DESIGN-N01` y `DESIGN-N02` para decidir más adelante si Rastreo sigue siendo maestría.
- Sección **🌿 Ramas de maestría** en `/rulebook`, con el rango, el precio y el ejemplo de 10 % → 10,5 %.

## [0.10.15] - 2026-10-20

Profesiones (F15, 7.ª parte): cada actividad se paga con las reglas con las que empezó, y el hallazgo raro se tira una vez.

### Añadido
- **Instantánea de reglas al empezar** (la casilla pendiente de F08): una recolección o una expedición guardan su tabla de recursos, su rango y sus modificadores, y al cobrarla se resuelven con eso, no con el contenido de ese momento. Reiniciar el bot o publicar un cambio de catálogo ya no puede alterar un premio en marcha. Las actividades anteriores a la instantánea se siguen pagando como antes.
- **El hallazgo raro es de la actividad, no de cada unidad**: los recursos de rango 3 o más salen de una sola tirada por trabajo, con la probabilidad que el catálogo tenía de dar al menos uno, y sustituyen una unidad común en vez de añadirse. Así la cantidad no cambia y el porcentaje que se anuncia es el que se cumple.
- **`Mods`**, el perfil de lo que una herramienta o una rama cambian: tiempo (`300 s` con −10 % son 270 s, con un suelo de 30 s), raro **relativo** (10 % × 1,05 = 10,5 %, nunca 15 %) y una unidad extra con **una sola oportunidad por actividad completa**, sin XP. Las dos cosas que lo rellenarán —rama y herramienta— llegan en sus fases.
- Pruebas de distribución con semilla que comparan la economía nueva con la vieja: las mismas unidades por trabajo y las gemas en el mismo orden de magnitud.

## [0.10.14] - 2026-10-20

Profesiones (F15, 6.ª parte): tu cuarto en el gremio, con cama y cofre.

### Añadido
- **Un cuarto propio**, misión nueva del tutorial (la 8, tras «Hierro para la Guardia», que ahora paga con un **hacha** en vez de con oro): talas robles, asierras los troncos en el gremio, montas el **cofre** con cuatro tablones y, con la **tela** que te da Vale y dos tablones más, la **cama**. Las dos son **recetas de iniciación**: no piden oficio ni plaza y solo existen mientras esa misión dura.
- **Dormir en tu cama** es el descanso largo de siempre —lo mismo que recupera, lo mismo que tarda— pero **no cuesta oro**.
- **El cofre**, con 20 huecos (`CHEST_SLOTS`). Lo guardado **no se lleva encima**: no se vende, no se gasta ni se fabrica con ello hasta sacarlo, y cada pieza conserva su identidad y quién la hizo, porque se mueve la fila, no una copia. Depositar y retirar son atómicos y bloquean las filas.
- **`/room`** (alias `/stash`) abre el cuarto: la cama, el cofre con lo que hay dentro y lo que llevas en la mochila. Con **`/stash_<objeto> 5`** y **`/take_<objeto> 5`** se mueve cualquier cosa sin abrir menús; repetir el mismo mensaje no lo mueve dos veces.
- **Mejora del cofre**, una receta de Carpintería (rango 1): seis tablones y un lingote por 10 huecos más, sin tocar lo guardado. El carpintero se la hace; los demás se la comprarán.
- La tela del gremio es **material de misión, no vendible**, y Vale la repone mientras no tengas la cama montada ni la tela encima: ni se pierde la misión ni se puede pedir una y otra vez.
- Sección **🏠 Tu cuarto y el cofre** en `/rulebook`, con las cifras del motor.
- Migración **0012**: `item_instances.container` (la mochila o el cofre) y `characters.home`.

## [0.10.13] - 2026-10-20

Profesiones (F15, 5.ª parte): Sastrería, las técnicas y los planos.

### Añadido
- **Sastrería**, el octavo oficio, con su puesto: el **Telar de Hedda**, maestra sastra. La cadena es fibra vegetal → fibra limpia (Herboristería, en el gremio) → **hilo** → **tela** → **jubón acolchado** (CA 11) y, a rango 2, el **sedal** que la carpintería necesitará para sus cañas.
- **Técnicas**: cada rango nuevo enseña de golpe una técnica entera con todas sus recetas comunes, y lo dice en una línea («📘 Técnica aprendida: Forja de armas · Espada de hierro»). Dieciséis técnicas repartidas entre los ocho oficios y las dos aficiones.
- **Planos** (`type: blueprint`): un pliego que enseña una receta especial. Leerlo gasta ese ejemplar y el conocimiento ya no se pierde, tampoco al cambiar de oficio; si ya la conoces, no se gasta y puedes vender el plano. La ficha `/item_` de un plano dice qué enseña y trae el botón «📘 Aprender la receta».
- La primera receta especial: la **daga de colmillo** (1d6 perforante, sutil), que se forja con un lingote, dos colmillos y cuero. Su plano lo suelta **el Viejo Colmillo**, el jefe del tutorial.
- Migración **0011**: `characters.crafting` guarda lo aprendido de los planos (y, más adelante, la rama y la herramienta elegidas de cada disciplina).

### Cambiado
- El reglamento cuenta los ocho oficios, las técnicas por rango y los planos.

## [0.10.12] - 2026-10-20

Profesiones (F15, 4.ª parte): el refinado pertenece a las maestrías, y las recetas tienen panel y comandos.

### Añadido
- **Refinar es cosa de la maestría, no del oficio.** En el Gremio de Aventureros, cualquiera funde **lingotes de hierro** y **de cobre** en el horno (XP de Minería), asierra **tablones de roble** y **de fresno** (Tala), cura **cuero** en el secadero (Desuello) y limpia **fibra** en la mesa de preparación (Herboristería). Sin oficio, sin plaza y con el rango de esa maestría.
- **Tres materiales nuevos**: lingote de cobre, tablón de fresno y fibra limpia.
- **`/recipes`**: todas las recetas de tus disciplinas por pestañas —✅ Puedo fabricar · ❌ Faltan materiales · 🔒 Por aprender · T0 · T1—, de 8 en 8, cada una con su `/r_<receta>`.
- **`/r_<receta>`**, la ficha: qué hace y cuánto da, su disciplina y su rango, dónde está su estación, los ingredientes con `tengo/necesito` y, de lo que falta, **de dónde sale** (el lugar donde se recoge, la maestría que lo refina, la criatura que lo suelta o quién lo vende), la XP que paga y el nivel que pide para equiparse. Abajo, botones **🔨 ×1 · ×5 · ×máx**, limitados por los materiales y por `CRAFT_BATCH_MAX`.
- **`/craft_<receta> n`**: fabricar escribiendo, sin abrir un menú; sin número, abre la ficha. Repetir el mismo mensaje no fabrica dos veces.
- El reglamento explica el refinado y los lotes, con la cifra del motor.

### Cambiado
- **Las recetas de refinado cambian de disciplina y de estación**, conservando sus ids: `iron_ingot` y `copper_ingot` a Minería, `oak_plank` y `ash_plank` a Tala, `treated_leather` y `wolf_leather` a Desuello y `clean_fiber` a Herboristería. Los objetos ya fabricados no se tocan.
- El **anillo de cobre** se hace con un lingote de cobre (antes, con mena cruda) y el **bastón de roble**, con fibra limpia. El mismo material de partida, un paso más de oficio.
- Las guías de **Herrería**, **Carpintería** y **Peletería** cuentan lo que hacen ahora: forjar, trabajar la madera y coser, con el refinado hecho en el gremio.
- El panel de fabricar enlaza cada receta con su ficha y lleva un botón «📜 Recetas».

## [0.10.11] - 2026-10-20

Profesiones (F15, 3.ª parte): el Gremio de Aventureros y una calle con un puesto por oficio.

### Añadido
- **Gremio de Aventureros** (`adventurers_guild`), un lugar nuevo al este de la plaza. Dentro están el **horno de fundición**, el **puesto de aserrado**, el **secadero** y la **mesa de preparación** —las estaciones del refinado de las maestrías, abiertas a cualquiera— y un fogón. Es también donde la sargenta **Vale** alista ahora a los reclutas: pasa de la plaza al gremio y deja de hablar en nombre de la Guardia para hacerlo en nombre del gremio.
- **Siete puestos de oficio**, cada uno un lugar del mapa con su estación, su descripción de día y de noche y su maestro: la **Forja de Tessa** (herrería), la **Botica del Alquimista** de Ilva, el **Taller del Carpintero** de Garrick, la **Curtiduría** de Oda, el **Banco del Joyero** de Pell, el **Escritorio del Escriba** de Lorent y el **Taller del Ingeniero** de Dunn. Seis PNJ nuevos con su carácter, su horario y sus textos de respaldo; Tessa trabaja de día en su forja y sigue vendiendo lo que vendía. El telar de Sastrería llegará con su oficio.
- **Cada oficio se aprende en su puesto** (`teaches` en el lugar): con el maestro que lo practica, no con un botón en cualquier parte. Quien lo intente donde no toca recibe el nombre del lugar al que ir.
- **El mapa agrupa los puestos**: salen nombrados bajo su calle y un botón «🛠️ Puestos (7)» los abre, así que la ciudad sigue cabiendo en una pantalla aunque tenga trece lugares.
- Los prompts del gremio y de los siete puestos, en `TODO-images.md`.

### Cambiado
- **El Barrio de Oficios conserva su id y se queda sin estaciones**: ahora es la calle de la que cuelgan los puestos. Las misiones, los logros y los textos que lo nombran siguen funcionando.
- **El tutorial se adapta**: «Alistamiento» empieza en el gremio (la plaza enseña por dónde se va), «Calles de Crownreach» habla de los puestos y «El mercado» manda a Tessa a su forja. El botón «🛒 Pico · ir a…» lleva ahora a la forja.
- El reglamento, las guías y la ficha del héroe dicen que cada oficio se aprende con su maestro, en su puesto.

## [0.10.10] - 2026-10-20

Profesiones (F15, 2.ª parte): el contrato de las recetas. Nada cambia todavía para el jugador; cambia lo que una receta puede decir de sí misma.

### Añadido
- **Estación por receta**: una receta puede traer su propia `station` en vez de heredar la de su oficio. Es lo que permitirá fundir en el horno sin ser herrero, y lo que hacía falta para separar el refinado del oficio.
- **La disciplina de una receta puede ser una maestría** (minería, tala, herboristería, desuello): entonces no ocupa plaza, cualquiera la trabaja y su XP va a esa maestría, nunca a un oficio. El rango exigido también es el de la maestría.
- **Cinco estaciones nuevas** con sus nombres ES/EN: telar, horno de fundición, puesto de aserrado, secadero y mesa de preparación.
- **Fabricar por lotes**: `craft` acepta una cantidad (hasta `CRAFT_BATCH_MAX`, 10 por defecto). Comprueba todos los materiales antes de gastar uno y produce el lote entero o ninguno; la XP se multiplica por lo fabricado. El botón `craft` acepta `receta:cantidad`.
- **Requisito de nivel para equipar y usar** (`min_level`): un objeto T1 se fabrica por rango y se lleva por nivel, así que un artesano de nivel bajo puede forjarlo y no equiparlo. Desequipar nunca se bloquea.
- **Planos** (`type: blueprint`, campo `teaches`) y recetas `special`, `technique` y de misión (`quest`): el esquema ya las admite y el cargador las valida; el aprendizaje llega en su fase.
- **Validaciones del cargador**: la disciplina existe como oficio o maestría, una receta de maestría trae su estación, la estación existe en algún lugar, las cantidades son positivas, la misión de una receta existe, un plano enseña una receta que de verdad es especial y una receta especial tiene quien la enseñe.

### Cambiado
- Las fichas `/item_` y el panel de fabricar hablan de «disciplina», no de «oficio»: el icono y el nombre salen del oficio o de la maestría, según cuál sea.

## [0.10.9] - 2026-10-20

Profesiones, maestrías y aficiones (F15, 1.ª parte): el contrato. Solo documentación; el juego no cambia.

### Añadido
- **`planning/roadmap-profesiones.md`**, el contrato de F15 auditado sobre 0.10.8: veinticinco decisiones (D01–D25), la cadena de refinado de cada maestría, las dos ramas por disciplina, las herramientas con sus porcentajes, los ocho oficios con Sastrería, las técnicas y los planos, el Gremio de Aventureros, la calle con un puesto por oficio, la habitación con cama y cofre, los contratos técnicos, la interfaz y once fases de entrega con su puerta de salida. Las trece notas de experimentos y balance (N01–N13) quedan al final, sin recortar.
- Decisiones nuevas de esta revisión: **T0 son las recetas de rango 0–2 y T1 las de rango 3–5**, así que el tier no es un campo que mantener a mano; el catálogo T1 se publica entero y su equipo de combate pide nivel 10 para equiparse; el **Barrio de Oficios conserva su id** y pasa a ser una calle de la que cuelgan ocho puestos, cada uno un lugar con su estación y su **maestro**; **Tessa** se convierte en la maestra de Herrería en su Forja; el **Gremio de Aventureros** reúne a Vale, el refinado, un fogón, las especializaciones y la habitación; y la habitación entra **dentro del tutorial**.

### Cambiado
- **F15 en `planning/roadmap.md`** deja de ser una lista de auditorías y pasa a ser once fases con su versión (0.10.9–0.10.19), enlazadas al contrato. El hito 0.10-F abarca ese tramo.
- El **cofre personal** de F06 y la **instantánea de reglas** que le falta a F08 se entregan dentro de F15 (fases 5 y 6); sus casillas lo dicen.
- `planning/opificia.md` recoge lo decidido y lo que queda futuro, y advierte de dos trampas del código: las maestrías están fijas en `engine/gathering.py`, no en el contenido, y la estación de una receta sale de su oficio, no de la receta.
- `planning/mundus.md`, `mercatura.md`, `facies.md`, `README.md` e `iter.md` apuntan al contrato con lo que les toca.

## [0.10.8] - 2026-10-19

Logros (F04): auditoría, un solo nombre y el título donde se ve.

### Añadido
- **Cuatro logros** sobre lo que ya existe: «Héroe de Crownreach» (nivel 5, con el título *de Crownreach*), «Oficial del gremio» (rango 2 en un oficio) y dos **ocultos**, que no se ven hasta conseguirlos: «Volví por ti» (huir de un combate y luego acabar con el Guardián de la Cripta) y «Lo que caza de noche» (ganar después del anochecer). Son 36 logros y 5 títulos.
- **El título se ve fuera de `/hero`**: junto al nombre en `/sheet`, en la cabecera del Libro del Héroe («de Morgana, *Rompecriptas*») y como dato en el contexto del narrador y de los PNJ, que pueden saludarte por él. La IA lo recibe; concederlo sigue siendo solo del motor.

### Cambiado
- **Un solo nombre, «Logros»**: desaparecen «Ver hazañas», «puntos de hazaña» y «Tu historia recuerda esta hazaña». Los ids, el comando `/achievements` y las tablas no cambian.

### Arreglado
- Una expedición o un rastreo que acaba en derrota ya no cuenta como actividad completada para «Vida de campo» ni «Herramientas del oficio».
- Los desafíos decían «nivel 3–5»: la pareja de lobos pide nivel 4 y la de murciélagos nivel 3, y el límite es empezar a nivel 5 o antes.
- Destacar o seguir un logro con la clave «-» (que solo significa «quitar el título») se rechaza en vez de añadir un hueco a la lista.

## [0.10.7] - 2026-10-19

Diario y reglamento (F03): el Libro del Héroe.

### Añadido
- **Crónica de hechos** (`hero_facts`, migración 0010): el registro que ya deduplicaba los logros ahora guarda también el tipo de hecho, sus datos y el día de juego, y marca los que merecen una entrada. Sustituye a `achievement_event_receipts`, cuyas filas se conservan. Hechos nuevos: nivel alcanzado, rango de oficio y misión aceptada.
- **🕯️ Crónica** en el diario: lo que has hecho, de lo más reciente a lo más antiguo, agrupado por día y de 8 en 8 con ◀ ▶. Siempre misión terminada, decisión, logro, nivel, derrota, secreto y descubrimiento; la primera vez que pisas un lugar, fabricas una receta, ves una criatura o subes un rango; nunca lo repetido. Lo reconocido del progreso anterior va bajo «Antes de este libro». No gasta IA.
- **📖 Ahora**, la portada del diario: la actividad en marcha con lo que le queda, el viaje que dejaste a medias, el objetivo de cada misión en curso y los objetivos seguidos, cada uno con su botón para continuar. Sin misiones, un botón hacia quien las da: el diario ya no es un callejón sin salida.
- **Estadísticas verificables**: misiones terminadas, fabricaciones y recetas distintas, secretos, criaturas conocidas y especies abatidas, niveles y logros, contados desde la crónica. Las antiguas siguen, y cada bloque dice desde cuándo cuenta.
- Sección **🏆 Logros y títulos** en `/rulebook`: qué reconocen, que no dan poder y cómo se equipa un título.
- Una prueba de contenido exige que cada `{marcador}` del reglamento y de las guías de oficio tenga valor en el motor, en español y en inglés.

### Cambiado
- **Diario por pestañas**: 📖 Ahora · 📜 Misiones · 🕯️ Crónica · 🏆 Logros · 🐉 Bestiario · 🗣️ Rumores · 📈 Estadísticas, en un solo mensaje que se edita, con la activa entre «• … •». Las misiones terminadas pasan de «📚 Registro» a la pestaña de Misiones; el botón «Registro» de menús viejos abre la Crónica.
- **El reglamento lee el motor**: coste y duración del descanso, CD de huida, puntos de creación, nivel de la subida de atributo, nivel máximo, oro que cuesta una derrota, segundos de desuello y las CD por dificultad ya no están escritos a mano. Las frases de beta (descanso y tutorial instantáneos) aparecen según el flag.

### Arreglado
- El reglamento decía que un tramo ⚠️⚠️ tiene un 15 % de emboscada: son el 15 % por cada ⚠️ del peor tramo (30 %), más un 5 % por cada tramo peligroso de más, hasta un 45 %.
- Prometía una especialización a nivel 5, que todavía no existe: ahora dice que llegará más adelante.
- No mencionaba el descanso gratis en la Cripta Hundida, el crítico con 19 de algunas habilidades, que subir de nivel permite repetir una prueba, el enfriamiento del tónico del reposo ni que en el tutorial las actividades terminan al instante.
- El backfill de logros daba por hecho que ningún lugar estaba fuera de la ciudad, así que «Más allá de las puertas» no se reconocía nunca. Ahora también reconoce los niveles alcanzados.

## [0.10.6] - 2026-10-19

### Cambiado
- **Un solo botón, 🖼️ Ver lugar**: «🏙️ Ver ciudad» desaparece. En la plaza de una ciudad (lugar `hub`) sin imagen propia, «Ver lugar» enseña la panorámica de la ciudad; los botones «Ver ciudad» de menús viejos siguen funcionando igual.

### Arreglado
- En la Plaza de Crownreach salían «Ver ciudad» y «Ver lugar» a la vez, y «Ver lugar» decía que no había imagen.

## [0.10.5] - 2026-10-18

Audiovisual (F02, 2.ª parte): «Ver lugar».

### Añadido
- **🖼️ Ver lugar** en cada escena: envía la imagen del lugar (la nocturna de noche, si la hay) con su nombre y descripción, y la escena debajo. Si el lugar aún no tiene imagen, una ventanita: «🎨 Ningún pintor ha plantado aún su caballete en la Plaza de Crownreach. Por ahora, tendrás que imaginarlo.»

## [0.10.4] - 2026-10-18

Audiovisual (F02, 1.ª parte): estilo visual y Crownreach de día y de noche.

### Añadido
- **Crownreach de noche** (`panorama.night.jpg`): «🏙️ Ver ciudad» la enseña cuando es de noche en el juego.
- `TODO-images.md` en la raíz: las imágenes que faltan (zonas, mapa, los 17 lugares, PNJ, linajes, eventos, avatar y emblema) con su ruta y su prompt sugerido, más cómo hacer la versión de noche desde la de día.

### Cambiado
- **Estilo visual decidido**: ilustración de libro de rol en gouache, con un sufijo común para todos los prompts (`planning/ars.md` §5).
- Nueva panorámica de Crownreach de día en ese estilo.

## [0.10.3] - 2026-10-18

Solo documentación: no cambia el juego.

### Añadido
- `planning/facies.md`: notas de jugar en vivo con la cuenta de prueba en Chat Wars (castillo Moonlight) y AshWars — menú principal, perfil corto con estado actual, contenedores de inventario, el crafteo por estaciones móviles (probado montando una Tienda de campaña: botón solo con materiales completos, mejora medible al instante, contador de pendientes, coste visible aunque esté bloqueada) y el combate de incursión (enemigo oculto hasta identificarlo, confirmación al huir). Candidatas para revisar en F01/F08/F15; nada implementado todavía.

## [0.10.2] - 2026-10-18

Interfaz (F01, 3.ª parte): inventario ordenado y un icono para cada cosa.

### Añadido
- **Icono por objeto** (`icon` en `content/items.yaml`, los 62): 🪨 menas, 🪵 maderas, 🌺🍃🌿 hierbas, 🐗🐺 pieles, 🥩 carne, 🐟 pescado, ⛏️🪓🌾🔪🎣 herramientas… Siempre junto al nombre, nunca en su lugar (`Item.label`); sin icono propio, el de su tipo. Se ve en el inventario, el botín, las crónicas, las recetas, las tiendas, el combate y `/item_`. Una prueba de contenido exige que todos lo tengan.
- `/item_<clave>` de algo que llevas trae su botón de equipar o usar.

### Cambiado
- **Inventario con pestañas**: el resumen dice qué llevas puesto y cuántos objetos hay de cada tipo; las pestañas ⚔️ Equipo · 🧪 Consumibles · 🧱 Materiales · 🧰 Herramientas listan cada objeto en una línea («🪨 Mena de hierro ×3 · /item_iron_ore»), sin la descripción entera, con la pestaña activa marcada «• … •». Equipar está en Equipo y usar en Consumibles; Volver lleva al resumen.

## [0.10.1] - 2026-10-18

Interfaz (F01, 2.ª parte): textos claros.

### Cambiado
- **Pruebas de habilidad legibles**: «🎲 Supervivencia: 2 + 1 = 3 vs CD 13 · ❌ Fallo» (el d20, el bono, el total, la CD y el veredicto) en vez de «2 → 3 contra CD 13 ❌». Una sola función (`characters.add_check`) para investigar, acciones de misión, robar y texto libre.
- **Artículos**: cada lugar lleva el suyo (`article` en `place.yaml`) y el texto dice «Llegas al Mercado», «a la Taberna», «por el Camino del Viejo Rey», «Rastreo en el Prado», «Ve a la Capilla del Alba». El traductor contrae «a el» y «de el». En inglés, «the Old Pass Mine»; la taberna se llama «Broken Crown Tavern».
- **Singular**: «1 ronda», «1 turno», «1 terminada», «1 punto», «1 logro»… El traductor elige `<clave>_one` cuando la cuenta es 1.
- La pista de la misión de cocina dice dónde está ahora «🔨 Fabricar».

### Añadido
- Leyenda de las competencias en `/sheet`: «● competente · ○ practicada · · sin entrenar · ★ rango de práctica».

## [0.10.0] - 2026-10-18

Empieza la consolidación (0.10.x) con la interfaz (F01, 1.ª parte): menos mensajes, menos botones y siempre a mano lo que puedes hacer.

### Añadido
- **⚒ Actividades** en el teclado fijo, en la escena (con cuántas hay) y como `/activities`: cazar, recolectar, expedición larga, rastrear, desollar, descansar, fabricar y curar, cada una con su duración y lo que te falta. Sin herramienta no sale el botón: sale «🛒 Pico · ir a Mercado», que te lleva a quien la vende. La disponibilidad usa la misma regla que el servicio (`activities.check`), así que un botón nunca promete lo que luego se rechaza.
- **🛠️ Oficios** desde Héroe y desde Actividades, con las pestañas de oficios, maestrías y aficiones. `/activities`, `/masteries` y `/hobbies` en el menú de comandos.
- Pista «Escribe lo que haces…» en el campo de texto.

### Cambiado
- Teclado fijo de 3 + 3: 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario (`KEYBOARD_VERSION = 3`: los jugadores existentes lo reciben solo).
- La escena se queda con lo social: Viajar, Investigar, Hablar, Comerciar y ⚒ Actividades, más «Seguir viaje», las acciones de misión y «Ver ciudad».
- **Un mensaje por acción**: investigar, cazar, abandonar o un texto libre dejan un solo mensaje con el resultado y la cabecera del lugar con sus botones, y el panel pulsado se queda sin botones. Subidas de nivel, crónicas y combates siguen en mensajes propios. Una actividad que termina sola trae los botones del lugar en el mismo mensaje.
- Comprar, vender, equipar, usar, aprender un oficio y fabricar ponen el resultado encima del mismo menú, sin mensaje nuevo. Empezar una actividad convierte el mensaje en su panel; «🔄 Actualizar» lo refresca en el sitio.
- **Rechazos en ventanita**: «Necesitas un pico», sin oro, un menú viejo, un doble toque o un error de combate salen como aviso emergente de Telegram, sin escribir en el chat, y el mensaje pulsado pasa a la vista actual. Nada se gasta dos veces.
- Las pistas del tutorial y el `/rulebook` dicen dónde están ahora cazar, recolectar, minar, curar y descansar.
- Hoja de ruta renumerada: la consolidación son parches **0.10.x** (la serie 0.9 terminó en 0.9.1), empieza por F01 y el hito A va justo después (`planning/roadmap.md`, `planning/iter.md`).

### Arreglado
- Pulsar dos veces la misma vista ya no manda un mensaje repetido («Message is not modified»).
- Un conflicto de versión al pulsar un botón ya no deja «Aquí tienes el actual:» sin la vista detrás.

## [0.9.1] - 2026-10-18

Preparación de la 0.10: el plan antes de tocar el juego.

### Añadido
- `planning/roadmap.md`: hoja de ruta de **0.10 (consolidación de todos los sistemas individuales)** y **0.11 (multijugador)**. Veinte fichas por sistema con lo implementado, lo que falta decidir, tareas y criterio de terminado; hitos 0.10-A…H, puerta de salida, frontera de 0.11 y cobertura de las 73 casillas del TODO.
- Sección 0 del roadmap: qué cambió desde la auditoría (0.9.0 entregó los logros), reglas de numeración (parches 0.9.x por hito; 0.10.0 al superar la puerta) y tabla de versiones orientativas.
- `planning/releases/0.9.1.md`: anuncio para los canales (borrador, no enviado).

### Cambiado
- `planning/iter.md`: «Próximo» reemplaza los candidatos 0.10–0.12 por 0.10 consolidación y 0.11 multijugador, con enlace al roadmap. `planning/README.md` lista el roadmap.

## [0.9.0] - 2026-10-17

### Añadido
- 30 logros y dos metalogros por personaje, con condiciones verificables, progreso, evidencia, fecha y puntos de prestigio; catálogo bilingüe y edición fija.
- Cuatro títulos, tres logros destacados en el héroe y tres objetivos seguidos en el diario; comando /achievements, categorías, pistas revelables y páginas de seis entradas.
- Eventos mecánicos idempotentes y métricas persistentes de combate para desafíos repetibles; concesiones y recompensas en la transacción de la acción.
- Anuncios privados agrupados con recuperación tras fallos y reinicios; migración 0009 y comando achievements-backfill con simulación por defecto.
- Pruebas de reglas, contenido, duplicados, rollback, concurrencia PostgreSQL, preferencias, desafíos y recuperación.

### Cambiado
- La versión 0.9 se dedica a logros; el cooperativo queda sin versión asignada y conserva sus requisitos CORE-01..03 y AI-01..02.
- Los logros reconocen hechos del motor sin llamadas a Gemini ni ventajas económicas o de combate. Cada servicio emite su hecho (bestiario, maestría, viaje, combate…) y el estado guardado solo se recorre en el backfill.
- Los comandos de Telegram van siempre en inglés, sin alias en español; los textos de consola (`oath help`, `tgtest` y los comandos de jugadores, tutorial y bot) pasan a inglés.
- Los anuncios de logros salen de un único handler que corre después de cada update.

## [0.8.6] - 2026-10-17

### Cambiado
- TODO: ideas nuevas de la partida de prueba en su sección (botón «Oficios» que reúna maestrías, oficios y aficiones; botón «Actividades» del lugar; emojis para los materiales; fabricar con herramientas portátiles en vez de estaciones fijas).

## [0.8.5] - 2026-10-17

### Cambiado
- `AGENTS.md` recupera lo que salió del README: el flujo de una acción libre, las salvaguardas ante la IA y qué guarda cada carpeta de `artifacts/`.

## [0.8.4] - 2026-10-17

### Cambiado
- `README.md` raíz más simple: qué es el juego, qué te espera, la regla de oro, los canales y la instalación mínima. Solo se actualiza al final; los detalles de trabajo (pruebas, `tgtest`, anuncios en los canales) pasan a `AGENTS.md`.

## [0.8.3] - 2026-10-17

Planning reorganizado: un libro de ideas, resúmenes por tema en latín y una guía para trabajar gastando pocos tokens.

### Añadido
- `planning/Possibilium.md`: el libro de lo posible. Todas las ideas, alternativas y preguntas con IDs (`CLA-01`, `MIN-01`, `COO-01`…), la base vigente de la 0.8.2 y sus discrepancias, paquetes implementables y backlog semilla; en los anexos, el texto íntegro de los cuatro PDF de diseño y las versiones anteriores del planning.
- `planning/ars.md`: dirección audiovisual (auditoría de imágenes, biblia visual, cinco estilos, quince prompts para Leonardo, música, voces, mapas, formatos y licencias).
- `AGENTS.md`: invariantes, mapa del repo, cómo leer barato, pruebas y versionado para cualquier agente; `CLAUDE.md` lo importa.
- `content/officina/`: laboratorio de imágenes con su prompt al lado. El bot no lo lee y git solo guarda su README.

### Cambiado
- Planning en latín, cada archivo como resumen de Possibilium (estado actual, decidido, próximo y preguntas): `iter` (antes `roadmap`), `ordines` (clases), `progressio`, `pugna` (combate), `opificia` (profesiones), `mercatura` (comercio), `mundus` (mundo y misiones), `bestiarium`, `societas` (multijugador), `narratio` (IA) y `facies` (interfaz Telegram).
- README raíz al día (12 trasfondos, 7 oficios y 2 aficiones, tutorial de 10 misiones, viaje directo); TODO y comentarios de `content/` y del código apuntan a los archivos nuevos.

### Eliminado
- `planning/referencias/`: los cuatro PDF (GDD, guía audiovisual, The Living Oath y Roadmap) y su README; su texto está en los anexos de Possibilium y los binarios en el historial de git.
- Los antiguos `planning/*.md` por tema y `planning/audiovisual.md`.

## [0.8.2] - 2026-10-17

Tutorial nuevo tras el speedrun con una maga: más corto, sin mazmorras y sin esperas en la beta.

### Añadido
- **Tutorial de 10 misiones**: hablar, la ciudad, el mercado (nueva: Mira y Tessa), cazar y desollar, recolectar, cocinar, minar, cazar en la mina, curarse y descansar, y el Viejo Colmillo como jefe final (lo da Bram). El relicario y la cripta pasan a ser la primera aventura después del tutorial.
- **Objetivo `hunt`**: «caza N veces en X» cuenta cualquier victoria de 🏹 Cazar o 🐾 Rastrear allí, de día o de noche. Los jabalíes y la mina lo usan.
- Poción de maná: con varios conjuros gastados, el inventario deja elegir cuál recupera.

### Cambiado
- **Beta** (marcado `# beta only` en el código):
  - durante el tutorial, toda actividad con tiempo (recolectar, minar, rastrear, desollar) termina al momento;
  - el descanso largo es instantáneo para todos;
  - las pociones de vida y de maná cuestan 1 de oro.
- «Colmillos en el prado» pide 2 de carne desollando (antes, una piel): ya no puedes quedarte sin carne para el guiso.
- «Heridas de guerra» pide también un descanso largo y abre el Viejo Colmillo.
- Viejo Colmillo: 24 → 18 PV, CA 12 → 11, ataque +4 → +3 y daño 2d6+1 → 1d8+1. En el simulador, el mago de nivel 4 gana el 89 %.
- Mina del Paso Viejo: parejas de murciélagos y de ratas desde nivel 3. Camino del Viejo Rey: parejas de bandidos y de trasgos desde nivel 3, capitán bandido desde nivel 4 (el tutorial pasa por ahí a nivel 1–3).
- Bosque de los Susurros: lobos desde nivel 3, parejas de lobos desde nivel 4 y la pareja trasgo + bandido desde nivel 3; a nivel 1–2 salen jabalíes y trasgos sueltos. En el Claro de la Raíz Roja, lobos desde nivel 3.

### Arreglado
- 📜 al objetivo:
  - ya no manda de día al prado a cazar murciélagos que solo salen de noche: solo cuenta las criaturas que salen a esa hora y a tu nivel;
  - funciona en el relicario (buscar en el bosque, entregarlo a Holt, el guardián).
- Objetivos sin lugar fijo: «Haz un descanso largo» en vez de «Descansa en cualquier sitio», y el 📜 lleva a la posada más cercana.
- El descanso del osario dice «gratis» en vez de «(0 🪙)».

## [0.8.1] - 2026-10-17

### Añadido
- `tests/features.md`: checklist de lo que hay que probar siempre, jugando con la cuenta de prueba, tras una feature grande (personaje, mapa y viaje, combate, actividades, comercio, misiones, diario). Cada feature grande añade sus casillas.

## [0.8.0] - 2026-10-17

Moverse por el mapa sin tedio: eliges adónde ir y el juego pone el camino.

### Añadido
- **Viaje directo a cualquier lugar conocido**, también entre zonas. De la cripta despejada a la plaza, o de la plaza a la mina, en un toque. Lo nuevo se sigue explorando tramo a tramo. El camino solo pasa por lugares visitados y sin combate fijo pendiente: a una sala con guardianes se entra, pero no se atraviesa.
- **Una tirada de emboscada por viaje**: 15 % × peor ⚠️ + 5 % por cada tramo ⚠️ extra, con un tope del 45 %. Con un solo tramo, igual que antes. Si sale, el viaje se para en un tramo peligroso y la escena ofrece «▶️ Seguir hacia…», que termina el viaje sin otra tirada. La derrota lo cancela.
- **Botón 📜 al objetivo** en el mapa. Lleva al lugar conocido más cercano donde se cumple el siguiente paso de cada misión activa: hablar con alguien, visitar, cazar, recolectar, fabricar. No revela sitios que no conozcas.
- Fase 2 del viaje (expediciones, estilos, atajos, favoritos) diseñada en `planning/mundo-y-misiones.md`.

### Cambiado
- **Mapa nuevo**:
  1. dónde estás;
  2. 📜 objetivo;
  3. esta zona;
  4. las demás zonas conocidas (con más de 2 lugares, un botón abre la zona);
  5. 🌫️ «Sin explorar» (antes «Más lejos»).
- Desde cualquier calle de la ciudad, las salidas (pasando por la plaza) están a un toque.
- **Menos mensajes**: al llegar sin nada más que contar, el mensaje del mapa se convierte en la escena del lugar («Llegas a X por Y, Z (N yd de camino)»).
- El `/rulebook` («Viajar y explorar») y las pistas del mapa explican el viaje directo y qué significan las ⚠️.

## [0.7.31] - 2026-10-17

Ajuste tras repetir el tutorial con una druida.

### Cambiado
- Jabalí, bandido y esqueleto de la cripta hacen 1d4 de daño (antes 1d4+1 tras la 0.7.28; originalmente 1d6+1). En el simulador, a nivel 1 las 8 clases ganan al menos un 92 % de los 1 contra 1 con jabalí, bandido, murciélago y esqueleto (mago y druida, las más frágiles, entre un 92 y un 96 %).
- El mapa enseña «Curar heridas (gratis)» en la capilla (decía 3 🪙, pero en la beta no se cobra).

## [0.7.30] - 2026-10-17

### Cambiado
- **Sin tiempos de viaje.** El mapa, los botones de viaje y el aviso de llegada enseñan solo la distancia en yardas («Llegas a Taberna La Corona Rota (200 yd de camino)»). En la beta viajar es instantáneo; el `/rulebook` («Viajar y explorar») lo explica. Los minutos de las actividades (minar, rastrear, descansar…) no cambian.
- **Saludo de quien ya te conoce**: Vale y Holt saludan de otra forma cuando ya has terminado una misión suya (`greeting_return` en `npcs.yaml`).
- Inventario: lo equipado sale primero y los botones de equipar/quitar llevan el icono del hueco, para distinguir dos armas iguales.
- Crónicas de plantilla: «ocupa tu estancia en…» pasa a «ocupa tu jornada en…» en todas las crónicas de plantilla.

## [0.7.29] - 2026-10-17

Gemini ya no deja sin IA a todo el bot por un fallo suelto.

### Cambiado
- **Reintento tras una sobrecarga**: si el último modelo disponible responde 500/502/503/504, se reintenta una vez a los 1 s. Los timeouts no se reintentan (el jugador nunca espera dos).
- **Cooldown corto**: tras un timeout o una sobrecarga, un modelo se salta 20 s (antes, 120 s). La cuota diaria (429) sigue saltándose las horas que indique Google.
- **Modelo de respaldo opcional**: `GEMINI_MODEL_FALLBACK` en `.env` se prueba el último, para cualquier tipo de llamada, si fallan los demás. Vacío por defecto.

### Arreglado
- Un `TimedOut` de Telegram al pulsar un botón ya no muestra «Algo salió mal»: la acción se hace igualmente. Los errores de red de Telegram se registran como aviso, sin traceback ni mensaje al jugador.

## [0.7.28] - 2026-10-17

Tutorial más fácil para todas las clases, tras jugar las 11 misiones con una pícara.

### Cambiado
- **Criaturas más blandas** (la XP y el botín no cambian):
  - Jabalí, bandido y esqueleto de la cripta: 11 → 7 PV, −1 al ataque y daño 1d6+1 → 1d4+1.
  - Murciélago de cueva: 6 → 5 PV, −1 al ataque y daño 1d4+1 → 1d4.
  - Capitán bandido: 32 → 26 PV, −1 al ataque y daño 1d8+3 → 1d8+1.
  - El Viejo Colmillo: 34 → 24 PV, −1 al ataque y daño 2d6+3 → 2d6+1.

  Con el simulador, a nivel 1 la clase más floja (mago/druida) gana un 83–90 % de los 1 contra 1 (antes 52–85 %) y a nivel 2 más de un 96 %; la pícara pasa al 98–100 %.
- **Nivel 1: un enemigo cada vez en el prado.** Las entradas de las tablas de encuentros tienen `min_level`: las parejas de jabalíes y de murciélagos del Prado de los Colmillos salen desde el nivel 2.
- **Esconderse** llega a nivel 1 para el Pícaro (antes, nivel 2): sin él, el Ataque Furtivo del nivel 1 no se podía activar.
- **La hermana Ysolde cura todos los PV** durante la beta (antes, 1d8+4); su saludo y la pista de «Heridas de guerra» dicen que no cobra por ahora.
- «Colmillos en el prado» ya no dice «sin peligro»: aconseja ir con la vida llena y una poción.
- Al terminar «Heridas de guerra», Vale manda al Bosque de los Susurros (donde empieza «El relicario sellado»), no directamente a Holt.

### Arreglado
- Cazar fuera del prado ya no dice «Rastreas el prado…»: el texto es genérico y cada lugar puede definir el suyo (`hunt_day` / `hunt_night` en `place.yaml`).
- «Has perdido 0 de oro» y «Pagas 0 de oro» ya no salen cuando no cuesta nada.

## [0.7.27] - 2026-10-15

### Añadido
- **«📍 Lugar»** en el teclado fijo: muestra la escena, lo mismo que `/start` o `/look` (dónde estás, tu vida, quién hay y lo que puedes hacer), o el combate si estás peleando. El teclado queda así: 📍 Lugar · 🧝 Héroe · 🗺 Mapa / 🎒 Inventario · 📖 Diario. Quien ya tenía el de 4 botones recibe el nuevo en su siguiente vista.
- `oath restart` y `oath stop`, en `oath help`:
  - `oath stop` para el bot en marcha;
  - `oath restart` lo para y lo arranca de nuevo en segundo plano, con la salida en `artifacts/logs/bot-console.log`.

  El bot guarda su PID en `.run/bot.pid`. Un bot arrancado antes de esta versión se encuentra por su línea de comandos.

## [0.7.26] - 2026-10-15

Más arreglos de la partida de prueba.

### Arreglado
- Informe de batalla:
  - «🏆 Victoria» ya no sale dos veces al final del informe completo;
  - los botones del resumen dicen la ronda real («Ronda 0 ▶», «◀ Ronda 1»).
- Tras una emboscada o una presa rastreada, la crónica llega en el mismo mensaje que el botín, con el resultado en la cabecera.
- Las crónicas genéricas nombran a la criatura con artículo: «te topas con un murciélago de cueva» y no «You find Cave bat».
- `/map` estando ocupado ya no enseña caminos que no se pueden tomar: dice que estás ocupado.
- «Obtienes: … ×1 · /item_…» sin el punto antes del enlace.
- En inglés, las cifras de las estadísticas llevan coma («3,400 yards»).

### Cambiado
- Las tiendas se abren por categorías (⚔️ Armas, 🛡️ Armaduras, 🧪 Consumibles, 🧰 Herramientas…), con la ficha `/item_` de cada objeto. Después de comprar sigues en la misma categoría.
- La poción de curación cuesta 20 de oro (antes, 50).
- El ala de murciélago es un material y sirve para la poción de maná (receta nueva de alquimia, rango 1).
- La escena y el panel de actividad ya no repiten Inventario · Héroe · Diario: están en el teclado fijo. El icono de Héroe es 🧝 en todas partes.

## [0.7.25] - 2026-10-15

Arreglos de la partida de prueba con Brannoc.

### Arreglado
- **Herido y sin oro ya no te deja atascado.** Durante la beta, la hermana Ysolde cura gratis y cierra también las heridas graves de una derrota. Antes cobraba 3 de oro y no curaba a quien estaba herido, y el descanso cuesta 5.
- **«Colmillos en el prado» se puede hacer a cualquier hora**: de noche, en el prado salen también jabalíes.
- **Si la IA no responde, quien te dio la misión te recuerda lo que toca**: la pista de la misión activa, en vez de una frase genérica como «no lo sé».

### Añadido
- Aviso de poca vida (menos de la mitad) al cazar, rastrear o empezar una expedición larga.
- Al cumplir un objetivo de una misión que aún no ha terminado, el bot dice lo siguiente. Por ejemplo, tras hablar con Vale: «📜 Alistamiento: ahora, Consulta en el /rulebook: Actividades».

## [0.7.24] - 2026-10-15

### Añadido
- `oath tutorial-stats`: para medir el tutorial en la beta. Muestra:
  - la mediana de minutos reales de cada misión;
  - cuántos jugadores la acabaron y cuántos están en ella;
  - por jugador, cuántas misiones lleva, en cuánto tiempo y en cuál está atascado y desde cuándo.

  Usa las fechas que ya guarda la base de datos, sin migración. Quien tiene el tutorial hecho por `legacy_done` no cuenta.

### Cambiado
- `planning/roadmap.md`: 0.7.15–0.7.24 hechas; lo siguiente es la 0.8.0 (multijugador).

## [0.7.23] - 2026-10-15

### Añadido
- «📈 Estadísticas» en el diario:
  - distancia recorrida;
  - lugares y ciudades visitados;
  - combates ganados, perdidos y huidas;
  - monstruos derrotados (los tres más cazados);
  - esquivas (ataques enemigos fallados), golpes críticos y actividades terminadas.

  Los monstruos cuentan desde siempre (salen del bestiario); lo demás, desde esta versión.
- Texto largo (`details`) para todas las habilidades de las 8 clases, en `/skill_<clave>`. Antes solo lo tenía el Paladín.

## [0.7.22] - 2026-10-15

### Añadido
- **Ronda 0** en el panel y en el informe: la iniciativa de cada uno con su d20 y su DES, antes de la ronda 1.
- Con ventaja o desventaja salen **los dos d20** y el que cuenta: «🎲 [6 · 14] → 14 +5 = 19».
- **Botones por clase**:
  - en la primera fila, los ataques y la habilidad destacada 🌟 de la clase (`signature` en `classes.yaml`: Golpe Consagrado, Esconderse, Oleada de Acción o Segundo Aliento, Llama Sagrada, Rayo de Fuego, Látigo de Espinas, Burla Cruel y Estallido Sobrenatural);
  - «✨ Acciones» abre el resto de poderes que puedes usar en ese momento.
- **Informe completo**: «📜 Informe» cuenta todas las rondas seguidas, quién hizo qué, en varios mensajes si hace falta.

### Cambiado
- Lo que antes era «📜 Informe» es ahora «📊 Resumen»: el resultado, las cifras y el botín, con las páginas por ronda.

## [0.7.21] - 2026-10-15

### Añadido
- **Las actividades terminan solas.** Cada 10 s, el bot cierra las tareas de campo (trabajar, expedición, rastreo, descanso, desuello) que han llegado a su hora y te manda el resultado aunque hayas cerrado Telegram.
  - Si una expedición acaba en emboscada, llega el aviso con el panel de combate, que espera a que vuelvas.
  - Un reinicio del bot no pierde nada: el temporizador está en la base de datos.
- **Desollar con `/skin`** o con el botón «🔪 Desollar» del panel de victoria. Es una actividad corta:
  - 10 s por presa pequeña, 15 el jabalí, 20 el lobo y 40 el Viejo Colmillo (`skin_seconds` en `monsters.yaml`);
  - si viajas o empiezas otra cosa, la pieza se pierde.

  En el tutorial, el primer desuello sigue siendo instantáneo.

### Cambiado
- Al empezar una actividad llega un solo mensaje («Te pones a trabajar…», cuánto falta y «🔄 Actualizar» / «Abandonar») en vez del aviso y la escena repetida. Ya no hay botón «Recoger».
- La crónica y el botín llegan en un solo mensaje: «⛏️ ✅ Terminas tu trabajo en X», la crónica, lo obtenido, la XP y «Crónica 1/15».
- El desuello ya no es automático al ganar; los trofeos del rastreo sí.

## [0.7.20] - 2026-10-15

### Cambiado
- **Artificiería → Ingeniería** (clave `engineering`), para no confundirla con la clase Artificiero. Su estación es el «banco de ingeniero». `/prof_artificing` sigue llevando a `/prof_engineering`.
- **La Pesca es una afición de verdad**, como la Cocina:
  - es una entrada de `professions.yaml` con `practice: fishing`: sin estación ni recetas, sube pescando;
  - su XP se guarda con la de los oficios y avisa como un oficio («📈 +10 XP de Pesca»);
  - tiene guía propia, `/prof_fishing`.

  `gathering.HOBBIES` desaparece: las maestrías de campo son minería, tala, herboristería, desuello y rastreo.
- Migración `0008`: cambia `artificing` por `engineering` en los oficios guardados y mueve la XP de pesca de las maestrías a la afición.

## [0.7.19] - 2026-10-15

### Añadido
- `/item_<clave>`, por ejemplo `/item_skinning_knife`: la ficha de un objeto. Muestra:
  - qué es y para qué sirve;
  - de qué recetas es ingrediente;
  - dónde se consigue (lugares, criaturas, oficios, tiendas y misiones);
  - cuánto vale y por cuánto se vende.

  Cada «Obtienes…» y cada línea del inventario la enlazan.
- `/monster_<clave>`: solo la imagen y el nombre de una criatura. Al empezar un combate, «👁 Míralos:» enlaza a cada enemigo.
- `/masteries` y `/hobbies`, como `/classes`: cada maestría con su herramienta y dónde se practica, y cada afición con su estación y su guía. Funcionan sin personaje y se enlazan con `/professions` mediante pestañas.

### Cambiado
- `/rulebook`:
  - «Actividades» explica cada acción con su duración, qué da y su riesgo;
  - «Recolección y oficios» distingue maestrías, oficios y aficiones.

  Las cifras salen del motor, así que no se desfasan.
- `/help` lista `/masteries`, `/hobbies` y `/rulebook`.

## [0.7.18] - 2026-10-15

### Añadido
- La escena muestra la hora del juego y cuánto falta para el cambio, por ejemplo «☀️ 14:30 · anochece en 55 min».
- «📚 Registro» en el diario: las misiones terminadas, cada una con su página.

### Cambiado
- `/quests` solo enseña las misiones en curso o disponibles; las terminadas están en el registro.
- «👥 Aquí:» de la escena es una lista, un PNJ por línea.
- «📜 Nueva misión…» enlaza a `/quests`.

## [0.7.17] - 2026-10-15

### Añadido
- **Teclado fijo** bajo el chat: 🧝 Héroe · 🗺 Mapa · 🎒 Inventario · 📖 Diario.
  - Llega al crear el personaje y con `/start`. Quien ya jugaba lo recibe en su siguiente vista, una vez por idioma.
  - Cada botón abre lo mismo que su comando (`/hero`, `/map`, `/inventory`, `/journal`) y nunca llega a la IA como texto libre.

### Cambiado
- Iconos: el diario pasa a 📖, el reglamento a 📘 y el bestiario a 🐉, para que no se repitan.

## [0.7.16] - 2026-10-15

### Añadido
- **Tutorial acelerado**. Las misiones del tutorial llevan `tutorial: true`. Cuando una pide recolectar o desollar algo:
  - la primera recolección o expedición en un lugar que tiene ese recurso termina al momento, sin emboscada, y da justo lo que falta (por ejemplo, 3 menas de hierro);
  - el primer desuello da seguro el cuero que pide.

  Solo cuenta la acción que pide la misión activa, y una vez por misión. Lo demás dura lo normal.

### Cambiado
- Las pistas de «Raíz de sangre» y «Hierro para la Guardia» avisan de que la primera vez termina al momento.

## [0.7.15] - 2026-10-15

### Añadido
- Objetivo de misión `read`: abrir una sección del `/rulebook`. El diario lo muestra como «Consulta en el /rulebook: …».
- Sección «🧺 Actividades» en el `/rulebook`: minar, talar, recolectar hierbas, pescar, expedición larga, rastrear, cazar y descansar, con lo que dura cada una y la herramienta que pide.
- «Alistamiento», la primera misión del tutorial, pide leer esa sección después de hablar con Vale.

### Cambiado
- El tutorial ya no depende de la hora:
  - en la Mina del Paso Viejo hay murciélagos de día y de noche (más que antes, junto a las ratas);
  - «Alas al anochecer» manda a cazarlos a la mina.
- «Calles de Crownreach» pide también ir a la taberna La Corona Rota, además del Barrio de Oficios, antes de hablar con Bram.
- Los tests ignoran `GAME_CLOCK_OFFSET_HOURS` del `.env`.

## [0.7.14] - 2026-10-14

### Añadido
- `GAME_CLOCK_OFFSET_HOURS` en `.env`, solo para pruebas: adelanta el reloj del juego para todos (horas de juego; con `12`, la noche se hace día). Se aplica al reiniciar el bot.

### Arreglado
- «📜 Más trasfondos…» volvía siempre a los 4 básicos, así que no se podía elegir, por ejemplo, Noble.

### Cambiado
- TODO: las notas de la partida de prueba del 14-10 ordenadas en sus secciones, con lo ya decidido:
  - las misiones se entregan a quien las dio;
  - el tutorial no dependerá de la hora (murciélagos en la mina);
  - las imágenes de los linajes quedan apuntadas para más adelante.

## [0.7.13] - 2026-10-14

### Añadido
- **Tutorial de la sargenta Vale**: 8 misiones de nivel 1 a 3. La sargenta Vale, nueva PNJ, espera en la plaza día y noche, y la plaza invita a hablar con ella nada más crear el personaje. Cada misión enseña una cosa y su recompensa es la herramienta de la siguiente:
  1. hablar con un PNJ;
  2. moverse por la ciudad con `/map`;
  3. cazar jabalíes y desollar;
  4. salir de la ciudad y recolectar raíz de sangre;
  5. cocinar un estofado en el fogón de la taberna;
  6. minar hierro;
  7. cazar murciélagos de noche;
  8. curarse con la hermana Ysolde y volver con Vale.

  Son unos 520 XP con los combates. Al acabarlo se abre «El relicario sellado».
- 12 réplicas de respaldo para Vale cuando la IA no responde.
- Campo `legacy_done` en las misiones: quien ya completó las misiones antiguas (hasta «Alas al anochecer») tiene el tutorial hecho, sin cobrar sus recompensas otra vez.

### Cambiado
- El tutorial sustituye a «Bienvenido a Crownreach», «Colmillos en el prado» y «Alas al anochecer». El relicario, la cripta y el Viejo Colmillo pasan a ser las misiones 9–11.
- Bram ya no habla de «problemas al norte»: manda a los nuevos con la sargenta Vale y les ofrece el fogón.
- Los atributos solo se alinean en el bloque monoespaciado de `/hero` y `/sheet`. En la creación salen sin espacios de más.

## [0.7.12] - 2026-10-14

### Añadido
- Objetivos de misión nuevos:
  - `gather`, `skin` y `craft`: un objeto, y cuenta la cantidad conseguida al recoger (también lo que se salva de una emboscada), al desollar (también los trofeos de un rastreo) o al fabricar;
  - `rest`: un descanso largo que termina en ese lugar;
  - `heal`: curarse con la curandera de ese lugar.

  `rest` y `heal` aceptan `target: any`. El diario los muestra como «Recoge», «Consigue desollando», «Fabrica», «Descansa en» y «Cúrate en». Son la base del tutorial de la próxima versión.
- La validación del contenido comprueba que el objetivo de cada misión existe.

## [0.7.11] - 2026-10-14

### Añadido
- `/skill_<clave>`, por ejemplo `/skill_lay_on_hands`: la página de una habilidad de clase. Muestra:
  - la clase y el nivel;
  - el tipo de acción y los usos;
  - una explicación más larga;
  - «⚙️ Cómo funciona», generado con los mismos datos que usa el motor (daño, salvación, área, curación, estados, CA, crítico…).

  Funciona sin personaje y, con tu propia clase, marca si ya la tienes (✅) o en qué nivel llega (🔒).
- Campo opcional `details: {es, en}` en las habilidades de `content/classes.yaml`. Las del Paladín ya lo tienen.

### Cambiado
- `/class_<clase>`, la tarjeta de subida de nivel y `/sheet` enlazan cada habilidad con su `/skill_<clave>`.

## [0.7.10] - 2026-10-14

### Añadido
- `/rulebook` (alias `/rules`) en el menú de Telegram. Es un reglamento con un índice de botones y una página por sección, con ◀ ▶ para pasar de una a otra:
  - tiradas y dificultad;
  - atributos y modificadores, con la lista de los seis;
  - CA;
  - puntos de vida y dado de golpe;
  - combate;
  - descanso y curación;
  - linajes, trasfondos y clases;
  - recolección y oficios;
  - viajar.

  Funciona sin personaje.
- Los textos del reglamento están en `content/rulebook.yaml` (es/en). Añadir una sección nueva solo pide añadir una entrada.

### Cambiado
- La bienvenida de `/start` invita a leer el `/rulebook` y trae el botón «📖 Reglamento».

## [0.7.9] - 2026-10-14

### Añadido
- **Trasfondo propio**: «✍️ Escribir mi propio trasfondo» en la creación. El jugador escribe un nombre y una historia (20–300 caracteres), Gemini la revisa (`oathforge/ai/moderation.py`) y, si la acepta, elige 2 habilidades; empieza con 10 de oro, una antorcha y una cuerda.
- La revisión rechaza insultos, odio, contenido sexual, gore gratuito, personas reales o datos personales y los intentos de ventaja («empiezo con mil de oro», «soy el admin»), y explica qué cambiar. Si la IA no responde, el trasfondo propio no se acepta y se ofrece la lista.
- Columna `characters.custom_background` (migración 0007). El nombre y la historia salen en `/hero`, `/sheet`, las crónicas y el contexto del narrador.

### Cambiado
- `/background` recuerda que también se puede escribir uno propio.

## [0.7.8] - 2026-10-14

### Añadido
- `/lineage` (alias `/race`) y `/background`: cada linaje con sus bonificadores, competencias y rasgo, y cada trasfondo con sus habilidades, oro y equipo. Funcionan sin personaje y a mitad de la creación sin cortar el asistente.
- 8 trasfondos nuevos (12 en total): artesano de gremio, ermitaño, noble, forastero, marinero, huérfano callejero, artista y héroe del pueblo, cada uno con 2 habilidades, oro y equipo inicial.

### Cambiado
- El paso de trasfondo explica los 4 básicos (habilidades, oro y equipo) y el botón «📜 Más trasfondos (12)…» muestra todos; «◀ Los básicos» vuelve.

## [0.7.7] - 2026-10-14

### Añadido
- Cada atributo tiene su emoji (💪 FUE, 🏹 DES, 🫀 CON, 🧠 INT, 🦉 SAB, 🎭 CAR; campo `icon` en `content/abilities.yaml`), y lo mismo cada linaje y trasfondo.

### Cambiado
- Creación de personaje con emojis: linajes y trasfondos con su icono, «⚔️ Elige tu clase (ℹ️ /classes)» con el icono y el dado de golpe de cada clase, y una confirmación con 🦸, ❤️ y los atributos en dos filas.
- Los atributos se pintan igual en la compra por puntos, la confirmación, `/hero` y `/sheet` (`render.attribute`).
- TODO: las ideas nuevas (tutorial de la sargenta, `/lineage`, `/background`, trasfondo propio, `/rulebook` y `/skill_<clave>`) ordenadas en sus secciones.

## [0.7.6] - 2026-10-14

### Añadido
- `/map` (y el botón «🧭 Viajar», que abre la misma vista): dónde estás, a dónde puedes ir, cuánto tardas en minutos y yardas, y qué se puede hacer en cada lugar (tiendas, curandera, descanso, recolección, caza, fabricar, gremio y quién está ahora).
- El mundo como grafo (`oathforge/services/world_map.py`): las salidas son aristas con peso en minutos de juego y distancia a 100 yd/min (ritmo normal de D&D; 1 km ≈ 1094 yd). Una salida puede fijar `yards:` si el terreno es lento (la galería inundada: 3 min, 150 yd).
- Validación al arrancar: una ciudad tiene un único `hub`, solo se sale de ella desde él, sus calles no tienen peligro ni combates fijos y todos sus lugares están conectados. Un test comprueba que cada ruta va y vuelve igual.

### Cambiado
- En una ciudad vas directo a cualquier lugar por el camino más corto (Dijkstra); se sale de la ciudad solo desde la plaza. En tierras salvajes y mazmorras se avanza tramo a tramo (cada camino tira su emboscada; la cripta, sala a sala); el mapa enseña el resto de la zona con su ruta. El viaje sigue siendo instantáneo mientras probamos.
- La IA también entiende «voy a la capilla» desde cualquier punto de la ciudad.

## [0.7.5] - 2026-10-14

### Añadido
- Comando corto `oath` (mismo que `oathforge`, que sigue funcionando). Tras actualizar, `.venv\Scripts\pip install -e .` lo instala.
- `oath delete-player [id|nombre] [--yes]`: borra un solo jugador y todo lo suyo (personaje, objetos, combates, memorias de NPC, misiones…). Sin argumentos lista los jugadores; sin `--yes` solo muestra qué borraría. Los objetos que fabricó y tienen otros se quedan (sin autor) y el registro de acciones se conserva anónimo. Lógica en `oathforge/services/admin.py`.

### Cambiado
- `oath help` más limpio: comandos agrupados (Bot, Jugadores, Pruebas, Ayuda), con `oath` delante, descripciones de una línea alineadas y una nota sobre `--yes`.
- Mensajes de `reset-players` en español.

## [0.7.4] - 2026-10-14

### Cambiado
- Prompts de Leonardo AI anotados en su `.prompt.md`: las 10 criaturas del bestiario, la barda, los retratos de Guerrero, Pícaro, Sacerdote y Paladín (el mismo prompt para hombre y mujer) y la panorámica de Crownreach. Faltan Mago, Druida, Brujo y el bardo.

## [0.7.3] - 2026-10-14

### Añadido
- Ilustraciones del bestiario: una por criatura (10) en `content/monsters/<criatura>/images/portrait.jpg`, con el botón «🖼️ Ver ilustración» en su ficha una vez vista.
- Retrato de la barda (`content/classes/bard/images/portrait.female.jpg`).
- Junto a cada imagen de `content/`, un `<nombre>.prompt.md` para guardar el prompt con el que se generó (de momento pendiente de rellenar); el catálogo avisa si falta.
- `tools/prepare_image.py --trim-bottom N` quita la firma o el texto falso que pinta el generador.

### Arreglado
- Cada criatura tiene su propio icono en el bestiario (campo `icon` en `content/monsters.yaml`): el murciélago ya no sale con 🐗.

## [0.7.2] - 2026-10-14

### Cambiado
- La guía de los textos de respaldo pasa de `content/fallbacks/README.md` a `planning/ia-y-narracion.md`; los YAML de respaldo apuntan ahí.

## [0.7.1] - 2026-10-14

### Añadido
- 612 variantes de respaldo en español e inglés: 348 crónicas, 168 narraciones, 72 réplicas de PNJ y 24 avisos; al menos 12 por caso.
- Crónicas propias de minería, tala, hierbas y pesca para cada desenlace de recolección o estancia larga, conservando las crónicas ya guardadas.
- Validación de cobertura, variantes distintas, traducciones y marcadores; guía de mantenimiento en `content/fallbacks/README.md`.

### Arreglado
- La narración de respaldo prioriza victoria, derrota y huida, distingue el robo fallido y no presenta el inicio de descanso como curación.
- Un fallo de conversación muestra una réplica neutral y un único aviso; las compras y demás botones siguen funcionando.
- Los avisos distinguen presupuesto diario del juego agotado de indisponibilidad sin causa confirmada, sin prometer una recuperación inmediata.
- Las respuestas de IA vacías también activan el respaldo.

## [0.7.0] - 2026-10-13

### Añadido
- **Aficiones**: Cocina y Pesca dejan de ser oficio y maestría y pasan a ser aficiones opcionales, sin plaza. Cualquiera cocina en el fogón de La Corona Rota. Quien tenía Cocina como oficio recupera la plaza y conserva la XP.
- **📜 Escribanía** (mesa de escriba, Barrio de Oficios):
  - Materiales: tinta (raíz de sangre + carbón) y pergamino (cuero de jabalí).
  - Pergaminos de un solo uso que cualquier clase lee en combate: Dardo de fuego (rango 0, ataque +5, 2d6 de fuego), Curar heridas (rango 1, 2d8+2 PV), Égida (rango 1, 2d6+3 PV temporales) y Sueño (rango 2, salvación de SAB CD 13).
- **💣 Artificiería** (banco de artificiero, Barrio de Oficios):
  - Materiales: pólvora (carbón + mena de hierro) y mecha (fibra vegetal).
  - Bombas: de humo (rango 0, huyes sin tirada), de fuego (rango 1, toda una fila, salvación de DES, 2d6 de fuego y ardiendo) y cegadora (rango 2, aturdido 1 turno).
- **«🎒 Objetos» en el panel de combate** para usar pergaminos y bombas. También funciona con una acción escrita («le lanzo la bomba de fuego»).
- **Guía de cada oficio y afición**: `/prof_<oficio>`, como `/class_<clase>`. Cuenta qué hace, dónde se trabaja, de qué maestrías salen los materiales y las recetas por rango (✅/🔒 según el tuyo). Enlazada desde `/professions`.
- **Capilla del Alba** (a 2 min de la plaza) con la **hermana Ysolde**: «🙏 Curar heridas» por 3 de oro (1d8+4 PV). Respeta el techo de «herido» y no cobra si estás sano. La inscripción del altar está ahora en la capilla.
- **⚙️ `/settings`**: idioma y tiradas manuales en un solo sitio.
- **Textos genéricos de respaldo** en `content/fallbacks/` para cuando Gemini no responde:
  - `chronicles.yaml`: las crónicas, igual que antes.
  - `dialogue.yaml`: réplicas por NPC, sin adjetivos con género.
  - `narration.yaml`: una frase de ambiente por tipo de desenlace.
  - `freetext.yaml`: avisos de «el DM no te oye, usa los botones».
  - Se validan al arrancar y se eligen con `ai/fallbacks.pick`.

### Cambiado
- **Descanso largo**: ahora son 8 horas de juego (80 min reales) acostado en la posada. Pagas al acostarte y quedas ocupado. Un aviso «☀️» te despierta y «Levantarse» recupera PV, usos y «herido». Si te levantas antes, no recuperas nada.
- **Gemini 3.1 Flash-Lite para todo** (interpretar, narrar, NPC y crónicas).
- **Respaldo rápido cuando Gemini cae**: un modelo nunca se reintenta a sí mismo y queda en pausa 2 min tras un fallo. El timeout baja a 10 s (8 s en crónicas). Con la API caída, la primera acción tarda como mucho 10 s y las siguientes responden al momento con el texto genérico (antes, unos 45 s cada una).
- **Tiradas manuales**: desactivadas por defecto. Al activarlas se avisa de que el dado animado de Telegram es solo decoración (un d6) y que la tirada real es el d20 del motor. `/roll` sale del menú de comandos: la tirada se lanza con el botón «🎲 Tirar el dado» cuando se pide.
- **Barra de XP**: muestra el avance del nivel, «XP 14/300 hacia el nivel 3 (214 en total)», y barra y números cuentan lo mismo.
- **Enemigos repetidos** llevan letra: «Jabalí A», «Jabalí B».
- El botón «🧪 Poción» solo sale en combate si llevas pociones.
- **Cambiar de oficio**: el botón dice el precio («Cambiar por Alquimia (25 🪙)») y, tras elegir cuál dejas, se pide confirmación.
- «🔨 Fabricar» sin recetas aquí dice dónde está la estación de cada uno de tus oficios y aficiones.
- **Tienda**: la lista va agrupada (armas, armaduras, consumibles, herramientas) con lo que hace cada objeto (daño, CA, curación, maestría).
- Todo lo que vale al menos 1 de oro se vende por al menos 1 (la antorcha ya no se vende por 0).

### Arreglado
- El texto de reserva de los NPC decía «pensativo» también de Tessa o Mira.

## [0.6.2] - 2026-10-13

### Añadido
- **Poción de maná** (alquimia rango 1: 2 hojas de luna + 1 frasco de agua; también la vende Mira): devuelve un uso del conjuro más gastado. Solo para clases que lanzan conjuros (sacerdote, mago, druida, bardo, brujo). Sin conjuro gastado no se gasta.
- **Tónico del reposo** (alquimia rango 3: 2 musgos del reposo + 1 hoja de luna + 1 frasco): un descanso corto embotellado. Recupera el 20 % de los PV y un uso de una habilidad gastada; enfriamiento de 4 horas. No quita «herido» ni supera su techo, y si no hace falta no se gasta.
- Efectos tipados en los objetos (`effects`: `restore_hp`, `restore_spell_charge`, `short_rest`), validados al arrancar. El antiguo `heal` sigue funcionando (fuera de combate cuenta como `restore_hp`).

### Cambiado
- El botón de la posada se llama «Descanso largo».
- Cualquier consumible con efectos tiene botón «Usar» en el inventario.

## [0.6.1] - 2026-10-13

### Añadido
- **Oficios**: herrería, alquimia, carpintería, peletería, cocina y joyería. Cada personaje tiene **dos activos**.
  - Se aprenden en el nuevo **Barrio de Oficios** (junto al mercado), gratis mientras haya plaza libre. Cambiar uno cuesta 25 de oro y su experiencia no se pierde.
  - Rango 0–5 con la misma curva que las maestrías; una receta 2 rangos por debajo del tuyo da la mitad de XP.
- **Estaciones**: yunque, mesa alquímica, banco de carpintero, curtiembre y banco de joyero en el Barrio de Oficios; fogón de cocina en La Corona Rota.
- **12 recetas**: lingote y espada de hierro, poción de curación, tablones y bastón de roble, cuero curtido (de jabalí o de lobo) y cuero reforzado (CA 12), estofado del cazador y ración del pescador (curan fuera de combate), anillo de cobre y anillo con gema.
- **«🔨 Fabricar»** en los lugares con estación: las recetas de tus oficios con lo que tienes y lo que falta, y un botón por cada una que puedes hacer. Fabricar comprueba todo antes de gastar: o se gastan todos los ingredientes o ninguno. Lo fabricado guarda quién lo hizo.
- **`/professions`** (también en el menú de comandos): tus oficios y las seis maestrías con rango y XP; en el Barrio de Oficios, botones para aprender o cambiar.
- Mira vende frascos de agua para la alquimia.
- `/sheet` muestra «🛠️ Oficios 1/2».

### Cambiado
- `inventory.add_item` acepta `crafted_by`.
- `content/professions.yaml` y `content/recipes.yaml`, validados al arrancar; `Location.stations` y `Location.guild`.

## [0.6.0] - 2026-10-13

### Añadido
- **Actividades de campo con espera real** (diseño en `planning/profesiones.md`):
  - ⛏️ **Trabajar 5 min** (minar, talar, recolectar hierbas, pescar): 2–3 materiales y 10 XP de maestría, sin riesgo.
  - 🏕️ **Expedición larga 15 min**: 8–10 materiales y 25–30 XP, pero al recoger puede haber emboscada (0–25 % según el lugar). Victoria: te lo llevas todo; huida: la mitad; derrota: nada.
  - 🐾 **Rastrear 5 min** donde hay caza: 75 % encuentras presa (combate normal, +18 XP de rastreo y trofeos) y 25 % solo rastros (+10 XP). Si hay un jefe de misión pendiente, el rastreo lo encuentra. «Cazar» sigue siendo inmediato.
  - Mientras dura, el personaje está ocupado: no puede viajar, cazar, investigar, descansar ni hacer acciones de misión. La escena muestra el tiempo que falta y los botones «Recoger», «Actualizar» y «Abandonar». Un aviso ⏰ llega cuando termina.
  - El temporizador vive en la base de datos: un reinicio del bot no pierde nada. El resultado se tira una vez, con la semilla de la actividad, y se paga una sola vez.
- **6 maestrías de campo** (minería, tala, herboristería, desuello, pesca, rastreo), rango 0–5 con XP acumulada 0/80/240/500/900/1500. Cada rango da un 4 % de unidad extra (tope del 20 %, sin XP) y abre recursos mejores (cobre a rango 1, gemas y musgo del reposo a rango 3). Salen en `/sheet`.
- **Desuello automático** al vencer a jabalíes, lobos y al Viejo Colmillo si llevas cuchillo de desollar: cuero, pieles y carne, y XP de desuello.
- **Lugares nuevos**: Mina del Paso Viejo y Ribera de Silverbrook (desde el Camino del Viejo Rey), Arboleda Antigua y Claro de la Raíz Roja (desde el Bosque de los Susurros). El Bosque de los Susurros también tiene hierbas.
- **Rata gigante** en el bestiario (Mina del Paso Viejo).
- 14 materiales (mena de hierro y cobre, carbón, gema en bruto, roble, fresno, fibra, raíz de sangre, hoja de luna, musgo del reposo, piel de lobo, cuero de jabalí, carne, pescado y trucha de escamas de plata) y 5 herramientas que vende Tessa (pico, hacha, hoz, cuchillo de desollar, caña).
- **Crónicas de expedición** (el «presupuesto de misiones»): al terminar cada actividad llega una crónica personal con el nombre, la clase y el linaje del héroe y lo que pasó.
  - La escribe **Gemini 3.1 Flash-Lite** (`GEMINI_MODEL_CHRONICLE`), con un presupuesto de **15 al día por jugador** (`AI_USER_DAILY_CHRONICLES`). También cuenta para el límite diario de IA.
  - Después, o si la IA falla, sale un texto genérico de `content/chronicles.yaml` (3 por desenlace, en español e inglés). La crónica se guarda con la actividad y nunca decide el botín.
  - `/sheet` muestra «📜 Crónicas de hoy: X/15».
- `planning/profesiones.md`: decisiones de profesiones y recolección, y lo que queda para 0.6.1 (oficios y recetas) y 0.6.2 (pociones de maná y reposo).

### Cambiado
- Nuevo estado `busy` del personaje; `characters.ensure_free` sustituye a las comprobaciones de «en combate» en viajar, cazar, investigar, descansar, pruebas de habilidad y acciones de misión.
- El cliente de Gemini tiene un tercer tier, `chronicle`, que no cae al modelo rápido.
- Migración `0006`: tabla `world_activities` (una actividad abierta por personaje, con índice único parcial) y columnas `masteries`, `professions` y `cooldowns` en `characters`.

### Arreglado
- `load_content` usaba `world["start"]` en vez de `world.start` cuando ningún lugar tenía `respawn`.

## [0.5.11] - 2026-10-12

### Cambiado
- `README.md` ya no lleva número de versión (estaba congelado en v0.5.1): describe solo la idea del proyecto y remite a `CHANGELOG.md` para los cambios.

## [0.5.10] - 2026-10-12

### Cambiado
- Los testers editan y empujan su `TODO-<nombre>.md` directamente en `main`: el ruleset de `main` deja pasar a quien tiene permiso de escritura. Antes lo hacían en su rama y una GitHub Action copiaba el archivo.
- `README.md`, `CLAUDE.md` y `.github/CODEOWNERS` describen el flujo nuevo.

### Eliminado
- `.github/workflows/todo-sync.yml` y, con él, la necesidad de la deploy key `TODO_SYNC_KEY`.

## [0.5.9] - 2026-10-12

### Añadido
- **Informe de batalla**: botón «📜 Informe» en el panel al acabar un combate y comando `/report` (la última batalla terminada).
  - Resumen: resultado y rondas; 🗡️ daño hecho, aciertos y 💥 críticos; 🩸 daño recibido y cuántas veces te acertaron; 💚 curación; 💀 enemigos derrotados; recompensas (XP, oro, botín, subidas de nivel) o la penalización por derrota.
  - Una página por ronda con cada tirada, en el mismo formato que el panel. Botones ◀ ▶ y «Resumen» que editan el mismo mensaje.
- `/report` en el menú de comandos de Telegram y en `/help`.

### Cambiado
- `combat_actions` guarda también la apertura del combate (`actor="start"`: iniciativa y turnos enemigos antes del primero del jugador) y el final (`actor="end"`: recompensas o penalización). Sin migración. Las batallas anteriores salen sin apertura ni recompensas.
- Nuevo `combat_service.battle_report()` (solo lectura) con `battle_stats()`.

## [0.5.8] - 2026-10-12

### Cambiado
- **Panel de combate más bonito y fácil de leer**:
  - Cada combatiente: ❤️ PV, barra de vida y 🛡️ CA.
  - Cada acción es un bloque: la línea del ataque y, sangradas debajo (└), sus consecuencias: 🩸 daño con los PV que le quedan al objetivo, 💀 cae, salvaciones, estados.
  - 🗡️ acierto, 💥 **crítico** en negrita (ahora también muestra la CA), 💨 fallo. La tirada se lee como «🎲 14 +5 = 19 vs 🛡️ 13 ✅».
  - Separador «── Ronda N ──» entre rondas y líneas ━━━ entre combatientes, registro y botones. Se ven las 6 últimas acciones.
  - Iconos en todas las líneas del registro: ⏱️ iniciativa, 💚 curación, 🧪 poción, 🌀 estado, 💤 dormido, 🏃 huir, 🥷 esconderse, 🪝 objeto del escenario…
- Los golpes ya no se repiten en el mensaje de viñetas (al empezar un combate o con una acción escrita): solo salen en el panel, que llega justo después.
- Motor: nueva entrada `combat.round` al empezar cada ronda (también la 1). El daño guarda `hp` y `max_hp` del objetivo.

## [0.5.7] - 2026-10-12

### Añadido
- **`/classes` y `/class_<clase>`** (por ejemplo `/class_paladin`) para ver cada clase:
  - Dado de golpe, atributo principal, atributo de magia, competencias y equipo inicial.
  - Habilidades por nivel con icono, tipo (pasiva, acción, acción adicional), usos por descanso y descripción.
  - Especializaciones de nivel 5.
  - Con tu propia clase, ✅ en lo desbloqueado y 🔒 en lo que falta, y botón a la ficha completa.
- Los `/class_<clase>` que salen en un mensaje se pueden tocar. Los enlazan la tarjeta de subida de nivel y `/sheet`. La lista tiene un botón por clase y funciona sin personaje.
- `/classes` en el menú de comandos de Telegram y en `/help`.

### Cambiado
- Los textos de la tarjeta de nivel pasan a su propio bloque `level_card.*` (son plantillas de vista con HTML, no eventos).

## [0.5.6] - 2026-10-12

### Cambiado
- **La subida de nivel llega en un mensaje propio**, después del de XP, oro y botín, en lugar de mezclarse con ellos. Una tarjeta por nivel ganado:
  - ❤️ PV máximos antes → después (+lo ganado).
  - 💪 Mejora de atributo (nivel 4).
  - Cada habilidad nueva con su icono, tipo (pasiva, acción, acción adicional y usos por descanso) y su descripción.
  - Enlace `/class_<clase>` para ver la clase entera.
- Los eventos `progress.level_up` y `progress.new_ability` llevan la clase, la clave de la habilidad y los PV máximos anteriores.
- Nuevo helper `send_outcome` en los handlers: mensaje de viñetas y después las tarjetas de nivel. Lo usan las acciones con botón, hablar con NPC, el texto libre y el final del combate.
- `TODO.md` ordenado: lo hecho pasa a «Hecho», las notas sueltas van a su sección, las pociones se dejan para la 0.6.0 con la alquimia y moverse por `/map` para más adelante.
- Roadmap: la alquimia y las pociones pasan a la 0.6.0, junto a las especializaciones.

## [0.5.5] - 2026-10-12

### Añadido
- **`oathforge tgtest`**: una cuenta de Telegram de prueba juega con el bot de verdad (Telethon), para probar cambios de punta a punta.
  - `login <teléfono>` y después `login <teléfono> <código>` (con `--password` si tiene verificación en dos pasos).
  - `send "<texto>"` escribe al bot e imprime lo que responde, incluidos los mensajes editados, los botones y el dado. `press "<botón>"` pulsa un botón del último mensaje que lo tenga. `show -n N` muestra el historial.
  - Configuración en `.env`: `TG_TEST_API_ID`, `TG_TEST_API_HASH` (de https://my.telegram.org) y `TG_TEST_BOT`. La sesión se guarda en `.telegram/`, que está en `.gitignore`.
  - `telethon` pasa a las dependencias de desarrollo.

## [0.5.4] - 2026-10-12

### Añadido
- **Simulador de batallas** (`python -m oathforge.tools.simulate` u `oathforge simulate`): cientos de combates clase × enemigo × nivel con el motor real, sin base de datos ni IA.
  - El héroe se construye como al crearlo (array de la clase, linaje, trasfondo y equipo inicial) y al subir de nivel (PV, usos, +2 al atributo principal a nivel 4).
  - Política fija del jugador: cura con la acción adicional por debajo del 50 % de vida; usa bendiciones, maldiciones y ocultarse; gasta primero las habilidades con usos limitados; una habilidad ilimitada solo si pega al menos como el arma; Oleada de Acción si la tiene. `--no-abilities` ataca solo con armas.
  - Métricas por fila: % de victorias, rondas, % de vida restante, daño por ronda, vida perdida por ronda y % de combates que llegan al tope de 50 rondas.
  - Opciones: `--n`, `--level 1-5`, `--classes`, `--monsters` (grupos con `+`), `--lineage`, `--background`, `--seed`. Es reproducible (`Random(seed + i)`) y guarda JSON y CSV en `artifacts/simulations/`.

### Cambiado
- `characters.combatant_from(char, gear, skills)`: la parte pura de `build_combatant`, que la usa el simulador.

## [0.5.3] - 2026-10-12

### Añadido
- **Test estadístico de los dados** (`tests/engine/test_dice_fairness.py`): chi-cuadrado sobre 200 000 tiradas del d20 (uniforme), de la ventaja y la desventaja (máximo y mínimo de dos d20), de 1d6 y de 2d6; frecuencia de 20 y 1 naturales (≈ 5 %) y medias (10,5 / 13,825 / 7,175). Usa semillas fijas, así que no falla por azar, y una prueba con el RNG real del bot.

## [0.5.2] - 2026-10-12

### Arreglado
- **Ya no se puede repetir la misma tirada hasta que salga.** Una prueba de habilidad libre (escrita) se puede intentar una vez por habilidad y lugar al día de juego (4 h reales). Se desbloquea al día siguiente o al subir de nivel. Si se repite, sale «Ya intentaste {habilidad} aquí hoy».
  - Investigar: cada secreto que se falla queda bloqueado hasta el día siguiente; si todos los pendientes están bloqueados, sale «Ya has registrado este lugar hoy».
  - Con las tiradas manuales activadas, una tirada bloqueada no pide el dado.
  - Prueba de habilidad e interacción con el entorno comparten bloqueo (misma habilidad, mismo lugar).
  - Nueva columna `characters.checks_tried` (migración `0005`); guarda solo los intentos del día actual.

## [0.5.1] - 2026-10-11

### Añadido
- **`/roll` y tiradas manuales**, opcionales por jugador (`users.settings.manual_rolls`).
  - Sin tirada pendiente, `/roll` las activa o desactiva.
  - Con ellas activadas, la prueba de habilidad espera a que el jugador haga `/roll` o pulse «🎲 Tirar el dado». Afecta a investigar, a las acciones de misión con prueba y a las acciones escritas que piden tirada (prueba de habilidad, interacción con el entorno, inspeccionar o acción de misión).
  - Al tirar, sale el dado animado de Telegram y después el resultado del motor: d20 + bonificador contra la CD. El dado de Telegram solo va de 1 a 6, así que es decorativo.
  - El combate no espera a `/roll`.
  - Si el jugador se ha movido antes de tirar, la tirada se anula.
- **Retratos de hombre y de mujer** para las 8 clases: Bardo, Maga y Mago, Druida y Druidesa, Guerrera, Pícara, Sacerdotisa y Paladina. La barda aún no tiene retrato y usa el del bardo. Se quitó la franja inferior con texto falso de la IA.

### Cambiado
- Los retratos neutros de Paladín, Sacerdote, Pícaro y Guerrero eran de hombre: pasan a `portrait.male.jpg`.
- Las pruebas de habilidad se muestran con 🎲 delante.
- Las acciones escritas se separan en interpretar (`handle_free_text`) y resolver (`execute_free_text`), para poder resolverlas después de `/roll`.

## [0.5.0] - 2026-10-11

### Añadido
- **Sistema de misiones**: cadena automática de 6 misiones que lleva a nivel 5 (Bienvenido a Crownreach, Colmillos en el prado, Alas al anochecer, El relicario sellado, Huesos inquietos y El Viejo Colmillo). Al completar una se abre la siguiente (`after` o `unlock_flag`). Los objetivos (matar N, hablar con, ir a) cuentan solos y dan su recompensa. El avance se guarda en `quest_progress.counters` (migración `0004`) y los personajes antiguos reciben las misiones nuevas sin perder su progreso.
- **Diario renovado**: muestra las misiones en curso con su avance y tiene tres secciones. En «📜 Misiones» se toca cada misión para ver quién la da, el resumen, los objetivos (`2/3`), una pista de dónde ir y la recompensa. Las otras dos son «📖 Bestiario» y «🗣️ Rumores». Nuevo comando `/quests`.
- **Prado de los Colmillos**, zona de caza a 20 minutos de la plaza y sin peligro en el camino. Con el botón «🏹 Cazar» salen **jabalíes de día** y **murciélagos de noche** (`night_encounters`, también en las emboscadas). El jefe **Viejo Colmillo** aparece con la misión 6. Botín vendible: colmillos de jabalí y alas de murciélago.
- **Bestiario** (`characters.bestiary`): cuenta las criaturas vistas y derrotadas. Su ficha se desbloquea por partes: al verla, descripción, historia y hábitat; a la primera derrota, PV, CA y ataques; a la tercera, puntos débiles, XP y botín. Los monstruos tienen `lore`, `habitat` y `active` (día o noche).
- **Compra de atributos por puntos** al crear el personaje: todos empiezan en 8 y hay 27 puntos (14→15 cuesta 2), con botones ➖/➕. «⭐ Recomendado» carga el array de la clase y «🔄 Reiniciar» vuelve a empezar. Cada atributo explica para qué sirve (`effect` en `content/abilities.yaml`) y se ve la vida resultante.
- Emojis en XP (✨), oro (🪙), subidas de nivel (🎉) y habilidades nuevas (🌟).

### Cambiado
- **Curva de XP comprimida**: los niveles 2–5 piden 200 / 500 / 1.000 / 1.800 XP (antes 300 / 900 / 2.700 / 6.500).
- **La Cripta Hundida es más fácil**:
  - esqueleto: 11 PV, +3, 1d6+1;
  - Guardián: 40 PV, +4, 1d8+2, miedo al 25 %;
  - descanso gratis en el osario antes del santuario.
- «El relicario sellado» empieza bloqueado hasta completar «Alas al anochecer». Sus finales dan 300 XP y abren la misión del Viejo Colmillo.
- **Botones de combate a prueba de doble clic**: cada botón lleva `<encounter.version>.<turn_index>.<nonce>`. Un botón de un panel viejo o de otro turno ya no actúa: vuelve a pintar el panel.

### Arreglado
- `TimedOut` al subir retratos: el bot tiene ahora timeouts de 30 s, y 60 s para subir fotos. Si una imagen falla por red, se registra un aviso y se sigue con la vista sin mostrar el error genérico.
- Reintentos inútiles a Gemini con la cuota diaria agotada: ante un 429 se respeta el `retryDelay` de Google (si la cuota es diaria, se salta ese modelo hasta que vuelva, como máximo 24 h). Se deja de llamar y de avisar cada 2 minutos.

## [0.4.4] - 2026-10-11

### Añadido
- **Brujo** (d8, CAR, retaguardia): Estallido Sobrenatural (1d10 de fuerza, ilimitado), Maleficio (acción adicional: maldice a un enemigo 3 turnos sin salvación y cada golpe que recibe suma 1d6 necrótico), Armadura de Sombras (2d4 + CAR PV temporales), Susurros del Vacío (salvación de SAB de toda una fila: 2d6 psíquico, la mitad si salva, miedo a quien falla) y Estallido Agónico (+CAR al daño de conjuros). Especializaciones previstas: Pactista Infernal, Nigromante, Filo Maldito y Vacío.
- Habilidades de maldición (`kind: curse`): ponen un estado a un enemigo elegido, sin tirada de salvación; estado `hexed` (🕯️).
- **Hombre o mujer** al crear el personaje (paso nuevo tras el nombre): se guarda en `characters.gender` (migración `0003`), sale en el resumen de creación y en la ficha, y la IA lo recibe para narrar con el género correcto.
- Retratos por sexo: `portrait.male.jpg` / `portrait.female.jpg` en `content/classes/<clase>/images/`; `/sheet` envía el del personaje, o el neutro (`portrait.jpg`) si no hay. Retratos de Brujo y Bruja (768 × 1024).

### Arreglado
- `/sheet` no aparecía en el menú de comandos de Telegram (`MENU_COMMANDS` en `oathforge/main.py`).

## [0.4.3] - 2026-10-11

### Añadido
- **Comandos de consola** `oathforge` (`oathforge/cli.py`, también `python -m oathforge`): `oathforge help` lista los comandos con una descripción breve, `oathforge bot` arranca el bot y `oathforge reset-players [--yes]` borra los jugadores.

### Cambiado
- `scripts/reset_players.py` pasa a ser `oathforge reset-players`.

## [0.4.2] - 2026-10-11

### Añadido
- **Cambios de estado en `artifacts/`**: cada cambio confirmado en la BD (PV, oro, XP, nivel, ubicación, flags, recursos, objetos, habilidades, misiones, relaciones y memorias de PNJ, reputación, rumores y acciones de botón del registro de auditoría) se guarda como diff en `events/` (`kind: state`) y como bloque «⚙️ estado» en la conversación del jugador, venga del camino que venga. Lo revertido no se registra.
- `artifacts/logs/<día>.log`: avisos y errores de cualquier logger (reintentos y JSON inválido de Gemini, presupuesto de IA…), que antes solo salían por consola.
- Evento `boot` al arrancar el bot con versión, commit, modelos y base de datos.
- Las conversaciones registran también stickers, fotos, voz y demás mensajes que no son texto.
- `scripts/reset_players.py`: borra todos los jugadores y sus datos para empezar una ronda de pruebas limpia (sin `--yes` solo muestra qué borraría); conserva `media_files`.

## [0.4.1] - 2026-10-11

### Añadido
- **Retratos de clase** (768 × 1024) para Paladín, Guerrero, Pícaro y Sacerdote en `content/classes/<clase>/images/`, con créditos en `media.yaml`; el catálogo de medios los carga (`class_images`) y rechaza carpetas de clases que no existen.
- **Ficha completa** con `/sheet` y el botón «📜 Ficha completa»: envía el retrato de la clase (si lo hay, con caché de `file_id`) y debajo la ficha con descripción y especialización de la clase, dado de golpe, ataques con bonificador al impacto y daño, conjuros (característica, ataque y CD), percepción pasiva, inmunidades, todas las competencias (● competente, ○ practicada, · sin entrenar), habilidades de clase, reputación, rasgo del linaje y trasfondo, y el uso de IA del día.

### Cambiado
- `/hero` y el botón «🦸 Héroe» muestran ahora un **resumen** (PV, XP, CA, atributos, equipo y habilidades desbloqueadas) con un botón a la ficha completa; `/sheet` deja de ser un alias de `/hero`.
- `services/characters.py`: `spell_stats` e `immunities` calculan la CD de conjuro y las inmunidades en un solo sitio (combate y ficha).
- Ayuda y descripciones de comandos mencionan `/sheet`.

## [0.4.0] - 2026-10-11

### Añadido
- **Mago** (d6, INT): Rayo de Fuego, Armadura de Mago (+3 CA sin armadura), Dormir, Bola de Fuego (toda una fila, mitad si salva), Proyectil Mágico (nunca falla).
- **Druida** (d8, SAB): Látigo de Espinas, Curar Heridas, Enredar (toda una fila), Forma Salvaje (PV temporales), Furia Elemental (+SAB al daño de conjuros).
- **Bardo** (d8, CAR): Burla Cruel, Inspiración Bárdica (+1d6 al próximo ataque), Canción Sanadora, Patrón Hipnótico (toda una fila), Palabras Cortantes.
- **Tiradas de salvación** (DES y SAB) contra la CD de conjuro (8 + competencia + característica); habilidades `save` contra un objetivo o contra toda su fila.
- Estados `asleep` (pierde el turno, despierta al recibir daño), `restrained` (ventaja contra él, desventaja en sus ataques), `inspired` y `wild_shape`.
- **PV temporales**: absorben el daño primero y se ven en el panel de combate como `(+N)`.
- Tipos de daño `force` (fuerza) y `psychic` (psíquico).
- Objetos: bastón y estoque (tienda de Tessa).

### Cambiado
- Los monstruos usan su modificador de SAB para las salvaciones.
- Las habilidades `save` piden objetivo a distancia como los conjuros.

## [0.3.0] - 2026-10-11

### Añadido
- **Mundo en carpetas**: `content/world/<continente>/<zona>/<lugar>/place.yaml`, con `world.yaml`, `continent.yaml` y `zone.yaml` (zona = ciudad, territorio salvaje o mazmorra). Primer continente: **Terra Coronata**, con Crownreach, Thornwood y la Cripta Hundida.
- **Catálogo de imágenes** por convención: cada carpeta puede tener `images/` (el sufijo `.night` marca la variante nocturna) y un `media.yaml` opcional con créditos y licencia (`oathforge/content/media.py`).
- **Caché de `file_id` de Telegram** por bot y checksum (tabla `media_files`, migración `0002`, `services/media.py`): cada imagen se sube una sola vez y se vuelve a subir sola si cambia el archivo.
- Botón **«🏙️ Ver ciudad»** en la plaza de Crownreach (lugar `hub`), solo si la ciudad tiene imágenes: envía la panorámica con su descripción de día o de noche y vuelve a mostrar la escena.
- Panorámica de Crownreach (1280 × 720).
- `tools/prepare_image.py` (Pillow, extra `dev`): recorta, escala y optimiza imágenes a la escala del juego.

### Cambiado
- `content/locations.yaml` se reparte en la nueva estructura; los ids de lugar no cambian.

## [0.2.2] - 2026-10-11

### Añadido
- **Hoja de héroe**: el botón «🦸 Héroe» y el nuevo comando `/hero` (`/sheet` sigue funcionando) muestran una ficha detallada con barras de PV y XP, atributos en tabla (★ en el principal de la clase), equipo con daño y CA, competencias con su bonificador, habilidades de clase con usos y las de niveles futuros bloqueadas, reputación con etiqueta (hostil, neutral, amistoso…) y rasgo del linaje. Botones directos a Inventario y Diario.
- La hoja muestra las llamadas al Dungeon Master usadas hoy y las que quedan.
- Aviso al jugador cuando agota su presupuesto diario de IA, en acciones libres y en conversaciones.

### Cambiado
- Límite de IA en la fase de testeo: **150 llamadas al día por jugador** (antes 200).

## [0.2.1] - 2026-10-11

### Añadido
- `planning/referencias/` con los documentos de diseño: el GDD *Aetherfall Chronicles* y la guía de recursos audiovisuales (PDF), más un índice que indica en qué archivo de planning se recoge cada capítulo y en qué difieren de lo ya decidido.
- `planning/audiovisual.md`: imágenes, música de taberna, voces de NPC, mapas, stickers, envío por Telegram, catálogo de activos y licencias.
- `planning/interfaz-telegram.md`: escenas, botones, comandos, estados de acción y sesiones.

### Cambiado
- Planning ampliado con ideas del GDD: 12 clases y talentos del Paladín (`clases.md`), tipos de acción, estados e IA enemiga (`combate.md`), proficiencias, equipo y juramentos (`progresion.md`), profesiones, contratos y libro mayor (`comercio.md`), regiones, eventos, misiones, facciones y rumores (`mundo-y-misiones.md`), espacios de Telegram, expediciones y PvP (`multijugador.md`), roles del DM, memoria y control de calidad (`ia-y-narracion.md`) y visión a largo plazo (`roadmap.md`).
- `TODO.md` reorganizado por temas con prioridades y enlaces a planning, con nuevas tareas sacadas de los PDF.

## [0.2.0] - 2026-10-11

### Añadido
- Clase **Guerrero** (d10, FUE, vanguardia): Segundo Aliento, Estilo Defensa, Oleada de Acción (N2), Crítico Mejorado 19–20 (N3), Ataque Extra (N5).
- Clase **Sacerdote** (d8, SAB, retaguardia, lanza con SAB): Llama Sagrada (ataque de conjuro a distancia, ilimitado), Palabra Sanadora, Expulsar No-muertos (N2), Bendición +2 a impactar (N3), Golpe Divino +1d8 radiante (N5).
- Tipos de daño y de criatura: los monstruos tienen `type` (humanoide, bestia, no-muerto), `resist` (½), `vulnerable` (×2) e `immune_damage`. El panel muestra «¡débil!», «resiste» o «inmune».
- Esqueletos vulnerables a contundente y radiante; el Guardián de la Cripta vulnerable a radiante y resistente a necrótico y frío; los no-muertos son inmunes al veneno.
- Nuevos tipos de habilidad en el motor: `spell`, `turn`, `buff`, `surge`; campos `heal_dice`/`heal_add`, `crit_range`, `bonus_damage`; estado `blessed`.
- Objetos: martillo de guerra, maza, hacha de mano (arrojadiza) y cota de escamas; a la venta en la tienda de Tessa.

### Cambiado
- El daño extra de otro tipo (Golpe Consagrado, Golpe Divino) se aplica por separado para que cuenten las resistencias y debilidades.
- Una tirada dentro del rango de crítico siempre impacta.
- Las habilidades ilimitadas ya no muestran «(None)» en el botón.

### Arreglado
- Un enemigo sin ataques ya no rompe el turno enemigo.
- `/help` (v0.1.1): error de sintaxis en el pie de versión que impedía arrancar el bot.

## [0.1.1] - 2026-10-11

### Añadido
- Versionado: `oathforge.__version__` es la única fuente (pyproject la lee); se muestra al arrancar el bot y al pie de `/help`.
- `CHANGELOG.md` y convención de commits `vX.Y.Z: resumen`.
- Carpeta `planning/` con los puntos de partida: clases, combate, comercio, progresión, mundo y misiones, multijugador, IA y roadmap.
- Registro de partidas en `artifacts/` (ignorado por git) para depurar y analizar: conversaciones jugador ↔ bot, eventos en JSONL, combates turno a turno (.md legible + .json), cada llamada a Gemini (prompt, respuesta, modelo, tokens, latencia) y errores. Se controla con `ARTIFACTS_ENABLED` y `ARTIFACTS_DIR`.

## [0.1.0] - 2026-10-10

### Añadido
- Vertical slice en solitario: creación de personaje (4 linajes, 4 trasfondos, Paladín y Pícaro con habilidades hasta nivel 5).
- Crownreach, el Camino del Viejo Rey, el Bosque de los Susurros y la Cripta Hundida (5 salas + jefe).
- Combate por turnos: iniciativa, acción/adicional/movimiento, filas, críticos, ataque furtivo, estados y objetos del escenario.
- Misión ramificada «El relicario sellado», NPC con memoria, reputación con facciones, tiendas con precios por reputación y rumores entre jugadores.
- Gemini como Dungeon Master: interpreta texto libre y narra; el motor decide. Presupuesto diario, plantillas de respaldo y fallback al modelo rápido.
- Español e inglés.
- Flujo de colaboración: ramas por persona y TODO de testers sincronizados a `main`.
