# Mundo y misiones

## Estado actual

- Aetherfall: Crownreach (plaza, taberna La Corona Rota, mercado), el Camino del Viejo Rey, el Bosque de los Susurros, el Prado de los Colmillos y la Cripta Hundida (5 salas + jefe).
- **Zona de caza** (v0.5.0): el Prado de los Colmillos, a 20 minutos de la plaza y sin peligro en el camino. Botón «🏹 Cazar»: de día salen jabalíes y de noche murciélagos (`night_encounters`). El Viejo Colmillo aparece cuando la misión 6 está activa.
- **Capilla del Alba** (v0.7.0), a 2 min de la plaza: la hermana Ysolde cura heridas (diseño: 3 de oro y 1d8+4 PV; en la beta, gratis y todos los PV desde la 0.7.28). La inscripción del altar se mudó aquí desde la plaza.
- **Descanso largo** (v0.7.0): en la posada, 5 de oro y 8 horas de juego (80 min reales) acostado, como una actividad (`kind: rest`): ocupado, aviso al despertar y «Levantarse» para recuperar PV, usos y «herido». Levantarse antes no cura ni devuelve el oro.
- Reloj día/noche (un día de juego = 4 horas reales); los NPC tienen horario.
- Misiones como máquinas de estados en YAML (`content/quests.yaml`): etapas, acciones (botón o texto libre con tirada) y disparadores.
- «El relicario sellado», con tres finales.
- **Cadena de misiones** (v0.5.0), automática: al completar una se abre la siguiente (`after` o `unlock_flag`). Las misiones con `objectives` (matar N, hablar con, ir a) cuentan solas y dan `rewards`; el avance se guarda en `quest_progress.counters`. El diario muestra las misiones en curso con su avance y, en «Misiones», la ficha de cada una (quién la da, objetivos, pista y recompensa).

  **Tutorial de la sargenta Vale** (v0.7.13, misiones 1–8). Sustituye a las antiguas «Bienvenido a Crownreach», «Colmillos en el prado» y «Alas al anochecer». Vale está en la plaza día y noche; el primer mensaje de la plaza invita a hablar con ella. Cada misión enseña una cosa y su recompensa es la herramienta de la siguiente:

  | # | Misión | Objetivo | Enseña | XP | Recompensa |
  |---|---|---|---|---|---|
  | 1 | Alistamiento | Hablar con Vale + leer «🧺 Actividades» en el `/rulebook` | hablar con PNJ, el reglamento | 25 | cuchillo de desollar |
  | 2 | Calles de Crownreach | Ir al Barrio de Oficios y a la taberna + hablar con Bram | `/map`, moverse por la ciudad | 25 | 5 de oro |
  | 3 | Colmillos en el prado | 2 jabalíes + 1 cuero desollado (de día o de noche desde la v0.7.25) | caza, combate, desuello | 100 | hoz |
  | 4 | Raíz de sangre | Recoger 3 raíces de sangre | salir de la ciudad, recolección, emboscadas | 50 | 5 de oro |
  | 5 | Guiso del cazador | Fabricar un estofado del cazador | aficiones, fogón, fabricar | 50 | pico |
  | 6 | Hierro para la Guardia | Sacar 3 menas de hierro | minería, expedición larga | 60 | 10 de oro |
  | 7 | Alas al anochecer | 3 murciélagos en la mina (a cualquier hora desde la v0.7.15) | caza en grupo de enemigos | 75 | — |
  | 8 | Heridas de guerra | Hablar con Ysolde + volver con Vale | curación y descanso | 40 | poción de curación |

  **Tutorial acelerado** (v0.7.16): las misiones llevan `tutorial: true`. La primera recolección (o expedición) o desuello que encaja con el objetivo activo termina al momento, sin emboscada, y da justo lo que falta. Una vez por misión (`char.flags.tutorial_boosts`); lo demás dura lo normal.

  Total: 425 de misión + unos 95 de combates ≈ 520 → nivel 3. Quien ya había completado «Alas al anochecer» tiene el tutorial hecho (`legacy_done`, sin recompensa).

  | # | Misión | Objetivo | XP |
  |---|---|---|---|
  | 9 | El relicario sellado | Tres caminos hasta el Guardián | 50 + 100 + 300 |
  | 10 | Huesos inquietos | 3 esqueletos de la cripta | 300 |
  | 11 | El Viejo Colmillo | El jabalí jefe | 300 |

  Con la XP de los combates se llega a nivel 2 en la misión 3, a 3 al acabar el tutorial, a 4 en la cripta y a 5 al vencer al Guardián.
