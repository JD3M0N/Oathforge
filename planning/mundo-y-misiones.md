# Mundo y misiones

## Estado actual

- Aetherfall: Crownreach (plaza, taberna La Corona Rota, mercado), el Camino del Viejo Rey, el Bosque de los Susurros, el Prado de los Colmillos y la Cripta Hundida (5 salas + jefe).
- **Zona de caza** (v0.5.0): el Prado de los Colmillos, a 20 minutos de la plaza y sin peligro en el camino. Botón «🏹 Cazar»: de día salen jabalíes y de noche murciélagos (`night_encounters`). El Viejo Colmillo aparece cuando la misión 6 está activa.
- **Capilla del Alba** (v0.7.0), a 2 min de la plaza: la hermana Ysolde cura heridas por 3 de oro (1d8+4 PV, sin pasar del techo de «herido»). La inscripción del altar se mudó aquí desde la plaza.
- **Descanso largo** (v0.7.0): en la posada, 5 de oro y 8 horas de juego (80 min reales) acostado, como una actividad (`kind: rest`): ocupado, aviso al despertar y «Levantarse» para recuperar PV, usos y «herido». Levantarse antes no cura ni devuelve el oro.
- Reloj día/noche (un día de juego = 4 horas reales); los NPC tienen horario.
- Misiones como máquinas de estados en YAML (`content/quests.yaml`): etapas, acciones (botón o texto libre con tirada) y disparadores.
- «El relicario sellado», con tres finales.
- **Cadena de misiones** (v0.5.0), automática: al completar una se abre la siguiente (`after` o `unlock_flag`). Las misiones con `objectives` (matar N, hablar con, ir a) cuentan solas y dan `rewards`; el avance se guarda en `quest_progress.counters`. El diario muestra las misiones en curso con su avance y, en «Misiones», la ficha de cada una (quién la da, objetivos, pista y recompensa).

  | # | Misión | Objetivo | XP |
  |---|---|---|---|
  | 1 | Bienvenido a Crownreach | Hablar con Bram | 50 |
  | 2 | Colmillos en el prado | 3 jabalíes (de día) | 150 |
  | 3 | Alas al anochecer | 4 murciélagos (de noche) | 200 |
  | 4 | El relicario sellado | Tres caminos hasta el Guardián | 50 + 100 + 300 |
  | 5 | Huesos inquietos | 3 esqueletos de la cripta | 300 |
  | 6 | El Viejo Colmillo | El jabalí jefe | 300 |

  Con la XP de los combates se llega a nivel 2 en la misión 2, a 3 en la 3, a 4 en la cripta y a 5 al vencer al Guardián.
- Facciones con reputación: Pacto de Plata y Sindicato Carmesí.
- Rumores: lo que hace un jugador se cuenta en las tabernas de los demás.

- **Objetivos de misión (v0.7.12)**: además de `kill`, `talk` y `visit`, existen `gather`, `skin` y `craft` (el objetivo es un objeto y cuenta la cantidad conseguida recogiendo, desollando o fabricando), `rest` (un descanso largo que termina en ese lugar) y `heal` (la curandera de ese lugar). `rest` y `heal` aceptan `target: any`. Son la base del tutorial.

## Ideas

- Eventos mundiales encadenados (asedio de bandidos a Crownreach si nadie limpia el camino).
- Misiones que crucen facciones y obliguen a elegir.
- Mazmorras con salas aleatorias montadas a partir de piezas en YAML.
- Misiones de clase (el Sacerdote purifica la capilla, el Guerrero entrena a la milicia).
- Diario con pistas que la IA resume a partir de los hechos, sin inventar.

### Mapa y rutas (v0.7.6)

- **Grafo**: cada lugar es un nodo y cada `exit` una arista dirigida con peso en **minutos de juego**; la distancia sale del ritmo normal de D&D, 300 pies/min = **100 yd/min** (1 km ≈ 1094 yd; 1 yd = 0,9144 m). `yards:` en la salida cuando el terreno es lento. Las rutas van y vuelven igual (test).
- **Ciudad**: movimiento libre por el camino más corto (Dijkstra sobre la zona). Solo se sale desde el `hub` (la plaza), que es el punto de partida de los viajes. El cargador exige un hub, calles sin peligro ni combates fijos y todo conectado.
- **Tierras salvajes y mazmorras**: tramo a tramo; cada camino tira su emboscada y cada sala su combate fijo. El mapa enseña el resto de la zona salvaje con la ruta y los minutos, sin botón; en la mazmorra marca las salas despejadas.
- `/map` y «🧭 Viajar» son la misma vista, con las actividades de cada lugar y quién está ahora.
- **Pendiente**: el viaje es instantáneo (para probar); `/travel` con tiempo real, viajes entre ciudades desde su punto de partida, estados de descubrimiento y niebla de guerra.

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
