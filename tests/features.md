# Checklist de features

Lo que hay que probar **siempre** tras una feature grande, jugando de punta a punta con la cuenta de prueba (`oath tgtest send|press|show`). Cada feature grande nueva añade aquí sus casillas.

Cada pasada se hace con una clase distinta (la que menos se haya probado) y se anota el tiempo de cada misión del tutorial.

## Personaje
- [ ] `/start` sin personaje: elegir idioma, clase, linaje y trasfondo, nombre
- [ ] Trasfondo propio: ver la guía, aceptar uno compatible, adaptar un anacronismo, editar/aceptar la propuesta y comprobar que un botón viejo no actúa
- [ ] Ficha 🧝 Héroe: stats, PV, maná/recursos, habilidades de la clase
- [ ] Todo el texto sale en el idioma elegido (sin claves de i18n crudas)

## Teclado fijo y escena
- [ ] 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario (los jugadores viejos reciben el teclado nuevo)
- [ ] `/start` y `/look` enseñan la escena; en combate, el combate
- [ ] La escena no repite botones del teclado fijo
- [ ] La escena solo tiene Viajar, Investigar, Hablar, Comerciar, ⚒ Actividades (n) y lo de la misión
- [ ] ⚒ Actividades: cada actividad con duración y qué falta; sin pico, «🛒 Pico · ir a Mercado» lleva al mercado
- [ ] ⚒ Actividades mientras trabajas: el panel de la actividad; en combate: el combate
- [ ] 🛠️ Oficios desde Héroe y desde Actividades, con sus pestañas
- [ ] Investigar, cazar o abandonar: un solo mensaje con el resultado y los botones; el panel viejo se queda sin botones
- [ ] Un botón viejo o un doble toque: ventanita «Ese menú ya no vale» y el mensaje pasa a la vista actual, sin gastar nada
- [ ] Un rechazo («Necesitas un pico», sin oro): ventanita, sin mensaje nuevo
- [ ] Pulsar la misma vista dos veces no manda un mensaje repetido
- [ ] Comprar, equipar, aprender o fabricar: el resultado encima del mismo menú
- [ ] Una actividad que termina sola trae los botones del lugar en el mismo mensaje
- [ ] Investigar: «🎲 Percepción: 12 + 2 = 14 vs CD 12 · ✅ Éxito»
- [ ] «Llegas al Mercado», «a la Taberna», «por el Camino del Viejo Rey» (en inglés, «the Old Pass Mine»)
- [ ] Informe de un combate de una ronda: «1 ronda»
- [ ] `/sheet` explica ● ○ · y ★
- [ ] 🎒 Inventario: resumen con lo puesto y cuántos de cada tipo; pestañas con una línea por objeto e icono
- [ ] Equipar desde ⚔️ Equipo y usar desde 🧪 Consumibles vuelven a su pestaña; `/item_` de algo tuyo trae su botón
- [ ] Botín, recetas y tiendas con el icono de cada objeto

## Mapa y viaje (0.8.0)
- [ ] Mapa: dónde estás · 📜 objetivo · esta zona · otras zonas · 🌫️ Sin explorar
- [ ] Viaje directo a un lugar conocido, también entre zonas, en un toque
- [ ] El camino no atraviesa salas con combate fijo pendiente
- [ ] 📜 al objetivo lleva al siguiente paso de cada misión activa sin revelar sitios desconocidos
- [ ] 📜 respeta la hora: de día no manda a cazar criaturas que solo salen de noche
- [ ] 📜 aparece también en misiones con decisiones (rumor de Bram, agua de la cantera)
- [ ] Tramos ⚠️: emboscada con una sola tirada; «▶️ Seguir hacia…» termina el viaje
- [ ] Al llegar sin más que contar, el mapa se convierte en la escena («Llegas a X…»)
- [ ] Solo distancias en yardas, sin tiempos
- [ ] `/map` estando ocupado avisa en vez de enseñar caminos

## Combate
- [ ] Ataque básico y habilidades de la clase (maná/recursos se gastan bien)
- [ ] Informe de batalla: rondas correctas, «🏆 Victoria» una sola vez
- [ ] Botín y crónica en el mismo mensaje
- [ ] Huida
- [ ] Derrota → heridas graves; Ysolde las cura gratis (beta)
- [ ] El jefe del tutorial (Viejo Colmillo) es ganable por la clase más frágil
- [ ] Aviso de poca vida al cazar/rastrear/expedición

