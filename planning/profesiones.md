# Profesiones, recolección y crónicas

Fuente: el documento de diseño *Profesiones, recolección y mundo productivo* (octubre de 2026, escrito sobre la v0.4.4). Aquí se recoge lo que decidimos de él y en qué se aparta. Los números son una primera hipótesis de balance: hay que probarlos y cambiarlos.

El bucle que buscamos: **ir a una zona → elegir actividad → esperar o arriesgarse → materiales → maestría → fabricar → usar, vender o llevarlo a una aventura.**

## Estado actual

### Tres capas de progresión

- **Nivel del personaje**: combate, atributos y habilidades de clase. No cambia.
- **Maestrías de campo** (v0.6.0): minería, tala, herboristería, desuello, pesca y rastreo. Libres para todos, sin plazas, rango 0–5. No son habilidades d20: «Supervivencia» sigue existiendo para las tiradas.
- **Oficios** (v0.6.1): herrería, alquimia, carpintería, peletería, cocina y joyería; **dos activos** a la vez.

### Actividades de campo (v0.6.0)

| Actividad | Espera | Botín | XP de maestría | Riesgo |
|---|---|---|---|---|
| ⛏️ **Trabajar** (minar, talar, recolectar, pescar) | 5 min | 2–3 unidades | 10 | Ninguno |
| 🏕️ **Expedición larga** | 15 min | 8–10 unidades | 25–30 | Emboscada al final (0–25 % según el lugar) |
| 🐾 **Rastrear** | 5 min | Trofeos al ganar | 10 si solo hay rastros, 18 si ganas | 75 % presa (combate normal) |

- El temporizador vive en la base de datos (`world_activities.ends_at`), nunca en memoria: un reinicio del bot no pierde nada. Un aviso «⏰ Tu tarea ha terminado» llega por la `job_queue` (si el bot se reinicia, ese aviso se pierde, la tarea no).
- Mientras dura, el personaje está **ocupado** (`state = busy`): no puede viajar, cazar, investigar, descansar ni hacer acciones de misión. Sí puede mirar el inventario y usar pociones. «Abandonar» cancela sin premio.
- **Recoger** tira el resultado con la semilla de la actividad, lo guarda y lo paga una sola vez (bloqueo de fila + índice único parcial: una actividad abierta por personaje).
- **Emboscada en la expedición larga**: el botín queda pendiente y empieza un combate normal. Victoria: todo; huida: la mitad; derrota: nada (más la penalización de siempre). Nunca hay combate sin que el jugador esté delante: la emboscada salta al pulsar «Recoger».
- **Rastrear** se añade a «Cazar», no lo sustituye: la cadena de misiones pide 3 jabalíes y 4 murciélagos, y 5 minutos por presa la haría lentísima. Rastrear da XP de rastreo y una segunda tanda de desuello como trofeos. Si hay un jefe de misión pendiente (el Viejo Colmillo), el rastreo lo encuentra seguro.
- **Desuello automático** tras cualquier victoria contra bestias con `harvest` (jabalí, lobo, Viejo Colmillo), si llevas cuchillo de desollar. Da XP de desuello.
- Rango de maestría: XP acumulada 0 / 80 / 240 / 500 / 900 / 1500. Cada rango suma un 4 % de probabilidad de unidad extra (tope del 20 %, que no da XP) y abre recursos con `min_rank` (cobre a rango 1, gemas a rango 3...).

### Lugares nuevos (v0.6.0)

| Lugar | Desde | Maestría | Emboscada | Caza |
|---|---|---|---|---|
| Mina del Paso Viejo (`ironvein_mine`) | Camino del Viejo Rey | Minería (pico) | 25 % | Ratas gigantes, murciélagos |
| Arboleda Antigua (`elderwood_grove`) | Bosque de los Susurros | Tala (hacha) | 20 % | Lobos, jabalíes |
| Claro de la Raíz Roja (`redroot_clearing`) | Bosque de los Susurros | Herboristería (hoz) | 20 % | — |
| Ribera de Silverbrook (`silverbrook_bank`) | Camino del Viejo Rey | Pesca (caña) | 0 % | — |
| Bosque de los Susurros | — | Herboristería básica | 15 % | — |

Las herramientas las vende Tessa. Sin la herramienta no se puede trabajar ese recurso.

### Crónicas de expedición (v0.6.0)

- Al terminar una actividad (al recoger, o al acabar el combate de una emboscada o de un rastreo) llega una **crónica**: un párrafo personal con el nombre, la clase y el linaje del héroe, el lugar y lo que pasó.
- La escribe **Gemini 3.1 Flash-Lite** (`GEMINI_MODEL_CHRONICLE`), con un presupuesto propio de **15 al día por jugador** (`AI_USER_DAILY_CHRONICLES`). También cuenta para las 150 llamadas diarias.
- Cuando se agota (o la IA falla), sale un texto genérico de `content/chronicles.yaml`: 3 variantes por desenlace, en los dos idiomas, elegidas por la semilla de la actividad.
- La crónica se guarda con la actividad: pulsar otra vez no gasta presupuesto. El motor ya ha pagado antes de que la IA escriba nada: la crónica **no decide** botín ni resultados.
- `/sheet` muestra «📜 Crónicas de hoy: 3/15».

## Ideas (siguientes pasos)

- **v0.6.1, oficios**: dos plazas, cambio en el Barrio de Oficios por 25 de oro sin perder XP, unas 12 recetas, estaciones (yunque, mesa alquímica, banco de carpintero, curtiembre, banco de joyero, fogón de la taberna).
- **v0.6.2, pociones con efectos tipados**: vida (como ahora), maná (+1 uso de un conjuro gastado) y reposo breve (20 % de PV y +1 uso, enfriamiento de 4 h).
- Afinidades a rango 3 (Prospector / Excavador...), durabilidad de herramientas, vetas finitas con regeneración, encargos de NPC, mercado entre jugadores y un tercer oficio como recompensa. **Ninguna antes de tener datos de la beta.**
- Antifarmeo más fino: menos XP en nodos de nivel bajo a partir de rango 3 y por repetir el mismo contexto.
- Clima y fauna que cambian qué sale (peces de noche, alfas raros).
- Métricas: recursos y XP por minuto en cada modo, porcentaje de expediciones emboscadas y su resultado, tiempo hasta rango 3.

## Preguntas abiertas

- ¿Las expediciones largas compensan? Objetivo: que sean algo mejores de media, sin que la de 5 minutos deje de tener sentido.
- ¿15 crónicas con IA al día son muchas o pocas? Medir en `artifacts/ai/` el coste real de Flash-Lite.
- ¿Hace falta notificación también para el combate pendiente, o basta con el aviso de «terminado»?
