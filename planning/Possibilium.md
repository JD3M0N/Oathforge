# Possibilium

## El libro de lo posible para Oathforge

**Proyecto:** Oathforge, RPG narrativo multijugador para Telegram, ambientado en Aetherfall.
**Consolidación:** 17 de octubre de 2026, sobre la versión **0.8.2** (`oathforge/__init__.py`). Integrado en el repositorio en la 0.8.3.
**Naturaleza:** catálogo de diseño, alternativas y preguntas; no es un compromiso de implementación.
**Idioma de trabajo:** español. Todo contenido que llegue al jugador debe admitir español e inglés.

> Una aventura deja hechos; los hechos alimentan relaciones, oficios, rumores y nuevas aventuras. La IA interpreta y cuenta; el motor valida y resuelve.

Este libro reúne el planning anterior del repositorio, los cuatro PDF de diseño (GDD *Aetherfall Chronicles*, guía audiovisual, *The Living Oath* y el Roadmap de la 0.7.6), su README de referencias y las ideas debatidas con Josue. Reorganiza ideas repetidas, desarrolla conexiones y conserva alternativas incompatibles sin hacerlas pasar por decisiones.

**Cómo encaja con el resto de `planning/`:** cada archivo con nombre latino (`ordines.md`, `pugna.md`, `opificia.md`…) es el **resumen de trabajo** de uno o varios capítulos de este libro: estado actual, decidido, próximo y preguntas. `iter.md` elige entregas concretas y versiones. Este archivo conserva el espacio de posibilidades. La dirección audiovisual completa vive en `ars.md`.

**Alcance de la revisión:** documental. Se leyeron los Markdown de `planning/`, el README raíz, la versión, el TODO general y el changelog, además de los PDF. No se ejecutó una auditoría nueva del motor ni de la suite. Los diagnósticos técnicos de los PDF se conservan como hallazgos históricos por verificar.