## Actividades
- [ ] Cazar y rastrear (texto propio del lugar); las misiones de caza cuentan de día y de noche
- [ ] Beta: en el tutorial las actividades terminan al momento; el descanso largo es instantáneo
- [ ] Recolectar hierbas, minar
- [ ] Descanso largo en la taberna
- [ ] Fabricar (estofado, poción de maná con ala de murciélago)
- [ ] El atajo del tutorial al desollar no deja sin la carne que pide la misión siguiente
- [ ] Poción de maná: con varios conjuros gastados, deja elegir cuál recupera
- [ ] Beta: pociones de vida y de maná a 1 de oro

## Comercio e inventario
- [ ] Tienda por categorías; tras comprar sigues en la categoría
- [ ] Fichas `/item_…`
- [ ] Inventario: equipado primero, iconos de hueco en equipar/quitar

## NPCs y misiones
- [ ] Aceptar y entregar misiones; al cumplir un objetivo, aviso del siguiente
- [ ] Saludo de regreso (`greeting_return`) tras terminar una misión del NPC
- [ ] Sin IA: el NPC recuerda la pista de la misión activa
- [ ] Las 10 misiones del tutorial se completan sin salir del camino principal; anotar minutos de cada una

## Diario y reglas
- [ ] 📖 Diario: misiones activas/hechas, 📈 Estadísticas
- [ ] `/rulebook` (Viajar y explorar, Actividades)

## Herramientas
- [ ] `oath tutorial-stats` refleja la partida

## 0.9 — Logros e identidad

Validación 2026-10-17: suite automatizada con PostgreSQL y recorrido real con la cuenta de prueba. «Automático» identifica los casos que no se han forzado en la partida real.

- [x] /achievements: portada, pendientes y obtenidos en español e inglés (Telegram); categorías y paginación (automático).
- [x] Condición y progreso (Telegram); revelar una pista sin conceder el logro (automático).
- [x] Seguir tres objetivos y sustituir uno (automático); seguimiento en el diario (Telegram).
- [x] Equipar/quitar título y límite de destacados (automático); destacado en /hero (Telegram).
- [x] Actividad automática con un único anuncio agrupado (automático); anuncio retroactivo agrupado (Telegram).
- [x] 1.000 repeticiones, concurrencia y rollback sin duplicados (automático, PostgreSQL).
- [x] Reinicio conserva destacados (Telegram); recuperación de anuncio tras fallo y vencimiento de lease (automático).
- [x] Backfill en simulación y aplicado en la base local; segunda ejecución sin nuevas concesiones.
- [x] Personaje nuevo: fabricación, victoria y decisiones concedidas por el motor sin IA (automático).

La cuenta de prueba conserva su idioma original y quedó sin los destacados ni objetivos temporales usados en el recorrido.

## 0.10.7 — El Libro del Héroe (F03)
- [x] 📖 Diario por pestañas: la activa entre «• … •» y el mismo mensaje se edita (Telegram, ES y EN).
- [x] 📖 Ahora: objetivo de misión con botón de ruta; sin misiones, botón hacia quien las da (Telegram).
- [ ] 📖 Ahora con una actividad en marcha y con un viaje interrumpido (Telegram).
- [x] 🕯️ Crónica: entradas por día, «Antes de este libro» para lo retroactivo (Telegram, ES y EN); paginación de 8 (automático).
- [x] Una visita o fabricación repetida no añade entrada pero sí cuenta (automático); rango 0 no es entrada (automático).
- [x] 📜 Misiones incluye las terminadas; el botón «Registro» de un menú viejo abre la Crónica (automático).
- [x] 📈 Estadísticas: contadores de la crónica junto a los antiguos, cada bloque con su «desde» (Telegram).
- [x] Abrir el diario no genera llamadas a Gemini (`artifacts/ai/`).
- [x] `/rulebook`: descanso y emboscada con las cifras del motor y la frase de beta (Telegram); cada marcador tiene valor (automático).
- [x] Migración 0010 en una base de prueba: los recibos se conservan como `legacy`, y `downgrade` los devuelve.
- [ ] Un logro nuevo durante la partida aparece en la Crónica como «🏆 Logro: …» (Telegram).

