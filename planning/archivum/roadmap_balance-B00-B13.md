# roadmap_balance — fases B00 a B13 (cerradas, archivo)

Fichas de trabajo de las fases hechas (0.10.21–0.10.41), sacadas de [`roadmap_balance.md`](../roadmap_balance.md) §14. El estado de cada una sigue en la tabla de §0.

### B00 · Fijar base y reconocer lo ya entregado

**Objetivo:** partir de la rama actual sin rehacer F15.
- [x] Leer versión, rama y diff desde este SHA; actualizar tabla de auditoría si se movió. (0.10.21, §2.3)
- [ ] Ejecutar validaciones de F15 que quedaron pendientes con bot y PostgreSQL disponibles. *La partida ES/EN con `tgtest` sigue pendiente; se hace con contenido nuevo que probar.*
- [x] Inventariar referencias a clase, nivel 5, cripta, usos por descanso y tutorial acelerado. (0.10.21, §2.3)
- [x] Registrar fuentes y separar defectos anteriores de cambios nuevos. (0.10.21; los 5 fallos de la línea base eran del `.env` y se arreglaron en 0.10.22)
**Archivos:** AGENTS, CHANGELOG, tests/features, planning/opificia, config, loader.
**Terminado:** baseline reproducible, fallos conocidos escritos, sin afirmar concurrencia validada con SQLite.

### B01 · Contratos de contenido y estado

**Objetivo:** separar clase, rama artesanal, recursos y elecciones.
- [x] Añadir esquemas de rama de clase, modificadores, recursos e hitos. (0.10.22)
- [x] Diseñar catálogo efectivo único; mantener contratos pequeños. (0.10.22, `engine/class_build.py`)
- [x] Elegir persistencia versionada y migraciones. (0.10.22, `characters.build` y migración 0013)
- [x] Validar ids únicos, referencias ES/EN, niveles 1–20 y opciones por clase. (0.10.22)
**Archivos:** content/schemas.py, loader.py, database/models.py; nuevos class_specializations/progression y class_build propuestos.
**Pruebas:** contenido inválido, rama ajena, duplicado de habilidad, coste negativo, requisito circular.
**Terminado:** una ficha de prueba puede cargarse, calcularse y serializarse sin alterar maestrías. **Hecho en 0.10.22.** Los modificadores existen como elección encolada (`Choice`), pero su contenido concreto —las dos opciones de cada rama— es de B07. Las 41 ramas están declaradas y validadas, ninguna elegible.

### B02 · XP híbrida y entrega al PNJ

**Objetivo:** implementar la regla central antes de diseñar recompensas definitivas.
- [x] Separar grant_xp de aplicación de niveles. (0.10.24, `characters.apply_levels`)
- [x] Añadir cap por hitos y recalcular tras premio/hito. (0.10.24, efecto `milestone`)
- [x] Estado ready_to_turn_in, validación de dador y pago atómico. (0.10.24, estado `ready` y `quests.turn_in`)
- [x] Mostrar por separado XP faltante e hito faltante. (0.10.24, `sheet.level_gate`)
- [x] Integrar diario, logs y logros de nivel. (0.10.24; el diario y `/quests` muestran la misión lista y su dador)
**Archivos:** engine/progression.py, services/characters.py, services/quests.py, schemas, callbacks, render, locales, rulebook.
**Pruebas:** casos §4.2; entrega doble; falta de XP; XP acumulada; reinicio después del commit.
**Terminado:** misión de prueba permite nivel 10 solo con ambas condiciones y sin duplicar pago. **Hecho en 0.10.24**, probado con `tgtest` en ES y EN sobre El Viejo Colmillo, que ya se entrega a Bram. Los dos hitos existen y funcionan; las misiones que los conceden las escribe B09. Pendiente: la carrera de dos entregas simultáneas con PostgreSQL.

### B03 · Motor de recursos y efectos

