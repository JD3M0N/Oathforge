# roadmap.md — fichas cerradas (archivo)

F01, F03 y F04, con todas sus casillas hechas, sacadas de [`roadmap.md`](../roadmap.md) §4.

<a id="F01"></a>
### F01 · Interfaz Telegram y accesibilidad

**Referencias:** [TODO L62](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L62) · [TODO L63](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L63) · [TODO L64](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L64) · [TODO L66](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L66) · [TODO L68](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L68) · [TODO L69](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L69) · [TODO L70](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L70).

**Implementado:** Teclado fijo, escenas, menús de combate y mapa que ya se editan en determinados flujos.

**Diseño por cerrar:** Qué permanece en el teclado fijo, cuántas acciones caben por pantalla y cuándo una notificación merece mensaje nuevo.

**Propuesta base 0.10:**

- [x] Añadir «Oficios / Trades» como acceso a maestrías, profesiones y aficiones, sin eliminar sus consultas directas (0.10.0: botón 🛠️ Oficios en Héroe y en Actividades, con sus pestañas).
- [x] Añadir «Actividades / Activities» contextual, con requisitos, duración y motivo de bloqueo (0.10.0: en el teclado fijo y en la escena; sin herramienta, botón a la tienda que la vende).
- [x] Unificar volver/cancelar, tiradas traducidas, leyenda de competencias, singular/plural y artículos (0.10.0: Volver de cada vista a su madre; 0.10.1: tiradas con bono y veredicto, leyenda en `/sheet`, `_one` automático y artículo por lugar).
- [x] Editar paneles de estado; preservar hitos y recompensas como mensajes recuperables. Tratar mensajes eliminados y callbacks caducados (0.10.0: la navegación edita; cada acción deja un mensaje con su resultado y los botones, y el viejo pierde los suyos; rechazos y menús viejos en ventanita).

**Flujo de jugador:** Lugar → Actividades → Minar → «Necesitas un pico / Pickaxe required» → tienda pertinente.

**Dependencias y riesgos:** F08 y F15 aportan reglas y opciones. Un botón no puede prometer una acción que el servicio rechazará por otra regla.

**Se considera terminado cuando:** Un tester encuentra su siguiente acción sin memorizar comandos; ES/EN muestran las mismas opciones; un botón viejo no gasta nada.

**Estado (0.10.2):** base entregada en 0.10.0–0.10.2 (Actividades, Oficios, un mensaje por acción, ventanitas, textos claros, inventario por pestañas e iconos). Falta validarla con los testers.

**Archivos a revisar/actualizar:** [planning/facies.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/facies.md), [oathforge/bot/keyboards.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/bot/keyboards.py), [oathforge/bot/render.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/bot/render.py), [oathforge/bot/handlers/callbacks.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/bot/handlers/callbacks.py).

**Ampliación o frontera 0.11:** Paneles de grupo y /party en 0.11. Mini App fuera de este alcance.

<a id="F03"></a>
### F03 · Diario, estadísticas y reglamento

**Referencias:** [TODO L17](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L17) · [TODO L62](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L62) · [TODO L63](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L63).

**Implementado:** Diario con misiones, registro, bestiario, rumores y estadísticas; rulebook parametrizado.

**Diseño por cerrar:** Qué merece una entrada duradera y cómo mostrar cambios sin convertir el diario en una copia del chat.

**Propuesta base 0.10:**

- [x] Añadir acceso a logros y objetivos de especialización cuando existan (0.10.7: pestaña 🏆 Logros en el diario y objetivos seguidos en la portada; las especializaciones aún no existen).
- [x] Generar cifras de reglas desde los datos del motor; corregir menciones a maná cuando se trata de usos (0.10.7: descanso, huida, creación, derrota, desuello, CD y emboscada desde el motor, frases de beta según el flag y una prueba que exige valor para cada marcador; el reglamento ya decía «usos»).
- [x] Definir estadísticas verificables por eventos: victorias, fabricación, descubrimientos y entregas (0.10.7: contadas desde `hero_facts`; las entregas llegarán con F12).
- [x] Paginar el historial y permitir continuar la actividad o misión actual (0.10.7: Crónica de 8 en 8 con ◀ ▶; la portada 📖 Ahora continúa actividad, viaje y objetivo de misión con un toque).