## 0.10.8 — Logros auditados (F04)
- [x] Toda la interfaz dice «Logros» y «puntos de logro» (Telegram, ES).
- [x] El título sale junto al nombre en `/sheet` y en la cabecera del Libro (render con un personaje con título).
- [x] El título llega al narrador y a los PNJ como dato (automático).
- [x] Una expedición o rastreo perdido no cuenta como actividad (automático).
- [x] Destacar o seguir con la clave «-» se rechaza (automático).
- [ ] «Héroe de Crownreach» al llegar a nivel 5, con su título (Telegram).
- [ ] «Oficial del gremio» al alcanzar rango 2 en un oficio (Telegram).
- [ ] Los dos ocultos no aparecen en Pendientes y sí al conseguirlos (Telegram).

## 0.10.9–0.10.18 — Oficios, maestrías y aficiones (F15)

Recorrido completo, con la cuenta de prueba, en ES y EN. Lo marcado (automático) ya lo cubre la suite.

### El mundo nuevo
- [ ] La plaza enseña por dónde se va al Gremio de Aventureros, y Vale alista allí (Telegram).
- [ ] El mapa de la ciudad cabe en una pantalla: los puestos salen bajo «Barrio de Oficios» con «🛠️ Puestos (8)» (Telegram).
- [x] Cada oficio se aprende solo en su puesto; en otro, dice a cuál ir (automático).
- [ ] Tessa está de día en su forja y de noche en la taberna, y sigue vendiendo herramientas (Telegram).
- [ ] Los ocho maestros responden al hablarles, con y sin IA (Telegram, ES y EN).

### Refinar y fabricar
- [x] Fundir, aserrar, curtir y limpiar fibra en el Gremio sin tener oficio, con XP de la maestría (automático).
- [x] El lote comprueba todos los materiales antes de gastar uno (automático).
- [ ] 🔨 Fabricar: ingredientes con tengo/necesito y botón solo con todo completo (Telegram).
- [ ] `/recipes` con sus cinco pestañas, `/r_<receta>` con el origen de lo que falta y `/craft_<receta> 5` (Telegram, ES y EN).
- [ ] Reenviar el mismo `/craft_` dos veces no fabrica dos veces (Telegram).

### Sastrería, técnicas y planos
- [x] Fibra → fibra limpia → hilo → tela → jubón; el sedal a rango 2 (automático).
- [ ] Al subir de rango sale «📘 Técnica aprendida: …» con sus recetas (Telegram).
- [x] Un plano se gasta una vez, no se gasta si ya la conoces y no se olvida al cambiar de oficio (automático).
- [ ] El plano del Viejo Colmillo cae al derrotarlo y su ficha trae «Aprender la receta» (Telegram).

### La habitación
- [ ] La misión «Un cuarto propio» de punta a punta: talar, aserrar, cofre, tela y cama (Telegram, ES y EN).
- [x] Las recetas de iniciación solo existen durante la misión y no se hacen por lotes (automático).
- [x] Dormir en tu cama no cuesta oro y mantiene las reglas del descanso largo (automático).
- [x] El cofre mueve la misma fila: nada se duplica, nada se pierde, y lo guardado no se gasta ni se vende (automático).
- [ ] `/room`, `/stash_<objeto> 5` y `/take_<objeto> 5` (Telegram).
- [ ] Pedir la tela dos veces: el botón no está mientras la llevas o ya tienes la cama (Telegram).
- [ ] Migración 0012 en una base de prueba, con su `downgrade`.

### Ramas y herramientas
- [x] Rango 1 rechazado, rango 2 permitido; la primera rama gratis y el cambio cobrado una vez (automático).
- [x] La rama pausada no suma y no se pierde (automático).
- [x] Rama y herramienta quedan fijadas al empezar; con un trabajo en marcha no se cambian (automático).
- [ ] 🌿 Especializaciones y 🧰 Herramientas desde Oficios → Maestrías (Telegram, ES y EN).
- [x] Una caña rápida convierte 300 s en 270 s; 10 % × 1,05 = 10,5 %; el extra se tira una vez (automático).
- [ ] El reglamento explica el porcentaje relativo frente a los puntos (Telegram, ES y EN).