- Facciones con reputación: Pacto de Plata y Sindicato Carmesí.
- Rumores: lo que hace un jugador se cuenta en las tabernas de los demás.

- **Objetivos de misión (v0.7.12)**: además de `kill`, `talk` y `visit`, existen `gather`, `skin` y `craft` (el objetivo es un objeto y cuenta la cantidad conseguida recogiendo, desollando o fabricando), `rest` (un descanso largo que termina en ese lugar) y `heal` (la curandera de ese lugar). `rest` y `heal` aceptan `target: any`. Son la base del tutorial.

## Ideas

- Eventos mundiales encadenados (asedio de bandidos a Crownreach si nadie limpia el camino).
- Misiones que crucen facciones y obliguen a elegir.
- Mazmorras con salas aleatorias montadas a partir de piezas en YAML.
- Misiones de clase (el Sacerdote purifica la capilla, el Guerrero entrena a la milicia).
- Diario con pistas que la IA resume a partir de los hechos, sin inventar.

### Mapa y rutas (v0.7.6; viaje directo en v0.8.0)

Regla: **el jugador elige adónde ir; el motor hace el recorrido y solo lo interrumpe si pasa algo que merece una decisión.** La distancia no se convierte en número de pulsaciones.

- **Grafo**: cada lugar es un nodo y cada `exit` una arista dirigida con peso en **minutos de juego**; la distancia sale del ritmo normal de D&D, 300 pies/min = **100 yd/min** (1 km ≈ 1094 yd; 1 yd = 0,9144 m). `yards:` en la salida cuando el terreno es lento. Las rutas van y vuelven igual (test).
- **Planificador** (`world_map.destinations` / `route_to`, v0.8.0): Dijkstra global, entre zonas. Se puede ir a:
  - cualquier lugar **conocido**: visitado (`stats.places`) o calle de una ciudad en la que ya has estado;
  - cualquier lugar **adyacente** (así se explora lo nuevo, tramo a tramo);
  - desde una ciudad, a las salidas de su `hub`.

  El camino solo pasa por lugares conocidos y **sin combate fijo pendiente** (`blocks_passage`): a una sala con guardianes se puede entrar, pero no atravesarla. Solo se sale de la ciudad por el hub (lo garantiza el cargador).
- **Una tirada de emboscada por viaje**:

  ```
  min(45 %, 15 % × peor ⚠️ + 5 % por cada tramo ⚠️ extra)
  ```

  Con un solo tramo da lo mismo que antes. Si sale, el viaje se para en un tramo peligroso con criaturas (pesado por su ⚠️), y `flags.trip = {to, rolled}` guarda el resto. «▶️ Seguir hacia…» en la escena lo termina sin otra tirada. La derrota (respawn) lo borra.
- **Objetivo**: el mapa ofrece hasta dos botones 📜 al lugar conocido más cercano donde se cumple el siguiente paso de cada misión activa. Ese lugar sale del mundo (`exploration.objective_routes`):
  - `visit`, `rest` y `heal`: su lugar;
  - `talk`: dónde está el NPC ahora;
  - `kill`: sus tablas de encuentros;
  - `gather`: los recursos de cada lugar;
  - `craft`: las estaciones;
  - además, las acciones de misión con `location`.

  Nunca revela un sitio que no se conozca.