Los PDF se retiraron del repositorio en la 0.8.3. Su texto extraído por página, sus enlaces y las instantáneas de los Markdown anteriores al refactor están en los [anexos](#s32). **Preservar texto no equivale a reproducir el diseño gráfico, las imágenes ni los binarios originales**, que siguen en el historial de git. Los anexos son archivo histórico: no tienen precedencia sobre las decisiones actuales y **no hace falta leerlos** salvo para comprobar una cita.

<a id="indice"></a>
## Índice

1. [Cómo leer este libro y registrar decisiones](#s01)
2. [Base vigente y discrepancias](#s02)
3. [Visión, referentes y bucles de juego](#s03)
4. [Interfaz, tutorial y sesiones en Telegram](#s04)
5. [Clases nuevas e identidad de las actuales](#s05)
6. [Sacerdote o Clérigo](#s06)
7. [Especializaciones y talentos](#s07)
8. [Linajes, culturas, trasfondos y progresión](#s08)
9. [Juramentos, relaciones y legado](#s09)
10. [Combate, enemigos y jefes](#s10)
11. [Derrota, descanso y recuperación](#s11)
12. [Cooperativo y campañas asíncronas](#s12)
13. [Mapa, viaje y expediciones](#s13)
14. [Regiones y geografía productiva](#s14)
15. [Maestrías y especialización de recolección](#s15)
16. [Oficios, aficiones y recetas](#s16)
17. [Equipo, botín, almacén y procedencia](#s17)
18. [Economía, pedidos, mercados y caravanas](#s18)
19. [Misiones, investigación y aventuras propuestas](#s19)
20. [Bestiario, fauna y caza](#s20)
21. [Facciones, política y justicia](#s21)
22. [Tabernas, rumores y comunidad](#s22)
23. [Mundo vivo, eventos y temporadas](#s23)
24. [Gremios, endgame y PvP](#s24)
25. [IA, memoria, coherencia y presupuesto](#s25)
26. [Arte, música, voces, mapas y recursos](#s26)
27. [Arquitectura, confiabilidad y operación](#s27)
28. [Paquetes implementables, métricas y criterios de salida](#s28)
29. [Documentación, D&D y organización del planning](#s29)
30. [Preguntas pendientes y ficha de aprobación](#s30)
31. [Fuentes, trazabilidad y cobertura](#s31)
32. [Anexos históricos íntegros de texto](#s32)

<a id="s01"></a>
## 1. Cómo leer este libro y registrar decisiones

### 1.1 Estados que no deben confundirse

| Estado | Significado | Qué hace falta para cambiarlo |
|---|---|---|
| **Implementado** | El código y `content/` lo tienen | Confirmar código y pruebas cuando una implementación dependa de ello |
| **Decisión explícita del usuario** | Josue la ha indicado directamente o figura en las instrucciones del proyecto | Registrar el alcance exacto; no extenderlo por interpretación |
| **Registrado en planning** | Un resumen latino lo presenta como «Decidido» | Conservar procedencia; no inventar quién ni cuándo lo aprobó |
| **Propuesta** | Idea del chat, de los PDF o del planning sin aprobación demostrada | Evaluación y aprobación explícita |
| **Alternativa** | Opción que compite con otra | Elegir o diseñar coexistencia |
| **Pregunta abierta** | Falta una regla necesaria | Decisión antes de implementar el sistema afectado |
| **Histórico / por verificar** | Observación o plan de otra versión | Contrastar con el estado actual |
| **Descartado / aplazado** | Estado que deberá asignar una decisión posterior | Conservar el motivo y la condición de reconsideración |

**Regla de lectura:** salvo indicación contraria, los capítulos de expansión contienen propuestas. Los identificadores como `CLA-01` o `MIN-01` sirven para discutir una idea sin copiar un párrafo entero; los resúmenes latinos los citan. Ninguna prioridad sugerida la convierte en tarea aprobada.

### 1.2 Decisiones explícitas que sí se conservan

- `planning/` se organiza en este libro, resúmenes por tema con nombre latino e `iter.md` como roadmap por versión (v0.8.3). Los PDF se retiraron.
- Se deben separar las decisiones aprobadas de las propuestas.
- La IA interpreta intenciones y narra; el motor determinista valida y resuelve.
- Solo `oathforge/services/` escribe estado. La instrumentación no debe abrir otra vía de mutación de gameplay.
- El proveedor actual es Gemini; no se propone sustituirlo sin petición o evaluación explícita.
- El contenido del jugador debe funcionar en español e inglés.
- Un ejemplo con Paladín se generaliza a las demás clases cuando el sistema sea transversal.
- Las excepciones de beta llevan la marca `# beta only` en el código y se retiran al cerrar la beta.

La afinidad minera, las clases nuevas y la revisión Sacerdote/Clérigo se incluyen **para valorar**. Josue pidió desarrollarlas; no ha aprobado todavía su balance, alcance ni versión.

### 1.3 Cómo trabajar sin releerlo todo

Para una conversación de diseño: el resumen latino del tema y, si hace falta, el capítulo de aquí. Para una afirmación histórica, el anexo de la fuente. Para programar, confirmar primero el código y `content/`. No cargar los anexos en cada llamada de IA ni en cada tarea. Tras aprobar algo, actualizar su estado en el resumen latino y su alcance en `iter.md`; tras implementarlo, registrar versión y changelog.

<a id="s02"></a>
## 2. Base vigente y discrepancias

### 2.1 Foto de la v0.8.2

| Sistema | Base existente | Expansión pendiente |
|---|---|---|
| Personaje | Ocho clases, cuatro linajes, compra de 27 puntos, hombre o mujer; doce trasfondos y opción personalizada revisada por Gemini | Especializaciones seleccionables y nuevos arquetipos |
| Progresión | Niveles 1–5; umbrales 0/200/500/1000/1800 XP | Extender contenido antes de subir el límite |
| Combate | Iniciativa (ronda 0), acción/adicional/movimiento, dos filas, críticos, estados, salvaciones DES/SAB, consumibles, entorno e informe completo | Apoyo aliado, tácticas y objetivos alternativos |
| Mundo | Crownreach, Camino del Viejo Rey, Bosque de los Susurros, Prado de los Colmillos, Cripta Hundida y cuatro zonas productivas | Regiones con función propia y exploración más profunda |
| Viaje | Destinos conocidos en un toque, una emboscada por viaje, «▶️ Seguir» y botón 📜 al objetivo; instantáneo en beta | Expediciones, estilos, atajos y favoritos |
| Misiones | **Tutorial de 10 misiones** (Vale, y Bram con el Viejo Colmillo como jefe final); después el relicario y la cripta. Objetivos `kill/talk/visit/read/hunt/gather/skin/craft/rest/heal` | Entrega a PNJ, ramificación y contenido posterior a nivel 5 |
| Profesiones | Siete oficios, dos activos; Cocina y Pesca como aficiones; cinco maestrías de campo | Afinidades, encargos y especialización |
| Actividades | Espera persistida y finalización automática; desuello activo (`/skin`); instantáneas durante el tutorial en beta | Precisar recuperación de todos los avisos y emboscadas |
| Bestiario | Diez criaturas, ilustraciones y descubrimiento por experiencia | Rarezas, ecología, investigación y colecciones |
| Social | Memoria básica de PNJ, reputación con dos facciones, rumores | Favores tipados y conocimiento con procedencia |
| Multijugador | Infraestructura de tablas; juego todavía individual | Expedición compartida real (candidata 0.9.0) |
| IA | Gemini 3.1 Flash-Lite, presupuestos (150/día, 15 crónicas), textos de respaldo y resiliencia (cooldown corto, un reintento por sobrecarga, modelo de respaldo opcional) | Reservas atómicas y medición por función |
| Medios | Panorámica de Crownreach, retratos de las 8 clases por sexo y de las 10 criaturas, caché `file_id` por bot | Lugares, PNJ, voces y música (ver `ars.md`) |
| Pruebas | Suite pytest, simulador de combates, `oath tgtest`, `oath tutorial-stats` y `tests/features.md` | Pruebas de concurrencia en PostgreSQL y de abuso |

**Excepciones de beta vigentes** (`# beta only`): durante el tutorial toda actividad con tiempo termina al momento; el descanso largo es instantáneo; las pociones de vida y de maná cuestan 1 de oro; Ysolde cura gratis todos los PV y las heridas graves; el viaje no consume tiempo. No extrapolar esas excepciones a la economía definitiva.

### 2.2 Qué no debe trasladarse como verdad vigente

1. **Cooperativo en 0.8.0:** era la asignación del roadmap antiguo. La 0.8.0 publicada es viaje; el cooperativo es candidato a 0.9.0.
2. **Seis misiones, cuatro trasfondos y seis oficios:** fotos anteriores (README raíz hasta la 0.8.2 y PDF). La tabla anterior prevalece.
3. **Tutorial de ocho misiones** (0.7.13): en la 0.8.2 son diez, con «El mercado» y el Viejo Colmillo dentro; el relicario y la cripta son la primera aventura posterior.
4. **Pesca como maestría:** cambió a afición en 0.7.20. Se mantiene su árbol de ideas, pero no se reclasifica silenciosamente.
5. **Artificiería:** el oficio se llama Ingeniería desde 0.7.20. Artífice/Artificiero como clase sigue siendo una propuesta distinta.
6. **Recoger manualmente:** desde la 0.7.21 las actividades terminan solas; quedan descripciones antiguas por revisar.
7. **Viajes de veinte minutos, descanso de 80 minutos y capilla por tres monedas:** son reglas de diseño suspendidas por la beta; no son lo que vive hoy el jugador.
8. **Un día real por día de mundo:** alternativa del GDD; el juego usa cuatro horas reales por día de juego.
9. **Salvaciones y simulador como futuras:** existen desde la 0.4.0 y la 0.5.4; ampliar su alcance no equivale a crearlos.
10. **Retrato de la barda ausente, solo Paladín con texto largo:** superados en 0.7.3 y 0.7.23.
11. **Reintentos prohibidos y pausa de dos minutos:** descripción histórica de IA; la 0.7.29 introdujo cooldown de 20 s, reintento limitado y respaldo opcional.
12. **Niveles 1–20, 0–100 en competencias y 48 especializaciones:** visión del GDD, no sistemas implementados ni aprobados.
13. **287 tests aprobados y dos omitidos:** resultado del informe de la 0.7.6; no certifica versiones posteriores.

Los recuentos históricos de objetos, recetas y lugares están en los anexos con su versión. Antes de usarlos en balance o en un anuncio, obtenerlos de los YAML vigentes.

<a id="s03"></a>
## 3. Visión, referentes y bucles de juego

### 3.1 La experiencia a perseguir

**VIS-01 · Aventurero, artesano y ciudadano.** El jugador puede identificarse como «explorador que vende mapas y fabrica arcos», «sacerdotisa joyera que restaura reliquias» o «pícaro que sostiene una red de favores». Sus actividades se conectan; no son minijuegos aislados. Primera versión: una misión que use un recurso, una fabricación y una elección de facción en los lugares actuales.

**VIS-02 · Mundo compartido y aventuras instanciadas.** Mercado, noticias y proyectos pueden ser comunes; la cripta y sus decisiones se guardan por grupo para proteger coherencia y ritmo. Es una propuesta de alcance, no una decisión cerrada. Debe definir qué pasa si un PNJ muere en una campaña y sigue vivo para otros.

**VIS-03 · Progreso horizontal.** Colecciones, reputaciones, técnicas, mapas y relatos permiten seguir jugando a nivel 5. No todo tiene que añadir daño o un nivel. Una región nueva debe aportar decisiones antes que enemigos idénticos con más PV.

**Promesa propuesta (Living Oath §1):** tus juramentos tienen consecuencias, tus aventuras dejan huellas y tus amigos pueden intervenir en ellas. Tres pilares: decisiones con consecuencias legibles; cooperación accesible sin horarios obligatorios; resolución auditable independiente de la IA. Cada feature nueva refuerza al menos uno y no rompe los otros.

**El núcleo que hay que proteger (GDD §20):** un jugador actúa con libertad, el motor resuelve con rigor, el DM cuenta lo sucedido y el mundo lo recuerda. Secuencia recomendada y estado: (1) un buen turno y una buena escena ✅; (2) una misión resoluble de dos formas ✅ relicario; (3) un NPC que recuerda ✅ básico; (4) una aventura compartida — pendiente; (5) un hecho que cambia la ciudad — pendiente; (6) economía y facciones que reaccionan — parcial.

### 3.2 Qué tomar de cada referente

| Referente | Patrón útil | Adaptación a Oathforge | Riesgo de copiar demasiado |
|---|---|---|---|
| D&D | d20, agencia, múltiples soluciones y consecuencias | Pruebas relevantes, objetos útiles y acciones improvisadas validadas | Exceso de excepciones y ventanas de reacción |
| WoW | Identidad de clase, especializaciones, jefes anunciados, profesiones y encargos | Pocas habilidades reconocibles y artesanos distintos | Rutinas obligatorias, inflación de equipo y árboles enormes |
| Chat Wars | Comunidad organizada desde un bot, economía y conflictos colectivos | Pedidos, preparación y proyectos asíncronos | Guerras que exijan horarios o población inexistente |
| SimpleMMO | Entrar y hacer algo útil en pocos minutos | Menús claros y avances pequeños | Miles de objetos sin decisiones diferentes |
| MUD clásicos | Grafo textual, comandos y descubrimiento | Lugares conectados, pistas y rutas conocidas | Desplazamiento repetitivo y comandos opacos |
| Torn | Economía social y rivalidades persistentes | Reputación comercial y necesidades entre jugadores | Complejidad financiera y ventaja de conexión permanente |
| Generative Agents / CALYPSO | Memoria selectiva y apoyo narrativo | PNJ con hechos, objetivos y voz coherente | Agentes permanentes caros y sin límites de autoridad |

Son patrones de diseño procedentes de las fuentes, no una auditoría actual de esos productos.

### 3.3 Tres bucles conectados

- **Activo:** problema → preparación → viaje → decisión o encuentro → consecuencia → regreso con algo que hacer.
- **Asíncrono:** elegir trabajo con duración y riesgo conocidos → esperar → resultado persistido → volver sin penalización por tardar.
- **Social:** expresar necesidad → encontrar colaborador → cumplir encargo o aventura → dejar una relación y una noticia.

Ritmo propuesto: microacciones de 1–3 minutos, sesiones de 10–25 y expediciones de 30–90 minutos o repartidas en días. Hipótesis para probar, nunca requisito de permanencia.

<a id="s04"></a>
## 4. Interfaz, tutorial y sesiones en Telegram

**UX-01 · Una escena que se entiende de un vistazo.** Lugar, hora, PV, estado, actores visibles, objetivo relevante y tres opciones prioritarias. Los detalles quedan detrás de botones. El teclado fijo conserva Lugar, Héroe, Mapa, Inventario y Diario.

**UX-02 · Resumen y detalle.** Vista normal breve; informe completo, tiradas, reglas y lore bajo petición. Mostrar por qué una pasiva afectó al resultado, sin repetir su explicación cada turno. Medir cuántos mensajes necesita un jugador para decidir.

**UX-03 · Inicio guiado y avanzado.** Recomendaciones editables para clase y atributos; ayuda contextual sin abandonar la creación. El jugador puede profundizar en compra de puntos, linajes o trasfondos cuando quiera.

**UX-04 · Acción explícita.** Estados pendiente, interpretando, requiere tirada, resuelta, interrumpida o rechazada. Una acción antigua explica qué cambió y ofrece la vista actual. Bloquear botones visualmente no sustituye idempotencia en servicios.

**UX-05 · Retomar sin recordar comandos.** Candidatos `/resume` y `/unstuck`: reconstruyen estado y siguiente decisión; no curan ni teletransportan. `/party` y `/rest` abrirían flujos claros. Valorar alias españoles sin duplicar menús.

**UX-06 · Diario orientado a la próxima acción.** Separar misiones activas, listas para entregar, registro, pistas, rumores y logros. «Ahora puedes hablar con Vale» es más útil que una barra completa sin destino.

**UX-07 · Preferencias.** Idioma, detalle de tiradas, avisos, audio y ritmo de grupo. El idioma privado puede diferir del de grupo. Las notificaciones importantes se agrupan.

**UX-08 · Accesibilidad textual.** Los iconos acompañan palabras. Todo audio tiene transcripción. No depender del color para distinguir rarezas, peligros o estados. En una futura Mini App, controles grandes y equivalentes de texto.

**UX-09 · Tutorial medido.** El tutorial de 10 misiones se mide con `oath tutorial-stats` (mediana por misión y dónde se atasca cada jugador). Ajustar con datos de la beta; la alternativa del campamento de clase (PRO-06) va después.

Pendientes concretos del TODO: leyenda de competencias ●/○/· en `/sheet`, nombres de pruebas traducidos, artículos correctos al llegar a un lugar, singular de ronda, inventario comparativo y mensajes de estado editables. Interfaz y comandos vigentes: `facies.md`.

<a id="s05"></a>
## 5. Clases nuevas e identidad de las actuales

### 5.1 Nuevas clases candidatas

| ID | Clase | Decisión distintiva | Utilidad fuera de combate | Dependencia y riesgo |
|---|---|---|---|---|
| CLA-01 | Explorador / Ranger | Marcar, preparar trampa o disparar | Huellas, rutas y caza selectiva | Evitar convertirlo en requisito para explorar |
| CLA-02 | Monje | Encadenar técnica y elegir golpe o evasión | Disciplina, movilidad y lectura corporal | Los combos deben caber en una decisión por turno |
| CLA-03 | Bárbaro | Entrar en furia exponiéndose | Rescate físico, resistencia y presencia | Distinguirlo del Guerrero Berserker |
| CLA-04 | Hechicero | Alterar un conjuro mediante poder innato | Percibir o canalizar anomalías | Diferenciarlo del repertorio del Mago |
| CLA-05 | Artífice / Artificiero | Configurar dispositivo y auxiliar | Reparar mecanismos y examinar tecnología | No exigir Ingeniería como oficio |
| CLA-06 | Chamán | Elegir tótem y vínculo elemental | Espíritus, clima y rituales | No duplicar al Druida ni al Sacerdote |
| CLA-07 | Caballero de la muerte | Convertir vida y marcas en presión | Ecos funerarios y pactos | Solapamiento con Paladín, Brujo y Nigromante |

**Explorador.** Primera versión: arco, presa marcada (los monstruos ya tienen `type`, útil para «enemigo predilecto»), técnica de rastreo y trampa con cargas. El compañero animal puede empezar como efecto acotado. Ramas: Cazador, Tirador/Francotirador, Acechador, Señor de Bestias y Trampero Salvaje.

**Monje.** Secuencia corta: Palma abierta prepara una apertura; en el siguiente turno eliges empujar o golpear. Recurso de foco con recuperación clara. Ramas: Puño de Hierro, Espiritual, Sombra y Elemental. Su defensa necesita reglas de equipo; nada de armadura invisible gratuita.

**Bárbaro.** Furia y postura temeraria crean riesgo visible. Si entra como clase, decidir qué ocurre con la rama homónima del Guerrero y ofrecer migración.

**Hechicero.** Pocos conjuros y variaciones: prolongar, penetrar o dividir. Ramas: Sangre Dracónica, Magia Salvaje, Tormenta y Astral. La magia inestable requiere tabla publicada; la IA no inventa consecuencias mecánicas.

**Artífice.** Un dispositivo principal y uno auxiliar; recursos propios aunque no fabrique profesionalmente. Ramas del GDD: Ingeniero, Alquimista, Forjador Rúnico y Autómata; alternativas: Armadura Rúnica y Artillería.

**Chamán y Caballero de la muerte.** Banco de expansión posterior; demostrar identidad y compatibilidad con el mundo antes de ocupar una versión. No importar la cosmología de otros juegos.

### 5.2 Dar profundidad a las clases existentes

| Clase | Decisión que desarrollar | Aportación narrativa | Precaución |
|---|---|---|---|
| Paladín | Castigo, protección o sello | Garantizar acuerdos y reconocer profanación | Un juramento transversal no se vuelve exclusivo suyo |
| Guerrero | Interceptar, maniobrar o rematar | Liderazgo militar y resistencia | Consistencia no debe equivaler a no tener decisiones |
| Pícaro | Crear oportunidad o aprovecharla | Infiltración, falsificación y trampas | Evitar turnos repetidos de preparación sin recompensa |
| Sacerdote | Curar, prevenir o purificar | Ritos, duelo y refugio | No obligar al grupo a llevar sanador |
| Mago | Daño inmediato o control | Identificar magia y abrir sellos | Repertorio comprensible y concentración limitada |
| Druida | Forma, terreno o restauración | Fauna y rutas naturales | Forma Salvaje actual (PV temporales) no equivale a formas completas |
| Bardo | Inspirar, perturbar o mantener melodía | Rumores, pactos y actuación | La diplomacia no resuelve automáticamente todo |
| Brujo | Maldición, pacto o defensa | Secretos y conocimiento prohibido | Pactos de facción opcionales; no bloquear al brujo actual |

Carga inicial: tres botones principales por clase y una opción de detalle (la 0.7.22 ya separa ataques + habilidad destacada 🌟 y «✨ Acciones»). Evaluar cada clase en combate aislado, secuencia de encuentros y grupo: victoria, PV restantes, recursos, rondas y decisiones disponibles. Un 95 % de victoria contra un jabalí no demuestra equilibrio de campaña.

Recursos de clase (GDD §4.5): como máximo dos por clase para no saturar el panel, con recuperación clara (turno, encuentro, descanso corto, largo o día del mundo). Pendiente de TODO: renombrar el golpe base del Paladín a **Castigo divino**.

<a id="s06"></a>
## 6. Sacerdote o Clérigo

**Estado:** pregunta abierta. La clase implementada se llama Sacerdote; el GDD usa Clérigo. No se ha aprobado un renombrado.

| Alternativa | Resultado | Ventaja | Coste |
|---|---|---|---|
| NOM-01 · Renombrar a Clérigo | Una clase divina amplia con dominios | Evita duplicación y conserva base | Migrar textos y decidir nombre inglés sin romper ids |
| NOM-02 · Mantener Sacerdote | Religión propia y ramas amplias | Continuidad con jugadores actuales | Explicar que puede ser más que un sanador |
| NOM-03 · Separar ambos | Sacerdote ritual a distancia; Clérigo armado | Dos fantasías claramente diferenciadas | Balance, equipo y solapamiento con Paladín |

**Recomendación, pendiente:** una clase amplia llamada Clérigo, con Sacerdote como identidad narrativa o rama, antes que dos clases casi idénticas. Si se mantienen dos, probar tres turnos representativos de cada una y del Paladín: deberían tomar decisiones diferentes.

Si se renombra, conservar la clave interna `priest` y traducir con criterio (`Clérigo / Cleric`, `Sacerdote / Priest`). Actualizar clases, guías, retratos, reglamento, misiones, narración y documentos. El renombrado no exige cambiar habilidades.

<a id="s07"></a>
## 7. Especializaciones y talentos

### 7.1 Catálogo de 32 ramas

Los nombres están en `content/classes.yaml`; las mecánicas son propuestas. El GDD usa variantes de nombre que no sustituyen a las actuales.

| Clase | Ramas registradas | Direcciones mecánicas propuestas |
|---|---|---|
| Paladín | Venganza, Guardián Sagrado, Redentor, Inquisidor | Perseguir una presa; interceptar; purificar/negociar; revelar defensas |
| Pícaro | Asesino, Espía, Duelista, Trampero | Preparar remate; obtener información; aislar rival; controlar terreno |
| Guerrero | Campeón, Maestro de Batalla, Guardián, Berserker | Consistencia/críticos; maniobras; proteger fila; riesgo por presión |
| Sacerdote | Vida, Luz, Guerra, Tumba | Curación; radiante/limpieza; apoyo ofensivo; evitar caída y tratar no-muertos |
| Mago | Piromante, Criomante, Arcanista, Cronomante | Desgaste; control; eficiencia; iniciativa con límites |
| Druida | Cambiaformas, Guardián, Invocador, Esporas | Transformaciones; raíces/defensa; una criatura acotada; zonas y desgaste |
| Bardo | Ilusionista, Diplomático, Cantor de Guerra, Embaucador | Señuelos; herramientas sociales; apoyo por fila; desviar amenazas |
| Brujo | Pactista Infernal, Nigromante, Filo Maldito, Vacío | Poder con coste; servidor; marca cercana; control con contraprestación |

### 7.2 Profundidad manejable

**ESP-01 · Paquete por rama.** Una pasiva, una activa, una interacción narrativa y una misión corta de desbloqueo.

**ESP-02 · Árbol corto.** Tres elecciones relevantes: especialidad principal, modificación de una habilidad y técnica final. Evitar quince nodos porcentuales.

**ESP-03 · Reentrenamiento.** En ciudad, con confirmación, progreso conservado y coste moderado. Bloqueado en combate o actividad. Recalcular máximos y usos para impedir llenar reservas cambiando de rama.

**ESP-04 · Configuraciones guardadas.** Solitario y grupo, con cambios solo en puntos seguros.

**ESP-05 · Desbloqueo por identidad.** Proteger a un testigo, desactivar un ritual o defender una posición enseña cómo juega la rama.

Alternativas de entrega: una rama funcional por clase (Living Oath propone Protection, Duelist, Battle Master, Life, Cryomancer, Warden, War Chanter y Hexblade, por diversidad de roles) o dos iniciales por clase. No mostrar como seleccionable una rama que solo guarda un nombre.

### 7.3 Ejemplo generalizable

Guardián Sagrado podría interceptar un golpe de un aliado y tener una pasiva limitada de protección. Criomante podría cerrar una ruta de ataque una ronda con salvación. Duelista podría aprovechar un objetivo aislado. Todos requieren coste, objetivo válido, duración, límites y utilidad individual; el mismo catálogo efectivo (clase + especialización) debe alimentar motor, descanso, ficha y simulador.

Contrato técnico propuesto: `specialization_key`, requisitos, efectos tipados, coste, cooldown, targeting, descripción es/en y versión de reglas.

Talentos del Paladín del GDD (conceptos, no implementados): Juramento Implacable, Castigo Resonante y Último Veredicto; Muro de Fe, Guardia Compartida y Fortaleza del Juramento; Palabra de Tregua, Gracia Persistente y Segundo Aliento; Sello de Silencio, Juicio Radiante y Lectura de Herejía.

<a id="s08"></a>
## 8. Linajes, culturas, trasfondos y progresión

### 8.1 Linaje no es destino

Separar biología, cultura, clase, oficio previo y moralidad. Un orco erudito o un elfo minero deben ser opciones viables. Revisar primero humano, elfo, enano y orco.

Preguntas de balance históricas: comparar el humano con +1 en seis atributos y la inmunidad enana al envenenamiento. Simular escenarios relevantes antes de cambiar rasgos.

| ID | Linaje candidato | Posibilidad acotada | Relación con el mundo |
|---|---|---|---|
| LIN-01 | Ashborn | Reducir una vez daño de fuego o reconocer anomalía | Supervivientes de catástrofe arcana |
| LIN-02 | Tidekin | Ayuda limitada en travesía acuática | Silverbrook y Stormport |
| LIN-03 | Hollowbound | Percibir un eco funerario por escena | Cripta y Hollow Choir |
| LIN-04 | Ironwrought | Resistir una condición con mantenimiento definido | Talleres de Frosthold |
| LIN-05 | Thornblood | Reconocer planta o paso natural | Thornwood y Verdant Pact |
| LIN-06 | Smallfolk | Repetir una prueba concreta por descanso | Caravanas y rutas |

También se preservan los arquetipos del GDD: dracónido, tiefling, mediano y cambiante, sin prioridad. Pendiente del TODO: imagen de cada linaje en `/lineage`.

### 8.2 Culturas y trasfondos

Culturas candidatas: ciudadanía de Crownreach, artesanos de Frosthold, exiliados de Thornwood, marineros de Stormport y caravanas fronterizas. Pueden ofrecer idioma ficticio, contacto, rumor o receta común, dentro de un presupuesto de ventajas equivalente.

Trasfondos propuestos: Cartógrafo, Minero, Cazador, Mensajero, Médico de campaña, Aprendiz de escriba, Noble caído, Superviviente de la cripta, Desertor, Cocinero de caravana, Contrabandista y Acólito disidente. Compararlos con los doce existentes antes de duplicar nombres.

**PRO-01 · Destinos del trasfondo.** Una escena corta, un contacto y una elección reutilizando lugares existentes. No convertir cada trasfondo personalizado en una cadena de recompensas inventada por Gemini.

### 8.3 Crecer por lo que importa

- **PRO-02:** XP por resolver peligros, descubrir, investigar, fabricar con objetivo y completar decisiones; no por spam de mensajes.
- **PRO-03:** nivel 4 con elección entre atributo o dote, con un catálogo pequeño y comparable.
- **PRO-04:** competencias legibles; comparar 0–3 actual con 0–100 interno y cinco rangos. No mezclar maestrías con habilidades d20.
- **PRO-05:** mentores, manuales y pruebas de oficio para aprender técnicas.
- **PRO-06:** campamento opcional de entrenamiento por clase tras el tutorial, ajustado a nivel real y sin bloquear veteranos; podría albergar el juramento de clase.
- **PRO-07:** ampliar a 6–8 o 10 solo con un arco que sostenga habilidades y encuentros; 1–20 queda como horizonte.
- **PRO-08:** colecciones por cuenta a largo plazo; juramentos y relaciones por personaje. Requiere decidir si habrá varios personajes por usuario.

Si se cambia un rasgo o atributo, ofrecer revisión gratuita o compensación explícita y explicarlo en es/en.

<a id="s09"></a>
## 9. Juramentos, relaciones y legado

**JUR-01 · Promesas verificables.** Ofrecido → aceptado → activo → cumplido, roto o reparado. Cada juramento declara condiciones observables, plazo, consecuencias y reparación antes de aceptar. Es transversal; el Paladín puede tener interacciones propias sin monopolizarlo.

| Juramento candidato | Condición observable | Eco y reparación |
|---|---|---|
| Guard the Witness | Testigo llega vivo a destino | Acceso/confianza; rescate o restitución si falla |
| No Blood for Iron | Resolver contrato minero sin matar humanos | Apoyo del pacto; compensar afectados |
| Keep the Ember | Sostener refugio durante evento | Beneficio comunitario; reconstrucción |
| Return What Was Taken | Devolver una instancia de objeto | Memoria/reputación; recuperación equivalente |
| Never Leave One Behind | No abandonar aliado caído bajo reglas definidas | Reconocimiento; misión de rescate |
| Speak Before Steel | Intentar negociación válida antes de pelear | Ruta social; penitencia breve |

«No mentir» o «ser honorable» son demasiado ambiguos para un primer detector automático. Una promesa libre puede existir como rol sin premio mecánico. La IA recuerda el compromiso y explica evidencia; no sanciona por impresión moral. Implementación propuesta: `oath_definitions` en YAML, `character_oaths` con definición/versión/estado/contadores, actualización desde eventos canónicos en la misma transacción y una clave por evento.

**REL-01 · Favores concretos.** Bram te debe alojamiento o una pista, no «cualquier cosa». El favor se consume una vez y tiene origen. Separar confianza personal, reputación pública, miedo, deuda y gratitud.

**REL-02 · Rivales y redenciones.** PNJ que compite contigo, enemigo que puede ayudar y aliado que exige reparación. Sus cambios se derivan de acciones, no de adulación.

**REL-03 · Títulos y cicatrices.** Marcan momentos y alteran saludos, acceso o apariencia; nunca penalizaciones permanentes irrecuperables.

**REL-04 · Legado.** Retirar un aventurero puede dejar un libro, objeto o relato. No transferir riqueza sin reglas.

**REL-05 · Vínculos de grupo.** Reconocer rescates y aventuras compartidas con ventajas situacionales pequeñas o escenas propias.

<a id="s10"></a>
## 10. Combate, enemigos y jefes

### 10.1 Más verbos, no más pulsaciones

| ID | Idea | Qué ve o hace el jugador | Primera versión y límite |
|---|---|---|---|
| COM-01 | Proteger aliado | Elige a quién cubrir hasta su siguiente turno | Una reacción o acción con alcance claro |
| COM-02 | Ayudar | Prepara una apertura o una prueba de aliado | Consume oportunidad real; no bono universal gratis |
| COM-03 | Empujar entre filas | Aparta al protector para alcanzar retaguardia | Salvación y restricciones de tamaño |
| COM-04 | Cobertura | Se protege tras columna o barricada | Etiqueta de escena; comparar con tercera posición |
| COM-05 | Romper entorno | Corta cuerda, vuelca carro o destruye foco | Solo objetos existentes con efectos tipados |
| COM-06 | Interrumpir ritual | Renuncia a daño para frenar un contador | Objetivo alternativo visible |
| COM-07 | Negociar o rendirse | Explota una disposición concreta del enemigo | No disponible contra todo ni sin coste |
| COM-08 | Retirada organizada | Cubre a otro o abandona con consecuencias | Huida individual no cierra batalla de todos |
| COM-09 | Reacción preseleccionada | Interceptar, conservar o responder a conjuro | Evita ventanas de chat por cada golpe |
| COM-10 | Entrenamiento seguro | Prueba un poder sin botín ni pérdidas reales | Estado de simulación separado |

Ejemplo del GDD §5.8: «Corto la cuerda de la lámpara para que caiga sobre los goblins» → intención `interact_environment: cut_rope`; el motor confirma lámpara y enemigos bajo ella, fija dificultad y daño de área y tira; el DM narra solo lo confirmado.

### 10.2 Estados y sinergias

Ampliaciones: ralentizado, derribado, silencio, concentración, vulnerabilidad temporal y defensas por contexto. Cada efecto necesita `source`, `duration`, `stacking_rule`, `dispel_type` y momento de activación.

Combos iniciales: distraer → ataque oportunista; inmovilizar → disparo preparado; marcar → remate; mojar → frío. Empezar con dos interacciones tipadas. Limitar cadenas de control con resistencia creciente o inmunidad temporal.

### 10.3 Inteligencia enemiga sin llamada por turno

- Básica (la actual): elegir objetivo alcanzable (el de menos PV), huir según regla, usar un ataque válido.
- Táctica: proteger sanador, buscar cobertura, priorizar una amenaza o aprovechar estado.
- Jefe: anuncio, oportunidad de respuesta y resolución; fases con transiciones visibles.

Arquetipos: depredador persigue heridos, guardián protege, cultista canaliza, arquero busca cobertura y capitán cambia órdenes. Roles de enemigo (GDD §5.6): tanque, atacante, invocador, sanador y controlador. Primera prueba: capitán bandido o esqueletos (pregunta abierta). Nunca Gemini para escoger cada golpe.

### 10.4 Encuentros que cambian el objetivo

- Patrulla con arquero protegido: romper cobertura o flanquear.
- Ritual de tres focos: cortar canalización en vez de matar a todos.
- Criatura hambrienta: distraerla con comida o enfrentarse.
- Defensa de carro o puerta con PV propios y límite de rondas.
- Guardián que marca una fila antes de atacar: cambiar de fila, defender o destruir un sello.
- Sigilo de grupo con fallo definido.
- Jefe que recuerda una táctica anterior mediante estados diseñados.

Objetivo tentativo: 3–5 rondas normales. Medir tiempo real, esperas, consumo y sensación de contribución.

<a id="s11"></a>
## 11. Derrota, descanso y recuperación

**REC-01 · Caído antes que derrotado.** Permite rescate o estabilización cuando exista targeting aliado. Salvaciones contra muerte frente a regla simplificada. La cura no resucita salvo efecto autorizado.

**REC-02 · Derrota recuperable.** Rescate, retirada, pérdida parcial limitada (hoy: 10 % del oro y estado «herido») y cicatriz narrativa opcional. Muerte permanente: alternativa muy posterior, no para la beta.

**REC-03 · Descanso corto accesible.** Recuperar parte de vida y algunos usos sin depender del tónico. Publicar qué devuelve y con qué frecuencia. Resolver si el osario gratuito debe tener duración.

**REC-04 · Descanso largo activo/offline.** Diseño: ocho horas de juego (80 minutos reales) en la posada. En la beta es instantáneo. Al cerrar la beta, valorar una variante compatible con sesión activa y otra para desconectarse.

**REC-05 · Capilla y economía de beta.** La curación gratuita actual previene bloqueos. Antes de cobrar, garantizar una vía recuperable para quien está herido y sin oro. Distinguir sanar PV, quitar herida grave y recuperar habilidades.

**REC-06 · Campamento.** Kit, guardia, cocina y recuperación parcial; riesgo anunciado. No sustituye gratis la posada ni desencadena combate contra un jugador ausente.

<a id="s12"></a>
## 12. Cooperativo y campañas asíncronas

### 12.1 Primera aventura compartida

**COO-01:** dos amigos completan la Cripta Hundida con escena e iniciativa comunes, cura o protección aliada, recompensas individuales y recuperación tras reinicio. Ampliar después a cuatro. El 2–5 del GDD queda como pregunta.

Flujo: crear grupo → invitar → aceptar → elegir destino y ritmo → confirmar preparación → entrar → resolver escenas → repartir → salir. El líder propone; no gasta pertenencias privadas de otros.

### 12.2 Reglas necesarias antes de abrir el menú

- Un personaje no puede estar en dos grupos activos ni recolectar en otra región durante una expedición.
- Invitaciones con identidad, capacidad y caducidad verificadas; un enlace no concede autoridad (deep links con token firmado).
- Congelar participantes al iniciar combate; sustituciones en punto seguro.
- Resolver actor desde el usuario autenticado. Pulsar un panel ajeno nunca otorga control.
- Transferencia de liderazgo definida; salir no destruye progreso de compañeros.
- Misiones y objetos de instancia separados del diario individual.
- Recompensa por participante y tipo entregada una vez; no entrar al final solo para cobrar.
- Botín individual como opción inicial; necesidad/codicia y subasta después.

### 12.3 Ritmo y ausencias

| Modalidad candidata | Plazo de ejemplo | Política por decidir |
|---|---|---|
| Sesión rápida | 90 segundos por turno | Aviso, defensa preautorizada o pausa |
| Campaña lenta | 6–24 horas | Respuesta diferida y resumen de retorno |
| Pausa acordada | Entre rondas o escenas | Conservar la decisión pendiente |

No mezclar velocidades en un combate. No gastar pociones ni controlar libremente al personaje ausente. El temporizador vive en BD; JobQueue despierta el trabajo y comprueba el turno esperado.

### 12.4 Información y ruido

Panel común editado para combate; inventario, ficha y secretos por privado. Pistas con registro y opción de compartir. Si el bot no puede escribir al usuario, explicar cómo iniciar el privado y aplazar la entrega; no publicar el secreto en el grupo.

Votación solo para dilemas importantes, con desempate explícito. Medir mensajes por ronda, tiempo de decisión y quién siente que no contribuye. Probar equipos sin sanador, sin tanque y con control.

Espacios de Telegram (GDD §2.2): chat privado (personaje, secretos), grupo de expedición, grupo de gremio, comunidad con temas, canal de noticias (*Herald*) y Mini App futura (validando `initData`). Convivencia: nombres de personaje y nunca datos de Telegram no públicos; consentimiento para interacciones privadas; sanciones permanentes con revisión humana.

<a id="s13"></a>
## 13. Mapa, viaje y expediciones

### 13.1 Proteger la comodidad ya conseguida

**Implementado en 0.8.0:** el jugador elige un lugar conocido; el motor calcula el recorrido global (Dijkstra entre zonas) sin atravesar combates fijos pendientes. Lo nuevo se descubre por adyacencia. Distancia en yardas (100 yd/min); viaje instantáneo en beta. Una tirada de emboscada por viaje: `min(45 %, 15 % × peor nivel de peligro + 5 % por cada tramo peligroso adicional)`. La derrota cancela la continuación. Los botones 📜 usan lugares conocidos y, desde la 0.8.2, solo criaturas que salen a esa hora y nivel.

**VIA-01 · Separar viajar y explorar.** Viajar resuelve rutina; explorar abre una expedición con recursos, pistas y problemas.

| Tipo de recorrido | Escenas |
|---|---|
| Rutina conocida | 0 |
| Primera visita | 1 |
| Expedición corta | 1–2 |
| Viaje de misión | Las de esa misión |

### 13.2 Fase dos

- **VIA-02:** estilos Prudente, Explorador y Directo; guardan preferencia y no gastan objetos solos.
- **VIA-03:** rutas distintas de verdad: patrullada, atajo o paso descubierto; mostrar el intercambio sin tabla excesiva.
- **VIA-04:** atajos por descubrimiento o reputación (`requires_flag`): Sendero de los Carboneros, barquero, puerta secundaria, carro.
- **VIA-05:** tres favoritos cuando el mapa crezca.
- **VIA-06:** caminos afectados por derrumbes o eventos, revalidados al salir y continuar.
- **VIA-07:** estados desconocido, rumoreado, descubierto, visitado y cartografiado.
- **VIA-08:** campamentos, guías y caravanas como elecciones puntuales.
- **VIA-09:** geografía secreta por eclipse o ritual, con reglas razonables.
- **VIA-10:** mapa de pistas o tesoro que conecta tabernas y regiones.

Ejemplo: puente dañado → cuerda, vado o desvío. El motor comprueba herramienta y prueba; el fallo puede aumentar coste o abrir rescate. Cada tramo y decisión se resuelve una vez (nonce), también tras doble clic o reinicio.

Si el viaje vuelve a consumir tiempo, decidir cómo mueve el reloj de juego (hoy, tiempo real: 1 día = 4 h), cómo afecta a actividades y avisarlo en el reglamento.

<a id="s14"></a>
## 14. Regiones y geografía productiva

| Región candidata o existente | Función | Recurso o servicio | Conflicto |
|---|---|---|---|
| Crownreach | Centro social, oficios y política | Mercado, archivos, banca | Corrupción y legitimidad |
| Thornwood (≈ Bosque de los Susurros) | Naturaleza y exploración | Hierbas, madera, caza | Juramentos e industria |
| Frosthold | Clanes y producción | Hierro, plata, forja | Derrumbes y suministro |
| Ashen Peaks | Magia volcánica y forjas | Cristales y reliquias | Cultos y bestias ígneas |
| Mirefen | Investigación y alquimia | Venenos, hongos, ruinas | Enfermedad ficticia y maldiciones |
| Sunscar | Comercio y arqueología | Caravanas y tumbas | Agua, tormentas y saqueadores |
| Stormport | Navegación y autonomía | Pesca, transporte, contrabando | Piratas y política mercante |

The Living Oath añade Ashen March y Hollow Depths como alternativas de ambientación. Aetherfall es el mundo; Terra Coronata es el continente en `content/world/`. La jerarquía del GDD no renombra carpetas.

**GEO-01 · Segunda región pequeña con propósito.** Frosthold o Stormport; presupuesto propuesto: cinco lugares, tres misiones, una facción, un recurso, un jefe y retorno a Crownreach. Cada lugar sirve a dos actividades.

### 14.1 Mejorar antes los lugares existentes

- Mina: veta segura, túnel profundo, «algo brilla» convertido en hallazgo y reparación comunitaria.
- Arboleda: maderas distintas, resinas, semillas y permiso de tala.
- Claro: ciclos simples de plantas, hongos y descubrimientos.
- Silverbrook: cebos, especies, tamaño y criatura que altera la pesca.
- Prado: rastreo de especie, ejemplares raros y elección de conservar una presa.
- Cripta: puertas con varias soluciones, ecos, sellos y modificadores de expedición.

**GEO-02 · Clima propio.** Dos o tres estados persistidos por región: lluvia favorece hierbas, niebla cambia rastreo, helada abre un paso. Sin clima real ni IA permanente.

Horizonte: ciudad subterránea, archipiélago itinerante, bosque con ciclos temporales, reino de los muertos y fortaleza flotante.

<a id="s15"></a>
## 15. Maestrías y especialización de recolección

### 15.1 La idea solicitada por Josue

El rango demuestra práctica; la especialización expresa preferencias. Dos mineros del mismo rango pueden servir a mercados distintos: uno obtiene más hierro para herrería y otro busca gemas para joyería. **Propuesta solicitada, no balance aprobado.**

Tres capas: rango acumulado, rama elegida y técnica seleccionada. Primera versión: una elección a rango 3, sin perder XP al cambiar. Rangos actuales 0–5 con umbrales 0/80/240/500/900/1500 y +4 % de unidad extra por rango (tope 20 %).

### 15.2 Minería desarrollada

| ID | Rama | Ventaja | Sacrificio o restricción | Usuario probable |
|---|---|---|---|---|
| MIN-01 | Extracción abundante | Más volumen común | Menos selección o hallazgos | Vendedor y productor de lotes |
| MIN-02 | Metalurgia de campo | Favorecer una mena disponible | Reduce diversidad; no crea menas ausentes | Herrero |
| MIN-03 | Prospección | Más gemas y raros | Menor rendimiento común | Joyero |
| MIN-04 | Excavación cuidadosa | Fósiles, reliquias y pistas | No maximiza el ingreso | Arqueólogo y explorador |

Ejemplo de panel:

> ⛏️ Mina del Paso Viejo · Minería rango 3
> Especialización: Prospección
> Enfoque guardado: gemas
> Recursos posibles: hierro, carbón y gemas
> [Trabajar] [Expedición] [Cambiar enfoque] [Mi maestría]

No fijar aún «+20 % de gema»: decidir si afecta probabilidad, cantidad secundaria o tabla condicionada. Simular valor esperado, tiempo y oferta.

### 15.3 Extensión a las demás disciplinas

| Actividad | Cantidad | Selección/calidad | Descubrimiento |
|---|---|---|---|
| Tala | Más troncos | Especie, piezas para arcos | Resinas, semillas y nidos |
| Herboristería | Hierbas comunes | Medicinales, venenosas o difíciles | Hongos y flores inusuales |
| Desuello | Más cuero | Piel bien conservada | Escamas, glándulas y componentes |
| Rastreo | Presa común fiable | Especie concreta | Ejemplar raro y rastros |
| Pesca (afición) | Más pescado | Especie, tamaño o pesca segura | Trofeos, mensajes y tesoros |

**MAS-01:** cuaderno de campo. **MAS-02:** maestros que enseñan técnicas mediante misión. **MAS-03:** herramientas especializadas, no mejores en todo; durabilidad solo si añade decisiones. **MAS-04:** cebo, aceite o bolsa de muestras. **MAS-05:** hallazgos compartibles y trabajos cooperativos. **MAS-06:** menos XP por trivialidad sin volver inútil la zona inicial. **MAS-07:** tercera plaza de oficio como alternativa futura.

### 15.4 Límites de balance y persistencia

- Favorecer solo materiales presentes y desbloqueados.
- Misiones obligatorias no dependen de un raro sin protección contra mala suerte.
- Preferencia persistida; no preguntar técnica en cada pulsación.
- Persistir al iniciar la versión de tabla, rango/enfoque y semilla (hoy la semilla se guarda pero `claim` lee el contenido vigente).
- Separar recompensa de crónica; Gemini no decide si aparece una gema.
- Nodos comunes personales; agotamiento compartido solo en ocasiones especiales.
- Una actividad automática puede dejar combate pendiente; nunca jugar turnos por el ausente.

Medir recursos y XP por minuto, valor esperado por rama, tiempo a rango 3, riesgo de expediciones y demanda de cada material.

<a id="s16"></a>
## 16. Oficios, aficiones y recetas

### 16.1 Ampliaciones de los siete oficios

| Oficio | Productos útiles candidatos | Ramas propuestas |
|---|---|---|
| Herrería | Escudos, herramientas, reparación, soportes de obra | Armas, armaduras, herramientas/artefactos |
| Alquimia | Antídotos, preparación de jefe, reactivos | Medicina, venenos, transmutación |
| Carpintería | Arcos, campamentos, mobiliario | Arquería, construcción, navegación |
| Peletería | Bolsas y equipo de exploración | Armaduras ligeras y equipo de campo |
| Joyería | Gemas situacionales y talismanes | Engastes, reliquias, gemas |
| Escribanía | Pergaminos, mapas, glifos y contratos | Runas, cartografía, documentación |
| Ingeniería | Bombas, mecanismos y herramientas | Demoliciones, dispositivos, mecanismos |

Cocina y Pesca siguen como aficiones sin plaza.

### 16.2 Nuevas ocupaciones y clasificación pendiente

- **OFI-01 · Sastrería:** ropa mágica, vendas, bolsas y estandartes.
- **OFI-02 · Encantamiento:** propiedades limitadas y recuperar componentes.
- **OFI-03 · Runistería:** comparar con Escribanía antes de separar.
- **OFI-04 · Cervecería:** rama de Cocina o afición propia.
- **OFI-05 · Arqueología:** restauración y conocimiento; afición candidata.
- **OFI-06 · Cartografía:** mapas, rutas y tesoros; oficio, afición o rama.
- **OFI-07 · Primeros auxilios:** actividad accesible, sin sustituir curaciones de clase.
- **OFI-08 · Juegos de taberna:** progresión cosmética o social, sin oro infinito.
- **OFI-09 · Servicios:** guía, entrenador, médico, domador y mercader.
- **OFI-10 · Logística:** caravanero, navegante y escolta.
- **OFI-11 · Construcción:** arquitecto, albañil y encantador de estructuras.
- **OFI-12 · Encargos clandestinos:** espionaje, falsificación ficticia y contrabando ligados a misiones.

Las aficiones nuevas seguirían el patrón de la Pesca (`hobby: true` en `professions.yaml`).

### 16.3 Recetas con decisiones

**RECETA-01 · Tres familias.** Taller, especializada y colaboración. Alternativa de Josue: T1–T3 y, dentro, básica (materiales del oficio) / media (añade algo de una afición) / compleja (algo de otro oficio). Comparar si las dos dimensiones aportan o duplican menús.

**RECETA-02 · Variantes sobre una base.** Espada ligera o resistente; plata para un uso concreto. No cincuenta nombres casi iguales (GDD §6.4: espada de acero templado = 3 lingotes + 1 madera noble + forja, «más ligera» o «más resistente»).

**RECETA-03 · Calidad pequeña.** Corriente y cuidada; mejor duración, fiabilidad o utilidad secundaria, no daño mayor obligatorio.

**RECETA-04 · Aprendizaje.** Maestro común, receta regional de misión, excepcional de jefe y fragmentos con protección de mala suerte.

**RECETA-05 · Lotes acotados.** Coste total y faltantes antes de confirmar; validar el lote entero y consumir una vez.

**RECETA-06 · Interdependencia amable.** Componentes comunes vía PNJ y especiales vía artesanos. Nada se bloquea porque falta el único carpintero.

**RECETA-07 · Restaurar y mejorar.** Reforja, reparación y recuperación de reliquias; desmantelar sin ciclo rentable infinito.

Primera prueba: pedido de herramienta de herrería, lote de pociones y comida de expedición.

<a id="s17"></a>
## 17. Equipo, botín, almacén y procedencia

**EQU-01 · Comparar antes de equipar.** Daño/CA, propiedad, pérdida y beneficio visibles.

**EQU-02 · Ranuras graduales.** Hoy cuatro: principal, distancia, secundaria/escudo y cuerpo. Alternativas: accesorio; o cabeza, manos, pies, cuello, dos anillos y capa. Elegir una ampliación que quepa en `/sheet`.

**EQU-03 · Rareza con función.** Común/inusual/rara/épica/legendaria o común/cuidada/singular/reliquia. Calidad y rareza no son la misma variable.

**EQU-04 · Un afijo al principio.** Consagrado, silencioso, resistente al barro o imantado para prospección. Efectos tipados con límites.

**EQU-05 · Sets pequeños.** Dos piezas y efecto situacional.

**EQU-06 · Firma e historia.** Fabricante (`crafted_by` ya existe), descubridor, propietarios, mejoras y batallas. Separar pilas cuando procedencia o propiedades importen; el historial no debe inflar un JSON sin límite.

**EQU-07 · Almacén y correo.** Cofre personal primero; depósito de gremio después; correo con custodia y caducidad a largo plazo.

**EQU-08 · Mala suerte acotada.** Contador para componentes o progreso hacia premio.

**EQU-09 · Apariencias.** Cosméticos separados de estadísticas; tarjeta compartible sin datos privados.

**EQU-10 · Reliquias singulares.** Custodia grupal consentida o varias copias; unicidad global solo con una comunidad que la sostenga.

<a id="s18"></a>
## 18. Economía, pedidos, mercados y caravanas

### 18.1 Tres flujos y tres capas

Oro creado por el sistema, transferido entre jugadores y destruido por servicios. Vender al PNJ crea oro; una compraventa entre jugadores solo lo mueve, salvo tasas. Medir creación/destrucción, riqueza mediana, precios básicos y circulación.

Capas: tiendas PNJ con básicos accesibles (hoy: valor ±25 % según reputación, venta al 50 %); mercado de materiales y objetos; encargos personalizados y transporte.

### 18.2 Pedido de fabricación

**ECO-01 · Custodia.** El cliente deposita materiales y comisión; el artesano acepta; el motor comprueba oficio, rango y estación; fabrica el objeto pactado, lo entrega y paga en una transacción. Cancelación o caducidad devuelve una vez. Guardar receta y condiciones aceptadas. Dos aceptaciones simultáneas admiten solo una. Ejemplo del GDD §7.5: un alquimista pide 8 lirios por 240 de oro retenidos; quien entrega cobra en la misma transacción.

### 18.3 Mercado y servicios

- **ECO-02:** órdenes de compra sin coincidencia de horario.
- **ECO-03:** listados a precio fijo con cantidad, caducidad, límite y comisión (3–5 % es hipótesis).
- **ECO-04:** intercambio seguro con depósito y confirmación doble.
- **ECO-05:** pedidos PNJ con demanda limitada por región y receta.
- **ECO-06:** puestos y tiendas de jugador.
- **ECO-07:** subastas de piezas especiales cuando haya población.
- **ECO-08:** regateo limitado por visita.
- **ECO-09:** segunda mano, alquiler de herramientas y depósito.
- **ECO-10:** reputación de artesano resistente a pedidos entre cuentas propias.
- **ECO-11:** ferias y concursos con premio cosmético.
- **ECO-12:** mercado negro según ley regional.

No publicar equipo equipado, vinculado o de misión. Recalcular precio y cantidad en servidor, con locks en orden coherente y operación única.

### 18.4 Caravanas y comercio regional

Origen, destino, carga, ruta, conductor, escolta, estado y llegada prevista. Límites de carga, pérdidas acotadas y seguros ficticios. Descubrir una emboscada puede producir información vendible.

Sumideros posibles: recetas avanzadas, almacén, servicios, cosméticos, sede y reparaciones previsibles. Evitar préstamos complejos.

### 18.5 Abusos que deben presupuestarse

Simular compra → fabricación → venta con reputación extrema; revisar joyería. Verificar el hallazgo histórico de robos PNJ repetibles sin bolsa/cooldown. El rate limit de mensajes no es límite económico. Registrar causa, origen, destino, cantidad y clave de operación. Criterio antes de comercio entre jugadores: **cero duplicados en 1.000 repeticiones** automatizadas.

<a id="s19"></a>
## 19. Misiones, investigación y aventuras propuestas

### 19.1 Estructura y progreso

**MIS-01:** gancho → objetivo aparente → descubrimiento → elección → consecuencia → eco. Cada misión declara alcance de personaje, grupo, instancia o mundo. Cuatro fuentes (GDD §12.1): hechas a mano, por plantilla, emergentes y personales.

**MIS-02:** estados disponible, aceptada, en curso, bloqueada, lista para entregar, completada, fallida y caducada. El TODO pide entregar a quien dio la misión (prioridad alta); candidato, no regla ya cambiada.

**MIS-03:** evidencias persistidas. Objetivos existentes: `kill/talk/visit/read/hunt/gather/skin/craft/rest/heal`; faltan entregar, investigar, rescatar, negociar y defender.

**MIS-04:** fallo que avanza: pista incompleta, coste o escena nueva. Hoy una prueba se intenta una vez por habilidad, lugar y día de juego; valorar `challenge_id` y enfoques para distinguir repetir de intentar otra solución.

**MIS-05:** plantillas válidas antes de generación libre. La IA redacta; no inventa XP ni requisitos imposibles.

### 19.2 Banco de aventuras

| ID | Aventura | Decisiones | Sistemas que conecta |
|---|---|---|---|
| AVE-01 | The Iron That Whispers | Explotar, sellar o investigar una veta que responde a muertos | Mina, cripta, receta y memoria |
| AVE-02 | The Witness at Silverbrook | Ruta rápida, bosque o capilla; revelar o guardar una carta | Escolta, facciones y juramento |
| AVE-03 | The Hollow Feast | Comprar, producir o negociar un banquete saboteado | Cocina, pesca y diplomacia |
| AVE-04 | A Crown Without a King | Comparar relatos y decidir el destino de una reliquia | Archivo, evidencias y legitimidad |
| AVE-05 | The Road That Forgot Us | Reconstruir ruta por tres pistas y rescatar caravana | Cartografía, exploración y grupo |
| AVE-06 | The Debt of Old Tusk | Cazar, trasladar o proteger a la criatura | Fauna, materiales y contratos |
| AVE-07 | La curandera acusada | Detener, absolver, negociar o probar contaminación | Agua, magia, robo e investigación |
| AVE-08 | Puerta del osario | Llave, fuerza o ritual | Objeto útil, prueba y evidencia |
| AVE-09 | Hierro para todos | Reparar infraestructura o pactar otra explotación | Profesiones, política y evento |

Para cada una: dos soluciones iniciales, un coste observable, una pista opcional y una consecuencia local. Las 8–12 consecuencias del GDD son un presupuesto de autoría, no ocho finales por frase. AVE-06 debe revisarse ahora que el Viejo Colmillo es el jefe final del tutorial.

### 19.3 Más tipos de aventura

Robo con sospechosos; escolta con preparativos; rescate con reloj; criatura distraíble; ruta abierta por contactos; reliquia con varios destinatarios; rehabilitación de reputación; misterio comunitario con verdad predefinida; misión breve de clase; encargo de trasfondo; maldición curable; juicio con tres pruebas. Repetibles (encargos de caza diarios) necesitan variación y demanda.

### 19.4 Tres recorridos completos del GDD (§18), como ejemplo de futuro

- **La primera noche de un paladín.** Aldric llega, la tabernera habla de un guardia desaparecido en Thornwood, investiga huellas (Supervivencia y Percepción validadas por el motor), sufre una emboscada que enseña el combate y decide entre auxiliar, interrogar, quedarse el cofre o perseguir al culpable; la decisión queda como evento y reaparece en diálogos.
- **La vida de una comerciante.** Lyra compara precios entre Frosthold y Crownreach, acepta una entrega, decide ante una tormenta (desvío pagado, espera o riesgo), descubre un campamento de saqueadores y vende esa información o pide protección; sus ganancias dependen de tiempo, transporte y compradores.
- **Una campaña que cambia la política local.** Un gremio prueba que el gobernador de Stormport desvía impuestos; bardo, espía y guerrera reparten tareas con tiradas y permisos; si las pruebas bastan, hay elección extraordinaria y el periódico publica el resultado.

Mara y Elian son PNJ de ejemplo de los documentos; no sustituyen a Bram ni a otros existentes.

<a id="s20"></a>
## 20. Bestiario, fauna y caza

**Base:** ver criatura abre identidad/lore/hábitat; primera derrota abre estadísticas; tres derrotas abren puntos débiles y recompensas. Diez criaturas con ilustración.

- **BES-01:** descubrir debilidades antes con Naturaleza, Religión o Arcanos.
- **BES-02:** rarezas de encuentro (10–15 %) con pistas y probabilidad limitada; después por hora y clima.
- **BES-03:** ejemplares con tamaño/peso; récord de presa larga y pesada.
- **BES-04:** desuello por especie o peso (hoy `skin_seconds` fijo por bestia).
- **BES-05:** migraciones, actividad nocturna y clima.
- **BES-06:** alfas y criaturas transformadoras que cambian un nodo.
- **BES-07:** observación no letal y estudio.
- **BES-08:** colección por zona, título y siluetas «???».
- **BES-09:** compañeros animales; diferenciar mascota cosmética de aliado mecánico.

Balance del tutorial (0.8.2): criaturas blandas, parejas por `min_level` y Viejo Colmillo rebajado. Pendiente: el lobo gris a nivel 1 y la tabla del camino con el capitán. Un raro peligroso no aparece sin aviso en la ruta obligatoria de un novato.

<a id="s21"></a>
## 21. Facciones, política y justicia

### 21.1 Organizaciones propuestas

| Facción | Interés y servicio | Conflicto |
|---|---|---|
| Pacto de Plata / Silver Covenant, existente | Orden, refugio y protección | Justicia frente a fanatismo |
| Sindicato Carmesí / Crimson Syndicate, existente | Contactos y comercio clandestino | Autonomía frente a explotación |
| Verdant Pact | Rutas, hierbas y equilibrio natural | Conservación frente a producción |
| Hollow Choir | Ritos y archivos funerarios | Memoria frente a tabú |
| Ashen Circle | Saber y experimentación | Innovación frente a control |
| Iron Dominion | Disciplina y expansión | Seguridad frente a conquista |
| Veiled Court | Diplomacia e intriga | Institución frente a manipulación |
| Free Companies | Mercenarios | Honor contractual frente a interés |
| Ironbound Consortium | Herramientas y suministro minero | Huelga y recursos del bosque |
| Wayfarers’ League | Mapas, escolta y refugios | Peajes y fronteras |
| Ashen Collegium | Identificación y anomalías | Investigación dañina |
| Crown Remnants | Historia y símbolos del reino | Legitimidad actual |

Decidir si Circle/Collegium o Dominion/Consortium coexisten, se fusionan o son rivales. No sumar todos por aparecer en una lista.

### 21.2 Reputación con consecuencias legibles

Separar reputación de facción, fama local y confianza personal. Rangos del GDD sobre −100..100: perseguido (≤ −61), hostil, desconfiado, neutral, conocido, aliado y venerado (≥ 80). Cada facción nueva sostiene una misión, un servicio y una tensión. Rehabilitación y caminos alternativos siempre.

### 21.3 Política y ley a largo plazo

Consejos, asambleas, embajadas, tratados secretos, espionaje doble, embargos, contratos mercenarios, escuelas de facción y festivales de reconciliación. Leyes por ciudad sobre caza, armas, impuestos o necromancia; un delito ficticio produce búsqueda, multa o juicio con evidencia. Ningún mensaje «soy rey» cambia soberanía. Empezar por un juicio diseñado o una disputa minera.

<a id="s22"></a>
## 22. Tabernas, rumores y comunidad

**SOC-01 · Taberna como encuentro de sistemas.** Comer, descansar, buscar grupo, aceptar pedidos, oír noticias, jugar y conversar. La Corona Rota ya tiene fogón y posada.

**SOC-02 · Rumor con fuente y certeza.** Verdadero, falso, incompleto o no verificado; región, caducidad y vínculo a evento. Un rumor no abre una puerta: el hecho confirmado sí.

**SOC-03 · Mercado de información.** Comprar pista parcial, vender mapa, denunciar hallazgo o publicar crónica. Nunca datos reales ni chats privados.

**SOC-04 · Oír tu propia historia.** Un bardo recita un rescate semanas después; una pieza firmada recuerda al artesano.

**SOC-05 · Aficiones sociales.** Dados internos, acertijos, cartas del mundo, improvisación, relatos y música. Apuestas solo con fichas sin valor real.

**SOC-06 · Campfire y temas.** Comunidad separada en taberna, mercado, reclutamiento y noticias. Las conversaciones libres no activan acciones.

**SOC-07 · Reconocimiento.** Cartas de agradecimiento PNJ, gaceta, museo, trofeos, banquetes y clasificaciones de rescate/artesanía/exploración. No premiar volumen de mensajes.

**Logros y colecciones:** exploración, bestiario, artesanía, diplomacia, cooperación y decisiones. Secretos con pistas y visibles para orientar. Recompensas cosméticas o de acceso social; sin rachas que castiguen ausencias.

**Estado 0.9.0:** implementados 30 logros y dos metalogros individuales, puntos de prestigio, cuatro títulos, destacados y seguimiento; conjuntos de contenido fijos y reconocimiento retroactivo verificable. Cooperación, escenas secretas nuevas y acceso social siguen pendientes. Ver [progressio](progressio.md) y [entrega 0.9.0](releases/0.9.0.md).

<a id="s23"></a>
## 23. Mundo vivo, eventos y temporadas

### 23.1 Un mundo que cambia con límites

**MUN-01:** rutinas PNJ calculadas por horario al consultarse (los NPC ya tienen horario). **MUN-02:** clima regional persistido. **MUN-03:** eventos con `trigger`, `preconditions`, `participants`, `location`, `duration`, `effects`, `followups` y `visibility`, con topes y cierre.

Familias: naturales, sociales, económicas, políticas, militares, mágicas, de aventura y misterios.

### 23.2 Primer evento candidato: crisis del hierro

1. **Anuncio:** derrumbe de una veta y rumores parciales.
2. **Preparación:** información, materiales y decisiones de explotación.
3. **Contribución:** madera, soportes, limpieza de túnel, rescate y negociación.
4. **Resolución:** éxito, éxito parcial o reconstrucción posterior.
5. **Epílogo:** veta temporal, precio acotado, placa, receta o noticia persistente.

Umbrales ajustados a la comunidad observada. Fallar no destruye Crownreach. Precios y rutas cambian con modificadores temporales, no editando YAML. Implementación propuesta: `world_events` con estado/versión/inicio/fin, contribución con `unique(event_id, operation_id)`, reducers deterministas y scheduler persistente.

### 23.3 Noticias e historia

**MUN-04 · Herald of Aetherfall.** Plantilla o borrador de Gemini a partir de eventos públicos confirmados, dos boletines semanales o por hitos, publicado vía outbox en los canales (`t.me/OathForge`, `t.me/OathForge_es`).

**MUN-05 · Temporadas sin borrar personaje.** Arcos de 4–8 semanas. Conservar profesión, amistades y juramentos; PvP podría reiniciar solo clasificación.

Otros: tres portales arcanos, festival, epidemia ficticia con alquimistas, convoy diplomático, jefe por contribuciones, reloj de catástrofe acotado; batallas por bandos en el bosque, defensa de la ciudad, raids semanales.

<a id="s24"></a>
## 24. Gremios, endgame y PvP

### 24.1 Endgame sin escalar niveles indefinidamente

Expedición de tres escenas con recursos limitados, jefe de dos fases, rescate, juramento, reliquia elegida y proyecto artesanal. Dos modificadores (oscuridad, ritual) bastan para una primera variante. Después: expedición roguelite, biblioteca prohibida, ciudad maldita, ritual cooperativo y raid asíncrona por contribución.

### 24.2 Gremios pequeños

**GRE-01:** nombre, emblema, tablón, miembros y proyecto; útil con tres amigos. **GRE-02:** sede narrativa antes de multiplicadores. **GRE-03:** banco con límites, permisos y auditoría. **GRE-04:** talleres, cosechas y refugios comunitarios. **GRE-05:** asambleas y liderazgo con reglas de ausencia. Roles iniciales: líder, oficial y miembro; tesorería como permiso aparte.

### 24.3 Escalera de PvP, siempre por decidir

| Modalidad | Primera regla | Dependencia |
|---|---|---|
| Duelo amistoso | Consentimiento doble, sin pérdidas permanentes | Guardar y restaurar recursos sin duplicar objetos |
| Arena normalizada | Equipo o reglas equivalentes | Balance y estado competitivo separado |
| Arena 1v1/2v2 | Emparejar fuerza y limitar repeticiones puntuables | Datos y revisión de acuerdos |
| Competición de facciones | Aportaciones por varias vías | Comunidad y evento confiable |
| Guerra por objetivo temporal | Ventana, límites y retirada | Roles, permisos y moderación |
| Frontera/territorio | Zona señalizada y protección a novatos | Población y operación maduras |

Recompensas cosméticas; nada de robo libre, persecución constante ni pérdidas irreparables.

<a id="s25"></a>
## 25. IA, memoria, coherencia y presupuesto

### 25.1 Funciones, no agentes permanentes

Intérprete, narrador, diálogo, director de arcos, simulador social y cronista son funciones lógicas, no seis llamadas por acción. Gemini sigue siendo el proveedor.

| Operación | Motor/servicio | IA candidata |
|---|---|---|
| Inventario, oro, mercado, receta y talento | Toda la regla | Ninguna |
| Combate estándar | Tiradas, efectos y cierre | Hitos o resumen opcional |
| Acción libre | Validación y resolución | Interpretar intención |
| PNJ corriente | Rutina y servicios | Plantillas |
| PNJ importante | Estado, memoria y permisos | Voz con recuerdos pertinentes |
| Diario y periódico | Eventos visibles | Síntesis por lote |
| Audio de ambiente | Archivo aprobado | No generación por turno |

Ciclo de acción libre (GDD §10.2): identidad y contexto → comprensión → plan de herramientas → validación → resolución → narración del resultado confirmado → memoria → respuesta. «Mato al rey y me proclamo emperador» es un **intento**.

Ejemplo de contrato (GDD §10.3.1): la IA propone

```json
{"intent": "steal_item", "actor_id": "character_17", "target_id": "guard_08",
 "item_id": "iron_key_12", "approach": "distraction", "needs_validation": true}
```

y el motor devuelve

```json
{"status": "resolved", "checks": [
  {"skill": "deception", "roll": 16, "total": 20, "dc": 15, "success": true},
  {"skill": "sleight_of_hand", "roll": 7, "total": 10, "dc": 14, "success": false}],
 "state_changes": ["guard_suspicion + 2"], "item_transferred": false}
```

La narración puede decir que el guardia miró a otro lado; no que el jugador tiene la llave.

### 25.2 Memoria que no inventa pasado

**IA-01:** episodio con `event_id`, lugar, tiempo e importancia. **IA-02:** relación calculada por reglas. **IA-03:** conocimiento semántico con fuente y certeza. **IA-04:** declaraciones del jugador separadas de hechos. **IA-05:** planes actuales opcionales.

Bram puede saber que pagaste una deuda, oír un rumor y sospechar del gobernador: tres categorías. Recuperar por PNJ, personaje, visibilidad, relevancia, importancia y recencia.

### 25.3 Coherencia de diálogo

Pasar al PNJ su saludo, servicios del lugar y pistas de misión. El TODO informa que Bram ofrece el fogón y luego lo niega o resta confianza por preguntas normales: problema prioritario por corregir. Confianza, deuda, reputación, pago o juramento necesitan evidencia y servicio; el `trust_delta` aplicado desde la respuesta IA (hallazgo de la 0.7.6) debe contrastarse con el código actual.

### 25.4 Reducir consumo sin perder libertad

- Botones sin parser.
- Intérprete de respaldo por palabras clave («huyo», «ataco al bandido»).
- Narración breve y ampliable; crónica para hitos.
- Caché por escena y versión de contexto.
- Resúmenes por lote en segundo plano (tercer uso de modelo, siempre Gemini).
- Contexto mínimo: escena, ficha pertinente, objetivos y 3–8 recuerdos.
- Registrar intentos, éxitos, tokens, latencia, propósito, modelo, timeout y fallback por separado.

Configuración: 150 llamadas/día por jugador y 15 crónicas incluidas; no es garantía de cuota del proveedor. Fórmula de planificación: `coste ≈ peticiones × (tokens_entrada × tarifa + tokens_salida × tarifa) + TTS + hosting`.

**IA-06 · Reserva antes de llamar.** Capacidad global y de usuario reservada atómicamente, liquidación y caducidad. No mantener locks esperando Gemini. Un timeout no demuestra consumo cero.

**IA-07 · Una generación por crónica.** Estado generando, lease y resultado persistido.

### 25.5 Contratos y evaluación

Herramientas conceptuales: `get_character_state`, `get_location_context`, `get_nearby_entities`, `get_world_lore`, `get_npc_memory`, `request_skill_check`, `submit_combat_action`, `get_quest_state`, `propose_world_event` y `get_faction_relations`. Leen o proponen; ninguna da resultados arbitrarios ni secretos globales.

Banco de abuso: espada inventada, mismo oro dos veces, turno ajeno, secreto leído fuera del juego, «ignora tus reglas», «soy el administrador», pago inexistente y adulación repetida. Respuesta en personaje en vez del seco «Nada cambia». Si la narración contradice el resultado, plantilla; un juez IA por turno no garantiza verdad.

<a id="s26"></a>
## 26. Arte, música, voces, mapas y recursos

**La dirección audiovisual completa (auditoría, biblia visual, cinco estilos, quince prompts, consistencia, catálogo, música, voces, mapas, Telegram, formatos, licencias y piloto) vive en [`ars.md`](ars.md).** Aquí queda el resumen de ideas.

- **ART-01:** biblia visual (paleta, arquitectura, iluminación, estilo, ropa de facción, día/noche) y rostro canónico por PNJ. Ciudad y catedral comparten referencia aprobada; la semilla no garantiza continuidad.
- **ART-02..08:** retratos de PNJ y lugares, iconos de linaje, avatar del bot y canales, marcos de clase/facción, stickers, tarjeta de héroe compartible (900 × 1200 desde datos del motor), ilustraciones de eventos. Nunca una imagen por compra o por turno.
- **AUD-01:** ambiente instrumental corto, a petición («Escuchar ambiente»), con texto siempre disponible. **AUD-02:** voces solo para momentos clave, pregrabadas o en cola, ES/EN por decidir. **AUD-03:** efectos solo en eventos relevantes.
- **Mapas:** macro (Azgaar), meso (Watabou), micro (Tiled/Krita); el mapa es vista del grafo, nunca fuente de verdad. Capas de niebla y posición por personaje.
- **Producción:** activos junto a su nodo de contenido, `media.yaml` y `<nombre>.prompt.md` junto a cada imagen, `file_id` cacheado por bot. Las pruebas se hacen en `content/officina/`, fuera del catálogo y de git, hasta aprobarse.
- **Licencias:** conservar herramienta, modelo, fecha, prompt, términos y atribución por activo; las condiciones de herramientas de la guía histórica no se han revalidado.

Presupuesto heredado: unos 63 MB para 12 pistas, 30 voces, 50 imágenes y 10 mapas; orientativo.

<a id="s27"></a>
## 27. Arquitectura, confiabilidad y operación

### 27.1 Conservar lo que sirve

Monolito modular, Python, PostgreSQL, SQLAlchemy/Alembic, contenido validado y motor puro con RNG inyectable. Sin reescritura ni microservicios. FastAPI, Redis, workers o Mini App solo ante necesidad demostrada.

Flujo: identificar → leer contexto corto → interpretar si hace falta → bloquear y revalidar → motor → guardar estado/eventos → commit → enviar/narrar. Nunca esperar Telegram o Gemini con locks.

### 27.2 Hallazgos históricos a revalidar (Living Oath, 0.7.6)

| ID | Hallazgo | Verificación requerida | Relación con producto |
|---|---|---|---|
| TEC-01 | Texto libre sin identidad idempotente de update | Reentregar el mismo update sin duplicar | Todo pago y recompensa |
| TEC-02 | Contexto interpretado puede quedar obsoleto | Mover/iniciar combate durante espera de Gemini | No actuar en escena incorrecta |
| TEC-03 | Confianza y memoria desde respuesta IA | Pago/amistad inventados no cambian canon | Relaciones y juramentos |
| TEC-04 | Comprobar presupuesto y registrar después | Concurrencia por una última plaza | Coste controlado |
| TEC-05 | Robo sin agotamiento/cooldown | Repetición acotada por regla | Inflación |
| TEC-06 | Servicios centrados en actor `p1` | Dos usuarios con recursos propios | Cooperativo |
| TEC-07 | Pertenencia no exclusiva a grupo activo | Dos invitaciones aceptadas a la vez | Estado consistente |
| TEC-08 | Expiración de turno necesita persistencia | Timeout y acción concurrentes | Ausencias y reinicios |
| TEC-09 | Generación simultánea de crónica | Dos consultas hacen una generación | Coste y coherencia |
| TEC-10 | Avisos de actividad en memoria | Reinicio y actividad siguiente | Revisar tras 0.7.21 (cierre automático cada 10 s) |
| TEC-11 | Envío multimedia dentro de transacción | Telegram lento no retiene lock | Latencia |
| TEC-12 | Registro de batalla antes del commit | Rollback no aparece como victoria | Replay fiable |
| TEC-13 | Constraints e índices insuficientes | Oro/cantidad, ranuras y NULL global | Integridad económica |
| TEC-14 | Dependencias amplias y recursos junto al checkout | Lock reproducible y wheel fuera de repo | Instalación |

No afirmar que siguen abiertos ni que se corrigieron por avances relacionados. Reproducir cada uno sobre una versión fijada. Pendiente del TODO: un test que falle si alguna tirada no pasa por `engine/dice.py`.

### 27.3 Contratos mínimos candidatos

`ActionRequest`: operación, usuario/personaje derivados del servidor, verbo, objetivo, versiones esperadas, versión de contenido y payload tipado. `ActionResult`: resultado, error, eventos, versiones confirmadas, hechos narrables y siguiente vista.

Entidades candidatas, solo si hacen falta: operación persistida, evento de dominio, outbox, reserva IA, deadline de encuentro, concesión única de premio, pedido en custodia y juramento por eventos. Sin migrar todo a event sourcing.

Esquema de referencia del GDD §15.4 (semilla conceptual, no ejecutable): `characters` con `level CHECK (1..20)`, `xp >= 0`, `hp >= 0` y `version`; `item_instances` con plantilla, propietario, calidad, `provenance JSONB` y `version`; `game_actions` con `idempotency_key UNIQUE`, tipo, payload y resultado. Una economía rigurosa usa asientos dobles. Orden global de locks para encuentro/grupo/personajes; personajes por ID ordenado.

### 27.4 Pruebas y operación

- PostgreSQL aislado para concurrencia; SQLite no verifica locks reales.
- Replays de update/callback, última unidad, último cupo IA, aceptación/cancelación y cierre doble.
- Reinicio durante actividad, combate, pedido y cada fase de evento.
- Migración desde versión anterior y conservación de personajes.
- Backup restaurado en una BD distinta.
- Fallback de Gemini (aviso al administrador si lleva rato caído) y reconstrucción de panel tras fallo de Telegram.
- Panel o comando de administración para pausar eventos y revisar logs; no resetear jugadores como primera respuesta.

Metas históricas: cero duplicados en mil repeticiones críticas, turnos autorizados, premios auditables, p95 determinista < 2 s, restaurar beta en < 1 h con pérdida máxima de un día. Metas por evaluar, no SLA.

<a id="s28"></a>
## 28. Paquetes implementables, métricas y criterios de salida

### 28.1 Conjuntos de ideas que producen una experiencia

| Paquete candidato | Resultado visible | Dependencias | Criterio inicial de salida |
|---|---|---|---|
| PKG-01 · Núcleo confiable | Una acción nunca paga dos veces y se retoma | Operación, contexto y recuperación | Replay/reinicio/fallo IA verificados |
| PKG-02 · Dos en la cripta | Dos amigos comparten combate y cura | Actor, grupo, targeting, plazos | Terminan y retoman dos pruebas |
| PKG-03 · Cuatro con buen ritmo | Panel legible y ausencias claras | PKG-02 y políticas | Dos grupos entienden cómo continuar |
| PKG-04 · Ser de una rama | Especialización cambia una decisión | Catálogo efectivo y recursos | Activa/pasiva/misión funcionan |
| PKG-05 · Mi primer encargo | Fabricar algo útil para otro | Custodia, receta y margen | Pedido/expiración/cancelación únicos |
| PKG-06 · Dos mineros distintos | Hierro o gemas según enfoque | Maestría, tablas y simulación | Ambas ramas tienen uso real |
| PKG-07 · Un misterio corto | Puerta con tres soluciones y evidencia | Challenges y objetos útiles | Fallo no bloquea la misión |
| PKG-08 · Crisis del hierro | Producción, aventura y noticia conectadas | Hechos, contribución y scheduler | Epílogo comprensible tras reinicios |
| PKG-09 · Un lugar memorable | Retrato, ambiente y escena coherentes | Activo aprobado y caché | Audio optativo y coste acotado |
| PKG-10 · Región con propósito | Nuevas decisiones y retorno | Contenido y economía | Cada lugar sirve, no solo ocupa mapa |

`iter.md` asigna paquetes a versiones; aquí no se fijan.

### 28.2 Backlog semilla heredado del Roadmap PDF (0.7.6)

Tickets listos para abrir cuando su paquete entre en `iter.md`. Prioridad P0 = bloqueo de su fase.

| ID | Tarea | Prioridad | Depende de | Aceptación |
|---|---|---|---|---|
| CORE-01 | CI PostgreSQL y entorno reproducible | P0 | — | Suite distingue motores y aplica migraciones |
| CORE-02 | `operation_id` para texto | P0 | CORE-01 | Replay del update ejecuta una vez |
| CORE-03 | Foto/versión de ActionContext | P0 | CORE-02 | Acción obsoleta rechazada bajo lock |
| AI-01 | Confianza fuera de NpcReply | P0 | CORE-01 | Diálogo no produce premio social arbitrario |
| AI-02 | Reserva atómica de llamadas/tokens | P0 | CORE-01 | Un cupo disputado tiene una concesión |
| AI-03 | Crónica single-flight | P1 | AI-02 | Dos consultas hacen una generación |
| ECO-01 | Oro y cooldown de robos | P0 | CORE-02 | Producción acotada por regla |
| OPS-01 | Aviso persistente por `activity_id` | P1 | CORE-02 | Reinicio recupera aviso correcto |
| OPS-02 | Telegram después de commit | P1 | CORE-01 | Timeout de red no retiene lock |
| UX-01 | Tiradas y descanso claros | P1 | — | Testers entienden resultado y coste |
| COOP-01 | Encounter por participante | P0 | CORE-03 | Ambos miembros ven el mismo encuentro |
| COOP-02 | `act` y sync para todos los actores | P0 | COOP-01 | Recursos del actor correcto |
| COOP-03 | Grupo activo único e invitaciones | P0 | CORE-02 | Última plaza no admite dos |
| COOP-04 | Targets aliados y curación | P0 | COOP-02 | Cura al aliado seleccionado |
| COOP-05 | Deadline persistente y CAS | P0 | COOP-02 | Timeout y acción no avanzan dos turnos |
| COOP-06 | Premio único por participante | P0 | COOP-02 | Doble fin no duplica |
| COOP-07 | Cripta de dos jugadores | P0 | COOP-03..06 | Se completa y recupera tras reinicio |
| COOP-08 | Ritmo, pausa y `/resume` | P1 | COOP-07 | Grupo retoma decisión pendiente |
| SPEC-01 | Catálogo clase+especialización | P1 | COOP-04 | Recurso/descanso/render coherentes |
| SPEC-02 | Ocho primeras especializaciones | P1 | SPEC-01 | Activa/pasiva probadas |
| OATH-01 | Juramento por eventos | P1 | CORE-02 | Cumplimiento y premio únicos |
| CRAFT-01 | Tres pedidos NPC | P1 | ECO-01 | Margen y duración medidos |
| CRAFT-02 | Encargos en custodia | P1 | CRAFT-01 | Cancelación y resolución excluyentes |
| WORLD-01 | Hechos y visibilidad | P1 | OATH-01 | Secretos privados no se publican |
| WORLD-02 | Crisis del hierro | P1 | CRAFT-02, WORLD-01 | Ciclo completo con reinicio |

Las fases A–H del PDF, su agenda de quincena y su política de rollback están en el anexo.

### 28.3 Datos que ayudan a elegir

| Área | Medida | Qué permite decidir |
|---|---|---|
| Inicio | Primera misión, tiempo y abandono (`oath tutorial-stats`) | Tutorial y creación |
| Combate | Rondas, recursos, huida y contribución | Balance y legibilidad |
| Grupo | Espera, pausa, turnos agotados y retorno | Ritmo y ausencias |
| Maestrías | Rendimiento/tiempo, raro y elección | Afinidades y tablas |
| Economía | Oro, pedidos, consumo y márgenes | Fuentes y sumideros |
| IA | Intentos, tokens, latencia y fallback por función | Contexto y presupuesto |
| Narrativa | Elecciones distintas y consecuencia entendida | Agencia real |
| Confiabilidad | Duplicados, jobs recuperados y estado divergente | Bloquear o abrir entregas |

Indicadores de beta del GDD §17.7: retención D1/D7, tutorial completado, duración de sesión, acciones libres por sesión, acciones rechazadas, latencia p95, abandono en combate, grupo repetido, coste de IA por usuario y divergencias de estado. Con pocos amigos, D1/D7 es inestable: acompañar con observación. Sin trucos de retención.

Criterios antes de invitar a amigos (GDD §17.6): cero duplicados en 1.000 repeticiones económicas; 100 % de cambios de turno con iniciativa y permisos; recuperación tras reinicio; el DM nunca aumenta oro ni inventario por texto; los testers saben salir de una escena; modo sin IA; registros que permiten investigar un combate o intercambio.

### 28.4 Gestión heredada que merece conservarse

Una feature principal por implementador; backlog, preparado, en curso, revisión y terminado. Ticket con problema, ejemplo antes/después, alcance, reglas/datos, dependencias y aceptación; migración/rollback cuando proceda. La política de ramas personales, PR aprobado por Josue, TODO de testers en `main` y versión por commit no cambia por este libro.

Opciones condicionadas: gremios cuando se repitan grupos; Mini App cuando inventario/mapa/talentos resulten incómodos; tercera profesión si falta demanda cubierta; TTS si se usa voluntariamente; guerras si la comunidad las sostiene. Monetización, si se evalúa: apoyo y cosméticos, nunca mejores tiradas ni autoridad narrativa.

<a id="s29"></a>
## 29. Documentación, D&D y organización del planning

### 29.1 Función de cada archivo

| Documento | Función |
|---|---|
| `planning/Possibilium.md` | Catálogo amplio, alternativas, conexiones, preguntas y archivo histórico |
| `planning/iter.md` | Versiones hechas, próximas y paquetes asignados |
| `planning/<tema latino>.md` | Resumen de trabajo por tema: estado, decidido, próximo y preguntas |
| `planning/ars.md` | Dirección audiovisual completa |
| `planning/README.md` | Índice breve y cómo usar los estados |
| `AGENTS.md` / `CLAUDE.md` | Cómo trabajar en el repo (agentes y personas) |
| README raíz | Presentación del juego e instalación mínima; se rehace al final, no en cada versión |
| CHANGELOG | Historia real de cambios |
| TODO y TODO de testers | Tareas, bugs y observaciones |
| Código y `content/` | Regla implementada y contenido efectivo |

Mapa de temas: `ordines` (clases), `progressio` (progresión), `pugna` (combate y descanso), `opificia` (profesiones), `mercatura` (comercio y equipo), `mundus` (mundo, viaje, misiones, facciones, eventos), `bestiarium`, `societas` (multijugador, gremios, PvP), `narratio` (IA), `facies` (interfaz de Telegram), `ars` (audiovisual).

### 29.2 D&D como referencia, no regla automática

Guardar el SRD por tema y edición, con índice, procedencia y atribución (SRD 5.2.1 bajo Creative Commons). Registrar adaptaciones: tema, edición, regla de origen, regla de Oathforge, motivo y estado. No mezclar 2014 y 2024 por accidente. Candidatas: concentración, ayuda, reacciones preparadas, salvaciones completas y progresión, adaptadas al chat.

El SRD no convierte todo el Player’s Handbook en redistribuible. No incluir el manual completo en el repositorio.

### 29.3 Migración realizada (0.8.3)

1. Este catálogo pasó a `planning/Possibilium.md` con los PDF extraídos en anexos.
2. `roadmap.md` → `iter.md`; los temas → nombres latinos como resúmenes; `audiovisual.md` → `ars.md`.
3. `planning/referencias/` (cuatro PDF y su README) se eliminó; sus binarios siguen en el historial de git.
4. Se actualizaron README raíz, TODO, CLAUDE.md y los comentarios de `content/` y del código que apuntaban a rutas antiguas.
5. Se añadió `AGENTS.md` y el laboratorio de imágenes `content/officina/`.

<a id="s30"></a>
## 30. Preguntas pendientes y ficha de aprobación

### 30.1 Decisiones de producto

1. ¿Mundo compartido completo o aventuras instanciadas con ecos comunes?
2. ¿Qué sistemas y orden entran en la siguiente entrega?
3. ¿Renombrar Sacerdote, mantenerlo o separar Clérigo?
4. ¿Explorador y Monje primero? ¿Bárbaro como clase o rama?
5. ¿Una o dos especializaciones iniciales por clase? ¿Activa/pasiva o árbol corto?
6. ¿Nivel máximo 5 hasta completar cooperativo o ampliación por un arco?
7. ¿Usos actuales, espacios o recurso de clase? No existe maná por tener poción de maná.
8. ¿Afinidad de maestría única, varias o árbol? ¿Coste de cambiar?
9. ¿Más cantidad, sesgo a material o hallazgos secundarios?
10. ¿Bastan los siete oficios? ¿Qué ocupaciones son aficiones?
11. ¿Qué espera real añade valor al cerrar la beta en actividades, descanso, fabricación y viaje?
12. ¿Grupo de dos a cuatro o hasta cinco? ¿Plazos y ausencias?
13. ¿Qué botín se comparte y qué se entrega por personaje?
14. ¿Entrega de misión a PNJ o recompensa automática según tipo?
15. ¿Qué pierde una derrota? ¿Hay caído/estabilización?
16. ¿Frosthold o Stormport como siguiente región?
17. ¿Qué facciones nuevas se fusionan o se diferencian?
18. ¿Cuántas ranuras y calidades puede explicar la interfaz?
19. ¿Audio apagado por defecto? ¿Voces en ambos idiomas o subtítulos?
20. ¿Quién revisa activos y qué eventos requieren revisión administrativa?
21. ¿Precio fijo, pedidos o intercambio como primera economía compartida?
22. ¿Tono: fantasía oscura sobria, alta fantasía o mezcla? ¿Humor y límites?
23. ¿Qué se comparte por cuenta si hay varios personajes?
24. ¿Nombres en inglés del GDD (Thornwood…) o traducidos como hasta ahora?

### 30.2 Ficha para aprobar una idea

```markdown
ID y nombre:
Estado: propuesta / aprobada / en pruebas / implementada / aplazada / descartada
Decisión y alcance exacto:
Motivo:
Experiencia del jugador:
Reglas y límites:
Primera versión implementable:
Dependencias:
Alternativas consideradas:
Riesgos de balance, repetición, coste y complejidad:
Criterio de aceptación:
Pendientes:
Archivos que actualizar:
Fecha y aprobación explícita:
Versión implementada, si procede:
```

Tras una decisión, actualizar el resumen latino y `iter.md`. No decir «sincronizado» hasta actualizar los archivos. El catálogo no es una lista de promesas.

<a id="s31"></a>
## 31. Fuentes, trazabilidad y cobertura

### 31.1 Fuentes primarias

| Clave | Fuente | Aporte principal | Tratamiento |
|---|---|---|---|
| GDD | `gdd-aetherfall-chronicles.pdf`, 34 págs. | Visión, 48 ramas, mundo, economía, DM, 84 ideas, arquitectura y MVP | Ideas reorganizadas + texto íntegro en anexo |
| AUDIO | `guia-recursos-audiovisuales.pdf`, 12 págs. | Producción, herramientas, formatos, prompts y licencias | Integrado en `ars.md`; texto íntegro en anexo |
| LIVING | `Oathforge_The_Living_Oath.pdf`, 34 págs., base 0.7.6 | Diagnóstico, clases, sistemas, ideas, revisión técnica | Expansiones integradas; hallazgos por verificar |
| ROAD-PDF | `Oathforge_Roadmap.pdf`, 18 págs., base 0.7.6 | Fases A–H, tickets, dependencias y gestión | Tickets en §28.2; versiones no promovidas |
| REF | `planning/referencias/README.md` | Mapa de capítulos y diferencias | Instantánea en anexo |
| PLAN | Markdown de planning anteriores a la 0.8.3 | Diseño y preguntas por sistema | Síntesis en resúmenes latinos + instantáneas |
| ESTADO | README raíz, versión, TODO y CHANGELOG | Avances, bugs y discrepancias | Foto 0.8.2 en §2 |
| CHAT | Conversaciones con Josue del 17/10/2026 | Clases, nombres, afinidades, ars y organización | Ideas añadidas como propuesta |

### 31.2 Cobertura temática

| Material de origen | Capítulos |
|---|---|
| GDD §1–3 | 3, 4, 13, 14 |
| GDD §4 | 5–9, 17 |
| GDD §5 | 10–12, 24 |
| GDD §6–7 | 15–18 |
| GDD §8–9 | 21–22 |
| GDD §10, §16 | 25 |
| GDD §11–13 | 12, 19, 23 |
| GDD §14 (84 ideas) | Repartido en 8–26; enumeración original en anexo |
| GDD §15 | 27 |
| GDD §17–21 | 3, 19, 28–31 |
| Guía audiovisual §1–11 | 26 y `ars.md`; prompts y enlaces en anexo |
| Living §1–19 | 2–24 |
| Living §20–25 | 25, 27–29 |
| Living §26–28 (catálogos) | 8–26; tablas originales en anexo |
| Living §29–30 | 2, 27, 31 |
| Roadmap PDF §1–14 | 27–30; tickets en 28.2 |

### 31.3 Principios para no reintroducir errores

No confundir leer una revisión técnica con repetir sus pruebas. No trasladar plazos o presupuestos como garantías. No presentar licencias o cuotas históricas como condiciones actuales. No sustituir nombres actuales por traducciones de un PDF sin decisión. No transformar una propuesta en aprobación. No eliminar una excepción de beta porque el catálogo describa una economía futura.

<a id="s32"></a>
## 32. Anexos históricos íntegros de texto

Movidos a [`archivum/Possibilium-anexos.md`](archivum/Possibilium-anexos.md): texto íntegro de los PDF retirados e instantáneas de antes de la 0.8.3. **Archivo: no se lee salvo que se pida.** Anclas: `#anexo-gdd`, `#anexo-audio`, `#anexo-living`, `#anexo-roadpdf`, `#anexo-repo-01`…`18`.