### T1 y economía
- [x] Ningún ingrediente sin origen y ninguna receta que pida lo que produce (automático).
- [x] Comprar los componentes a un maestro y vender lo fabricado nunca da beneficio (automático).
- [x] El equipo T1 se fabrica a nivel bajo y no se equipa ni se bebe sin nivel 10 (automático).
- [ ] Un personaje de rango 4 encuentra hierro profundo, corazón de roble y fibra sedosa (Telegram o simulación).

### Concurrencia (PostgreSQL, `TEST_DATABASE_URL`)
- [ ] Doble toque en «Fabricar» con los materiales justos: una sola pieza.
- [ ] Depositar y retirar a la vez el mismo objeto: ni duplicado ni perdido.
- [ ] Dos lecturas del mismo plano: se gasta uno solo.

## 0.10-I · Progresión híbrida y entrega al PNJ (B02, v0.10.24)

### Nivel por XP e hito
- [x] Con la XP del nivel 12 y sin el hito del Recaudador, el héroe se queda en 9 y conserva toda su XP (automático).
- [x] El hito solo no da niveles; al llegar la XP sube sin repetir al jefe (automático).
- [x] Un hito se concede una vez y uno inventado no se concede nunca (automático).
- [x] La segunda puerta deja en 10 hasta el Ciervo (automático).
- [x] La puerta sobrevive a una transacción nueva (automático).
- [x] La ficha dice qué falta: ✨ la barra llena y 🔒 el hito que cierra el paso (Telegram, ES y EN).

### Entregar la misión a quien la dio
- [x] Abatir al Viejo Colmillo no paga: la misión queda «lista» y Bram debe la recompensa (automático).
- [x] Sin el dador delante no se entrega (automático).
- [x] Entregar dos veces paga una (automático y Telegram: el botón desaparece).
- [x] Una misión sin terminar no se entrega (automático).
- [x] Premio, hito y nivel en la misma transacción (automático).
- [x] «📜 Entregar: …» en la escena y en el panel del PNJ (Telegram, ES y EN).
- [x] El diario y `/quests` la muestran ✅ con el PNJ al que se le debe (Telegram).
- [ ] Doble toque simultáneo sobre «Entregar» con PostgreSQL: un solo pago.
- [ ] Migración 0013 en una base de prueba, con su `downgrade`.

## 0.10-I · La barra de clase (B03, v0.10.25)

### Pagar y recuperar
- [x] Un poder cuesta una vez, y sin barra suficiente se rechaza sin gastar nada ni el turno (automático).
- [x] El ataque básico es gratis y alimenta la barra; un Ataque Extra no la alimenta dos veces (automático).
- [x] La barra nunca pasa de su máximo ni baja de cero (automático).
- [x] Una clase que sigue con usos por descanso no cambia de comportamiento (automático).
- [x] La barra se rellena un poco al empezar tu turno y sobrevive a guardar y recargar el encuentro (automático).
- [x] Ganar devuelve su parte (solo el Maná de hoy); huir o entrar y salir no recarga nada (automático).
- [x] El descanso largo la llena; la poción de maná y el tónico del reposo devuelven su parte (automático).
- [x] Cuatro combates seguidos sin curación completa con Guerrero (Foco) y Hechicero (Maná) (automático).

### Enfriamientos y control
- [x] Un enfriamiento se cuenta en turnos de combate, bloquea mientras dura y se agota en tu propio turno (automático).
- [x] Un poder que no puedes pagar no se ofrece (automático).
- [x] El control duro no encadena a un jefe: dura un turno y el resto lo deja vulnerable, dicho en el registro (automático).
- [x] Un estado se refresca y nunca se acumula; un jefe sí sufre los estados blandos enteros (automático).

### Interfaz
- [x] 🔹 La barra en la cabecera del panel de combate y en `/sheet` (Telegram, ES y EN).
- [x] El botón del poder lleva su coste: «🌟 Second Wind (4)» (Telegram).
- [x] El registro dice «−4 Foco (0 restante)» con el nombre traducido, no la clave (Telegram, ES y EN).
- [ ] Un combate completo con Hechicero gastando Maná hasta quedarse en el Rayo de Fuego (Telegram).
- [ ] Migración 0014 en una base de prueba, con su `downgrade`.