- **Interfaz**: `/map` y «🧭 Viajar» son la misma vista, en este orden:
  1. dónde estás;
  2. 📜 objetivo;
  3. esta zona;
  4. las demás zonas conocidas (más de 2 lugares → un botón que abre la zona, `trvz`);
  5. 🌫️ sin explorar, solo texto.

  Al llegar sin nada más (ni combate, ni misión), el mensaje del mapa se edita y se convierte en la escena.
- **Pendiente**: el viaje es instantáneo (para probar); `/travel` con tiempo real, viajes entre ciudades desde su punto de partida, estados de descubrimiento y niebla de guerra.

### Fase 2 del viaje: expediciones (pendiente)

La comodidad (v0.8.0) cubre la rutina. La aventura del trayecto queda para cuando haya contenido que la merezca:

- **Viajar ≠ Explorar.** Viajar: llegar a un lugar conocido. Explorar: una expedición a lo desconocido («🌲 Explorar Thornwood»), con pistas, recursos y problemas. Así quien solo quiere fabricar no acaba en una aventura de veinte minutos.
- **Escenas de viaje con presupuesto** (cifras para probar):

  | Tipo de viaje | Escenas |
  |---|---|
  | Trayecto cotidiano | 0 |
  | Primera visita | 1 |
  | Expedición corta | 1-2 |
  | Viaje de misión | las suyas |

  Las escenas son decisiones (el puente de Silverbrook dañado: cuerda, vado o desvío): gastar una herramienta, una prueba, elegir un encuentro o renunciar a una oportunidad. No siempre combate. Pertenecen al descubrimiento o a algo que cambió en el mundo, nunca a cada viaje rutinario.
- **Estilos de expedición**:
  - 🛡️ **Prudente**: evita oportunidades peligrosas.
  - 🧭 **Explorador**: se para ante descubrimientos.
  - ⚡ **Directo**: ignora desvíos.

  Ninguno gasta consumibles ni acepta deudas solo.
- **Rutas alternativas solo cuando sean distintas de verdad.** Por ejemplo: patrullada (más segura, más larga o con peaje), atajo (más rápido, más riesgo) o paso antiguo (requiere haberlo encontrado). La interfaz expresa el intercambio («más seguro», «requiere cuerda»), no una tabla de números.
- **Atajos desbloqueables** con `requires_flag` (ya existe): Sendero de los Carboneros a la mina, un barquero, una puerta secundaria, un refugio, un carro a otra población.
- **Favoritos** (3) en el menú de viaje cuando el mapa crezca.
- **Cambios de ruta por eventos**: «el camino está cerrado por un derrumbe: [ayudar] [sendero del bosque]». La ruta se comprueba al partir y al continuar.
- **Restricciones explicadas**: «estás siguiendo unas huellas: puedes abandonar y viajar, pero perderás la oportunidad».
- **Grupos**: el líder propone el destino y todos ven la ruta. Se confirma al empezar una expedición peligrosa, no en cada calle.
- **Cada tramo y decisión se resuelve una vez** (nonce de `audit`), también tras un doble clic o un reinicio.

### Geografía y exploración (GDD §3)

- **Siete regiones** como objetivo de temporada (§3.2):

  | Región | Cultura | Recursos | Amenaza |
  |---|---|---|---|
  | Crownreach | Capital de nobles, gremios y guardias | Comercio, oficios, banca | Corrupción y conspiraciones |
  | Thornwood (≈ Bosque de los Susurros) | Bosque ancestral, pacto druídico | Hierbas, caza, espíritus | Criaturas y antiguos juramentos |
  | Frosthold | Montañas mineras y clanes | Hierro, plata | Derrumbes, gigantes, hielo |
  | Ashen Peaks | Volcanes y forjas | Cristales, armas, reliquias | Cultos y bestias ígneas |
  | Mirefen | Pantanos y ruinas sumergidas | Venenos, alquimia | Maldiciones y enfermedades |
  | Sunscar | Desierto, oasis, caravanas | Comercio, arqueología | Saqueadores y tormentas |
  | Stormport | Puerto libre | Navegación, pesca, contrabando | Piratas y política mercante |