**Flujo de jugador:** Diario → Misiones → «Lista para entregar» → Ir a Vale; Diario → Estadísticas → progreso comprobado.

**Dependencias y riesgos:** F04/F12/F19; las estadísticas antiguas no sustituyen un registro exacto para conceder premios.

**Se considera terminado cuando:** Ficha, reglamento y combate no discrepan en costes o duración; abrir consultas no consume IA.

**Archivos a revisar/actualizar:** [planning/facies.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/facies.md), [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [content/rulebook.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/rulebook.yaml), [oathforge/services/events.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/events.py).

**Estado (0.10.7):** entregada. El diario pasa a siete pestañas con la portada «Ahora» y la Crónica desde `hero_facts`; el reglamento lee el motor. Falta validarlo con los testers; el resumen narrado sigue siendo ampliación.

**Ampliación o frontera 0.11:** Resumen narrativo del diario solo desde eventos y bajo cuota; no es obligatorio para consultar progreso.

<a id="F04"></a>
### F04 · Logros y títulos

**Referencias:** [TODO L41](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L41).

**Implementado (0.9.0):** 30 logros y 2 metalogros por personaje, 4 títulos, destacados, objetivos seguidos, `/achievements`, eventos idempotentes, anuncios privados recuperables y backfill retroactivo. Lo que sigue describe el plan original; en 0.10 se **audita** y se conecta con lo nuevo, no se rehace.

**Diseño por cerrar:** Logros por personaje, retroactividad, secretos y recompensa. Recomiendo principalmente títulos/cosméticos, sin ventajas permanentes acumulativas.

**Propuesta base 0.10 (auditar lo entregado):**

- [x] Crear definiciones de logro con ID estable (0.9.0), condición determinista y textos ES/EN.
- [x] Colección inicial (0.9.0 entregó 30, más que los 12 propuestos): exploración, combate, bestiario, fabricación, aficiones y misiones; evitar premiar spam de mensajes.
- [x] Conceder cada logro una vez con unicidad por personaje y logro; separar desbloqueo de notificación (0.9.0).
- [x] Reconstruir únicamente logros demostrables con datos existentes (0.9.0, `oath achievements-backfill`).
- [x] Añadir logros de lo que 0.10 estrene (entrega de misiones, juramento, especializaciones, cofre) sin romper la unicidad ni el backfill (0.10.8: cuatro logros nuevos sobre lo que ya existe —nivel 5 con título, rango 2 de oficio y dos ocultos— en la misma edición `v0_9`, que es la única que el servicio consulta; los de entrega, juramento, cofre y especialización llegarán con F12/F17/F08/F19, y a sus servicios solo les falta emitir el hecho).

**Flujo de jugador:** Derrotas al Viejo Colmillo → «Logro: Un colmillo menos / One Tusk Less» → ver título en Diario.

**Dependencias y riesgos:** F20 aporta identidad de operación/evento. Añadido al TODO: reglas de retroactividad y concesión única, no descritas allí.

**Se considera terminado cuando:** Replay de la victoria no duplica título ni premio; ES/EN cambian el texto, no el ID.

**Archivos a revisar/actualizar:** [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [oathforge/services/events.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/events.py), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py), [oathforge/services/bestiary.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/bestiary.py).

**Estado (0.10.8):** auditada. Arreglado: las actividades perdidas no cuentan, el nivel real de cada desafío, la clave «-» y el `outside` del backfill (0.10.7). Un solo nombre, «Logros», y el título visible en `/sheet`, en el Libro del Héroe y como dato para la IA.

**Ampliación o frontera 0.11:** Logros de grupo/gremio/PvP en 0.11; ningún logro individual exige amigos.