## 0.10-I · El camino de clase (B04, v0.10.27)

### Rama, entrenamientos y modificadores
- [x] La rama se elige al 10, en el Gremio, una vez; con nivel bajo, lejos del Gremio, de otra clase o sin estar lista se rechaza sin escribir (automático).
- [x] Elegir rama cambia el catálogo en el motor, la ficha, el descanso y `/skill_<clave>`, y no recarga barra, usos ni vida (automático).
- [x] Entrenamiento del 5: PV, ataque, CD y barra cambian de verdad; los PV nuevos son reales y no curan el resto (automático).
- [x] Un entrenamiento no se toma dos veces, ni antes de su nivel, ni con una opción inventada (automático).
- [x] Saltar niveles encola los entrenamientos: del 4 al 13 de golpe no pierde el del 5 ni el del 12 (automático).
- [x] Un modificador afina una habilidad o concede otra; el de otro nivel o rama se rechaza; dos toques aplican uno (automático).
- [x] La segunda elección gratuita solo existe tras revisar la rama, es de un solo uso y conserva los entrenamientos (automático).
- [x] Dos modificadores a la vez dejan uno aplicado (PostgreSQL, automático).
- [x] `/path`: rama, elecciones pendientes, ficha de opciones y confirmación definitiva; el botón viejo ya no existe (Telegram, ES).
- [ ] `/path` en inglés y la tarjeta de subida del 5 con su aviso (Telegram, EN).
- [ ] Elegir una rama de verdad en el Gremio (pendiente de B07: ninguna rama está lista).

## 0.10-I · Compañeros, formas y dispositivos (B05, v0.10.28)

### Invocaciones y órdenes
- [x] Un aliado invocado espera al turno siguiente y luego actúa **una vez por turno**, nunca dos aunque haya acción adicional, menú o reintento (automático).
- [x] Como mucho dos invocaciones a la vez; la tercera se rechaza. Lo ya llamado en el combate no se vuelve a llamar, ni caído: reinvocar no cura (automático).
- [x] Una orden hace actuar al aliado ahora y no vuelve a actuar al acabar el turno; nombra a la presa y los aliados se ciñen a ella (automático).
- [x] Convergencia potencia lo que hay, se refresca y no se acumula, y no añade ni una tercera entidad ni un turno extra (automático).
- [x] El guardián absorbe el golpe en lugar del héroe, se rompe, deja pasar el resto y no vuelve (automático).
- [x] Un aliado que acosa no encadena a un jefe (automático).
- [x] Nada actúa si el dueño cayó o el combate acabó (automático).
- [x] Un aliado puede ganar el combate; guardar y recargar el encuentro da exactamente la misma pelea (automático).

### Formas
- [x] La forma sustituye los ataques; su reserva de PV temporales se da solo la primera vez (automático).
- [x] Alternar de forma no cura, no apila reservas y devuelve ataques y CA al salir (automático).
- [x] La forma sobrevive a un reinicio y morir transformado sigue siendo morir (automático).

### Compañero permanente
- [x] El servidor o la bestia es siempre el mismo ser, con el nombre del jugador (validado como dato, nunca como instrucción para la IA) (automático).
- [x] Caído, vuelve a medio PV; herido, sigue herido hasta un descanso largo; no es un objeto (automático).
- [x] Recorridos completos con una rama prestada: Demonólogo, Invocador y Cambiaformas, sobre el servicio y la base de datos (automático).
- [x] El panel muestra una línea por aliado, la forma y los textos nuevos sin marcadores sueltos, en ES y EN (automático).
- [ ] Jugar un combate con un Invocador o un Cambiaformas de verdad en Telegram (pendiente de B07: ninguna rama está lista).

## 0.10-I · Las catorce clases, primer grupo (B06, v0.10.29)

Guerrero, Bárbaro, Paladín, Pícaro y Monje. Cada clase con su barra, de nivel 1 a 9.