- **El mundo es un grafo** (§3.1): nodos con región, tipo, peligros, servicios y NPC; aristas con distancia, coste, riesgo y condiciones (rutas cortadas por eventos o reputación). Una ciudad se abre en distritos sin necesidad de cuadrícula. Encaja con `content/world/`, organizado como **mundo → continente → zona (ciudad, territorio salvaje, mazmorra) → lugar**; cada nivel es una carpeta (v0.3.0).
- **Estados de descubrimiento por personaje** (§3.3): `undiscovered`, `rumored`, `discovered`, `visited`, `mapped`. «Rumored» deja seguir una pista sin conocer el camino exacto.
- **Tipos de exploración** (§3.3): dirigida, por pistas, arriesgada, social (zonas que se abren con reputación), histórica y competitiva.
- **Viajes con decisiones** (§3.4): ruta segura, atajo, viajar con mercaderes, contratar guía, acampar. Encuentros aleatorios de tablas según región, hora, estación y reputación.
- **Campamentos**: descanso parcial, cocinar, vigilar por turnos; más baratos y más arriesgados que la posada.
- **Cadenas causales** (§3.5): un descubrimiento marca un `world_fact` (`hidden_ruin_discovered=true`) y de ahí salen un rumor, arqueólogos, compradores de mapas y una facción que quiere el sitio.

### Mundo vivo (GDD §11)

- **Reloj lógico y tareas programadas**: los cultivos crecen, las caravanas viajan y las facciones ganan o pierden recursos sin que ninguna IA «piense». Un día de juego = un día real al principio.
- **Familias de eventos** (§11.2): naturales, sociales, económicos, políticos, militares, mágicos, de aventura y misterios.
- **Estructura de un evento** (§11.3): `trigger`, `preconditions`, `participants`, `location`, `duration`, `effects`, `followups`, `visibility`, con topes para que las reacciones no crezcan sin fin.
- **Ejemplo, la crisis del hierro** (§11.3.1): día 1 se derrumba una veta (misión de rescate, rumor parcial); día 2 suben los precios y la herrería publica encargos; día 3 una facción acusa a otra; día 4 los jugadores escoltan, investigan o sabotean; día 5 se resuelve según pruebas y decisiones.
- **Rutinas de NPC** (§11.4): agendas declarativas (trabajo, mercado, taberna, casa); la posición se calcula solo cuando alguien la consulta. Ya tenemos horarios: ampliarlos.
- **Periódico *Herald of Aetherfall*** (§11.5): dos boletines por semana con descubrimientos, economía, conflictos y rumores, redactado por la IA **solo** a partir de eventos confirmados. Puede publicarse en un canal de Telegram (ver `multijugador.md`).
- **Eventos comunitarios** (§11.6): tormenta arcana con portales, festival, jefe mundial con contribución limitada por jugador. Anunciados con antelación y sin exigir que todos estén conectados a la vez.

### Misiones (GDD §12)

- **Cuatro fuentes** (§12.1): hechas a mano, por plantilla (rescatar, transportar, investigar, cazar, defender, fabricar), emergentes (de la economía o los conflictos) y personales (trasfondo, juramentos).
- **Estados** (§12.2): `locked`, `available`, `accepted`, `in_progress`, `blocked`, `ready_to_complete`, `completed`, `failed`, `expired`, con evidencia (`event_id`) en cada transición. Hoy las misiones son etapas en YAML; estos estados son el envoltorio.
- **Estructura** (§12.3): gancho → objetivo aparente → descubrimiento → elección → consecuencia → eco posterior. Una misma crisis da un gancho distinto a cada clase.
- **Ejemplo, «La curandera acusada»** (§12.4): 8–12 consecuencias semánticas verificables; la IA describe cómo se desarrollan.
- No generar misiones imposibles: una entrega de hierro solo existe si hay demanda y el hierro se puede conseguir.
- **Diario de aventuras** (§12.6): «resume mis últimas aventuras», construido desde eventos guardados, nunca reconstruido de memoria.

### Facciones y política (GDD §8)

