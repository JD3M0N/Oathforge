# Opificia — actividades, maestrías, oficios y recetas

Resumen de [Possibilium §15–16](Possibilium.md#s15). El bucle: **zona → actividad → esperar o arriesgarse → materiales → maestría → fabricar → usar, vender o llevarlo a una aventura.** Los números son hipótesis de balance.

## Estado actual (0.10.8)

### Tres capas de progresión

- **Nivel del personaje**: combate, atributos y habilidades de clase.
- **Maestrías de campo**: minería, tala, herboristería, desuello y rastreo. Libres, sin plaza, rango 0–5 (XP 0/80/240/500/900/1500). Cada rango: +4 % de unidad extra (tope 20 %, sin XP) y abre recursos con `min_rank` (cobre a 1, gemas y musgo del reposo a 3). No son habilidades d20.
- **Oficios**: herrería, alquimia, carpintería, peletería, joyería, escribanía e ingeniería; **dos activos**. Se aprenden en el Barrio de Oficios (cualquier lugar con `guild: true`, con un botón: todavía no hay maestros); cambiar uno cuesta 25 de oro (pide confirmación) y su XP no se pierde.
- **Aficiones**: cocina y pesca, sin plaza (`hobby: true` en `professions.yaml`; la pesca con `practice: fishing`, sin estación). Su XP vive con la de los oficios.

Dos cosas que conviene saber antes de tocar nada: las maestrías no están en el contenido, sino fijas en `engine/gathering.py` (con los iconos en `render.py` y la lista de crónicas en `schemas.py`), y la estación de una receta sale de su **oficio**, no de la receta.

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

El contrato completo de F15 está en [roadmap-profesiones.md](roadmap-profesiones.md) (decisiones D01–D25, fases y notas). En resumen:

- Dos oficios activos; recolección libre; aficiones sin plaza. **Sastrería** es ya el octavo oficio (telar de Hedda) y sí ocupa plaza.
- El **refinado básico pertenece a la maestría**: menas → lingotes en el horno (XP de Minería), troncos → tablones en el aserradero (Tala), pieles → cuero en el secadero (Desuello), plantas → fibra limpia en la mesa de preparación (Herboristería). Las cuatro estaciones están en el Gremio y no hace falta oficio para usarlas.
- **Dos ramas por maestría y por Pesca**, a rango 2, con una sola activa; cambiar cuesta oro en el Gremio y la rama anterior queda pausada, no borrada.
- **T0 = recetas de rango 0–2, T1 = rango 3–5.** El equipo de combate T1 se fabrica y se vende, y pide nivel 10 para equiparse.
- **Herramientas especializadas** con tres diseños (rápido, selectivo, productivo), una seleccionada por disciplina y sin desgaste. Los bonos de raro son relativos (10 % → 10,5 %) y la unidad extra se tira una vez por actividad.
- **Técnicas** comunes automáticas al subir de rango; **planos** individuales para las recetas especiales, que se gastan una sola vez.
- La **calle de los oficios** se refactoriza en ocho puestos, cada uno un lugar con su estación y su maestro; cada oficio se aprende con su maestro. El **Gremio de Aventureros** tiene refinado, especializaciones, fogón y la habitación con cama y cofre.
- Las armas fabricadas no superan al botín de su tramo: son equivalentes con utilidades distintas.

## Próximo

- Las **fases 1–10 de F15** (§11 del contrato), una por parche 0.10.x.
- Balance de la bomba de fuego (da a toda una fila) con datos de la beta.
- Lo que sigue futuro: afinidades como árbol, durabilidad, cebos, antifarmeo, variantes y reciclaje de recetas, aficiones nuevas (arqueología, cartografía, juegos de taberna, primeros auxilios), encantamiento, vetas finitas, clima y fauna. Está en las notas N01–N13 del contrato.

## Preguntas abiertas

- ¿Compensan las expediciones largas sin anular la de 5 minutos?
- ¿15 crónicas al día son muchas o pocas? Medir el coste en `artifacts/ai/`.
- ¿Cuánto cuesta cambiar de rama y cuántos espacios tiene el cofre? Valores semilla en el contrato, pendientes de balance (N11).