- [x] Cada clase tiene su barra, una técnica distintiva y algo que pagar desde el nivel 1; el ataque básico nunca cuesta nada (automático).
- [x] Ninguna necesita rama, aliado, oficio ni otro jugador; del 10 en adelante es de la rama (automático).
- [x] Calendario de poderes: de 6 a 9 llegan una o dos mejoras, no un botón nuevo cada nivel (automático).
- [x] Una barra que empieza vacía (Furia, Convicción) puede ganarse lo que cuesta su primera técnica (automático).
- [x] Todas ganan a un bandido en los niveles 1, 3, 5 y 9 y a una pareja de goblins desde el 5 (simulador, automático).
- [x] Tres combates seguidos sin descanso completo: la barra nunca sale de su rango y siempre queda un ataque gratis (automático).
- [x] El `strike` a distancia usa el arco y el cuerpo a cuerpo la hoja; la presa marcada recibe un dado extra de cada golpe (automático).
- [x] El Monje golpea con DES (las vendas son ligeras) y se viste de disciplina: CA 10 + DES + 3 (automático).
- [x] Las diez clases en el menú de creación, la ficha y `/class_<clase>` sin retrato ni marcadores sueltos (Telegram, EN).
- [ ] Las mismas pantallas en español.
- [ ] Un combate completo con Bárbaro (Furia desde cero) y con Paladín (Convicción) (Telegram).

## 0.10-I · Las catorce clases, segundo grupo (B06, v0.10.30)

Clérigo (Maná), Hechicero (Maná), Druida (Maná) y Bardo (Resonancia). Cuatro lanzadores sin un solo uso por descanso.

- [x] Las mismas exigencias que al primer grupo, ahora para las nueve clases: barra propia, técnica distintiva, nada que dependa de una rama, calendario sin un botón nuevo cada nivel, victoria sobre el bandido y sobre la pareja de goblins desde el 5 (automático).
- [x] La Resonancia del Bardo empieza vacía y se construye con su burla (+2), su ataque y cada turno (automático).
- [x] Ningún texto de estas clases habla ya de «usos por descanso» ni de «ilimitado»: hablan del Maná o de la Resonancia (automático).
- [x] Los nombres de habilidad nuevos llevan las mismas mayúsculas que los antiguos («Golpe de Gracia», «Cono de Frío») (a mano).
- [x] `/class_bard` en español: habilidad, acción y coste de barra («🔹 3») en cada línea (Telegram).
- [ ] Un combate de Hechicero gastando Maná hasta quedarse en el Rayo de Fuego, y uno de Bardo desde cero (Telegram).

## 0.10-I · Las catorce clases, último grupo (B06, v0.10.31)

Brujo (Esencia), Explorador (Foco), Artífice (Carga), Chamán (Maná) y Caballero de la Muerte (Poder rúnico). Con ellos terminan las catorce.

- [x] Las **catorce** clases cumplen las mismas exigencias: barra propia, técnica distintiva, nada que dependa de una rama, calendario sin un botón nuevo cada nivel, bandido en los niveles 1, 3, 5 y 9, pareja de goblins desde el 5, tres combates seguidos sin descanso (automático).
- [x] Ninguna clase usa ya «usos por descanso»; el camino antiguo sigue cubierto con una clase inventada (automático).
- [x] El reglamento habla de la barra, de las catorce clases y de `/path`, sin usos por descanso ni «las especializaciones llegarán» (automático y a mano).
- [x] Explorador: el Disparo certero usa el **arco**, gasta 4 de Foco y la barra vuelve (Telegram, EN).
- [ ] Las mismas pantallas en español para las seis clases nuevas.
- [ ] Un combate completo con Caballero de la Muerte (Poder rúnico desde cero) y con Artífice (Carga) (Telegram).
- [ ] Integrar los seis retratos cuando existan (`TODO-images.md`).

## 0.10-I · Las 41 ramas, lote A (B07, v0.10.32)

Veinte ramas de daño, marcas, defensa y maniobras: Vengador, Custodio Sagrado, Inquisidor, Maestro de Batalla, Baluarte, Berserker, Coloso, Asesino, Duelista, Saboteador, Puño de Hierro, Danzante de Sombras, Piromante, Criomante, Arcanista, Tempestario, Tirador, Filo Maldito, Sangre y Escarcha.