**Objetivo:** reemplazar dependencia universal de usos por descanso.
- [x] Barra principal, generación, coste y recuperación por fase. (0.10.25)
- [x] Estados con origen, duración y acumulación explícita. (0.10.25: se refrescan, no se acumulan)
- [x] Cooldowns por turno y adaptación de control a jefes. (0.10.25: un turno y el resto a vulnerable)
- [x] Sincronizar recursos del encuentro con personaje. (0.10.25, `characters.pools` y migración 0014)
- [x] Adaptar pociones/pergaminos y coste de acción. (0.10.25: la clase de quien bebe decide barra o usos)
- [x] Mantener ataque gratuito útil. (0.10.25: el coste solo lo llevan las habilidades)
**Archivos:** engine/combat.py, services/combat_service.py, characters.py, schemas.py, items.yaml.
**Pruebas:** falta de recurso, coste una vez, pasivas sin bucles, expiración, save/reload, repetición de bonus.
**Terminado:** un luchador de Foco y un usuario de Maná completan varios combates consecutivos sin economía rota. **Hecho en 0.10.25** con el Guerrero y el Hechicero como pilotos, probado en la suite y con `tgtest`. Las otras doce clases siguen con usos por descanso hasta B06, y las dos formas conviven sin tocarse. Pendiente: los contadores de apoyo por rama (B07).

### B04 · Catálogo efectivo, selección y elecciones

**Objetivo:** rama modifica juego, no solo nombre.
- [x] Catálogo usado por ficha, motor, descanso, simulador y reportes. (0.10.27, `characters.effective`)
- [x] Selección directa al 10 con confirmación y validación de clase. (0.10.27, `/path`)
- [x] Modificadores fijos al 13/17 y entrenamientos 5/12/18. (0.10.27)
- [x] Reelección excepcional por cambio sustancial de versión, de un solo uso. (0.10.27, `revision`)
- [x] Eliminar anuncio antiguo de especialización al 5. (0.10.27; también la mejora del nivel 4)
**Archivos:** class_build propuesto, class_specializations service propuesto, characters, render, handlers, locales.
**Pruebas:** dos ramas elegidas concurrentemente, rama ajena, elección repetida, elección pendiente al saltar niveles.
**Terminado:** la selección altera habilidades y recursos en todas las vistas y no recarga reservas gratuitamente. **Hecho en 0.10.27**, probado con una rama sintética completa porque ninguna de las 41 está lista aún: el contenido de cada rama es B07. El simulador aún no modela rama ni entrenamientos (B12).

### B05 · Compañeros, formas y dispositivos

**Objetivo:** base para ramas complejas antes de multiplicar implementaciones.
- [x] Auxiliar automático con propietario y frecuencia de acción. (0.10.28, `Entity` y `_run_entities`)
- [x] Identidad permanente de servidor y bestia; configuración de constructo. (0.10.28, `services/companions.py`; el constructo, la torreta y el tótem son plantillas con su tope de uno)
- [x] Dos entidades del Invocador y Convergencia. (0.10.28)
- [x] Transformación que sustituye acciones sin crear vida. (0.10.28, `content/forms.yaml`)
- [x] Logs agregados legibles y comportamiento al huir/derrota. (0.10.28: una línea por acción de aliado; nada actúa si el dueño cae)
**Archivos:** engine/combat, encounter state, services/combat_service, modelos/versionado, schemas.
**Pruebas:** objetivos muertos, doble actuación, muerte del dueño, carga desde JSON, límite dos, transformaciones sucesivas.
**Terminado:** Demonólogo, Invocador y Cambiaformas tienen un recorrido técnico completo en escenarios de prueba. **Hecho en 0.10.28**, con ramas prestadas en las pruebas porque ninguna está lista: lo que falta es escribir las ramas (B07) y el flujo para poner nombre al servidor en Telegram, que se hace con la rama del Demonólogo. El simulador aún no invoca (B12).

### B06 · Rediseñar 14 clases base y nivel 1–9

