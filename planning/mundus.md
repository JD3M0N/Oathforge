# Mundus — mundo, viaje, misiones, facciones y eventos

Resumen de [Possibilium §13–14, §19, §21–23](Possibilium.md#s13).

## Estado actual (0.9.0)

### Logros de mundo e historia

- Los conjuntos de ciudad y exploración son listas fijas de lugares de la edición v0_9; cuentan visitas efectivas, no destinos conocidos automáticamente.
- Los tres caminos del relicario son alternativas y el metalogro acepta cualquier final. Abrir el relicario requiere la acción explícita; completar la cripta en solitario no prueba su apertura.
- Descubrimientos y caza diurna/nocturna se registran como hechos; las expansiones no cambian condiciones ya publicadas.

### Lugares

Aetherfall → continente Terra Coronata → zonas (`content/world/<continente>/<zona>/<lugar>/place.yaml`):

- **Crownreach** (ciudad, 13 lugares): plaza (hub), **Gremio de Aventureros** (Vale; horno, aserradero, secadero, mesa de preparación y fogón: el refinado de las maestrías está abierto a cualquiera), taberna La Corona Rota (Bram, fogón, posada), mercado (Mira), Capilla del Alba (hermana Ysolde; cura gratis todos los PV y heridas graves en la beta) y el **Barrio de Oficios**, una calle de la que cuelgan los siete puestos de oficio, cada uno con su estación y su maestro: la Forja de Tessa (herrería), la Botica de Ilva (alquimia), el Taller de Garrick (carpintería), la Curtiduría de Oda (peletería), el Banco de Pell (joyería), el Escritorio de Lorent (escribanía), el Taller de Dunn (ingeniería) y el Telar de Hedda (sastrería). Cada oficio se aprende y se cambia solo en su puesto (`Location.teaches`). El mapa agrupa los puestos bajo la calle con un botón «🛠️ Puestos», para que la ciudad siga cabiendo en una pantalla. Son ocho puestos, uno por oficio.
- **Tierras salvajes**: Camino del Viejo Rey, Bosque de los Susurros, Prado de los Colmillos (caza de día y de noche), Mina del Paso Viejo, Arboleda Antigua, Claro de la Raíz Roja, Ribera de Silverbrook.
- **Cripta Hundida** (mazmorra): salas con combates fijos, osario con descanso gratis y santuario de Ser Aldren.
- Reloj día/noche: un día de juego = 4 h reales; los NPC tienen horario. `GAME_CLOCK_OFFSET_HOURS` lo adelanta para pruebas.

### Mapa y viaje (0.7.6, viaje directo en 0.8.0)

Regla: **el jugador elige adónde ir; el motor hace el recorrido y solo lo interrumpe si pasa algo que merece una decisión.**

- **Grafo**: cada `exit` es una arista dirigida con minutos de juego; distancia a 100 yd/min (`yards:` si el terreno es lento). Las rutas van y vuelven igual (test). Una ciudad tiene un único `hub`, solo se sale por él y sus calles no tienen peligro (lo valida el cargador).
- **Planificador** (`services/world_map.destinations` / `route_to`): Dijkstra global entre zonas. Destinos: lugares visitados, calles de una ciudad ya visitada, adyacentes (así se explora) y, desde una ciudad, las salidas de su hub. No atraviesa lugares con combate fijo pendiente (`blocks_passage`): se entra, pero no se cruza.
- **Una tirada de emboscada por viaje**: `min(45 %, 15 % × peor ⚠️ + 5 % por cada tramo ⚠️ extra)`. Si sale, el viaje se para en un tramo peligroso con criaturas y `flags.trip` guarda el resto; «▶️ Seguir hacia…» lo termina sin otra tirada. La derrota lo borra.
- **📜 al objetivo** (`exploration.objective_routes`): hasta dos botones al lugar conocido más cercano para el siguiente paso de cada misión (`visit`/`rest`/`heal`: su lugar o la posada más cercana; `talk`: dónde está el NPC ahora; `kill`/`hunt`: sus tablas, solo criaturas de esa hora y nivel; `gather`: recursos; `craft`: estaciones; acciones de misión con `location`; misiones sin objetivos contados: sus acciones o el jefe de sus disparadores). Nunca revela un sitio desconocido.
- Viaje **instantáneo** en la beta; se muestra solo la distancia en yardas.

### Misiones

Máquinas de estados en `content/quests.yaml`: `stages`, `actions` (botón o texto libre con tirada) y `triggers`. Con `objectives` se completan solas y dan `rewards`; la siguiente se abre con `after` o `unlock_flag`; avance en `quest_progress.counters`. Efectos: `give_item`, `take_item`, `gold`, `xp`, `reputation`, `set_flag`, `npc_memory`, `trust`, `damage`, `world_rumor`.

Objetivos: `kill`, `talk`, `visit`, `read` (sección del `/rulebook`), `hunt` (victorias de 🏹 Cazar o 🐾 Rastrear en un lugar, de día o de noche), `gather`, `skin`, `craft` (cantidad de un objeto), `rest` y `heal` (aceptan `target: any`).

**Tutorial** (misiones 1–10, sin mazmorras, `tutorial: true`):

| # | Misión | Objetivo | Enseña | XP | Recompensa |
|---|---|---|---|---|---|
| 1 | Alistamiento | Hablar con Vale en el Gremio + leer «🧺 Actividades» | PNJ, reglamento | 25 | cuchillo de desollar |
| 2 | Calles de Crownreach | Barrio de Oficios, taberna y Bram | `/map`, ciudad | 25 | 5 de oro |
| 3 | El mercado | Mira en el mercado y Tessa en su forja | tiendas | 25 | 5 de oro + poción |
| 4 | Colmillos en el prado | Cazar 2 veces en el prado + 2 de carne desollando | caza, combate, desuello | 100 | hoz |
| 5 | Raíz de sangre | Recoger 3 raíces de sangre | salir, recolectar, emboscadas | 50 | 5 de oro |
| 6 | Guiso del cazador | Fabricar un estofado del cazador | aficiones, fogón | 50 | pico |
| 7 | Hierro para la Guardia | Sacar 3 menas de hierro | minería | 60 | hacha |
| 8 | Un cuarto propio | Tablones del gremio: montar cofre y cama | refinado, habitación | 60 | cuarto con cama y cofre |
| 9 | Alas al anochecer | Cazar 3 veces en la mina | grupos de enemigos | 75 | — |
| 10 | Heridas de guerra | Ysolde + descanso largo + volver con Vale | curación y descanso | 40 | poción |
| 10 | El Viejo Colmillo | El jabalí jefe del prado (lo da Bram) | jefe | 300 | 80 de oro |

- Beta (`config.py`, `# beta only`): mientras hay una misión del tutorial activa, toda actividad con tiempo termina al momento y da lo que falta; el descanso largo es instantáneo; pociones a 1 de oro.
- `legacy_done`: quien completó las misiones antiguas tiene el tutorial hecho, sin recompensa.
- Después: **11. El relicario sellado** (Holt; tres finales: devolverlo al Pacto, venderlo al Sindicato o abrirlo; 50 + 100 + 300 XP) y **12. Huesos inquietos** (3 esqueletos; 300 XP).
- `oath tutorial-stats`: minutos por misión y dónde se atasca cada jugador.

### Facciones y rumores

Pacto de Plata y Sindicato Carmesí con reputación −100..100 (precios ±25 %). Rumores: lo que hace un jugador (derrotar al Guardián) se cuenta en las tabernas de los demás.

## Decidido

- El mapa y la imagen nunca son fuente de verdad: el grafo de `content/world/` manda.
- Los ids de lugar son globales y no cambian al mover carpetas; la jerarquía conceptual del GDD no renombra carpetas.
- Mundo compartido con ecos (rumores) mientras el juego sea individual.

## Próximo

- **Entregar misiones a quien las dio** (prioridad alta del TODO; **MIS-02**).
- **Lo que falta del Gremio** ([F15](roadmap.md#F15), [contrato](roadmap-profesiones.md)): las especializaciones de maestría (fase 7).
- Más misiones tras nivel 5 y encargos repetibles de caza (**MIS-05**, plantillas validadas).
- **AVE-01..09** banco de aventuras; puertas con varias soluciones (**AVE-08**, PKG-07).
- **Fase 2 del viaje** (**VIA-01..10**): viajar ≠ explorar; escenas con presupuesto (0 rutina, 1 primera visita, 1–2 expedición corta); estilos 🛡️ Prudente / 🧭 Explorador / ⚡ Directo, sin gastar consumibles solos; rutas distintas de verdad; atajos con `requires_flag` (Sendero de los Carboneros, barquero); 3 favoritos; cambios de ruta por eventos revalidados al salir y al continuar; cada tramo resuelto una vez (nonce). Si el viaje vuelve a gastar tiempo, mover el reloj y avisarlo en el rulebook.
- **GEO-01** segunda región pequeña (Frosthold o Stormport): cinco lugares, tres misiones, una facción, un recurso, un jefe. **GEO-02** clima por región.
- Facciones nuevas con misión, servicio y tensión (Verdant Pact para el bosque, Hollow Choir para la cripta); rangos de reputación legibles (perseguido … venerado).
- `world_facts` y eventos encadenados: la **crisis del hierro** (PKG-08: anuncio, preparación, contribución, resolución, epílogo).
- Rumores con veracidad que se investigan (**SOC-02**); *Herald of Aetherfall* en los canales (**MUN-04**).
- Logros, eventos por bandos, defensa de la ciudad y raids semanales, más adelante.

## Preguntas abiertas

- ¿Mundo compartido completo o aventuras instanciadas con ecos?
- ¿Frosthold (crisis del hierro, profesiones) o Stormport (comercio, contrabando)?
- ¿Nombres en inglés del GDD (Thornwood…) o traducidos?
- ¿Los eventos del mundo los aprueba un administrador al principio?
- ¿Cuánto contenido nuevo por versión es realista?
