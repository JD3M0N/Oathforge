# Profesiones, recolección y crónicas

Fuente: el documento de diseño *Profesiones, recolección y mundo productivo* (octubre de 2026, escrito sobre la v0.4.4). Aquí se recoge lo que decidimos de él y en qué se aparta. Los números son una primera hipótesis de balance: hay que probarlos y cambiarlos.

El bucle que buscamos: **ir a una zona → elegir actividad → esperar o arriesgarse → materiales → maestría → fabricar → usar, vender o llevarlo a una aventura.**

## Estado actual

### Tres capas de progresión

- **Nivel del personaje**: combate, atributos y habilidades de clase. No cambia.
- **Maestrías de campo** (v0.6.0): minería, tala, herboristería, desuello y rastreo. Libres para todos, sin plazas, rango 0–5. No son habilidades d20: «Supervivencia» sigue existiendo para las tiradas.
- **Oficios** (v0.6.1, v0.7.0): herrería, alquimia, carpintería, peletería, joyería, escribanía y artificiería; **dos activos** a la vez.
- **Aficiones** (v0.7.0): cocina y pesca. Opcionales y sin plaza: cualquiera las practica y las sube si quiere. Por dentro, la pesca sigue siendo una maestría (`gathering.HOBBIES`) y la cocina un oficio con `hobby: true`; solo cambia cómo se muestran y que no ocupan plaza.

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

### Oficios y recetas (v0.6.1)

- **Dos oficios activos** de siete (las aficiones no cuentan). Se aprenden en el **Barrio de Oficios** (junto al mercado): gratis mientras haya plaza libre; cambiar uno cuesta **25 de oro** y su XP no se pierde.
- Rango de oficio 0–5 con la misma curva que las maestrías. Una receta 2 o más rangos por debajo del tuyo da la mitad de XP.
- **Estaciones**: yunque, mesa alquímica, banco de carpintero, curtiembre, banco de joyero, mesa de escriba y banco de artificiero en el Barrio de Oficios; el fogón de cocina en La Corona Rota.
- **Guía** de cada oficio y afición en `/prof_<clave>` (campo `guide` de `content/professions.yaml`): qué hace, dónde, de qué maestrías salen los materiales y las recetas por rango.
- Cambiar de oficio pide confirmación y el botón muestra el precio.
- **Fabricar** es inmediato y atómico: se comprueba todo y después se gastan los ingredientes, o no se gasta nada. Los objetos no apilables guardan quién los fabricó (`crafted_by`).
- `/professions` muestra oficios y maestrías; en el Barrio de Oficios, los botones para aprender o cambiar. «🔨 Fabricar» lista las recetas de tus oficios en esa estación, con lo que tienes y lo que falta.

| Oficio | Rango 0 | Rango 1+ |
|---|---|---|
| ⚒️ Herrería | Lingote de hierro (3 mena + 1 carbón) | Espada de hierro (2 lingotes + 1 tablón) |
| ⚗️ Alquimia | Poción de curación (2 raíz de sangre + 1 frasco de agua) | Poción de maná, rango 1 (2 hoja de luna + 1 frasco); tónico del reposo, rango 3 (2 musgo + 1 hoja + 1 frasco) |
| 🪚 Carpintería | 2 tablones (3 troncos de roble) | Bastón de roble (2 tablones + 1 fibra) |
| 🧵 Peletería | Cuero curtido (2 cuero de jabalí o 1 piel de lobo) | Cuero reforzado, CA 12 (3 cuero curtido + 1 lingote) |
| 💍 Joyería | Anillo de cobre (2 cobre + 1 carbón) | Anillo con gema, rango 2 (anillo + gema en bruto) |
| 📜 Escribanía | 2 tintas (raíz + carbón), 2 pergaminos (cuero de jabalí), pergamino de dardo de fuego (tinta + pergamino) | Curar heridas y Égida, rango 1 (+ raíz / + hoja de luna); Sueño, rango 2 (2 tintas + pergamino + hoja de luna) |
| 💣 Artificiería | 2 pólvoras (2 carbón + mena de hierro), 2 mechas (2 fibras), bomba de humo (pólvora + mecha + fibra) | Bomba de fuego, rango 1 (2 pólvoras + mecha); bomba cegadora, rango 2 (pólvora + mecha + cobre) |
| 🍲 Cocina (afición) | Estofado del cazador, 1d6+2 PV (2 carne + 1 raíz) | 2 raciones del pescador, 2d4+1 PV (2 peces + 1 raíz) |

Las armas fabricadas no son más fuertes que las de tienda (la espada de hierro pega como la espada larga y se vende mejor); el cuero reforzado da +1 CA sobre el cuero normal. Los ingredientes cruzan oficios: la espada necesita un tablón de carpintería y el cuero reforzado, un lingote de herrería.

### Pergaminos y bombas (v0.7.0)