**Objetivo:** todas juegan bien antes de especializarse.
- [x] Hechicero fusionado y seis clases nuevas. (0.10.23 el renombrado; grupo 1 en 0.10.29, grupo 2 en 0.10.30, grupo 3 en 0.10.31)
- [x] Kit de inicio y curva por clase. (0.10.29–0.10.31)
- [x] Equipo recomendado, atributos y recurso descritos. (0.10.29–0.10.31; solo se añadió un objeto, las vendas del Monje)
- [x] No anticipar toda la especialización: conservar identidad base. (0.10.29–0.10.31: nada de lo de la rama está en las clases)
- [ ] Enseñanza adaptada a recurso y opciones de cada clase. *Es la campaña (B09): el tutorial actual no distingue barras.*
**Orden recomendado:** Guerrero/Bárbaro/Paladín/Pícaro/Monje; Clérigo/Hechicero/Druida/Bardo; Brujo/Explorador/Artífice/Chamán/Caballero.
**Pruebas:** 14 clases a niveles 1, 3, 5 y 9; encuentros individuales, grupos y varios combates sin descanso completo.
**Terminado:** ninguna necesita rama, oficio o compañero de otro jugador para superar iniciación. **Hecho en 0.10.31** para las catorce, con una prueba única (`tests/engine/test_class_roster.py`). Los suelos son de simulador, no de partida: la prueba de la iniciación con cada clase es B09. Faltan los seis retratos (`TODO-images.md`).

### B07 · Entregar las 41 ramas por familias

**Objetivo:** cumplir el catálogo completo, sin publicar nombres vacíos.
- [x] Lote A: daño directo, marcas, defensa y maniobras. (0.10.32: 20 ramas)
- [x] Lote B: curación, regeneración, melodías, reacciones y control. (0.10.33: 12 ramas, 32 de 41)
- [x] Lote C: entidades, formas, tótems y tiempo. (0.10.34: 9 ramas, 41 de 41)
- [x] Para cada rama: pasiva/técnica 10, desarrollo fijo, dos elecciones y culminación.
- [ ] Separar Catalyst de Alquimia en reglas y guías.
- [x] Crear prueba que demuestre una decisión característica de cada rama.
**Archivos:** classes.yaml, class_specializations propuesto, efectos del motor, simulador, i18n.
**Pruebas:** cuatro combinaciones 13×17 por rama (164 configuraciones al 20), con casos por mecánica y barridos de simulación.
**Terminado:** las 41 ramas son seleccionables solo cuando tienen recorrido 10–20 y material ES/EN completo.

### B08 · Tiempos, descanso, derrota y economía

**Objetivo:** dejar de equilibrar con ayudas de beta.
- [x] Aplicar tabla §12; retirar aceleración residual del tutorial. (0.10.35)
- [x] Descanso corto y largo con interrupción segura. (0.10.35)
- [x] Matriz de acciones busy; permitir consulta y gestión compatibles. (0.10.35: ya estaba casi toda; se añade no vender la herramienta en uso)
- [x] Herramientas en mochila y selección ya implementada preservadas. (0.10.35)
- [ ] Precios normales (hecho en 0.10.35), stock crítico y cobertura T0/T1 de clases (pendiente, con la campaña de B09).
- [x] Derrota inicial con coste limitado y retorno seguro. (0.10.35: 10 % con tope de 15 por nivel)
**Archivos:** activities.py, inventory.py, home.py, crafting.py, config.py, items/recipes/professions, render/rulebook.
**Pruebas:** reiniciar temporizador, cambiar/vender herramienta comprometida, doble claim, descanso cancelado, arbitraje de lotes, ausencia de oro.
**Terminado:** sesión de 60–90 minutos funcional sin atajos ni bloqueos económicos.

### B09 · Campaña común hasta el Recaudador

**Objetivo:** aprender sistemas mediante la historia.
- [x] Escribir lore del mentor y texto ES/EN. (0.10.37, provisional)
- [x] Actos I–VI con eventos y objetivos verificables. (0.10.37)
- [x] Ocho variantes de las tres tareas de oficio. (0.10.37: una misión con tres objetivos por oficio)
- [x] Habitación, plano, maestrías, pesca/cocina, diario, reputación, huida. (0.10.36–0.10.37; sin objetivo de diario ni de título)
- [x] Recaudador con señales, protección y recarga. (0.10.37)
- [x] Entrega que establece el hito 10 (0.10.37); el camino para la XP faltante ya lo cubre el hito sin perder XP (0.10.24).
**Archivos:** quests.yaml, npcs.yaml, monsters.yaml, content/world, fallbacks, quest service, media.
**Pruebas:** todas las clases; cada ruta de oficio; jugador que vende material o cambia oficio; falta/exceso de XP.
**Terminado:** primera sesión completa y campaña sin callejones hasta la selección al 10.

