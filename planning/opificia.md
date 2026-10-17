# Opificia — actividades, maestrías, oficios y recetas

Resumen de [Possibilium §15–16](Possibilium.md#s15). El bucle: **zona → actividad → esperar o arriesgarse → materiales → maestría → fabricar → usar, vender o llevarlo a una aventura.** Los números son hipótesis de balance.

## Estado actual (0.8.2)

### Tres capas de progresión

- **Nivel del personaje**: combate, atributos y habilidades de clase.
- **Maestrías de campo**: minería, tala, herboristería, desuello y rastreo. Libres, sin plaza, rango 0–5 (XP 0/80/240/500/900/1500). Cada rango: +4 % de unidad extra (tope 20 %, sin XP) y abre recursos con `min_rank` (cobre a 1, gemas y musgo del reposo a 3). No son habilidades d20.
- **Oficios**: herrería, alquimia, carpintería, peletería, joyería, escribanía e ingeniería; **dos activos**. Se aprenden en el Barrio de Oficios; cambiar uno cuesta 25 de oro (pide confirmación) y su XP no se pierde.
- **Aficiones**: cocina y pesca, sin plaza (`hobby: true` en `professions.yaml`; la pesca con `practice: fishing`, sin estación). Su XP vive con la de los oficios.

### Actividades de campo

| Actividad | Espera | Botín | XP | Riesgo |
|---|---|---|---|---|
| ⛏️ Trabajar (minar, talar, hierbas, pescar) | 5 min | 2–3 | 10 | Ninguno |
| 🏕️ Expedición larga | 15 min | 8–10 | 25–30 | Emboscada (0–25 % según lugar): victoria todo, huida la mitad, derrota nada |
| 🐾 Rastrear | 5 min | Trofeos al ganar | 10 rastros / 18 presa | 75 % presa (combate); encuentra el jefe de misión pendiente |
| 🔪 Desollar (`/skin`) | `skin_seconds` (10–40 s) | Cuero, pieles, carne | Desuello | La pieza se pierde si viajas |

- El temporizador vive en BD (`world_activities.ends_at`). Una tarea de `JobQueue` cada 10 s cierra las vencidas y manda el resultado aunque el jugador esté desconectado. Si hay emboscada, llega el panel de combate.
- Ocupado (`state = busy`): no viaja, caza, investiga, descansa ni hace acciones de misión; sí inventario y pociones. «Abandonar» cancela sin premio.
- El resultado se tira con la semilla de la actividad y se paga una vez (bloqueo + índice único parcial).
- **Tutorial** (`tutorial: true`): la actividad que encaja con el objetivo termina al momento y da lo que falta. **En la beta, siempre durante el tutorial**; fuera de la beta, una vez por misión (`char.flags.tutorial_boosts`).
- Herramientas (Tessa): pico, hacha, hoz, cuchillo de desollar, caña.

| Lugar | Desde | Maestría | Emboscada |
|---|---|---|---|
| Mina del Paso Viejo | Camino del Viejo Rey | Minería | 25 % |
| Arboleda Antigua | Bosque de los Susurros | Tala | 20 % |
| Claro de la Raíz Roja | Bosque de los Susurros | Herboristería | 20 % |
| Ribera de Silverbrook | Camino del Viejo Rey | Pesca | 0 % |
| Bosque de los Susurros | — | Herboristería básica | 15 % |

### Fabricación

- Estaciones: yunque, mesa alquímica, banco de carpintero, curtiembre, banco de joyero, mesa de escriba y banco de ingeniero en el Barrio de Oficios; fogón en La Corona Rota.
- Fabricar es inmediato y atómico: o se gasta todo o nada. Lo no apilable guarda `crafted_by`. Una receta 2+ rangos por debajo da la mitad de XP.
- Guía de cada oficio y afición en `/prof_<clave>` (campo `guide`); `/professions`, `/masteries`, `/hobbies`.
- 26 recetas en `content/recipes.yaml`. Ejemplos: lingote y espada de hierro; poción de curación, poción de maná (también con ala de murciélago) y tónico del reposo; tablones y bastón; cuero curtido y reforzado (CA 12); anillos; tinta, pergamino y pergaminos de dardo de fuego, curar heridas, égida y sueño; pólvora, mecha y bombas de humo, fuego y cegadora; estofado del cazador y ración del pescador.
- Pergaminos y bombas: misma resolución que los conjuros (`engine/combat._cast`), ataque +5, CD 13; cualquier clase los usa.
- Consumibles con `effects` tipados: `restore_hp`, `restore_spell_charge` (elige qué conjuro si hay varios), `short_rest` (20 % PV + 1 uso, enfriamiento 4 h, no quita «herido»).

### Crónicas

Cada actividad termina con una crónica personal de Gemini 3.1 Flash-Lite: 15 al día por jugador (`AI_USER_DAILY_CHRONICLES`), dentro de las 150 llamadas. Después, o si falla, texto genérico de `content/fallbacks/chronicles.yaml` por desenlace y oficio. Se guarda con la actividad; nunca decide botín.

## Decidido

- Dos oficios activos; recolección libre; aficiones sin plaza.
- Las armas fabricadas no superan a las de tienda; el valor está en la interdependencia.

## Próximo

- **MIN-01..04** afinidades a rango 3 (extracción, metalurgia, prospección, excavación) y su extensión a tala, hierbas, desuello, rastreo y pesca.
- **MAS-01..07** cuaderno de campo, maestros, herramientas especializadas y durabilidad, cebos, antifarmeo a partir de rango 3.
- **RECETA-01..07** familias o tiers T1–T3, variantes, calidad corriente/cuidada, lotes, reforja.
- **OFI-01..12** sastrería, encantamiento, arqueología y cartografía (aficiones candidatas), juegos de taberna, primeros auxilios.
- Persistir la versión de tabla al iniciar una actividad (hoy `claim` lee el contenido vigente).
- Balance de la bomba de fuego (da a toda una fila) con datos de la beta.
- Vetas finitas, clima y fauna que cambian qué sale. Ninguno antes de datos de la beta.

## Preguntas abiertas

- ¿Compensan las expediciones largas sin anular la de 5 minutos?
- ¿15 crónicas al día son muchas o pocas? Medir el coste en `artifacts/ai/`.
- ¿Afinidad única, varias o árbol? ¿Coste de cambiar?
