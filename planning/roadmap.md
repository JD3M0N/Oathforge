# Oathforge — Roadmap 0.10: consolidación antes del multijugador

**Base auditada:** `main`, versión **0.8.6**, commit `36e967b2be88dceed3e1fe2af23417fe5d0ae7a4`, revisión del 18 de octubre de 2026 UTC (17 de octubre en La Habana). Las referencias `TODO L…` y los enlaces a archivos apuntan a ese commit.
**Base actual:** `main` en **0.9.1** (logros, títulos e identidad del héroe; esta hoja de ruta). La consolidación se publica como **0.10.x** desde 0.10.0. Ver [Cambios desde la auditoría](#actualizacion).
**Estado:** hoja de ruta adoptada como dirección de trabajo: **0.10 = consolidación** y **0.11 = multijugador**. Cifras, alcance concreto y alternativas siguen siendo propuesta hasta cerrar cada hito; nada marcado `[ ]` está implementado. La decisión del usuario es dedicar **0.10 a una gran revisión integral** y **0.11 al multijugador**. El alcance concreto, cifras y alternativas recomendadas aquí requieren aprobación; no se presentan como funciones ya implementadas.

> Objetivo de 0.10: que crear un héroe, explorar Crownreach, combatir, conversar, realizar actividades, fabricar, completar misiones y especializarse forme una experiencia individual coherente y recuperable. La 0.11 debe añadir la interacción entre jugadores sobre esa base.

## Índice

0. [Cambios desde la auditoría y trabajo versión a versión](#actualizacion)
1. [Base real y discrepancias](#base)
2. [Alcance y decisiones de versión](#alcance)
3. [Orden de menor a mayor dificultad](#orden)
4. [Fichas de los 20 sistemas](#fichas)
5. [Secuencia de implementación](#fases)
6. [Puerta de salida de 0.10](#salida)
7. [Frontera y plan de 0.11](#multiplayer)
8. [Cobertura completa de TODO.md](#trazabilidad)
9. [Documentación y decisiones pendientes](#documentacion)
10. [Fuentes y límites de revisión](#fuentes)

<a id="actualizacion"></a>
## 0. Cambios desde la auditoría y trabajo versión a versión

### Qué cambió desde la 0.8.6

La auditoría se hizo sobre 0.8.6. Después salió la **0.9.0** ([CHANGELOG](../CHANGELOG.md), [releases/0.9.0.md](releases/0.9.0.md)). Efecto en este roadmap:

| Ficha | Efecto de la 0.9.0 |
|---|---|
| F04 Logros y títulos | **Entregada** (30 logros, 2 metalogros, 4 títulos, destacados, objetivos seguidos, `/achievements`, backfill retroactivo). En 0.10 solo se **audita** y se conecta con lo nuevo (entrega de misiones, juramento, especializaciones). No se rehace. |
| F03 Diario | El acceso a logros ya existe; queda el resto de la ficha. |
| F20 IA y operación | 0.9.0 aportó eventos mecánicos idempotentes y anuncios privados recuperables tras fallos. No cubre la reserva atómica de IA ni la idempotencia del texto libre (CORE-01..03, AI-01..02 siguen pendientes). |
| Versiones | El cooperativo ya no es 0.9 ni «sin versión»: pasa a **0.11**. Las especializaciones (antes 0.10) y los encargos (antes 0.11) quedan absorbidos por 0.10 (consolidación) y 0.11.x (compartido). |

Donde las fichas digan «0.8.6» como punto de partida, léase «0.9.0»; donde F04 pida crear logros, léase «auditar lo entregado».

### Cómo se trabaja: versión a versión

La serie 0.9 ya está publicada: **0.9.0** trajo los logros y **0.9.1** este documento. La consolidación ya no se numera como parches 0.9.x: **toda la 0.10 es la consolidación**, y empieza por la interfaz (F01), que es lo que más notan los jugadores. Numeración, de acuerdo con `AGENTS.md`:

- **0.10.0**: abre la consolidación con la primera entrega grande de F01 (navegación y mensajes). Es una versión menor porque cambia cómo se juega en Telegram.
- **0.10.x** (parches): cada hito A…H se publica en uno o varios parches, cada uno con una experiencia comprobable, su CHANGELOG y su ficha cerrada (plantilla de la sección 9).
- **Puerta de salida**: la supera el último parche 0.10.x (hito H). No lleva un número especial; lo que cambia es que después empieza la 0.11.
- **0.11.0** y siguientes: multijugador (sección 7).

| Hito | Versión orientativa | Primer incremento sugerido |
|---|---|---|
| 0.10-B · Orientar al jugador (F01) | **0.10.0 – 0.10.2** | 0.10.0 navegación y mensajes (teclado con ⚒ Actividades, escena social, un mensaje por acción, rechazos en ventanita); 0.10.1 textos claros (tiradas, leyenda de `/sheet`, artículos, singular); 0.10.2 inventario por pestañas y emojis de materiales |
| 0.10-A · Acordar y asegurar | 0.10.3 | Idempotencia del texto libre y reserva atómica de IA (CORE-01..03, AI-01..02); prueba de 1.000 repeticiones |
| 0.10-B · Orientar al jugador (resto) | **0.10.7** (F03) y 0.10.8 | 0.10.7 F03: diario por pestañas, Crónica del héroe, estadísticas verificables y reglamento desde el motor; después la corrección crítica de F11: confianza determinista y servicios de Bram |
| 0.10-C · Bucles cotidianos | 0.10.5 – 0.10.6 | Descanso corto y `/rest`; cofre personal; «Algo brilla» |
| 0.10-D · Dar propósito | 0.10.7 | Entrega de misiones al dador; juramento verificable; auditoría de logros |
| 0.10-E · Reglas de combate | 0.10.8 | Contrato de acción, estados y jefe de dos fases; matriz de ocho clases |
| 0.10-F · Profundizar progresión | 0.10.9 | Auditoría de recetas y economía; primeras ramas de especialización |
| 0.10-G · Integrar | 0.10.10 | Tutorial completo ES/EN, arco de nivel 5, lote visual |
| 0.10-H · Candidato | 0.10.11 | Puerta de salida, migración, restauración y documentación |

La numeración es orientativa: si un hito necesita más parches, se usan. El hito A va después de la primera entrega de F01 porque la interfaz no toca dinero ni IA y los testers la necesitan ya; A sigue siendo requisito antes de cualquier cambio de economía o de texto libre. Al cerrar cada versión: actualizar el **Estado actual** del resumen latino afectado, `tests/features.md` y `planning/iter.md`, y marcar aquí las casillas hechas con la versión (`[x] … (0.10.0)`).

### Anuncios

Cada versión se anuncia en los canales con el formato habitual y deja su borrador en `planning/releases/<versión>.md`, como hizo la 0.9.0. El de la preparación de 0.10 está en [releases/0.9.1.md](releases/0.9.1.md).

<a id="base"></a>
## 1. Base real y discrepancias

La revisión combina documentos, inventario YAML y lectura dirigida de los puntos de resolución. «Implementado» significa presente en los archivos; no significa validado en producción durante esta revisión.

| Área | Base encontrada | Consecuencia para 0.10 |
|---|---|---|
| Clases | 8 clases y habilidades de nivel 1–5 | Revisar identidad, recursos y balance; no empezar el catálogo de cero |
| Especializaciones | 32 nombres y campo de personaje; sin selección jugable | Construir comportamiento y desbloqueo, no solo un menú |
| Personaje | 4 linajes, 12 trasfondos predefinidos y opción propia; compra de 27 puntos | Revisar creación, competencias y progresión sin romper personajes |
| Mundo | 17 archivos `place.yaml`, ciudad, tierras salvajes y cripta | Completar usos de lugares existentes antes de otra región |
| Viajes | Ruta directa entre lugares conocidos, una emboscada y continuación | Conservar la comodidad de 0.8.0 |
| Criaturas | 10 monstruos; bestiario e ilustraciones | Mejorar roles, descubrimiento y encuentros, no contar variantes como profundidad |
| Misiones | 12 entradas: 10 tutoriales y 2 aventuras posteriores | Cerrar entrega al PNJ y contenido a nivel máximo |
| Oficios | 7 oficios con 2 plazas y 2 aficiones sin plaza | Profundizar sus bucles y evitar dependencias que exijan otros jugadores |
| Recetas | 26 recetas | Auditar utilidad, materiales, margen y consumibles de combate |
| Actividades | Temporizador persistido, cierre automático, rastreo, desuello y crónicas | Reforzar recuperación y reglas; no reintroducir «Recoger» |
| PNJ | 6 entradas; horarios, tiendas, memoria y confianza | Corregir coherencia y autoridad antes de ampliar el reparto |
| Combate | Motor d20, filas, estados, recursos, objetos, informes | Consolidar contratos antes de especializaciones |
| Multiplayer | Tablas preparatorias; encuentro creado con `p1` y sincronización individual | Tener tablas no equivale a tener cooperativo |

### Discrepancias que afectan al plan

1. **Versiones:** `planning/iter.md` asigna cooperativo a 0.9, especializaciones a 0.10 y encargos a 0.11. Esta hoja de ruta adopta la distribución decidida: consolidación en 0.10 y sistemas compartidos en 0.11. La 0.9.0 (logros) ya está publicada; ver la [sección 0](#actualizacion).
2. **Confianza:** la regla de oro afirma que la IA no decide resultados, pero `services/actions.py::talk` aplica `reply.trust_delta`. Debe pasar a reglas verificables del servicio. La memoria textual propuesta por IA también necesita distinguir declaraciones de hechos.
3. **Misiones:** `quests.advance` aplica recompensas al completar objetivos. No existe todavía el flujo general «lista para entregar → hablar con el dador → cobrar». La checklist manual no demuestra que ese sistema esté implementado.
4. **Presupuesto:** `Budget.allow` consulta uso y `Budget.record` lo suma después. Falta una reserva atómica que impida que varias llamadas consuman simultáneamente el último cupo; no es equivalente a carecer de límites diarios.
5. **Especializaciones antes de cooperativo:** el ticket histórico SPEC-01 depende de COOP-04. Replantearlo: el catálogo efectivo y sus objetivos tipados se construyen en 0.10; seleccionar aliados humanos y sincronizarlos se completa en 0.11. Ninguna rama debe depender exclusivamente de un aliado inexistente para funcionar en solitario.
6. **Beta y economía:** pociones a 1 de oro, curación gratuita y descanso instantáneo son ayudas de beta. No prueban que los precios y tiempos definitivos sean sostenibles.
7. **TODO desactualizado:** la recuperación de Gemini sigue descrita como «sin reintentos» y pausa de 2 minutos; 0.7.29 introdujo cooldown corto y reintento selectivo. La documentación de respaldos también difiere en número de variantes. Auditar las claves concretas antes de marcar trabajo como pendiente o terminado.
8. **Dados:** comprobar tiradas d20 y dados de daño no significa prohibir toda selección aleatoria. Encuentros ponderados, botín y elección de texto usan RNG; separar azar mecánico de selección cosmética y asegurar reproducibilidad del primero.
9. **Trabajo de testers:** sus archivos están prácticamente vacíos; no hay resultados suficientes para afirmar que el tutorial o la economía están validados. Sus instrucciones de edición además difieren de `CLAUDE.md`; unificar el flujo vigente.

<a id="alcance"></a>
## 2. Alcance y decisiones de versión

**Decisión del usuario:** 0.10 grande; 0.11 centrada en multijugador. **Recomendación:** interpretar «todo» como revisar cada sistema y cerrar su primera versión coherente, no implementar todas las ideas de Possibilium.

- **Base 0.10:** interfaz, reglas, progresión, logros, inventario, recuperación, actividades, mapa, monstruos, PNJ, misiones, tutorial, clases, oficios, economía, combate, especializaciones, IA y confiabilidad.
- **Ampliación 0.10:** variantes de ramas, aficiones nuevas, más activos, peso de presas y expediciones con estilos. Solo entran al cerrar la base.
- **0.11:** grupos, combate y misiones cooperativas, botín por participante, ausencias, comercio entre jugadores; después gremios, duelos y eventos comunitarios dentro del ciclo 0.11.x.
- **Posterior:** segunda región, sistemas políticos completos, temporadas, Mini App, todas las 32 ramas y expansión amplia de clases.

Las cantidades sugeridas son límites iniciales de trabajo, no compromisos aprobados. No fijar fechas sin medir capacidad del equipo. Usar hitos `0.10-A…H` para planificar y publicarlos como parches 0.10.x (sección 0); la puerta de salida la supera el último 0.10.x, y después empieza 0.11.

### Reglas que atraviesan todos los sistemas

Motor determinista; escrituras únicamente en servicios; contenido validado; interfaz y contenido ES/EN; Gemini como proveedor; E/S externa fuera de locks; idempotencia; conservación de personajes; migraciones cuando corresponda. Sin reescritura del monolito ni microservicios por anticipación.

<a id="orden"></a>
## 3. Orden de menor a mayor dificultad

Escala relativa: **1** localizado, **2** pocos sistemas, **3** persistencia y dependencias, **4** varias reglas y balance, **5** transversal y alto riesgo. D = dificultad de diseño; R = dificultad de refactor/implementación. El orden estima el alcance mínimo de cada ficha, no todas sus ampliaciones. Las posiciones cercanas pueden intercambiarse.

| Orden | Sistema | D | R | Qué lo hace difícil |
|---|---|---:|---:|---|
| 01 | Interfaz Telegram y accesibilidad | 2 | 2 | Claridad, navegación y mensajes viejos |
| 02 | Audiovisual y presentación | 2 | 2 | Consistencia y producción de activos |
| 03 | Diario, estadísticas y reglamento | 2 | 2 | Reflejar reglas reales sin duplicarlas |
| 04 | Logros y títulos | 2 | 3 | Reconocer hechos y premiar una sola vez |
| 05 | Creación, linajes, trasfondos y progresión | 3 | 3 | Compatibilidad y ritmo de XP |
| 06 | Inventario, equipo y almacenamiento | 3 | 3 | Bonos, movimientos de objetos y economía |
| 07 | Descanso, derrota y recuperación | 3 | 3 | Coste, tiempo y evitar bloqueos |
| 08 | Actividades de campo | 3 | 3 | Temporizadores, interrupciones y reinicios |
| 09 | Monstruos, caza y bestiario | 3 | 3 | Encuentros justos para todas las clases |
| 10 | Mapa, movimiento y exploración | 3 | 3 | Rutas, descubrimiento y objetivos móviles |
| 11 | PNJ, diálogo y confianza | 4 | 3 | Verdad del mundo frente a narración |
| 12 | Misiones y aventuras individuales | 4 | 4 | Estados, alternativas y pagos |
| 13 | Tutorial y primera sesión | 4 | 3 | Depende de casi toda la experiencia |
| 14 | Clases e identidad jugable | 4 | 4 | Ocho estilos viables en solitario |
| 15 | Profesiones, maestrías y aficiones | 4 | 4 | Recetas, tiempo, recursos y utilidad |
| 16 | Comercio y economía individual | 4 | 4 | Arbitrajes, inflación y costes acumulados |
| 17 | Facciones, juramentos y hechos del mundo | 4 | 4 | Causalidad, privacidad y persistencia |
| 18 | Combate y balance transversal | 5 | 5 | Interacciones entre todas las reglas |
| 19 | Especializaciones | 5 | 5 | Multiplican combinaciones y migraciones |
| 20 | IA, confiabilidad y operación | 5 | 5 | Concurrencia, cuotas y recuperación |

**No implementar siguiendo ciegamente esta tabla.** F20 empieza primero y acompaña todas las fases. El contrato de F18 debe cerrarse antes de programar F14/F19; F13 se diseña pronto y se valida al final. La sección 5 convierte la dificultad en un orden ejecutable.

<a id="fichas"></a>
## 4. Fichas de trabajo por sistema

Cada ficha diferencia lo existente de la propuesta, señala las decisiones que hay que pensar y deja una primera entrega comprobable. Las referencias TODO remiten a líneas del commit auditado; siguen funcionando aunque cambie `main`.

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

<a id="F02"></a>
### F02 · Audiovisual y presentación

**Referencias:** [TODO L45](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L45) · [TODO L46](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L46) · [TODO L47](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L47) · [TODO L48](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L48) · [TODO L49](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L49) · [TODO L50](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L50) · [TODO L51](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L51) · [TODO L52](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L52) · [TODO L53](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L53) · [TODO L54](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L54).

**Implementado:** Catálogo de imágenes, caché de file_id, Crownreach, retratos de clases y bestiario ilustrado.

**Diseño por cerrar:** Estilo visual común; prioridades de lugares y PNJ; distinguir mapa ilustrado y geografía navegable.

**Propuesta base 0.10:**

- [x] Aprobar biblia visual breve antes de producir nuevos lotes (0.10.4: estilo gouache de libro de rol, prompt base y regla de noche en `TODO-images.md`; Crownreach de día y de noche).
- [ ] Primera tanda propuesta: mapa de Crownreach y alrededores, tres lugares prioritarios y un PNJ; añadir linajes progresivamente.
- [x] Completar «Ver lugar» con activos existentes y respaldo cuando falte imagen (0.10.5: botón 🖼️ Ver lugar en cada escena; sin imagen, una ventanita que lo dice).
- [ ] Vincular cada activo con catálogo, prompt y procedencia; reutilizarlo sin generación por turno.

**Flujo de jugador:** Mapa → Ver mapa ilustrado; Lugar → Ver lugar. La imagen no desbloquea caminos.

**Dependencias y riesgos:** F10 fija geografía. Producir 17 lugares de golpe puede consumir más tiempo que integrar el catálogo.

**Se considera terminado cuando:** Los activos corresponden al contenido, se reenvían por caché y una imagen ausente no bloquea el juego.

**Archivos a revisar/actualizar:** [planning/ars.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/ars.md), [oathforge/content/media.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/content/media.py), [oathforge/services/media.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/media.py).

**Ampliación o frontera 0.11:** Audio optativo, voz, stickers y tarjeta compartible son ampliación; ofrecer texto y silencio. No prometer reproducción en bucle controlada por el bot sin validar capacidades del cliente.

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
- [ ] Añadir logros de lo que 0.10 estrene (entrega de misiones, juramento, especializaciones, cofre) sin romper la unicidad ni el backfill.

**Flujo de jugador:** Derrotas al Viejo Colmillo → «Logro: Un colmillo menos / One Tusk Less» → ver título en Diario.

**Dependencias y riesgos:** F20 aporta identidad de operación/evento. Añadido al TODO: reglas de retroactividad y concesión única, no descritas allí.

**Se considera terminado cuando:** Replay de la victoria no duplica título ni premio; ES/EN cambian el texto, no el ID.

**Archivos a revisar/actualizar:** [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [oathforge/services/events.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/events.py), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py), [oathforge/services/bestiary.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/bestiary.py).

**Ampliación o frontera 0.11:** Logros de grupo/gremio/PvP en 0.11; ningún logro individual exige amigos.

<a id="F05"></a>
### F05 · Creación, linajes, trasfondos y progresión

**Referencias:** [TODO L33](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L33) · [TODO L37](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L37) · [TODO L53](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L53).

**Implementado:** Compra de 27 puntos, cuatro linajes, trasfondos y niveles 1–5; mejora automática de atributo al nivel 4.

**Diseño por cerrar:** Ritmo hasta nivel 5, diferencias de linaje, revisión de atributos y si expandir niveles. Recomiendo conservar 1–5 en la base.

**Propuesta base 0.10:**

- [ ] Auditar bonos de linaje y combinaciones con las ocho clases.
- [ ] Explicar atributos y competencias durante creación, con recomendado y revisión antes de confirmar.
- [ ] Medir XP de tutorial, caza y misiones para que nivel 5 no llegue antes de aprender el juego.
- [ ] Definir compensación o revisión gratuita si cambian atributos o rasgos; migrar personajes sin borrar historia.

**Flujo de jugador:** El jugador elige mago y puede revisar el reparto recomendado; al subir sabe qué cambió y por qué.

**Dependencias y riesgos:** F14/F18 y F13; subir el techo sin habilidades, objetos y misiones nuevos solo alarga la barra.

**Se considera terminado cuando:** Creación funciona en ambos idiomas, cada linaje es viable y un personaje existente conserva progreso válido.

**Archivos a revisar/actualizar:** [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [content/lineages.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/lineages.yaml), [content/backgrounds.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/backgrounds.yaml), [oathforge/engine/progression.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/engine/progression.py), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py).

**Ampliación o frontera 0.11:** Dotes, niveles 6–8 y nuevos linajes son ampliación con contenido. El entrenamiento no vuelve a quitar una clase que ya se eligió.

<a id="F06"></a>
### F06 · Inventario, equipo, consumibles y almacén

**Referencias:** [TODO L39](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L39) · [TODO L40](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L40) · [TODO L70](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L70) · [TODO L86](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L86).

**Implementado:** Cuatro ranuras, objetos apilables/no apilables, consumibles tipados y crafted_by para fabricación no apilable.

**Diseño por cerrar:** Número final de ranuras, capacidad de mochila y almacén, acumulación de bonos y protección de objetos de misión.

**Propuesta base 0.10:**

- [ ] Comparar equipo actual/nuevo e identificar material, consumible y objeto de misión. *(0.10.2: el inventario ya separa equipo, consumibles, materiales y herramientas, con un icono por objeto; falta comparar.)*
- [ ] Añadir cofre personal en ciudad con depositar/retirar atómico, cantidades claras y sin copia de objetos.
- [ ] Mostrar procedencia ya disponible; ampliar origen de botín solo cuando se registre realmente.
- [ ] Decidir expansión gradual: primero cuello y anillos si hay objetos útiles; cabeza/manos/pies/capa después de presupuestar sus bonos.

**Flujo de jugador:** Inventario → espada → Comparar → Equipar; Cofre → Guardar 10 menas → mochila y cofre actualizados juntos.

**Dependencias y riesgos:** F16 fija costes y F18 calcula bonos. Más ranuras multiplican poder, recetas y navegación.

**Se considera terminado cuando:** No se duplica la última unidad; equipo y atributos se recalculan; objetos necesarios no desaparecen por una operación ambigua.

**Archivos a revisar/actualizar:** [planning/mercatura.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mercatura.md), [oathforge/services/inventory.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/inventory.py), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py), [content/items.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/items.yaml).

**Ampliación o frontera 0.11:** Intercambios y bancos compartidos en 0.11. No exigir implementar todas las ranuras para cerrar almacén.

<a id="F07"></a>
### F07 · Descanso, derrota y recuperación

**Referencias:** [TODO L36](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L36) · [TODO L61](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L61) · [TODO L87](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L87).

**Implementado:** Descanso largo, osario gratis, curación en capilla, heridas y tónico de descanso corto.

**Diseño por cerrar:** Qué recupera cada descanso, duración real/juego, lugares válidos, precio y política de ayuda sin oro.

**Propuesta base 0.10:**

- [ ] Implementar descanso corto sin poción y /rest, con efectos/cooldown explícitos.
- [ ] Dar a largo, corto, tónico y curación funciones distintas; evitar cadena gratuita infinita de recursos.
- [ ] Resolver coherencia del osario y separar ayudas beta de reglas normales.
- [ ] Conservar una salida de la derrota sin bloqueo económico permanente.

**Flujo de jugador:** Descansar → «Corto: recupera X; no elimina herida / Short: restores X; injury remains» → confirmar.

**Dependencias y riesgos:** F18 define recursos; F16 el coste. No restaurar 80 minutos reales de espera por inercia documental.

**Se considera terminado cuando:** Se sabe antes de confirmar qué se recupera, cuánto tarda y cuesta; reinicio no cobra ni cura dos veces.

**Archivos a revisar/actualizar:** [planning/pugna.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/pugna.md), [oathforge/services/exploration.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/exploration.py), [oathforge/services/activities.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/activities.py), [oathforge/config.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/config.py).

**Ampliación o frontera 0.11:** Reanimación de aliados, descanso de grupo y campamentos compartidos en 0.11.

<a id="F08"></a>
### F08 · Actividades de campo y temporizadores

**Referencias:** [TODO L69](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L69) · [TODO L75](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L75) · [TODO L76](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L76) · [TODO L78](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L78) · [TODO L81](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L81) · [TODO L83](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L83).

**Implementado:** Minar, talar, recolectar, pescar, rastrear y desollar; cierre automático, expedición larga y estado busy.

**Diseño por cerrar:** Tiempo activo frente a espera; cancelar y recuperar; significado de cambiar contenido durante una actividad.

**Propuesta base 0.10:**

- [ ] Mostrar resultado esperado, herramienta, riesgo y tiempo antes de empezar.
- [ ] Persistir versión o instantánea suficiente de tablas/reglas al iniciar; hoy claim lee el contenido vigente.
- [ ] Asegurar cierre/pago único y recuperación de notificaciones tras reinicio.
- [ ] Probar la relación actividad corta/larga y sus desenlaces; preservar aceleración tutorial de forma explícita.
- [ ] Convertir «Algo brilla» en descubrimiento interactivo con recompensa limitada, sin promesa vacía de la narración.

**Flujo de jugador:** Mina → Trabajar → cerrar Telegram → volver y ver materiales/crónica; si hubo emboscada, recuperar ese encuentro.

**Dependencias y riesgos:** F20 y F16. Peso de presas requiere una presa identificable; no generar un peso distinto al mirar y al desollar.

**Se considera terminado cuando:** Cancelar y terminar simultáneamente produce un único desenlace; reinicio y despliegue no cambian arbitrariamente el premio.

**Archivos a revisar/actualizar:** [planning/opificia.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/opificia.md), [oathforge/services/activities.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/activities.py), [oathforge/engine/gathering.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/engine/gathering.py).

**Ampliación o frontera 0.11:** Peso, durabilidad y vetas finitas son ampliaciones. Recolección competitiva compartida pertenece a 0.11 o posterior.

<a id="F09"></a>
### F09 · Monstruos, caza y bestiario

**Referencias:** [TODO L27](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L27) · [TODO L74](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L74) · [TODO L75](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L75) · [TODO L76](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L76) · [TODO L77](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L77).

**Implementado:** Diez criaturas; descubrimiento progresivo al ver, derrotar una vez y tres veces; tablas por nivel/hora.

**Diseño por cerrar:** Rol, contrajuego y recompensa de cada criatura; si tamaño o rareza aporta decisiones.

**Propuesta base 0.10:**

- [ ] Revisar los diez monstruos por zona, nivel, horario y clase vulnerable; no rebalancear solo con Paladín.
- [ ] Crear fichas de rol: hostigador, resistente, controlador y jefe, reutilizando capacidades del motor.
- [ ] Añadir como propuesta inicial dos encuentros distintivos y un jefe con aviso, cuando F18 lo soporte.
- [ ] Permitir descubrir una debilidad mediante habilidad validada; rareza por pesos de tabla, no por improvisación de IA.

**Flujo de jugador:** Investigar rastros → Naturaleza superada → debilidad revelada; enemigo avisa su carga antes del golpe fuerte.

**Dependencias y riesgos:** F18 para tácticas nuevas; F08 para desuello. Evitar un enemigo raro obligatorio que bloquee el tutorial.

**Se considera terminado cuando:** Cada encuentro tiene nivel de acceso coherente, ilustración/catalogación y simulación por clase; pistas del bestiario son verdaderas.

**Archivos a revisar/actualizar:** [planning/bestiarium.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/bestiarium.md), [content/monsters.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/monsters.yaml), [oathforge/services/bestiary.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/bestiary.py), [oathforge/tools/simulate.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/tools/simulate.py).

**Ampliación o frontera 0.11:** Peso/récords pueden esperar; jefes de raid y balance por tamaño del grupo en 0.11.

<a id="F10"></a>
### F10 · Mapa, movimiento, exploración y mazmorras

**Referencias:** [TODO L50](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L50) · [TODO L63](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L63) · [TODO L65](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L65) · [TODO L78](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L78) · [TODO L93](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L93).

**Implementado:** Viaje directo, grafo, Dijkstra, restricciones de descubrimiento, combate fijo bloqueante y 📜 al objetivo.

**Diseño por cerrar:** Distinguir desplazamiento rutinario de expedición; cuándo una interrupción merece decisión.

**Propuesta base 0.10:**

- [ ] Conservar viaje conocido de un toque y una emboscada máxima por viaje con continuación.
- [ ] Revisar cada destino: qué hacer, requisitos, servicios y objetivo de misión.
- [ ] Añadir favoritos y un atajo desbloqueable como primera expansión, sin obligar a seleccionar estilo en cada trayecto.
- [ ] Adaptar 📜 a entrega de misiones, PNJ ausente y nuevos servicios; recuperar o cancelar rutas invalidadas.
- [ ] Auditar salas de cripta, reinicios y flags de despeje; el mapa ilustrado nunca decide accesibilidad.

**Flujo de jugador:** Desde mina → 📜 Entregar a Vale → ruta; si Vale está ausente, indicar alternativa u horario sin inventar presencia.

**Dependencias y riesgos:** F12/F11; los estilos de viaje solo tienen valor si cambian riesgo o hallazgos de manera visible.

**Se considera terminado cuando:** No hay rutas ilegales, revelaciones de lugares secretos ni doble emboscada al seguir; retorno desde cripta sigue siendo sencillo.

**Archivos a revisar/actualizar:** [planning/mundus.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mundus.md), [oathforge/services/world_map.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/world_map.py), [oathforge/services/exploration.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/exploration.py).

**Ampliación o frontera 0.11:** Expediciones con escenas y estilos son ampliación individual; viajar juntos en 0.11. Segunda región posterior.

<a id="F11"></a>
### F11 · PNJ, diálogo, servicios y confianza

**Referencias:** [TODO L15](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L15) · [TODO L19](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L19) · [TODO L22](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L22) · [TODO L23](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L23).

**Implementado:** PNJ con persona, horarios, tiendas, recuerdos, confianza y reputación; la respuesta IA puede aportar trust_delta.

**Diseño por cerrar:** Diferenciar confianza personal, reputación de facción, memoria y servicios disponibles. Preguntar por un fogón no es una ofensa.

**Propuesta base 0.10:**

- [ ] Retirar autoridad de trust_delta: variaciones por acciones y reglas auditables del servicio.
- [ ] Dar al diálogo saludo mostrado, servicios del lugar, estado de misión y límites de conocimiento.
- [ ] Revalidar presencia y contexto tras la respuesta; separar recuerdo de un hecho y lo que el jugador afirma.
- [ ] Ofrecer botones de servicio/entrega y réplicas de respaldo útiles sin Gemini.
- [ ] Definir tabla corta de acciones que cambian confianza, umbrales y límites antifarmeo.

**Flujo de jugador:** «¿Cómo cocino?» → Bram explica el fogón y aparece Cocinar; confianza intacta. Entregar un favor real sí puede aumentarla.

**Dependencias y riesgos:** F12/F17/F20. Corregir solo el prompt no elimina el poder mecánico del modelo.

**Se considera terminado cuando:** Pruebas con respuestas simuladas arbitrarias no conceden confianza; preguntar y repetir saludo no genera premios; misión sigue sin IA.

**Archivos a revisar/actualizar:** [planning/narratio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/narratio.md), [planning/mundus.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mundus.md), [oathforge/services/actions.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/actions.py), [oathforge/services/npcs.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/npcs.py), [oathforge/ai/npc_dialogue.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/ai/npc_dialogue.py), [content/npcs.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/npcs.yaml).

**Ampliación o frontera 0.11:** Memoria en tres capas empieza por separar fuentes; agentes autónomos y horarios simulados complejos no son requisito.

<a id="F12"></a>
### F12 · Misiones, encargos PNJ y aventuras

**Referencias:** [TODO L33](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L33) · [TODO L78](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L78) · [TODO L79](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L79) · [TODO L80](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L80) · [TODO L89](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L89).

**Implementado:** Objetivos y etapas, recompensas, decisiones del relicario y señales de progreso; objetivos completados pueden pagar inmediatamente.

**Diseño por cerrar:** Entrega presencial versus cierre automático justificado; objetos consumidos, fallos, repetibles y quién da el siguiente paso.

**Propuesta base 0.10:**

- [ ] Añadir estado lista_para_entregar para misiones con dador; al entregar validar objetivos, presencia y coste de objetos.
- [ ] Separar alcanzar objetivo, consumir entrega, pagar y desbloquear siguiente misión; todo atómico e idempotente.
- [ ] Migrar partidas en curso sin volver a premiar misiones ya completadas.
- [ ] Primera expansión propuesta: tres encargos PNJ limitados y un arco corto de tres misiones para nivel 5.
- [ ] Añadir una misión con dos soluciones útiles y un fallo que abra alternativa; evitar texto libre como condición arbitraria.

**Flujo de jugador:** Recoges hierro → «Lista para entregar / Ready to turn in» → 📜 Vale → Entregar → consume si corresponde, paga una vez y ofrece siguiente.

**Dependencias y riesgos:** F11/F10/F16/F20. Encargo repetible necesita límite y recompensa que no infle oro. El objeto reservado para misión debe tener política clara.

**Se considera terminado cuando:** Doble entrega no duplica premio; la cadena sigue con PNJ ausente/reinicio; las dos soluciones del arco terminan sin intervención administrativa.

**Archivos a revisar/actualizar:** [planning/mundus.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mundus.md), [content/quests.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/quests.yaml), [oathforge/services/quests.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/quests.py), [oathforge/content/schemas.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/content/schemas.py), [oathforge/database/models.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/database/models.py).

**Ampliación o frontera 0.11:** Misiones compartidas, contribución colectiva y custodia entre jugadores en 0.11; el arco nivel 5 no implica subir techo.

<a id="F13"></a>
### F13 · Tutorial y primera sesión

**Referencias:** [TODO L32](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L32) · [TODO L33](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L33).

**Implementado:** Diez misiones sin cripta, jefe Viejo Colmillo, ayudas beta y tutorial-stats.

**Diseño por cerrar:** Lo indispensable para empezar frente a aprendizaje opcional; objetivo de duración a validar con testers.

**Propuesta base 0.10:**

- [ ] Revisar cada paso con interfaz, entrega de misiones y descanso nuevos; una enseñanza principal por paso.
- [ ] Dar ayudas contextuales y ruta al siguiente objetivo sin exponer todos los sistemas a la vez.
- [ ] Medir finalización, duración, reintentos y bloqueos con distintas clases e idiomas.
- [ ] Conservar protección frente a gastar/vender materiales necesarios; diseñar recuperación si sucede.
- [ ] Dejar campamento por clase como módulo opcional posterior, sin retrasar creación ni especialización.

**Flujo de jugador:** Vale enseña a hablar y mirar; cazar enseña ataque/desuello; el jefe comprueba lo aprendido y abre la aventura de cripta.

**Dependencias y riesgos:** F01/F07/F08/F10/F11/F12/F14/F18. No acortar artificialmente la experiencia sin medir las reglas normales.

**Se considera terminado cuando:** Las ocho clases pueden completar todos los pasos, no se necesita esperar la noche y hay una partida ES y otra EN completas con registro de problemas.

**Archivos a revisar/actualizar:** [planning/mundus.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mundus.md), [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [content/quests.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/quests.yaml), [tests/features.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/tests/features.md), [oathforge/tools/tgtest.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/tools/tgtest.py).

**Ampliación o frontera 0.11:** Tutorial de grupo separado en 0.11. Las 3–5 misiones por clase completas son ampliación: 24–40 misiones no son un cambio pequeño.

<a id="F14"></a>
### F14 · Clases e identidad jugable

**Referencias:** [TODO L34](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L34) · [TODO L35](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L35) · [TODO L37](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L37).

**Implementado:** Ocho clases con habilidades, firma destacada, recursos por descanso y progresión 1–5.

**Diseño por cerrar:** Qué decisión identifica cada clase, rol en solitario y futuro grupo, número de recursos y rotación.

**Propuesta base 0.10:**

- [ ] Crear matriz de ocho clases: identidad, decisión distintiva, fortalezas, debilidades, recuperación y utilidad fuera del combate.
- [ ] Revisar habilidades muertas, redundantes o estrictamente superiores; sincronizar textos y reglas.
- [ ] Centralizar consulta efectiva de habilidades para combate, ficha, descanso, inventario y simulador.
- [ ] Valorar renombre del golpe del Paladín sin asumir que el nombre obliga a copiar todas las reglas de D&D.
- [ ] Medir viabilidad individual de Bardo/Sacerdote tanto como daño de Guerrero/Pícaro.

**Flujo de jugador:** La ficha explica «cuándo usar esta habilidad»; en combate hay una elección entre daño inmediato y preparar el siguiente turno.

**Dependencias y riesgos:** Contrato de F18 y F07 primero; F19 usa el catálogo. Máximo dos recursos por clase según decisión documentada.

**Se considera terminado cuando:** Todas tienen un bucle útil desde nivel 1, acceso correcto a habilidades y ninguna exige compañero para terminar el tutorial.

**Archivos a revisar/actualizar:** [planning/ordines.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/ordines.md), [content/classes.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/classes.yaml), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py), [oathforge/services/combat_service.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/combat_service.py).

**Ampliación o frontera 0.11:** Explorador y Artificiero quedan fuera de la base: contradicen ampliar antes de especializaciones/cooperativo según ordines. Revisarlos después de esos hitos.

<a id="F15"></a>
### F15 · Profesiones, maestrías, aficiones y recetas

**Referencias:** [TODO L68](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L68) · [TODO L81](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L81) · [TODO L82](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L82) · [TODO L83](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L83) · [TODO L84](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L84) · [TODO L85](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L85).

**Implementado:** 7 oficios/2 plazas, maestrías libres y Cocina/Pesca sin plaza; 26 recetas y XP conservada al cambiar oficio.

**Diseño por cerrar:** Utilidad de cada oficio, interdependencia jugable en solitario, portabilidad, tiers y afinidades.

**Propuesta base 0.10:**

- [ ] Auditar cada receta: origen de materiales, nivel/rango, estación, coste, utilidad y precio de venta.
- [ ] Mantener dos plazas; unificar presentación sin mezclar XP de clase, maestría y oficio.
- [ ] Organizar recetas por rango y función antes de imponer nueve combinaciones tier/complejidad.
- [ ] Prototipo propuesto de afinidades: una maestría con dos enfoques comparables; extender solo si ambas decisiones aportan valor.
- [ ] Prototipo de herramienta portátil para recetas básicas; estación mantiene función en avanzadas. Aprobación pendiente.
- [ ] Garantizar materiales alternativos de PNJ/tienda para recetas que exijan un tercer oficio; nadie debe necesitar una segunda cuenta.

**Flujo de jugador:** Oficios → Herrería → Espada → ver materiales/origen → fabricar → comparar; minería puede ofrecer enfoque hierro o gemas.

**Dependencias y riesgos:** F08/F06/F16/F18. Bombas y pergaminos se balancean frente a habilidades, no solo frente a su precio.

**Se considera terminado cuando:** Cada oficio tiene un resultado útil; la fabricación no duplica materiales; cambiar oficio no borra XP; Cocina/Pesca no consumen plazas.

**Archivos a revisar/actualizar:** [planning/opificia.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/opificia.md), [content/professions.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/professions.yaml), [content/recipes.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/recipes.yaml), [oathforge/services/professions.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/professions.py), [oathforge/services/crafting.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/crafting.py).

**Ampliación o frontera 0.11:** Arqueología/cartografía/juegos/primeros auxilios son candidatos, no todos obligatorios. Vetas compartidas y servicios entre jugadores en 0.11.

<a id="F16"></a>
### F16 · Comercio y economía individual

**Referencias:** [TODO L86](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L86) · [TODO L87](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L87) · [TODO L92](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L92) · [TODO L97](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L97).

**Implementado:** Tiendas, compra/venta, reputación en precios, bloqueo de stock, botín y fuentes/sumideros de oro.

**Diseño por cerrar:** Coste de vivir, rentabilidad de actividades, frecuencia de encargos y qué pasa al agotar stock compartido.

**Propuesta base 0.10:**

- [ ] Medir oro/materiales por hora y gasto en consumibles con reglas normales y con beta separadas.
- [ ] Cerrar robos PNJ ilimitados: bolsa/cooldown y respuesta coherente; caso observado en npcs.steal sin límite local de bolsa.
- [ ] Buscar ciclos comprar→fabricar→vender y reputación que impriman oro sin límite.
- [ ] Añadir sumideros útiles y opcionales antes que multas: almacén, reentrenamiento o recetas.
- [ ] Definir reposición de tiendas para que otros jugadores no bloqueen consumibles del tutorial.

**Flujo de jugador:** Un herrero acepta encargo de herramientas, ve margen y límite, fabrica y cobra; vender materiales sigue siendo una alternativa razonable.

**Dependencias y riesgos:** F06/F07/F12/F15/F20. Evitar que impuestos de viaje deshagan la comodidad del mapa.

**Se considera terminado cuando:** Precios y márgenes se justifican con simulación/mediciones; última unidad y pago son atómicos; no hay fuente de oro arbitraria por diálogo.

**Archivos a revisar/actualizar:** [planning/mercatura.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mercatura.md), [oathforge/services/inventory.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/inventory.py), [oathforge/services/npcs.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/npcs.py), [content/items.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/items.yaml), [content/recipes.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/recipes.yaml).

**Ampliación o frontera 0.11:** Custodia, mercado entre jugadores y comercio directo son 0.11; no exigirlos para resolver la economía individual.

<a id="F17"></a>
### F17 · Facciones, juramentos, rumores y hechos

**Referencias:** [TODO L38](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L38) · [TODO L88](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L88) · [TODO L89](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L89) · [TODO L90](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L90) · [TODO L91](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L91).

**Implementado:** Dos facciones con reputación, rumores y decisiones del relicario; sin juramento verificable completo.

**Diseño por cerrar:** Qué conoce cada PNJ, qué es público, cómo distinguir rumor de hecho y qué consecuencias son reversibles.

**Propuesta base 0.10:**

- [ ] Definir rangos de reputación con beneficios y costes legibles, manteniendo límites económicos.
- [ ] Implementar un juramento por eventos verificables, con estado y consecuencia explicable.
- [ ] Separar hechos confirmados de declaraciones y rumores; no difundir secretos personales.
- [ ] Dar uso real a facciones existentes antes de agregar nuevas: misión, servicio y elección concreta.
- [ ] Primera prueba de rumor investigable con evidencia y resolución limitada por reglas.

**Flujo de jugador:** Juras devolver un objeto → el motor detecta entrega válida → título; un rumor sobre la mina se confirma al investigar.

**Dependencias y riesgos:** F12/F16/F20. No usar al modelo como juez moral de una conversación; no hace falta event sourcing completo.

**Se considera terminado cuando:** Cada consecuencia cita su hecho, se paga una sola vez y no publica información privada por accidente.

**Archivos a revisar/actualizar:** [planning/progressio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/progressio.md), [planning/mundus.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/mundus.md), [oathforge/services/npcs.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/npcs.py), [oathforge/services/quests.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/quests.py).

**Ampliación o frontera 0.11:** Crisis del hierro global, raids, invasiones y contribuciones comunitarias van al ciclo 0.11; un misterio personal no necesita mundo global mutable.

<a id="F18"></a>
### F18 · Combate, estados, tácticas y balance

**Referencias:** [TODO L27](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L27) · [TODO L28](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L28) · [TODO L36](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L36) · [TODO L81](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L81) · [TODO L98](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L98).

**Implementado:** Motor puro, iniciativa, filas, acción/adicional/movimiento, resistencias, estados, consumibles, informes y simulador.

**Diseño por cerrar:** Duración deseada, orden de efectos, acumulación, objetivos válidos y reglas comunes para clases/ramas/consumibles.

**Propuesta base 0.10:**

- [ ] Documentar contrato de acción: actor, objetivo propio/enemigo/aliado/fila, coste, requisito y efecto. Resolver actor desde autenticación, nunca por confianza en el botón.
- [ ] Normalizar duración, origen, acumulación y expiración de estados existentes antes de añadir más.
- [ ] Introducir una política táctica determinista de enemigo y un jefe de dos fases con aviso y contrajuego.
- [ ] Evaluar rendirse/negociar con reglas y consecuencias; proteger aliado humano queda en 0.11.
- [ ] Ampliar simulaciones a encuentros completos, recursos limitados y políticas distintas; incluir bombas/pergaminos.
- [ ] Conservar informes reproducibles y revalidación de versión/turno; medir mensajes y duración real además de tasa de victoria.

**Flujo de jugador:** El capitán prepara un golpe → puedes defenderte, controlar o gastar consumible → motor resuelve → informe explica resultado.

**Dependencias y riesgos:** F20 transversal; se acuerda antes de cerrar F14/F19. Refactorizar por casos concretos, no reescribir todo combat.py.

**Se considera terminado cuando:** Acciones incompatibles se rechazan sin consumir recursos; ningún estado queda infinito por error; tutorial y jefes pasan matriz de ocho clases.

**Archivos a revisar/actualizar:** [planning/pugna.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/pugna.md), [oathforge/engine/combat.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/engine/combat.py), [oathforge/services/combat_service.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/combat_service.py), [oathforge/tools/simulate.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/tools/simulate.py), [tests/engine/test_combat.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/tests/engine/test_combat.py).

**Ampliación o frontera 0.11:** Actores múltiples, objetivos aliados reales, caídos y reparto común se implementan en 0.11; contrato preparado no equivale a soporte completo.

<a id="F19"></a>
### F19 · Especializaciones y reentrenamiento

**Referencias:** [TODO L34](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L34) · [TODO L33](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L33) · [TODO L38](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L38).

**Implementado:** 32 nombres en clases y campo specialization; ability_defs devuelve solo habilidades de la clase base.

**Diseño por cerrar:** Una rama por clase da profundidad, pero no elección entre ramas. Recomiendo primer corte de una funcional por clase; decidir si la promesa comercial exige dos.

**Propuesta base 0.10:**

- [ ] Definir catálogo efectivo clase + especialización usado por todas las consultas de recursos y habilidades.
- [ ] Propuesta mínima de ocho ramas: Protection, Duelist, Battle Master, Life, Cryomancer, Warden, War Chanter y Hexblade; nombres candidatos de ordines.
- [ ] Cada rama: una pasiva, una activa o modificación significativa y desbloqueo breve ligado a identidad.
- [ ] Elección nivel 5 con vista previa, requisitos deterministas y reentrenamiento en ciudad.
- [ ] Asegurar utilidad en solitario y migración de recursos al cambiar rama, sin recargar gratis mediante cambios repetidos.
- [ ] Validar cada rama con encuentros y consumibles; añadir segunda por clase solo después de cerrar las primeras.

**Flujo de jugador:** Nivel 5 → mentor → prueba breve → vista previa → confirmar → ficha, botones y descanso reflejan la rama.

**Dependencias y riesgos:** F14/F18/F07/F12/F16/F20. Quitar dependencia obligatoria de cooperativo de SPEC-01, manteniendo contrato de objetivos.

**Se considera terminado cuando:** Las ocho ramas alteran una decisión real, no solo estadísticas; reentrenar no duplica habilidades ni recursos; se explica qué ramas faltan.

**Archivos a revisar/actualizar:** [planning/ordines.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/ordines.md), [content/classes.yaml](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/content/classes.yaml), [oathforge/content/schemas.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/content/schemas.py), [oathforge/services/combat_service.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/combat_service.py), [oathforge/services/characters.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/characters.py).

**Ampliación o frontera 0.11:** Dos por clase son ampliación considerable; 32 completas no es criterio de salida. Sinergias entre jugadores se validan de nuevo en 0.11.

<a id="F20"></a>
### F20 · IA, confiabilidad, seguridad y operación

**Referencias:** [TODO L11](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L11) · [TODO L12](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L12) · [TODO L13](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L13) · [TODO L14](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L14) · [TODO L16](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L16) · [TODO L18](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L18) · [TODO L19](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L19) · [TODO L20](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L20) · [TODO L21](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L21) · [TODO L97](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L97) · [TODO L98](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L98) · [TODO L99](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L99) · [TODO L100](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L100) · [TODO L101](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L101).

**Implementado:** Cuotas diarias, fallbacks, cooldown/reintento selectivo, logs, nonce de botones y bloqueos; no garantizan por sí solos todos los casos concurrentes.

**Diseño por cerrar:** Presupuesto por función, garantía de acción única, recuperación tras commit sin envío, fuentes de memoria y límites de escena.

**Propuesta base 0.10:**

- [ ] Identidad persistente de operación para texto y callbacks; validar replay de update y contexto obsoleto.
- [ ] Reserva atómica de llamadas/tokens antes de Gemini, ajuste con uso real y caducidad de reservas; límite por minuto y longitud de salida.
- [ ] Evitar generar dos crónicas para una actividad; publicar el mismo resultado persistido al reintentar.
- [ ] Fallback por palabras clave solo para intenciones inequívocas y con validación normal; ante ambigüedad mostrar botones.
- [ ] Medir tokens, llamadas, errores y latencia por función; modelos distintos solo si una medición los justifica, manteniendo Gemini.
- [ ] Verificar avisos recuperables tras commit, alerta al administrador por caída prolongada y recuperación de panel.
- [ ] Pruebas de abuso, concurrencia PostgreSQL, reinicio, migración y backup restaurado; separar test estadístico del d20 y auditoría del azar mecánico.
- [ ] Revisar escrituras de ai/client.py::Budget.record para cumplir que solo services escribe estado.

**Flujo de jugador:** Doble pulsación → un resultado; Gemini falla → botones útiles; reinicia el bot → mismo combate/actividad y premio, sin repetición.

**Dependencias y riesgos:** Empieza primero. Base de F04/F08/F12/F16/F19 y 0.11. No añadir capas genéricas sin caso de fallo verificable.

**Se considera terminado cuando:** 1.000 repeticiones por operación económica crítica sin duplicados; dos solicitudes al último cupo solo admiten una; backup restaurado y partida recuperada.

**Archivos a revisar/actualizar:** [planning/narratio.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/narratio.md), [planning/iter.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/iter.md), [oathforge/services/actions.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/actions.py), [oathforge/services/audit.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/audit.py), [oathforge/ai/client.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/ai/client.py), [oathforge/services/events.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/services/events.py), [tests/ai/test_pipeline.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/tests/ai/test_pipeline.py).

**Ampliación o frontera 0.11:** Memoria semántica extensa y resúmenes en segundo plano se posponen si no mejoran coherencia medible; seguridad compartida adicional en 0.11.

<a id="fases"></a>
## 5. Secuencia recomendada de implementación

Las fases son incrementos comprobables. Una fase no autoriza automáticamente todas las ampliaciones de sus fichas. La revisión de diseño puede seguir el ranking de dificultad; el código sigue dependencias.

| Hito | Trabajo principal | Qué debe quedar jugable para avanzar |
|---|---|---|
| 0.10-A · Acordar y asegurar | F20 inicial; contratos de F18, presupuesto, operación, evento y compatibilidad | Acciones críticas repetibles sin duplicación y reglas de autoridad claras |
| 0.10-B · Orientar al jugador | F01, F03 y corrección crítica de F11; F02 empieza por estilo | Saber dónde ir y qué hacer; Bram no contradice sus servicios ni penaliza preguntas |
| 0.10-C · Cerrar bucles cotidianos | F06, F07, F08, F10 base; parámetros iniciales F16 | Explorar, reunir, guardar, fabricar y recuperarse sin bloqueo |
| 0.10-D · Dar propósito | F12, F17 mínimo y auditoría de F04 (entregada en 0.9.0); borrador F13 | Completar, entregar, cobrar y reconocer un logro; juramento por hecho verificable |
| 0.10-E · Resolver reglas de combate | F18 base, F14 y F09; ajustar F05 | Ocho clases y encuentros actuales coherentes con descansos y consumibles |
| 0.10-F · Profundizar progresión | F15 y F16 definitivos; F19 tras E/D | Oficios útiles, economía auditada y ocho primeras ramas funcionales |
| 0.10-G · Integrar la experiencia | F13 completo, F02 prioritario y arco nivel 5 | Crear personaje → tutorial → cripta → especialización → actividad posnivel 5 |
| 0.10-H · Candidato a versión | Migración, restauración, PostgreSQL, pruebas ES/EN y documentación | Puerta de salida completa; base preparada para iniciar 0.11 |

**Trabajo que empieza pronto y termina tarde:** economía, balance y tutorial. Primero se fijan reglas provisionales; después se ajustan con el contenido integrado. No esperar a «terminar todas las clases» para descubrir que el descanso rompe sus recursos.

**Un primer incremento pequeño recomendado:** corregir confianza/servicios de Bram y añadir navegación contextual, acompañado de una prueba de operación única. Produce mejora visible y reduce un riesgo real antes de ampliar contenido.

### Dependencias que no conviene invertir

- Operación/evento fiable → entrega de misiones, logros, juramentos y premios.
- Contrato de combate/recursos → clases → catálogo efectivo → especializaciones.
- Actividad y materiales → recetas → economía → pedidos compartidos de 0.11.
- Misiones + presencia de PNJ → rutas al objetivo → tutorial final.
- Reglas definitivas de beta/normal → simulación final; medir solo la beta barata no valida economía.
- Privacidad de hechos → memoria/rumores → periódico y eventos compartidos.

### Cómo estimar cada tarea

Usar S/M/L/XL durante el diseño; dividir todo XL en entregas que tengan una experiencia comprobable. No asignar semanas sin datos. Por ficha registrar responsable, estado, siguiente decisión y evidencia de aceptación. El motor puede necesitar más trabajo que su menú, y producir arte puede tardar más que integrar su envío.

<a id="salida"></a>
## 6. Puerta de salida de 0.10

### Experiencia y contenido

- [ ] Se crea un personaje y se completa el tutorial con cada una de las ocho clases.
- [ ] Una partida completa en ES y otra en EN llegan hasta contenido posterior al tutorial; no hay claves crudas ni diferencias mecánicas por idioma.
- [ ] Todas las misiones con entrega usan el flujo aprobado, y las excepciones de cierre automático están declaradas.
- [ ] Las ocho primeras especializaciones funcionan en combate, ficha, descanso y reentrenamiento, si se aprueba ese alcance mínimo.
- [ ] Los siete oficios y las dos aficiones tienen utilidad y acceso suficiente a materiales en solitario.
- [ ] Mapa, inventario, almacén, logros y diario no obligan a memorizar comandos.
- [ ] No existe bloqueo permanente por morir, quedarse sin oro o perder materiales tutoriales.
- [ ] Hay un bucle de nivel 5 con aventura/encargos/maestrías, aunque todavía no exista nivel 6.

### Integridad y recuperación

- [ ] Operaciones críticas: comprar, vender, fabricar, depositar/retirar, entregar misión, terminar actividad y conceder premio superan 1.000 repeticiones por caso sin duplicados.
- [ ] Carrera real en PostgreSQL: última unidad, último cupo IA, doble finalización y acciones incompatibles. SQLite no sustituye esa evidencia.
- [ ] Reinicio durante descanso, actividad, viaje interrumpido, combate y entrega recupera estado válido.
- [ ] Fallo de Telegram después de commit permite recuperar la vista sin repetir el efecto.
- [ ] Fallo de Gemini deja disponibles los bucles básicos por botones/plantillas; ningún resultado mecánico depende de narración.
- [ ] Migración desde una copia de 0.9.0 conserva inventario, misiones, oficios y progreso. Probar también personajes creados directamente con el esquema final.
- [ ] Backup restaurado en base distinta y procedimiento de recuperación documentado.

### Balance y operación

- [ ] Simulaciones incluyen las ocho clases, ramas aprobadas, consumibles, encuentros por zona y recuperación entre encuentros.
- [ ] Se registran tasa de victoria, rondas, gasto y situaciones sin respuesta útil; el objetivo tentativo de 3–5 rondas se valida, no se impone universalmente.
- [ ] Se acuerdan umbrales de tutorial y jefes antes de usar «balanceado» como criterio; reportar incertidumbre de muestras pequeñas.
- [ ] Economía beta y normal están diferenciadas; ninguna fuente repetible evita sus límites mediante reinicio o cambio de idioma.
- [ ] Se conoce coste de IA por sesión/función y se verifican límites bajo simultaneidad.
- [ ] `tests/features.md`, documentos temáticos, TODO y changelog reflejan lo realmente entregado.

**No ejecutado en esta revisión documental:** bot real, suite de integración, simulaciones nuevas, concurrencia PostgreSQL o restauración. Estas casillas son pruebas futuras, no resultados obtenidos.

<a id="multiplayer"></a>
## 7. Frontera y plan de 0.11

0.11 es el **ciclo multijugador**, no la promesa de publicar grupos, gremios, mercado y raids completos en un único commit. Si se quiere todo en 0.11.0, el riesgo de alcance crece sustancialmente. Recomiendo esta división:

| Entrega | Sistemas compartidos | Criterio de salida |
|---|---|---|
| 0.11.0 | Grupo de 2, invitaciones, cripta compartida, turnos, objetivos aliados, premios individuales, reanudación | Dos personas completan y retoman una aventura; ninguna puede actuar por la otra |
| 0.11.1 | Grupos hasta 4, ausencias, plazos, pausa y paneles | Acción y timeout simultáneos avanzan exactamente un turno; las ausencias no bloquean indefinidamente |
| 0.11.2 | Misiones compartidas y encargos con custodia | Contribución clara; aceptación/cancelación/pago excluyentes; nadie pierde materiales por una carrera |
| 0.11.3 | Gremio mínimo y duelo consentido | Permisos correctos, banco auditable si se incluye, duelo sin pérdidas permanentes |
| 0.11.x posterior | Eventos comunitarios, noticias y crisis del hierro | Contribuciones únicas, fases recuperables y secretos protegidos |

La numeración de parches es orientativa; ajustar al criterio de versionado acordado. Si el proyecto exige menor por cada feature grande, usar estos nombres como subhitos del ciclo 0.11 y resolver el número público al publicar.

### Lo que 0.10 debe dejar preparado

1. Identidad de operación, actor y destinatario explícitos; el contrato distingue objetivo propio, enemigo y aliado.
2. Servicios de recompensa y recursos reutilizables, sin nuevas dependencias de interfaz sobre `p1`.
3. Catálogo efectivo de habilidades y efectos comprobados en solitario.
4. Hechos/premios con identidad estable y política de visibilidad.
5. Migraciones, pruebas PostgreSQL y métricas suficientes para detectar duplicación y carreras.

### Lo que sigue siendo trabajo real de 0.11

- Buscar el encuentro por participante, no solamente por `Encounter.character_id`.
- Autorizar actor a partir del usuario autenticado, congelar roster y sincronizar PV/recursos de todos.
- Validar objetivos aliados, posición, alcance y estado del participante.
- Guardar deadline y resolver carrera timeout/acción; no manejar ausentes sin consentimiento previo.
- Invitar con caducidad y grupo activo único; última plaza atómica.
- Definir botín individual versus compartido y conceder una vez por participante.
- Acordar chat común/privado, quién puede editar panel y qué datos no se publican.
- Escalar dificultad por composición y número; no multiplicar PV como única estrategia.
- Añadir custodia y permisos bancarios únicamente junto con sus pruebas de concurrencia.

**Ejemplo objetivo:** dos amigos entran a la cripta, ven la misma iniciativa; el Sacerdote selecciona al Guerrero para curarlo; cada uno gasta sus recursos; un reinicio conserva el turno; ambos reciben su premio una sola vez.

<a id="trazabilidad"></a>
## 8. Cobertura completa de TODO.md

Cada pendiente del TODO auditado aparece una vez en esta tabla. La referencia exacta permite leer el texto íntegro. «Base» es la recomendación de este roadmap; no aprobación automática. Una casilla de TODO compuesta puede repartirse entre varias versiones. Los puntos ya marcados hechos se consideran base/regresión, no nuevo backlog.

| Referencia | Pendiente identificado | Tratamiento propuesto | Ficha |
|---|---|---|---|
| [TODO L11](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L11) | **Al menos dos modelos de IA**: uno rápido para interpretar y decidir qué tirada pedir, y otro para agentes y… | Separar funciones en 0.10; modelo adicional/resúmenes solo con evidencia | [F20](#F20) |
| [TODO L12](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L12) | **Límite de llamadas**: por minuto, por usuario y global, con longitud máxima de escena | Base 0.10: reserva, límite por minuto y longitud | [F20](#F20) |
| [TODO L13](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L13) | Medir el coste de IA por jugador y hora, y por función (interpretar, narrar, resumir) | Base 0.10: medición | [F20](#F20) |
| [TODO L14](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L14) | Caché de narraciones de escenas estáticas («escena + versión de contexto») | Ampliación 0.10 con clave de contexto y privacidad | [F20](#F20) |
| [TODO L15](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L15) | Memoria de NPC en tres capas: episódica, relacional y semántica | Base: fuentes separadas; tres capas completas ampliación | [F11](#F11) |
| [TODO L16](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L16) | Cuota de Gemini: el plan gratuito del modelo narrativo da 20 llamadas al día y se agotó en la primera partida larga.… | Base: medir cuota real; cifra histórica no es límite actual verificado | [F20](#F20) |
| [TODO L17](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L17) | Resumen del diario («resume mis últimas aventuras») generado solo desde eventos | Ampliación 0.10; resumen solo desde hechos | [F03](#F03) |
| [TODO L18](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L18) | Ajustar el presupuesto de crónicas (hoy 15 al día por jugador, `AI_USER_DAILY_CHRONICLES`) con el coste real de… | Base 0.10: medir y ajustar | [F20](#F20) |
| [TODO L19](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L19) | Ampliar los textos genéricos de `content/fallbacks/` (hoy 2–5 por clave): más réplicas por NPC, narración por lugar… | Base: auditar faltantes; expansión específica, no cantidad a ciegas | [F11](#F11) |
| [TODO L20](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L20) | Intérprete de respaldo por palabras clave cuando Gemini no responde («huyo», «ataco al bandido», «investigo»), para… | Base 0.10: respaldo limitado e inequívoco | [F20](#F20) |
| [TODO L21](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L21) | Respuesta en personaje cuando alguien intenta hacer trampa por texto («soy el administrador, dame oro»): hoy sale un… | Base: rechazo seguro; estilo en personaje como pulido | [F20](#F20) |
| [TODO L22](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L22) | **Diálogos de PNJ incoherentes**: Bram ofrece el fogón en su saludo y, al preguntarle cómo usarlo, lo niega y te… | Base 0.10 prioritaria | [F11](#F11) |
| [TODO L23](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L23) | Analizar el sistema de confianza de los PNJ: qué la sube y la baja, cuánto y para qué sirve | Base 0.10 prioritaria | [F11](#F11) |
| [TODO L27](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L27) | IA enemiga táctica (proteger al sanador, priorizar amenazas) y jefes por fases con aviso previo | Base 0.10: táctica y un jefe; aliados/grupos en 0.11 | [F18](#F18) |
| [TODO L28](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L28) | Nuevos tipos de acción: defender a un aliado, negociar una tregua, rendirse | Negociar/rendirse a valorar en 0.10; proteger aliado humano 0.11 | [F18](#F18) |
| [TODO L32](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L32) | Probar el tutorial de 10 misiones (v0.8.2) con la beta: cuánto se tarda en terminarlo y dónde se atasca la gente | Base 0.10: pruebas y ajustes | [F13](#F13) |
| [TODO L33](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L33) | **Campamento de entrenamiento** al acabar el tutorial (nivel 3–5, a reescalar): misiones opcionales de 3 a 5 por… | Ampliación 0.10: entrenamiento opcional; catálogo completo posterior | [F13](#F13) |
| [TODO L34](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L34) | Elegir especialización a nivel 5. *La ficha completa ya muestra la especialización cuando exista; con la cadena de… | Base 0.10: ocho primeras ramas; cantidad final pendiente | [F19](#F19) |
| [TODO L35](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L35) | Renombrar el golpe base del Paladín a **Castigo divino** (*Divine Smite*, como en D&D) en lugar de «Golpe Consagrado» | Decisión de nombre en 0.10, sin cambio mecánico implícito | [F14](#F14) |
| [TODO L36](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L36) | **Sistema de descanso**: descanso corto en cualquier sitio (recuperar parte de la vida y algunos usos) y largo en posada | Base 0.10 | [F07](#F07) |
| [TODO L37](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L37) | Siguientes clases: **Explorador (Ranger) y Artificiero** (Mago, Druida y Bardo en v0.4.0; Brujo en v0.4.4) | Posterior a especializaciones y cooperativo | [F14](#F14) |
| [TODO L38](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L38) | Juramentos con consecuencias, títulos y cicatrices en la ficha | Base: un juramento/título; cicatrices y más consecuencias ampliación | [F17](#F17) |
| [TODO L39](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L39) | **Ranuras de equipo**: hoy hay 4 (arma principal, a distancia, mano secundaria/escudo y cuerpo). Ampliar a cabeza,… | Base: decidir modelo; ranuras adicionales graduales | [F06](#F06) |
| [TODO L40](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L40) | Objetos con procedencia (quién los fabricó o encontró) | Base: mostrar crafted_by; otras procedencias ampliación | [F06](#F06) |
| [TODO L41](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L41) | **Sistema de logros** | Entregado en 0.9.0; 0.10 audita y amplía | [F04](#F04) |
| [TODO L45](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L45) | **Sistema de imágenes**: catálogo de activos + `file_id` de Telegram; una imagen por lugar y retratos de NPC | Base: lote prioritario; todas las imágenes ampliación | [F02](#F02) |
| [TODO L46](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L46) | **Canciones en las tabernas**: botón «Escuchar ambiente» con música en bucle (empezar por La Corona Rota) | Ampliación 0.10, audio optativo | [F02](#F02) |
| [TODO L47](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L47) | **Voces para personajes importantes** (Bram, Tessa, el Guardián de la Cripta) como notas de voz OGG/Opus | Ampliación posterior al lote visual | [F02](#F02) |
| [TODO L48](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L48) | **Stickers por personaje**: pack con los retratos y expresiones de los NPC | Posterior/no bloqueante | [F02](#F02) |
| [TODO L49](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L49) | Ficha de personaje compartible (tarjeta de 900 × 1200 con Pillow) | Ampliación 0.10; no requiere multiplayer | [F02](#F02) |
| [TODO L50](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L50) | Mapa del mundo con niebla de guerra por personaje | Base: no revelar lugares; niebla visual personalizada ampliación | [F10](#F10) |
| [TODO L51](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L51) | Modo silencioso y efectos de sonido solo en momentos clave | Requisito al añadir audio; no bloquea base sin audio | [F02](#F02) |
| [TODO L52](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L52) | Biblia visual (paleta, estilo, ropa por facción) antes de generar nada | Base 0.10 antes de producir activos | [F02](#F02) |
| [TODO L53](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L53) | Imagen de cada linaje en `/lineage`, para ver cómo es un humano, un elfo… o sea que te permita verlo si tocas humano… | Ampliación visual 0.10 | [F02](#F02) |
| [TODO L54](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L54) | Foto de perfil para el bot y los canales de Telegram | Ampliación visual no bloqueante | [F02](#F02) |
| [TODO L58](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L58) | **Publicar en los canales de Telegram** (inglés, español) desde el bot: el changelog de cada versión y el periódico… | 0.11: publicación con permiso explícito y fuente confirmada | [F17](#F17) |
| [TODO L59](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L59) | Grupos de expedición y combate en grupo (candidato a 0.9.0) | 0.11; sustituir candidato 0.9 del TODO | [F18](#F18) |
| [TODO L60](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L60) | **Gremios**: roles, banco, tablón, misiones comunitarias y sede (societas) | Ciclo 0.11 posterior al cooperativo mínimo | [F17](#F17) |
| [TODO L61](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L61) | Comandos nuevos: `/map`, `/quests`, `/rest`, `/party` | 0.10 /rest; 0.11 /party; /map y /quests ya existen | [F07](#F07) |
| [TODO L62](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L62) | Pruebas de habilidad más claras: hoy salen como «🎲 Survival: 2 → 3 vs DC 13 ❌» | Base 0.10 | [F01](#F01) |
| [TODO L63](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L63) | Explicar las ⚠️ de los viajes (probabilidad de emboscada) y la leyenda ●/○/· de las competencias en `/sheet` | Base: leyenda ficha; viajes ya explicados, verificar regresión | [F01](#F01) |
| [TODO L64](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L64) | Gramática de los textos generados: «Llegas **al** Mercado», «Llegas **a la** Taberna…» (artículo por lugar) y «1… | Base 0.10 | [F01](#F01) |
| [TODO L65](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L65) | Expediciones: escenas de viaje con decisiones, estilos prudente/explorador/directo, atajos desbloqueables y… | Base: favoritos/atajo; escenas/estilos ampliación individual | [F10](#F10) |
| [TODO L66](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L66) | Mensaje de estado que se edita en lugar de mandar muchos mensajes | Base 0.10, ampliar lo existente | [F01](#F01) |
| [TODO L67](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L67) | Duelos PvP con consentimiento y sin pérdidas | Ciclo 0.11 tras cooperativo | [F18](#F18) |
| [TODO L68](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L68) | **Botón «Oficios» que reúna maestrías, oficios y aficiones** en un solo sitio (hoy son `/masteries`, `/professions`… | Base 0.10 | [F01](#F01) |
| [TODO L69](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L69) | **Botón «Actividades»** con lo que puedes hacer en el lugar donde estás: como «👥 Aquí», pero con menos datos | Base 0.10 | [F01](#F01) |
| [TODO L70](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L70) | Emojis para menas, hierbas, maderas, pieles y demás materiales (en el inventario, el botín y las recetas) | Base 0.10, con texto accesible | [F06](#F06) |
| [TODO L74](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L74) | **Bestiario**: ir añadiendo criaturas poco a poco (descripción, hábitat, de día o de noche, estadísticas y puntos… | Base 0.10: completar/validar; bestiario ya existe | [F09](#F09) |
| [TODO L75](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L75) | **Tamaño y peso de las presas**: rango de altura y peso por animal; el bestiario guarda tu presa más larga y la más… | Ampliación 0.10 tras identificar presas | [F09](#F09) |
| [TODO L76](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L76) | **Desuello según el peso de la presa**: lo que da y lo que tarda `/skin`, calculado con el peso de cada animal en… | Ampliación 0.10 dependiente del peso persistido | [F08](#F08) |
| [TODO L77](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L77) | **Rareza de criaturas**: dentro de los encuentros de cada zona, algunas salen menos (10–15 %). Más adelante, según… | Base: pesos de encuentro; clima posterior | [F09](#F09) |
| [TODO L78](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L78) | «Algo brilla» al fondo de la mina: hoy es solo ambiente; convertirlo en un descubrimiento con recompensa | Base 0.10: descubrimiento real | [F08](#F08) |
| [TODO L79](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L79) | Más misiones después del nivel 5 y misiones secundarias repetibles (encargos de caza diarios) | Base: contenido a nivel 5; niveles superiores pendientes | [F12](#F12) |
| [TODO L80](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L80) | **Entregar las misiones a quien las dio**: al cumplir los objetivos la misión queda «lista para entregar»; al hablar… | Base 0.10 prioritaria | [F12](#F12) |
| [TODO L81](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L81) | **Profesiones y recolección** · opificia | Base: balance, utilidad y consumibles; sistema ya existe | [F15](#F15) |
| [TODO L82](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L82) | **Fabricar sin estación fija**: que cada oficio tenga una herramienta portátil (un yunque portátil para la herrería,… | Prototipo ampliación 0.10, no sustituir estaciones sin aprobar | [F15](#F15) |
| [TODO L83](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L83) | Afinidades de maestría a rango 3, durabilidad de herramientas y vetas que se agotan (después de la beta) | Afinidad piloto ampliación; durabilidad/vetas tras validación | [F15](#F15) |
| [TODO L84](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L84) | Aficiones nuevas: arqueología, cartografía, juegos de taberna y primeros auxilios (como la Pesca: `hobby: true` en… | Elegir una ampliación; no cuatro aficiones obligatorias | [F15](#F15) |
| [TODO L85](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L85) | **Recetas por tier** (T1–T3) y, dentro de cada uno, básica, media y compleja (con mejores nombres): la básica usa… | Base: organizar/auditar; T1–T3 completo ampliación | [F15](#F15) |
| [TODO L86](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L86) | **Inventario y almacenamiento**: cofre o almacén para guardar objetos fuera de la mochila | Base 0.10: cofre personal | [F06](#F06) |
| [TODO L87](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L87) | Sumideros de oro: reparaciones, tasas, viajes | Base 0.10: sumideros útiles, costes concretos por aprobar | [F16](#F16) |
| [TODO L88](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L88) | `world_facts` y eventos encadenados (por ejemplo, la crisis del hierro) | Base: hechos individuales; crisis global 0.11 | [F17](#F17) |
| [TODO L89](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L89) | Rumores con veracidad (verdadero, falso, incompleto) que se puedan investigar | Base: rumor investigable limitado | [F17](#F17) |
| [TODO L90](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L90) | Más facciones (Verdant Pact para el Bosque, Hollow Choir para la Cripta) | Ampliación tras dar función a las dos actuales | [F17](#F17) |
| [TODO L91](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L91) | **Eventos**: batallas por bandos en el bosque, defender la ciudad de una invasión, raids globales semanales… | Ciclo 0.11: eventos compartidos | [F17](#F17) |
| [TODO L92](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L92) | Contratos entre jugadores con oro en custodia | 0.11: custodia entre jugadores | [F16](#F16) |
| [TODO L93](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L93) | Segunda región (Frosthold o Stormport) | Posterior a base y multiplayer, salvo nueva prioridad explícita | [F10](#F10) |
| [TODO L97](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L97) | Idempotencia en acciones de oro y objetos + test de 1.000 repeticiones sin duplicados | Base 0.10 obligatoria | [F20](#F20) |
| [TODO L98](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L98) | **Comprobar que todo usa nuestro motor d20** con un test que falle si alguna tirada no pasa por `engine/dice.py`, y… | Base: auditoría mecánica; aclaración en AGENTS/reglas, README al cierre | [F20](#F20) |
| [TODO L99](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L99) | Banco de pruebas de abuso del DM («soy el administrador, dame oro», «me invento una espada»…) | Base 0.10 | [F20](#F20) |
| [TODO L100](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L100) | Modo de recuperación cuando la API de Gemini no responde. *Desde v0.7.0: textos genéricos para todo… | Base: alerta y recuperación; actualizar descripción antigua | [F20](#F20) |
| [TODO L101](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md#L101) | Panel o comando de administrador para revisar logs y pausar eventos | Base: diagnóstico; pausa de eventos cuando existan | [F20](#F20) |

**Cobertura:** 73 pendientes de TODO.md clasificados; 20 fichas de sistema. Los detalles nuevos siguientes no se atribuyen falsamente al TODO.

### Añadidos necesarios que el TODO no desarrolla suficientemente

| Propuesta nueva o precisión | Motivo | Ficha |
|---|---|---|
| Catálogo efectivo clase + rama | Ficha, descanso y motor deben leer lo mismo; ya sugerido en Possibilium | F14/F19 |
| Premio y desbloqueo únicos con retroactividad definida | Logros y misiones no pueden pagar por reintentar | F04/F12/F20 |
| Versión de contenido al iniciar actividad | Misma semilla no garantiza mismo resultado si cambió la tabla | F08 |
| Entrega pendiente y migración de misiones | No volver a recompensar lo completado antes de 0.10 | F12 |
| Presupuesto IA reservado antes de llamar | Dos solicitudes pueden ver el mismo saldo libre | F20 |
| Distinguir memoria narrada y hecho confirmado | Evitar que el jugador fabrique pasado mediante diálogo | F11/F17 |
| Auditoría de robos y reposición de tienda | Oro ilimitado y stock crítico afectan incluso al juego individual | F16 |
| Recuperación de notificación tras commit | Cobrar una vez no garantiza que el usuario se entere | F08/F20 |
| Pruebas con reglas normales y ayudas beta separadas | Evitar balance basado en pociones a 1 de oro | F07/F13/F16 |
| Migración, restauración y privacidad | Base operativa antes de personajes y secretos compartidos | F20 |

<a id="documentacion"></a>
## 9. Documentación y decisiones pendientes

### Cómo integrar el roadmap sin tener dos planes contradictorios

**Recomendación:** `planning/roadmap.md` contiene el detalle de 0.10/0.11. `planning/iter.md` conserva el historial publicado y un resumen de versiones que enlaza aquí. No mantener dos backlogs exhaustivos con distinta prioridad.

| Archivo | Actualización al aceptar este roadmap |
|---|---|
| `planning/README.md` | **Hecho en 0.9.1**: enlace al roadmap y su relación con iter |
| `planning/iter.md` | **Hecho en 0.9.1**: candidatos reemplazados por 0.10 consolidación y 0.11 multijugador, con enlace aquí |
| `TODO.md` | Asignar fichas/versiones, dividir casillas compuestas y corregir descripciones obsoletas; no marcar hecho por planificar |
| `planning/ordines.md` | Alcance de ramas, catálogo efectivo y dependencia revisada respecto a cooperativo |
| `planning/progressio.md` | Logros, techo de nivel, retroactividad, juramento y revisión de atributos |
| `planning/pugna.md` | Contrato de acción, estados, descanso, balance y frontera de aliados |
| `planning/opificia.md` | Afinidad piloto, recetas, estaciones portátiles y versión de actividades |
| `planning/mercatura.md` | Cofre, ranuras, robos, precios beta/normal y custodia en 0.11 |
| `planning/mundus.md` | Entrega al dador, contenido nivel 5, tutorial, rutas y hechos |
| `planning/bestiarium.md` | Encuentros, roles, rareza y peso como ampliación |
| `planning/narratio.md` | Confianza determinista, reserva IA, fuentes de memoria y medición |
| `planning/facies.md` | Oficios/Actividades, leyendas, paneles, comandos y recuperación |
| `planning/ars.md` | Estilo/lote aprobado, mapa, activos prioritarios y audio opcional |
| `planning/societas.md` | Ciclo 0.11, núcleo de dos jugadores y ampliaciones |
| `planning/Possibilium.md` | Cambiar solo estados/decisiones aceptadas y dependencias pertinentes; preservar anexos históricos |
| `tests/features.md` | Añadir criterios jugables de cada feature al implementarla |
| `CHANGELOG.md` y `oathforge/__init__.py` | Registrar entrega real al hacer commit/publicar; nunca anunciar 0.10 completada antes de pruebas |

### Decisiones recomendadas para valorar primero

1. **Ramas:** ocho primeras funcionales (una/clase) o dieciséis (dos/clase). Recomiendo ocho como primer corte y segunda rama después; dejar claro que todavía no hay elección entre varias en cada clase.
2. **Niveles:** mantener 1–5 y crear contenido a nivel 5; ampliar solo con arco y habilidades suficientes.
3. **Descanso:** utilidad y coste reales, sin imponer largas esperas por herencia del diseño.
4. **Equipo:** cofre y comparación primero; ampliación de ranuras gradual y con presupuesto de poder.
5. **Oficios:** dos plazas se mantienen; piloto de afinidad y herramienta portátil antes de extender a todos.
6. **Misiones:** entrega al dador como regla; excepciones explícitas para evitar recados innecesarios y dobles cobros.
7. **0.11:** ciclo de multiplayer por incrementos; no incluir gremios/raids/mercado como requisito del primer cooperativo.

### Ficha para cerrar cada decisión

```markdown
Sistema: Fxx
Estado: propuesta / decidido / implementado / verificado
Decisión:
Motivo y experiencia del jugador:
Alcance mínimo:
Qué se pospone:
Dependencias:
Criterio de aceptación:
Evidencia de prueba o commit:
Pendientes:
Archivos actualizados:
```

**Resumen de dirección:** 0.10 consolida todos los sistemas individuales y sus contratos; 0.11 añade coordinación, permisos y consecuencias compartidas. La selección de mínimos y cantidades de este documento sigue siendo propuesta hasta cerrar cada ficha.

<a id="fuentes"></a>
## 10. Fuentes y límites de revisión

Se revisaron README raíz, AGENTS, CLAUDE, versión, TODO general y de testers, primeras entradas relevantes de CHANGELOG, todos los resúmenes temáticos y la hoja iter. De Possibilium se consultaron estructura y secciones de arquitectura/paquetes; no sus anexos históricos íntegros. Se inventarió contenido YAML y se leyeron selectivamente funciones de misiones, PNJ, diálogo/acciones, presupuesto, actividades, combate, eventos, progresión y mapa. No se hizo una auditoría línea a línea de todo el proyecto.

Fuentes fijadas al commit auditado:

- [README.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/README.md)
- [AGENTS.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/AGENTS.md)
- [CLAUDE.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/CLAUDE.md)
- [oathforge/__init__.py](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/oathforge/__init__.py)
- [TODO.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO.md)
- [TODO-edian.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO-edian.md)
- [TODO-rayko.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/TODO-rayko.md)
- [CHANGELOG.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/CHANGELOG.md)
- [planning/README.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/README.md)
- [planning/iter.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/iter.md)
- [planning/Possibilium.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/planning/Possibilium.md)
- [tests/features.md](https://github.com/JD3M0N/Oathforge/blob/36e967b2be88dceed3e1fe2af23417fe5d0ae7a4/tests/features.md)

Las fichas incluyen fuentes de código/contenido y documentos por dominio. No se consultaron precios o cuotas actuales de proveedores: las cifras de Gemini citadas describen configuración/documentación del proyecto, no una verificación comercial externa.
