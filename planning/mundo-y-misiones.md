# Mundo y misiones

## Estado actual

- Aetherfall: Crownreach (plaza, taberna La Corona Rota, mercado), el Camino del Viejo Rey, el Bosque de los Susurros y la Cripta Hundida (5 salas + jefe).
- Reloj día/noche; los NPC tienen horario.
- Misiones como máquinas de estados en YAML (`content/quests.yaml`): etapas, acciones (botón o texto libre con tirada) y disparadores.
- «El relicario sellado», con tres finales.
- Facciones con reputación: Pacto de Plata y Sindicato Carmesí.
- Rumores: lo que hace un jugador se cuenta en las tabernas de los demás.

## Ideas

- Eventos mundiales encadenados (asedio de bandidos a Crownreach si nadie limpia el camino).
- Misiones que crucen facciones y obliguen a elegir.
- Mazmorras con salas aleatorias montadas a partir de piezas en YAML.
- Misiones de clase (el Sacerdote purifica la capilla, el Guerrero entrena a la milicia).
- Diario con pistas que la IA resume a partir de los hechos, sin inventar.

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

- **El mundo es un grafo** (§3.1): nodos con región, tipo, peligros, servicios y NPC; aristas con distancia, coste, riesgo y condiciones (rutas cortadas por eventos o reputación). Una ciudad se abre en distritos sin necesidad de cuadrícula. Encaja con `content/locations.yaml`.
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