- **Ocho facciones** propuestas (§8.2). Ya existen dos:

  | Facción | Valores | Conflicto | En Oathforge |
  |---|---|---|---|
  | The Silver Covenant | Orden, protección, deber | Justicia frente a fanatismo | ✅ Pacto de Plata |
  | The Crimson Syndicate | Contrabando, libertad informal | Autonomía frente a explotación | ✅ Sindicato Carmesí |
  | The Ashen Circle | Saber arcano | Innovación frente a control | idea |
  | The Verdant Pact | Equilibrio natural | Conservación frente a industria | idea (encaja con el Bosque) |
  | The Iron Dominion | Expansión y disciplina | Seguridad frente a conquista | idea |
  | The Veiled Court | Diplomacia e intriga | Orden frente a manipulación | idea |
  | The Hollow Choir | Cultos funerarios | Memoria frente a tabú | idea (encaja con la Cripta) |
  | The Free Companies | Mercenarios | Honor contractual frente a interés | idea |

- **Rangos de reputación** (§8.3) sobre nuestro −100..100: perseguido (≤ −61), hostil (−60..−21), desconfiado (−20..−1), neutral (0..19), conocido (20..49), aliado (50..79), venerado (80..100). Siempre con misiones de rehabilitación.
- **Ley regional** (§8.5): cada ciudad con sus leyes (armas, necromancia, impuestos); los delitos generan «buscado», multas o juicios con pruebas registradas.
- **Política** (§8.4): consejos, elecciones, tratados, embargos. Un mensaje libre nunca destituye a un gobernante; el motor exige condiciones y recursos.

### Tabernas y rumores (GDD §9)

- **La taberna como centro social** (§9.1): descanso, conversación, contratos, rumores, minijuegos y encontrar grupo. Ambiente distinto por ciudad y por hora.
- **Ficha de NPC importante** (§9.2): papel, rutina, actitud, objetivos, secretos, conocimiento comprobado, necesidades y relaciones. El motor no deja que sepa lo que nunca pudo saber.
- **Rumores como objeto** (§9.3): `rumor_id`, afirmación, fuente, hecho vinculado, **veracidad** (verdadero, falso, incompleto, no verificable), regiones y caducidad. Dos tabernas pueden contar versiones opuestas y el jugador tiene que investigar. Difundir verdades da reputación de investigador; inventar, descrédito.
- **Mercado de información** (§9.4): comprar pistas, vender ubicaciones, bardo que narra sucesos públicos.
- **Minijuegos** (§9.5): dados de taberna, acertijos, torneos de relatos, cartas del mundo; apuestas solo con fichas sin valor real.
- **Crónicas** (§9.6): que un jugador oiga en la taberna la historia de una decisión que tomó semanas antes.

## Preguntas abiertas

- ¿Mundo compartido (lo que hace uno cambia para todos) o por jugador con ecos (rumores)?
- ¿Cuánto contenido nuevo por versión es realista?
- ¿Cuál es la segunda región: Frosthold (crisis del hierro, profesiones) o Stormport (comercio, contrabando)?
- ¿Adoptamos los nombres en inglés del GDD (Thornwood…) o los traducimos como hasta ahora?
- ¿Los eventos del mundo los aprueba un administrador al principio (§10.6) o se aplican solos?

## Ajustes tras la prueba de las 11 misiones (0.7.28–0.7.30)

- El prado, a nivel 1, solo saca 1 jabalí (o 1 murciélago de noche); las parejas llegan a nivel 2 (`min_level` en `encounters`).
- Ysolde cura todos los PV y cierra las heridas graves mientras dure la beta; `healer.heal` y `healer.cost` quedan para cuando entre la economía.
- Al terminar «Heridas de guerra», Vale manda al Bosque de los Susurros (ahí empieza «El relicario sellado»); Holt solo cuenta cuando llevas el relicario.
- El viaje es instantáneo y solo enseña la distancia en yardas; si más adelante gasta tiempo, habrá que mover el reloj de juego (hoy va a tiempo real: 1 día = 4 h) y avisarlo en el rulebook.