Los objetos con `combat` (un `ItemCombat`: `spell`, `save`, `heal`, `buff` o `escape`) se usan desde «🎒 Objetos» en el panel de combate, o escribiendo la acción. Usan la misma resolución que los conjuros de clase (`engine/combat._cast`) con números fijos (ataque +5, CD 13), así que cualquier clase los lanza igual. El motor los resuelve primero y después se gasta uno del inventario, en la misma transacción. El combatiente lleva sus consumibles (`Combatant.consumables`) para pintar solo los botones que tienen sentido (la poción, si quedan).

| Objeto | Efecto |
|---|---|
| Pergamino de dardo de fuego | Ataque +5, 2d6 de fuego |
| Pergamino de curar heridas | 2d8+2 PV |
| Pergamino de égida | 2d6+3 PV temporales |
| Pergamino de sueño | Salvación de SAB CD 13 o duerme 2 turnos |
| Bomba de humo | Sales del combate sin tirada |
| Bomba de fuego | Toda la fila: salvación de DES CD 13, 2d6 de fuego (mitad si salva) y ardiendo 2 turnos |
| Bomba cegadora | Salvación de DES CD 13 o aturdido 1 turno |

### Pociones con efectos tipados (v0.6.2)

Los objetos tienen `effects` (`restore_hp`, `restore_spell_charge`, `short_rest`), validados con Pydantic y aplicados en `services/inventory.py`. El campo antiguo `heal` sigue valiendo (es la poción del panel de combate) y fuera del combate cuenta como `restore_hp`.

| Consumible | Efecto | Protección |
|---|---|---|
| Poción de curación | 2d4+2 PV | Respeta el techo de herido (50 % de los PV) |
| Poción de maná (alquimia 1, o Mira) | +1 uso del conjuro más gastado | Solo clases que lanzan conjuros; sin conjuro gastado no se gasta |
| Tónico del reposo (alquimia 3) | 20 % de los PV y +1 uso de cualquier habilidad gastada | Enfriamiento de 4 h; no quita «herido»; si no hace falta, no se gasta |

Oathforge no tiene puntos de maná: los conjuros gastan usos (`Character.resources`). Una reserva de maná de verdad exigiría rediseñar el coste de los conjuros; queda como idea. La posada pasa a llamarse «Descanso largo».

### Lugares nuevos (v0.6.0)

| Lugar | Desde | Maestría | Emboscada | Caza |
|---|---|---|---|---|
| Mina del Paso Viejo (`ironvein_mine`) | Camino del Viejo Rey | Minería (pico) | 25 % | Ratas gigantes, murciélagos (de día y de noche) |
| Arboleda Antigua (`elderwood_grove`) | Bosque de los Susurros | Tala (hacha) | 20 % | Lobos, jabalíes |
| Claro de la Raíz Roja (`redroot_clearing`) | Bosque de los Susurros | Herboristería (hoz) | 20 % | — |
| Ribera de Silverbrook (`silverbrook_bank`) | Camino del Viejo Rey | Pesca (caña) | 0 % | — |
| Bosque de los Susurros | — | Herboristería básica | 15 % | — |

Las herramientas las vende Tessa. Sin la herramienta no se puede trabajar ese recurso.

### Crónicas de expedición (v0.6.0)

- Al terminar una actividad (al recoger, o al acabar el combate de una emboscada o de un rastreo) llega una **crónica**: un párrafo personal con el nombre, la clase y el linaje del héroe, el lugar y lo que pasó.
- La escribe **Gemini 3.1 Flash-Lite** (`GEMINI_MODEL_CHRONICLE`), con un presupuesto propio de **15 al día por jugador** (`AI_USER_DAILY_CHRONICLES`). También cuenta para las 150 llamadas diarias.
- Cuando se agota (o la IA falla), sale un texto genérico de `content/fallbacks/chronicles.yaml`: 3 variantes por desenlace, en los dos idiomas, elegidas por la semilla de la actividad.
- La crónica se guarda con la actividad: pulsar otra vez no gasta presupuesto. El motor ya ha pagado antes de que la IA escriba nada: la crónica **no decide** botín ni resultados.
- `/sheet` muestra «📜 Crónicas de hoy: 3/15».

## Ideas (siguientes pasos)

- Afinidades a rango 3 (Prospector / Excavador...), durabilidad de herramientas, vetas finitas con regeneración, encargos de NPC, mercado entre jugadores y un tercer oficio como recompensa. **Ninguna antes de tener datos de la beta.**
- Antifarmeo más fino: menos XP en nodos de nivel bajo a partir de rango 3 y por repetir el mismo contexto.
- Clima y fauna que cambian qué sale (peces de noche, alfas raros).
- Métricas: recursos y XP por minuto en cada modo, porcentaje de expediciones emboscadas y su resultado, tiempo hasta rango 3.

## Preguntas abiertas

- ¿Las expediciones largas compensan? Objetivo: que sean algo mejores de media, sin que la de 5 minutos deje de tener sentido.
- ¿15 crónicas con IA al día son muchas o pocas? Medir en `artifacts/ai/` el coste real de Flash-Lite.
- ¿Hace falta notificación también para el combate pendiente, o basta con el aviso de «terminado»?