### B10 · Ciervo y graduación

**Objetivo:** culminar aprendizaje usando la rama escogida.
- [x] Selección directa integrada con el gremio. (0.10.38: la misión «Tu camino» lleva a /path)
- [x] Preparación T1 asequible sin exigir conjunto completo. (0.10.38: una pieza de nivel 10 a elegir)
- [x] Ciervo: endurecimiento, carga y vulnerabilidad. (0.10.38)
- [x] Entrega de graduación (0.10.38); la apertura de región es B11.
- [x] Ayuda contextual con respuestas válidas por clase. (0.10.38)
**Pruebas:** 41 ramas al nivel 10; victoria, derrota, huida y retorno; ayuda sin revelar resultados futuros.
**Terminado:** todas las ramas superan el encuentro con preparación razonable y el diario explica el paso siguiente.

### B11 · Región y aventuras 11–20

**Objetivo:** que diez niveles nuevos tengan contenido.
- [ ] Validar lore y nombre de región cercana. (propuesta implementada en 0.10.39: pendiente de aprobación de Josue)
- [x] Grafo conectado, viajes directos, refugio y relación con Crownreach. (0.10.39)
- [x] Cuatro actos, criaturas con patrones y fuentes T1. (0.10.39; **sin** secundarias ni contratos repetibles)
- [x] Culminación 20 (la prueba de las balizas, 0.10.39). Contextos de modificadores 13/17: los combates normales del valle; sin encuentros a medida.
- [x] Actividades de veterano sin multijugador ni mazmorra. (0.10.39: recolección T1 en la cantera, el bosque y la ribera)
**Archivos:** mundo, NPC, misiones, monstruos, botines, recetas especiales, logros, arte.
**Pruebas:** rutas, recursos accesibles, contenido según nivel, objetivos alcanzables, regreso a ciudad.
**Terminado:** recorrido continuo hasta 20 y aventuras donde usar técnica final.

### B12 · Balance integral

**Objetivo:** medir campaña, no solo un jabalí.
- [x] Simulador usa builds efectivos, equipo y decisiones de recursos. (0.10.40: política informada, kit T1, pociones, secuencias)
- [x] Escenarios §15 (parcial) y política informada común. (0.10.40; sin barrido 13×17 ni uso conservador/explosivo)
- [ ] Runs de dos sesiones diarias para medir ritmo. (0.10.40: sólo un modelo con tiempos supuestos; faltan sesiones reales)
- [x] Ajustar XP, daño, recuperación, tiempos y economía por datos. (0.10.40: XP del valle, Custodio, Recaudador, criaturas 6–9; el ritmo sigue corto)
- [x] Duración entre HEAL/DEFF/DMG/CONTROL medida: defensa +30 % sobre daño, no el doble. (0.10.40)
**Terminado:** informe de balance con versión/semillas, defectos resueltos y limitaciones explícitas.

### B13 · Retirar cripta, corregir documentación y preparar reset

**Objetivo:** eliminar contradicciones antes de lanzar.
- [x] Revisar referencias de mundo, objetos, logros y pruebas a cripta. (0.10.41)
- [x] Sustituir misiones antiguas y logros incompatibles de la nueva edición. (0.10.41)
- [x] Actualizar resúmenes, TODO, roadmap e iter. (0.10.41; el README raíz se rehace en B14)
- [x] Crear procedimiento de reinicio que conserve preferencias. (0.10.41: `planning/reinicio_lanzamiento.md`)
- [ ] Ensayo de backup/restore y proceso en staging. (0.10.41: ensayado en pruebas contra PostgreSQL; falta el staging con una copia de producción)
**Terminado:** cero referencias activas rotas y reinicio ensayado sin tocar datos reales.