- [x] Cada rama lista tiene su recorrido entero: pasiva y técnica al 10, desarrollo al 15, dos modificadores en el 13 y dos en el 17, técnica culminante al 20 (automático).
- [x] El camino llega a su nivel: a los 10, 13, 17 y 20 el personaje tiene exactamente lo que le toca (automático).
- [x] Dos ramas de una misma clase no hacen las mismas decisiones: cada una aplica, gasta, responde, cura o protege de forma distinta (automático).
- [x] Cada modificador cambia de verdad al personaje, y las dos opciones de un nivel no dan lo mismo (automático).
- [x] Gastar un estado es una decisión real: sin el estado no se gasta nada, con él se gasta y hace daño (automático).
- [x] El robo de vida cura solo de daño hecho, y la represalia responde solo a una herida real (automático).
- [x] Ninguna rama es inútil contra un jefe de su nivel en los niveles 10, 13, 17 y 20 (simulador, automático).
- [x] En Telegram: `/path` en el Gremio ofrece las ramas listas y bloquea las que no, la ficha enseña el recorrido entero, la confirmación es definitiva y `/skill_` explica «gasta la marca» y su coste (Telegram, ES).
- [ ] Las mismas pantallas en inglés.
- [ ] Un combate real con Vengador marcando y gastando la marca (Telegram).

## 0.10-I · Las 41 ramas, lote B (B07, v0.10.33)

Doce ramas de curación, regeneración, melodías, reacciones y control: Redentor, Dominio de la Vida, de la Luz y de la Guerra, Guardián del Bosque, Círculo de las Esporas, Cantor de Guerra, Ilusionista, Armero Rúnico, Catalizador, Elementalista y Tejemareas.

- [x] Las mismas pruebas automáticas del lote A cubren las doce: recorrido entero, camino por nivel, decisiones distintas entre ramas hermanas, modificadores que cambian algo y suelo contra un jefe de su nivel.
- [ ] En Telegram (ES): `/path` ofrece las doce y la ficha enseña el recorrido; probar con un Clérigo de la Vida que la Curación radiante deja barrera.
- [ ] En Telegram (EN): las mismas pantallas.
- [ ] Un combate real con Elementalista: Espíritu de fuego y luego Estallido de vapor que gasta la quemadura.

## 0.10-I · Las 41 ramas, lote C (B07, v0.10.34)

Nueve ramas con entidades, formas y tiempo: Invocador, Cronomante, Cambiaformas, Demonólogo, Nigromante, Señor de Bestias, Artillero, Maestro de Constructos y Guardián Ancestral.

- [x] Las pruebas automáticas de ramas cubren las 41 (recorrido, camino por nivel, decisiones distintas, modificadores, suelo contra jefe) y que ninguna queda sin terminar.
- [ ] En Telegram (ES/EN): `/path` ofrece las 41; un Demonólogo ve a su servidor en el combate y lo ordena.
- [ ] En Telegram: un Cambiaformas toma forma de oso y vuelve a la humana sin curarse.
- [ ] En Telegram: un Maestro de Constructos monta el guardián y no puede montar también el de arco.

## 0.10-I · Tiempos, descanso, derrota y economía (B08, v0.10.35)

Sin ayudas de beta: todo lleva su tiempo real. Tabla única en `engine/timings.py`.

- [x] Pruebas automáticas: descanso largo con su tiempo y recompensa al terminar, descanso cancelado sin nada, doble cobro, descansos cortos limitados (dos) y devueltos por el largo, tope de la derrota, venta de la herramienta en uso, precios de las pociones.
- [ ] En Telegram (ES/EN): Actividades ofrece «💤 Descanso corto» (con cuántos quedan) y «🛏️ Descanso largo» con 15 min; el panel cuenta el tiempo y «Abandonar» no devuelve nada.
- [ ] En Telegram: el tutorial entero con tiempos reales (recolectar 4 min, desollar segundos); `oath tutorial-stats` cuadra con lo jugado.
- [ ] En Telegram: perder un combate con mucho oro cuesta como mucho 15 por nivel; con 0 de oro, nada; Ysolde cura aunque no te alcance.
- [ ] En Telegram: con el pico en uso, la tienda no te deja venderlo («la estás usando»).

## 0.10-I · Objetivos de misión nuevos (B09, 1.ª parte, v0.10.36)

- [x] Prueba automática: comprar, vender, equipar, guardar y sacar avanzan una misión (y comprar otro objeto no).
- [ ] En Telegram: una misión de prueba con «Equípate una pieza» se completa al equipar desde el inventario.
- [ ] En Telegram: salir de un combate con una bomba de humo cuenta como `smoke`; huir a pie no.

## 0.10-I · Campaña hasta el Recaudador (B09, v0.10.37)

- [x] Pruebas automáticas: cadena entera de misiones, llegada al jefe, material suficiente por oficio, decisión con reputación, humo siempre a la venta, mecánica del jefe (placa, aviso, descarga, recarga).
- [ ] En Telegram (ES/EN), jugando de cero con cuatro clases: del tutorial a «Una entrega sospechosa» y hasta «El Recaudador de Ceniza» sin quedarse atascado (`oath tutorial-stats` y diario).
- [ ] En Telegram: aprender cada uno de los ocho oficios y completar su encargo con el material que da el maestro.
- [ ] En Telegram: «Volver también es vencer» (coger el libro, salir con humo, curarse) y que el panel de combate avise «Apunta» y «Recarga».
- [ ] En Telegram: derrotar al Recaudador, entregar a Tamsin y comprobar el hito y el tope 10 con XP suficiente y con XP de menos.

## 0.10-I · Ciervo de Hierro y graduación (B10, v0.10.38)

- [x] Pruebas automáticas: mecánica del Ciervo, reglas de la ayuda (ES/EN), cadena de la graduación, piezas de equipo y suelo del 20 % de las 41 ramas al nivel 10.
- [ ] En Telegram (ES/EN): a nivel 10, «Tu camino» lleva a `/path`; elegir rama; «Equipo para la hondonada» ofrece cuatro piezas y una sola se equipa.
- [ ] En Telegram: examinar los troncos de la Arboleda Antigua, ir a la Hondonada del Ciervo y «🏹 Cazar» lleva al jefe.
- [ ] En Telegram: el panel avisa «Apunta» antes de la carga y «Recarga» después; 💡 ¿Qué hago? responde distinto con un Guerrero y con un Clérigo.
- [ ] En Telegram: vencer al Ciervo, entregar a Tamsin y ver el tope subir a 20; probar también derrota, huida con humo y volver a intentarlo.

## 0.10-I · Valle de la Fragua Gris (B11, v0.10.39)

- [x] Pruebas automáticas: grafo con ida y vuelta, puerta cerrada sin la bandera, refugio, cadena de las once misiones, objetivos alcanzables, núcleos suficientes, decisión del agua.
- [ ] En Telegram (ES/EN): tras entregar al Ciervo aparece «Cruce de los Carreteros» en el Camino del Viejo Rey; viajar, descansar y curarse en el Puesto del Vado.
- [ ] En Telegram: recorrer los ocho lugares; la recolección da hierro profundo, corazón de roble y seda; el mapa conecta todo.
- [ ] En Telegram: la decisión de «El agua de la cantera» cambia la reputación y no se puede repetir.
- [ ] En Telegram: reunir los núcleos, encender la baliza en tres pasos (limpiar, encajar, encender) y vencer al Custodio a nivel 20.

## 0.10-I · Balance integral (B12, v0.10.40)

- [x] Pruebas automáticas de `oath balance`: intervalos de Wilson, celdas reproducibles, kit T1, secuencias, informe y modelo de ritmo.
- [ ] Jugando a mano con tres clases (guerrero, clériga, hechicero) hasta el nivel 10: contrastar el modelo de ritmo del informe con el tiempo real (`oath tutorial-stats`).
- [ ] Pelear con un Pirómano o un Tirador contra el Custodio con pociones mayores y comprobar si se siente injusto.

## 0.10-I · Cripta retirada y reinicio (B13, v0.10.41)

- [x] Pruebas automáticas: el reinicio borra el juego y deja cuentas, presupuesto de IA, imágenes y auditoría; copia y restauración exactas; mazmorra de pruebas para el motor.
- [ ] En Telegram (ES/EN): el mapa no ofrece ningún lugar de cripta; el Bosque de los Susurros ya no tiene escalones ocultos; nadie habla del relicario (Mira, Holt, Ysolde, Tessa, Pell, Bram).
- [ ] En el diario de logros: aparecen «El valle se abre», «Cobrador cobrado» y las tres decisiones; no los de la cripta.
- [ ] En staging con una copia de producción: `oath launch-reset` en seco, `backup`, `launch-reset --yes`, `restore`, y comparar los conteos de cada tabla.
