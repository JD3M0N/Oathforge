# Oathforge — roadmap_balance.md
## Clases, especializaciones, progresión híbrida y campaña 1–20

**Base auditada:** `josue-development`, versión **0.10.19**, commit `107ccacba523004a0059a3f3b1be796c3591ee65`.
**Fecha de revisión:** 20 de octubre de 2026, zona America/Havana.
**Destino recomendado:** `planning/roadmap_balance.md`.
**Entrega:** documento de diseño e implementación; no implica cambios de código, publicación, reinicio de personajes ni sincronización con GitHub.
**Versionado:** próximos parches disponibles de **0.10.x**. No reservar números exactos mientras continúe el desarrollo. **0.11 queda para multijugador**.

> Objetivo: convertir la base individual de Oathforge en una aventura completa de nivel 1 a 20, con 14 clases rediseñadas, 41 especializaciones funcionales, oficios relevantes y una campaña que enseñe jugando. La IA interpreta y narra; el motor valida cada resultado.

### Estados usados

- **Aprobado:** decisión explícita del usuario durante el diseño.
- **Implementado en la base:** encontrado en código o contenido; no equivale a probado en producción en esta revisión.
- **Diseño de implementación:** solución concreta recomendada para ejecutar una decisión. Puede ajustarse si mantiene su intención.
- **Semilla de balance:** cifra o calendario de poderes que debe medirse antes de convertirse en definitivo.
- **Futuro / pendiente:** preservado al final, sin ampliar silenciosamente el alcance de esta entrega.

**Corrección de inventario:** el catálogo validado contiene **41 ramas**, no 38 como se dijo en la conversación. Se conservan todas las ramas aprobadas; no se añaden tres nuevas. Suma: 4+2+2+3+3+6+3+2+3+2+2+4+3+2 = 41.

## Índice

0. [Seguimiento de la implementación](#seguimiento)
1. [Contrato aprobado](#contrato)
2. [Auditoría y discrepancias](#auditoria)
3. [Arquitectura y contratos](#arquitectura)
4. [Progresión híbrida de XP e hitos](#progresion)
5. [Recursos, combate y progresión de poderes](#combate)
6. [Catálogo de clases y 41 especializaciones](#catalogo)
7. [Invocaciones, compañeros y transformaciones](#companeros)
8. [Misiones y campaña inicial](#campana)
9. [Jefes: Recaudador y Ciervo](#jefes)
10. [Región cercana y aventura 11–20](#region)
11. [Oficios, tiers, equipo y economía](#economia)
12. [Tiempo, descanso y acciones mientras estás ocupado](#tiempos)
13. [Interfaz, tutorial verificable e IA](#interfaz)
14. [Fases de implementación](#fases)
15. [Plan de balance y validación](#validacion)
16. [Reinicio y lanzamiento](#lanzamiento)
17. [Trazabilidad y documentación](#trazabilidad)
18. [Puerta de salida](#salida)
19. [Fuentes y límites](#fuentes)
20. [Notas e ideas futuras](#notas)

<a id="seguimiento"></a>
## 0. Seguimiento de la implementación

Hito **0.10-I** del [roadmap general](roadmap.md). Se avanza **fase a fase**: cada fase sale en uno o varios parches 0.10.x y se para para probarla antes de seguir. Al cerrar un parche se marcan aquí sus casillas (`[x] … (0.10.N)`), en el roadmap general y en `TODO.md`.

| Fase | Estado | Versión |
|---|---|---|
| B00 · Base y auditoría | ✅ Hecha | 0.10.21 |
| B01 · Contratos de contenido y estado | ✅ Hecha | 0.10.22 |
| B02 · XP híbrida y entrega al PNJ | ✅ Hecha | 0.10.24 |
| B03 · Motor de recursos y efectos | ✅ Hecha | 0.10.25 |
| B04 · Catálogo efectivo, selección y elecciones | Pendiente | — |
| B05 · Compañeros, formas y dispositivos | Pendiente | — |
| B06 · 14 clases base (1–9) | Pendiente | — |
| B07 · 41 ramas | Pendiente | — |
| B08 · Tiempos, descanso, derrota y economía | Pendiente | — |
| B09 · Campaña hasta el Recaudador | Pendiente | — |
| B10 · Ciervo y graduación | Pendiente | — |
| B11 · Región y aventuras 11–20 | Pendiente | — |
| B12 · Balance integral | Pendiente | — |
| B13 · Retirar cripta, documentación y reinicio | Pendiente | — |
| B14 · Candidato y lanzamiento | Pendiente | — |

Decisiones tomadas al empezar (21-10-2026): el mentor (N01) y la región 11–20 (N02) los **propone el agente como provisionales** en `planning/` y Josue los aprueba antes del texto final de B09 y B11. Antes de empezar se borraron todos los jugadores de la base de desarrollo (`oath reset-players --yes`); el reinicio de lanzamiento que conserva preferencias es otro procedimiento (§16, B13).

<a id="contrato"></a>
## 1. Contrato aprobado

| ID | Decisión |
|---|---|
| D01 | Nivel inicial 1 y máximo 20. No hay nivel 0. Expansiones futuras de diez niveles; T2 corresponde al tramo 21–30. |
| D02 | Progresión híbrida: XP y hitos narrativos. La misión del Recaudador abre el nivel 10 **si también hay XP suficiente**. No sube automáticamente a cualquiera. |
| D03 | Implementar todas las clases candidatas; fusionar Mago y Hechicero en Hechicero / Sorcerer. Son 14 clases. |
| D04 | Sacerdote pasa a Clérigo / Cleric. La clase de dispositivos se llama Artífice / Artificer. |
| D05 | Rediseñar las clases existentes. Libertad para mecánicas propias de Telegram, conservando la separación entre motor y narración. |
| D06 | Una especialización activa por personaje; múltiples opciones por clase. Catálogo de §6 aprobado en identidad, nombres y roles. |
| D07 | Elegir directamente la especialización al nivel 10 y antes del Ciervo. No pruebas prestadas, elección provisional ni misión de investidura adicional. |
| D08 | Progresión fija más una elección entre modificadores en nivel 13, otra en 17 y técnica culminante en 20. Modificadores fijos. |
| D09 | Sin cambio libre de especialización en esta entrega. Sí reelección gratuita si una actualización altera sustancialmente su funcionamiento. |
| D10 | Cada rama debe ser divertida y viable en solitario; el multijugador de 0.11 ampliará su utilidad. No se construye cooperativo encubierto. |
| D11 | Recursos propios: una barra principal y, cuando sea necesario, un contador sencillo. Recuperación explícita y acción básica útil. |
| D12 | Invocador: repertorio mixto, dos entidades activas como máximo y **Convergencia** al 20; no tercera entidad. Ayuda para elegir combinaciones. |
| D13 | Demonólogo: el mismo servidor permanente con nombre; evoluciona y cambia de forma, conservando identidad. |
| D14 | Artífice **Catalizador / Catalyst** conserva temática de reacciones. No es la rama Galvanista ni el oficio Alquimia. |
| D15 | Campaña inicial común, reescrita por completo, hasta nivel 10; practicar obligatoriamente sistemas relevantes, no todos los oficios. |
| D16 | Primer personaje sin salto del tutorial. Futuros personajes adicionales y su atajo quedan para después. |
| D17 | Nuevo mentor cálido, aventurero y memorable. Nombre, linaje, biografía y encaje preciso en el lore pendientes de escritura. |
| D18 | Trama de cargamentos desviados y órdenes falsas. Recaudador como primer jefe principal; Ciervo de Hierro como estreno de especialización. |
| D19 | Eliminar Cripta Hundida de la experiencia activa; no introducir mazmorras en esta versión. |
| D20 | Nueva región relativamente próxima a Crownreach para 11–20, con lore conectado. Crownreach sigue siendo ciudad principal. |
| D21 | Campaña inicial: 5–10 días. Nivel 20: 15–20 días acumulados. Referencia: dos sesiones diarias de 60–90 minutos. No hay cupo diario obligatorio aprobado. |
| D22 | Entregar misiones al PNJ antes de cobrar. El sistema comprueba hechos del jugador; leer una explicación no sustituye una acción mecánica. |
| D23 | Elegir al menos un oficio real durante la campaña. Cambiar oficio pagando sigue permitido; dos oficios activos, maestrías libres y aficiones sin plaza. |
| D24 | T0 artesanal de rango 0–2 y T1 de rango 3–5. Equipo de combate T1 desde nivel 10. Mantener utilidad de T0. |
| D25 | Se aprueba calibrar tiempos normales según §12; no conservar aceleraciones de beta ni la aceleración residual de una vez por misión. |
| D26 | Herramienta necesaria en mochila, sin equipar. Si hay varias especializadas se selecciona preferencia por disciplina, fijada al iniciar la actividad. |
| D27 | Mientras hay actividad: consulta y gestión compatibles; no viaje, combate voluntario, fabricación ni otra actividad física incompatible. |
| D28 | Botón 💡 ¿Qué hago? en primeros combates; consejos deterministas y sin coste de IA. |
| D29 | Enseñar preparación, pociones y huida con bomba de humo. Soluciones libres mediante IA y su enseñanza se posponen. |
| D30 | Ventajas ocasionales fuera del combate, sin bloquear misiones ni recursos esenciales por clase. |
| D31 | Derrota inicial: retorno seguro, coste temporal y pérdida económica pequeña y limitada; no perder equipo equipado. |
| D32 | Reinicio limpio del estado de juego antes del lanzamiento: personajes y progreso, inventarios, logros, reputaciones y consecuencias de sus partidas. Conservar preferencias de cuenta y registros técnicos necesarios. |
| D33 | ES/EN en todo contenido e interfaz. Gemini sigue siendo el proveedor. Solo services escribe estado. |

**Delegado al diseño:** atributos y cierre de primera sesión. Se recomienda mantener creación por puntos y añadir tres entrenamientos sencillos en 5, 12 y 18; primera sesión completa el ciclo alistamiento → salida → regreso → entrega. El nivel 3 al finalizar esa sesión es objetivo experimental, no requisito impuesto.

<a id="auditoria"></a>
## 2. Auditoría de la versión 0.10.19

### 2.1 Qué reutilizar

| Área | Evidencia leída | Consecuencia |
|---|---|---|
| Progresión | `engine/progression.py`: cinco umbrales 0/200/500/1000/1800; `level_for_xp` solo usa XP | Hay que construir los hitos; no asumir que el híbrido ya existe. |
| Subida | `services/characters.py::grant_xp`: aplica niveles, +2 principal en ASI_LEVEL, PV y usos de clase | Separar otorgar XP, calcular elegibilidad y aplicar nivel; reactivar cálculo al completar hitos. |
| Clases | `content/classes.yaml`, `GameClass` y `ClassAbility` | Ocho clases y nombres de ramas no equivalen a 41 ramas jugables. |
| Personaje | `Character.specialization` ya existe; `resources` almacena usos por habilidad | Reutilizar el campo de selección; versionar/revisar el significado de recursos. |
| Combate | `engine/combat.py`: estado serializable, acciones, bonos, estados y dos bandos | Extender por efectos tipados; no sustituir por decisiones de IA. |
| Catálogo de combate | `combat_service.ability_defs` devuelve solo habilidades de clase; sincronización copia usos de p1 | Construir catálogo efectivo y persistir barras, elecciones y compañeros correctamente. |
| Simulador | `tools/simulate.py`: clases/niveles, política por tipos de habilidad y usos | No evalúa correctamente las nuevas ramas sin nuevas políticas y escenarios. |
| Misiones | `quests.advance` da recompensas al completar objetivos | Añadir estado lista para entregar y entrega atómica al dador. |
| Oficios | Resumen 0.10.19: ocho oficios, 60 recetas, Sastrería, técnicas y planos | Reutilizar lo entregado; no repetir F15. |
| Maestrías | `services/specializations.py` y `schemas.Specialization` gestionan ramas de campo/Pesca | Crear dominio de especializaciones de clase separado, sin romper las doce ramas artesanales. |
| Actividades | `rules_snapshot` y modificadores fijados al iniciar | Conservar garantía ante cambios de catálogo, herramienta o reinicios. |
| Habitación | `characters.home`, contenedor de objetos y servicio `home.py` existente | Integrar en nueva campaña; no reconstruir el cofre. |
| Beta | `config.py`: beta_instant_rest y beta_instant_tutorial activos por defecto; `tutorial_boost` sigue una vez por misión fuera de beta | Apagar flags no basta: retirar también la aceleración residual. |
| Herramientas | `activities.check` valida existencia con inventario | No agregar ranura de equipo; preservar mochila frente a cofre. |
| Estadísticas | `admin.tutorial_runs` mide tiempo de pared entre misiones | Separar tiempo conectado, esperas e inactividad para calibrar sesiones reales. |
| Administración | `admin.delete_player` elimina User y dependencias | No usarlo sin adaptación para un reinicio que conserve preferencias de cuenta. |

### 2.2 Documentación desactualizada y cambios de criterio

- `ordines.md` sigue declarando ocho clases, sin nuevas antes del cooperativo y ramas al 5. Este contrato sustituye esas decisiones.
- `progressio.md` conserva 1–5 y referencias a cripta. Sustituir por 1–20 híbrido y la nueva campaña.
- `mundus.md` ya refleja habitación y once entradas tutoriales, pero conserva encabezados de diez y numeración repetida. Auditar YAML, no copiar esa tabla como fuente definitiva.
- `roadmap.md` tiene cabecera de base 0.9.1 y varias versiones orientativas ya ocupadas. No asignar esta expansión a parches históricos.
- `opificia.md` describe F15 cerrado; algunas secciones de otros resúmenes aún lo llaman pendiente.
- El cierre 0.10.19 **deja pendientes la partida ES/EN con tgtest y pruebas de concurrencia PostgreSQL**. No marcarlas aprobadas por leer el changelog.
- Se abandona la prueba previa de ramas, la investidura como misión obligatoria, nivel 25, tercera invocación y Galvanista. No reaparecen por copiar propuestas anteriores.
- Recaudador ya no es simplemente un jefe opcional de 7–8: su misión es la puerta narrativa al 10.
- Sin cripta hay que revisar botines, planos, materiales T1, logros, títulos, rumores, texto de PNJ, rutas, pruebas y referencias de arte.

### 2.3 Auditoría B00 sobre 0.10.20 (21-10-2026)

Hecha sobre `josue-development` en **0.10.20** (`e6f4999`), árbol limpio y sin nada nuevo en `origin/main`. Todo lo que §2.1 daba por existente se confirma en esta base; las migraciones siguen en `0012`, así que la de clases será la **0013**.

**Línea base de pruebas.** Suite completa: **410 pasan, 5 fallan**, y los cinco fallos son de configuración local, no defectos:

| Prueba | Causa |
|---|---|
| `tests/services/test_services.py::test_user_language_normalized` | `.env` tiene `DEFAULT_LANGUAGE=en` y la prueba espera el `es` por defecto. |
| 4 de `tests/ai/test_client.py` (reintentos y enfriamiento) | `.env` define `GEMINI_MODEL_FALLBACK`, que añade un modelo más a la cadena y consume la respuesta que la prueba deja sin usar. |

Ambos grupos pasan con los valores por defecto. Corresponde **neutralizar esos dos ajustes en `tests/conftest.py`** para que la suite no dependa del `.env` de cada máquina; se arregla en B01, no aquí, para no mezclar defectos previos con el trabajo nuevo. En Windows, `pytest` necesita `--basetemp` dentro de un directorio escribible si el temporal del sistema está restringido.

**Pendiente de F15 que sigue abierto:** la partida ES/EN con `tgtest` y las pruebas de concurrencia con PostgreSQL. No se dan por hechas.

**Inventario de lo que esta entrega tendrá que tocar:**

| Qué | Dónde aparece |
|---|---|
| ~~Ids de clase `priest` y `mage`~~ **Renombrados a `cleric` y `sorcerer` en 0.10.23**, con sus carpetas de retratos y los textos visibles | `content/classes.yaml`, `content/abilities.yaml`, `content/rulebook.yaml`, `class_specializations.yaml`, `bot/render.py`, `services/inventory.py`, `tools/simulate.py`, `content/classes/{cleric,sorcerer}/`, seis archivos de prueba |
| Rama anunciada al nivel 5 | `services/characters.py:308` (`progress.specialization_soon`), `bot/render.py:37,190,1989`, `i18n/locales/{es,en}.yaml:548` |
| Techo de nivel 5 | `engine/progression.py` (`XP_THRESHOLDS`, `MAX_LEVEL`), `bot/render.py:1225,1703` |
| ASI del nivel 4 (lo sustituyen los entrenamientos 5/12/18) | `services/characters.py:19,290` |
| Usos por descanso como único recurso | `characters.full_resources` y `grant_xp`, `exploration.py:287`, `inventory.py:169` (`restore_spell_charge`, `schemas.py:192`), `combat.py` (`abilities: {clave: usos}`), `simulate.py:46` |
| Atajos de beta | `config.py:55-58`, `activities.py:234,241,263,267,298,446,449`, `quests.py:172-201` (`tutorial_boost`), `render.py:1710-1711` |
| Cripta Hundida (se retira en B13) | zona entera `content/world/terra_coronata/sunken_crypt/` (5 lugares), 31 referencias en `content/*.yaml` (misión `crypt_bones`, monstruos `crypt_skeleton` y `crypt_warden`, logros, objetos, reglamento, respaldos), `services/{exploration,quests,achievements}.py`, `content/achievement_schemas.py`, ocho archivos de prueba |
| Misiones actuales | 13 en `content/quests.yaml`: once del tutorial (`tut_*`), `crypt_bones`, `old_tusk` y `sealed_box`; la campaña nueva las sustituye en B09 |

<!-- B00:AUDIT -->

<a id="arquitectura"></a>
## 3. Arquitectura y contratos de implementación

### 3.1 Reglas que no cambian

1. `engine/` puro, con RNG inyectable mediante dados existentes.
2. `services/` es la única capa que escribe; handlers y render no adjudican XP ni premios.
3. Bloquear personaje/encuentro al confirmar; no E/S de Gemini o Telegram mientras se sostiene el lock.
4. Botones y mensajes de fabricación/entrega con idempotencia. Reintentar no consume recursos dos veces.
5. Catálogo ES/EN validado antes de arrancar.
6. Narración basada en hechos; ausencia de IA no bloquea campaña, selección o combates.
7. Reutilizar temporizadores, diario, hechos, snapshots y menús existentes.

### 3.2 Separar tres conceptos de especialización

| Concepto | Persistencia recomendada | Regla |
|---|---|---|
| Rama de clase | Campo existente `Character.specialization` | Una, elegida al 10; sin cambio libre. |
| Modificadores de clase | Nuevo estado tipado/versionado de elecciones | Uno por hito 13/17; no se mezclan con planos. |
| Rama de maestría/Pesca | `Character.crafting["spec"]` actual | Mantener rango 2, cambio de pago y pausa de rama anterior. |

**Archivos nuevos propuestos**, no existentes: `content/class_specializations.yaml`, `content/progression.yaml`, `oathforge/engine/class_build.py`, `oathforge/services/class_specializations.py`. Verificar estructura al implementar y evitar renombrar el dominio artesanal si no hace falta.

El loader carga y valida ambas familias con nombres inequívocos. No reemplazar `content/specializations.yaml`, que contiene ramas de maestría.

### 3.3 Catálogo efectivo único

Entrada: clase, nivel aplicado, rama, modificadores, entrenamientos y versión de reglas.
Salida: habilidades utilizables, pasivas, máximos de recursos, invocaciones permitidas, formas y descripciones mecánicas.

Lo usan: motor, ficha, selección, descanso, consumibles, simulador, informes y botón de ayuda. Evitar listas paralelas en render o handlers.

Contrato sugerido:
- Identificador de habilidad estable y único por contexto.
- Requisito de nivel y rama.
- Coste de acción (acción, bonus o pasiva), recurso y reutilización.
- Objetivos tipados: propio, enemigo, fila enemiga, compañero propio. Reservar ally para futura ampliación; no habilita jugadores aliados todavía.
- Efectos: daño, sanar, barrera, estado, generar/gastar recurso, invocar, transformar, modificar habilidad.
- Duración, acumulación, expiración y reglas frente a jefes.
- ES/EN y explicación producida desde los datos.
- Sin expresiones Python ni fórmulas ejecutables provenientes de YAML.

No construir un lenguaje genérico de efectos ilimitado. Añadir primitivas pequeñas por familias, con validadores y resolución explícita.

### 3.4 Persistencia y migraciones

Diseño recomendado: un bloque JSON validado y versionado para progreso/elecciones y otro para recursos; conservar campos simples existentes cuando sirvan. Si se añaden columnas, crear migración Alembic después de la cabeza real (en la base están 0011 y 0012; no asumir numeración futura).

Campos conceptuales:
- `progression_version`, hitos confirmados y XP acumulada.
- Elecciones de entrenamientos y modificadores.
- `rules_version`, barras y cooldowns de combate.
- Compañero personal: identidad/nombre, forma, evolución; estado transitorio en encuentro.
- Derecho de reelección por revisión de balance, consumido una vez.
- `world_epoch` o mecanismo equivalente para invalidar trabajos/eventos del mundo anterior al reinicio.

La BD admite un personaje por User mediante unicidad. **No quitar esa restricción**: varios personajes son futuro.

### 3.5 Contratos de eventos

Reutilizar `hero_facts` y los Outcomes, extendiéndolos para hechos inequívocos:
`quest_ready`, `quest_delivered`, `milestone_unlocked`, `level_reached`, `class_specialized`, `modifier_selected`, `training_selected`, `boss_defeated`, `fled_with_item`, `resource_spent`, `blueprint_learned`.

Cada hecho lleva personaje, origen, versión y clave de deduplicación. No escribir cada ataque en la crónica visible: los hechos necesarios para validación pueden ser no notables. No usar el texto narrado como evidencia.

<a id="progresion"></a>
## 4. Progresión híbrida de XP e hitos

### 4.1 Regla fundamental

**XP demuestra experiencia; el hito permite cruzar una frontera narrativa. Ambos son necesarios.**

Diseño de implementación recomendado:
- Nivel potencial: obtenido de una tabla creciente de XP.
- Nivel permitido: máximo habilitado por hitos completados.
- Nivel efectivo: mínimo entre potencial, permitido y 20.
- La XP no se pierde al llegar a una puerta.
- Un hito no concede por sí solo niveles sin XP.
- El cálculo se reejecuta tanto al otorgar XP como al completar un hito.

Pseudocódigo conceptual, no implementación existente:

```python
def eligible_level(xp, milestones, rules):
    potential = rules.level_for_xp(xp)
    permitted = rules.cap_for(milestones)
    return min(potential, permitted, rules.max_level)
```

**Puerta aprobada:** sin entregar la misión del Recaudador no se alcanza nivel 10, aunque sobre XP. La derrota del jefe habilita entrega; la entrega concede premio y hito una sola vez. Esta elección de momento integra D02 y D22.

**Puerta adicional recomendada:** entre obtener nivel 10 y derrotar/entregar el Ciervo, mantener cap 10. Así se estrena la rama a nivel 10 y no se salta el cierre de iniciación por XP acumulada. Es diseño de implementación, no otro jefe exigido por el usuario.

No imponer puertas cada nivel. Para 11–20 usar inicialmente XP normal después del Ciervo; valorar una frontera de acto en 15 y otra en 20 solo si la campaña lo necesita. Esas puertas adicionales no están aprobadas.

### 4.2 Casos obligatorios

| Caso | Resultado esperado |
|---|---|
| Tiene XP para 10, no entregó Recaudador | Permanece en 9; conserva XP; diario muestra la misión necesaria. |
| Entrega Recaudador y recompensa alcanza umbral 10 | Premio + hito + nivel 10 en una transacción; se habilita selección. |
| Entrega Recaudador, sigue faltando XP | Hito queda cumplido; el diario ofrece aventuras disponibles para completar XP. |
| Gana después la XP faltante | Sube automáticamente a 10 sin volver a matar/entregar al Recaudador. |
| Tiene XP para 12 antes de especializarse | No salta el Ciervo; con la puerta recomendada queda en 10. |
| Termina Ciervo y desbloquea nuevo tramo | Recalcular niveles elegibles; conservar elecciones pendientes de entrenamientos, no autoelegirlas. |
| Dos entregas simultáneas o botón antiguo | Un solo premio, hito y evento de nivel. |
| Derrota, huida o reinicio tras jefe | Solo un hecho confirmado de victoria permite entrega; no basta haber entrado al combate. |
| Selecciona rama sin nivel 10 | Rechazo sin coste ni escritura. |
| Falla Telegram después del commit | Estado correcto; diario permite recuperar resultado sin repetir premio. |

### 4.3 Tabla de XP y ritmo

No reutilizar cinco umbrales añadiendo números arbitrarios hasta 20. Construir la tabla junto con el presupuesto de misiones.

Objetivos aprobados: 10–30 horas de sesiones hasta final de iniciación; 30–60 horas acumuladas hasta 20. Referencia útil para calibrar: 2 sesiones/día × 75 min = 2,5 h/día; mediana inicial orientativa 7 días (~17,5 h), nivel 20 ~17 días (~42,5 h). No prometer estos valores sin prueba.

Separar:
- Tiempo activo de decisiones/combate.
- Tiempo de lectura.
- Espera de actividad mientras se gestiona.
- Espera fuera de sesión.
- Inactividad real del usuario.
- Tiempo de red/IA.

Presupuesto de XP recomendado: 60–70 % misiones, 20–30 % combate y resto hitos/descubrimientos únicos. Son semillas de distribución de una ruta normal, no cuotas de un jugador. Hitos pueden desbloquear sin dar XP adicional para no contar dos veces.

Trabajo:
1. Estimar sesiones por acto y escribir actividades significativas.
2. Asignar recompensas a dificultad, duración y relevancia; no a número de mensajes.
3. Elegir umbrales que sitúen Recaudador cerca del 10 para quien sigue la ruta.
4. Probar rutas mínimas, con secundarias y de jugador dedicado.
5. Ajustar contenido si hay huecos; no rellenar 20 horas con cazar lo mismo.
6. Registrar exceso de XP en puertas para detectar acumulaciones que destruyan el arco siguiente.

### 4.4 Entrenamientos y niveles sin habilidad nueva

Conservar compra inicial por puntos; introducir elecciones en 5, 12 y 18 (diseño delegado).
- Dos paquetes por clase: recomendado ofensivo y alternativa resistente/secundaria.
- Mostrar cambios reales en PV, ataque, CD o recurso, no solo nombres.
- No autoaplicar la mejora antigua de nivel 4 además de estos entrenamientos.
- Límites de atributos explícitos; revisar el límite actual 20 antes de cambiarlo.
- Si la opción principal está al máximo, sustituir por alternativa válida explicada.
- Una subida puede dar PV/progreso sin botón nuevo.
- Si se salta varios niveles, encolar elecciones; no perder la de 5 o 12.

<a id="combate"></a>
## 5. Recursos, combate y calendario de poderes

### 5.1 Familias de recursos

| Clase | Recurso propuesto | Bucle |
|---|---|---|
| Paladín | Convicción | Acciones básicas generan; poderes sagrados gastan. |
| Guerrero | Foco | Recuperación acotada por turno; maniobras consumen. |
| Bárbaro | Furia | Ofensiva y presión generan; no solo recibir golpes. Se vacía o decae fuera de combate. |
| Pícaro | Energía + Apertura | Energía por turno; una apertura visible para remates. |
| Clérigo | Maná | Elegir intensidad de plegarias y recuperación. |
| Hechicero | Maná | Presupuesto compartido; contador temático solo donde aporte. |
| Druida | Maná | Poder natural; la forma cambia acciones, no añade tres barras. |
| Bardo | Resonancia | Interpretaciones generan; estribillos consumen. |
| Brujo | Esencia | Alimentar pacto, maldición o vestigios. |
| Explorador | Foco | Preparación y técnicas de presa. |
| Monje | Foco | Técnicas y remates de dos pasos. |
| Artífice | Carga | Alimentar aparato y administrar modos. |
| Chamán | Maná | Vínculo elemental/tótem; no barra por elemento. |
| Caballero de la Muerte | Poder rúnico | Ataques generan; técnicas rúnicas gastan. |

**Aprobada la estructura, valores por probar.** Una barra principal; como máximo un contador de apoyo visible por rama. No acumular contadores por quemadura en cada enemigo en la cabecera del héroe: son estados del objetivo.

Recuperación:
- Maná parcialmente tras victoria válida; resto mediante descanso y consumibles.
- Definir cantidades y condiciones; impedir recarga infinita entrando y huyendo.
- Foco/Energía con ritmo por turno; explicitar inicio y límite.
- Recursos de generación no conceden beneficio por daño absorbido inexistente o sobrecuración.
- Acción básica gratuita siempre relevante.
- Carga del Catalyst no son pociones físicas; cero conversión a inventario.
- Cooldown de combate en turnos; descanso/actividad en segundos reales. Nunca confundirlos.

### 5.2 Calendario común recomendado

| Nivel | Entrega |
|---|---|
| 1 | Ataque básico útil, técnica distintiva y presentación del recurso. |
| 2–4 | Herramienta defensiva o de preparación; completar bucle base. |
| 5 | Entrenamiento; refuerzo de identidad de clase. |
| 6–9 | Una o dos mejoras/accesos, no una habilidad obligatoria cada nivel. |
| 10 | Rama: pasiva y técnica que cambian realmente la forma de jugar. |
| 11–12 | Desarrollo de rama; entrenamiento al 12. |
| 13 | Elegir uno de dos modificadores A/B. |
| 14–16 | Mejora fija de una técnica o nueva respuesta situacional. |
| 17 | Elegir uno de dos modificadores C/D. |
| 18 | Tercer entrenamiento. |
| 19 | Ajuste final del bucle, sin botón obligatorio. |
| 20 | Técnica culminante identificable. |

Los nombres de técnicas, modificadores y culminaciones de §6 son **semillas de diseño**, salvo Convergencia y las identidades ya aprobadas. Cada ficha debe terminar con costes, objetivos y pruebas antes de implementar.

### 5.3 Estados, control y acciones automáticas

- Definir si un estado se aplica al empezar o terminar turno; duración decrece una vez.
- Especificar acumulación, refresco y retirada; prohibir apilar indefinidamente.
- Daños periódicos y represalias no se disparan a sí mismos.
- Sanar daño real genera sinergias; sobrecuración no.
- Control de jefe: resistencia explícita o sustitución por debilitamiento/ruptura, nunca inmunidad oculta a toda una rama.
- Una acción del héroe no habilita varios turnos de invocaciones por pulsar bonus, consulta o ayuda.
- Cronomante no retrocede transacciones ni modifica turnos ya resueltos; trabaja sobre próximos efectos o reutilizaciones.
- Mismo resultado y logs al reanudar un encuentro después de reiniciar.

### 5.4 Balance de roles en solitario

DMG = daño; DEFF = defensa; HEAL = recuperación; CONTROL = alterar opciones enemigas. Primer rol de la ficha es principal.

No equilibrar solo DPS. Medir victoria, duración, recursos, riesgo y complejidad. HEAL debe matar a un ritmo aceptable; DEFF no puede necesitar veinte minutos para un enemigo común; CONTROL necesita efecto útil sobre jefes; DMG no puede ignorar todas las señales con daño explosivo.

Dejar contratos de objetivos preparados para aliados futuros, pero no crear party, turnos humanos simultáneos ni escalado cooperativo ahora.

<a id="catalogo"></a>
## 6. Catálogo aprobado y fichas de implementación

Las **clases, ramas, nombres y roles** de este catálogo están aprobados. Los ejemplos de pasivas, técnicas y modificadores concretan cómo implementarlo, pero sus números y nombres finales se validan durante balance. Roles secundarios no obligan a dar todas las herramientas de ese rol.

### 6.1 Paladín / Paladin

**Identidad:** Convicción; combatiente sagrado que convierte acciones de compromiso en castigo y protección.

**C01-S1 · Vengador / Avenger — DMG · CONTROL**

- **Bucle aprobado:** Marca una presa y acumula presión. Castigos consumen Convicción; cambiar de blanco obliga a reconstruir parte de la ventaja.
- **Desarrollo candidato:** 13: marca más duradera o remate más intenso. 17: persecución eficiente o castigo de ataque anunciado. 20: Juicio del Vengador.
- **Riesgo y prueba particular:** No producir multiplicadores ilimitados contra un jefe ni reiniciar el recurso cambiando de presa.

**C01-S2 · Custodio Sagrado / Sacred Warden — DEFF · DMG**

- **Bucle aprobado:** Mantiene guardia sagrada y transforma impactos mitigados en respuesta. Protegerse es útil jugando solo; extenderlo a aliados queda para 0.11.
- **Desarrollo candidato:** 13: barrera más estable o contraataque más fuerte. 17: protección sostenida o descarga acumulada. 20: Bastión Sagrado.
- **Riesgo y prueba particular:** Mitigación contabilizada una vez; no generar Convicción de daño inexistente.

**C01-S3 · Redentor / Redeemer — HEAL · DEFF**

- **Bucle aprobado:** Alterna ataques que preparan curación y curaciones de daño real que preparan ataque. Su recuperación forma parte del combate cercano.
- **Desarrollo candidato:** 13: curación sostenida o respuesta inmediata. 17: conversión ofensiva o protección tras sanar. 20: Absolución.
- **Riesgo y prueba particular:** No fomentar dejarse golpear ni generar poder por sobrecurar.

**C01-S4 · Inquisidor / Inquisitor — CONTROL · DMG**

- **Bucle aprobado:** Aplica sellos que castigan acciones anunciadas, debilitan defensas o preparan interrupción. Escoge sello y momento.
- **Desarrollo candidato:** 13: sello persistente o activación potente. 17: control más fiable o daño al romper sello. 20: Veredicto.
- **Riesgo y prueba particular:** Un jefe resistente conserva una respuesta secundaria útil; no cadena infinita de silencio.


### 6.2 Guerrero / Warrior

**Identidad:** Foco; dominio de armas, maniobras y posturas. Decide la respuesta correcta al patrón del rival.

**C02-S1 · Maestro de Batalla / Battle Master — DMG · CONTROL**

- **Bucle aprobado:** Usa maniobras para abrir defensa, interrumpir o preparar remate. Repertorio corto de respuestas, sin exigir árbol de combos.
- **Desarrollo candidato:** 13: maniobra económica o potente. 17: apertura ofensiva o respuesta defensiva. 20: Superioridad Marcial.
- **Riesgo y prueba particular:** Reutilizar respuestas del motor sin permitir varias interrupciones gratuitas por turno.

**C02-S2 · Baluarte / Bulwark — DEFF · CONTROL**

- **Bucle aprobado:** Escudo, estabilidad y golpes que desequilibran. Bloquear prepara una intervención física; no depende de magia ni curación continua.
- **Desarrollo candidato:** 13: guardia firme o impacto de escudo. 17: mantener postura o consumirla en ruptura. 20: Línea Inquebrantable.
- **Riesgo y prueba particular:** Diferenciarlo del Custodio: posición y maniobra frente a barrera y poder sagrado.


### 6.3 Bárbaro / Barbarian

**Identidad:** Furia; presión ofensiva y riesgo visible. No es un Guerrero con otra animación.

**C03-S1 · Berserker / Berserker — DMG**

- **Bucle aprobado:** Sostiene frenesí mediante ataques. Gasta Furia en remates o la conserva para presión; aceptar exposición debe ser una decisión informada.
- **Desarrollo candidato:** 13: frenesí eficiente o temerario. 17: explosión breve o continuidad. 20: Furia Desatada.
- **Riesgo y prueba particular:** Furia generada también atacando. No exigir recibir daño ni dar inmunidad durante todo el combate.

**C03-S2 · Coloso / Colossus — DEFF · CONTROL**

- **Bucle aprobado:** Aguanta, carga impactos y desestabiliza. Convierte Furia en resistencia o en un golpe pesado.
- **Desarrollo candidato:** 13: resistencia o preparación rápida. 17: impacto amplio o concentrado. 20: Paso del Titán.
- **Riesgo y prueba particular:** Preparar no puede ocupar varios turnos sin utilidad. No necesita un escudo.


### 6.4 Pícaro / Rogue

**Identidad:** Energía y Apertura; crear una oportunidad y aprovecharla.

**C04-S1 · Asesino / Assassin — DMG**

- **Bucle aprobado:** Prepara un objetivo y descarga daño en una ventana. Puede crear nuevas aperturas durante combates largos.
- **Desarrollo candidato:** 13: preparación veloz o remate fuerte. 17: veneno sostenido o ejecución. 20: Sentencia Silenciosa.
- **Riesgo y prueba particular:** No depender solo del primer turno ni del sigilo inicial; ejecución con daño limitado, no muerte automática de jefe.

**C04-S2 · Duelista / Duelist — DMG · DEFF**

- **Bucle aprobado:** Fintas, paradas y réplicas contra un rival. Atacar y defender preparan oportunidades distintas.
- **Desarrollo candidato:** 13: parada o finta. 17: réplica sostenida o estocada final. 20: Duelo Perfecto.
- **Riesgo y prueba particular:** No exigir que el enemigo falle para poder usar la clase; apertura alternativa garantizada por técnica.

**C04-S3 · Saboteador / Saboteur — CONTROL · DMG**

- **Bucle aprobado:** Trampas, humo y venenos de clase. Prepara una ventaja y la activa o deja que el rival la desencadene.
- **Desarrollo candidato:** 13: trampa persistente o detonación. 17: humo defensivo o corrosión. 20: Sabotaje Encadenado.
- **Riesgo y prueba particular:** No requiere Ingeniería. Sus técnicas no crean bombas vendibles ni permiten precolocar infinitas.


### 6.5 Clérigo / Cleric

**Identidad:** Maná; plegarias, bendiciones y ritos. Su núcleo es administrar efectos divinos.

**C05-S1 · Dominio de la Vida / Life Domain — HEAL · DEFF**

- **Bucle aprobado:** Mantiene bendiciones y escoge recuperación inmediata o sostenida. Ataques devocionales ayudan a preparar la recuperación.
- **Desarrollo candidato:** 13: bendición larga o curación rápida. 17: barrera al sanar o eficiencia ofensiva. 20: Santuario de Vida.
- **Riesgo y prueba particular:** Viable solo; no requiere un aliado herido. Sin ciclos de curación/maná infinitos.

**C05-S2 · Dominio de la Luz / Light Domain — DMG · CONTROL**

- **Bucle aprobado:** Acumula fulgor para quemar, revelar o desorientar. Alterna concentración y área.
- **Desarrollo candidato:** 13: fulgor concentrado o extendido. 17: purificación o deslumbramiento. 20: Amanecer Radiante.
- **Riesgo y prueba particular:** La revelación debe tener efecto mecánico real; no duplicar Piromante con daño de otro color.

**C05-S3 · Dominio de la Guerra / War Domain — DMG · DEFF**

- **Bucle aprobado:** Armas y plegarias se preparan mutuamente. Combate ritual, diferente de la Convicción del Paladín.
- **Desarrollo candidato:** 13: bendición ofensiva o resistente. 17: secuencia corta o sostenida. 20: Liturgia de Guerra.
- **Riesgo y prueba particular:** Definir qué arma y equipo usa; las plegarias tienen coste y no son bonos permanentes apilables.


### 6.6 Hechicero / Sorcerer

**Identidad:** Maná; moldea magia. Incluye la antigua fantasía de Mago y magia innata, sin duplicar clases.

**C06-S1 · Piromante / Pyromancer — DMG**

- **Bucle aprobado:** Aplica quemaduras y decide entre mantenerlas o consumirlas para detonar. Puede preparar varios blancos.
- **Desarrollo candidato:** 13: combustión larga o rápida. 17: propagación o concentración. 20: Conflagración.
- **Riesgo y prueba particular:** Topes de quemadura y propagación; explosionar no vuelve a disparar su propio efecto.

**C06-S2 · Criomante / Cryomancer — CONTROL · DMG**

- **Bucle aprobado:** Acumula frío para limitar, congelar o volver frágil. Consume preparación al quebrar.
- **Desarrollo candidato:** 13: control o fragilidad. 17: frío en fila o daño en un objetivo. 20: Cero Absoluto.
- **Riesgo y prueba particular:** En jefes congelación se adapta a ruptura/debilitamiento; no invalida la rama.

**C06-S3 · Arcanista / Arcanist — DMG · DEFF**

- **Bucle aprobado:** Cargas arcanas aumentan potencia y presión de Maná. Puede descargarlas o invertirlas en barrera.
- **Desarrollo candidato:** 13: eficiencia o potencia. 17: descarga o defensa. 20: Ascendencia Arcana.
- **Riesgo y prueba particular:** No más de un contador auxiliar; eliminar bucles de coste negativo.

**C06-S4 · Tempestario / Stormcaller — DMG · CONTROL**

- **Bucle aprobado:** Marca conductividad y encadena descargas. Contra un rival concentra la tormenta en vez de perder su identidad.
- **Desarrollo candidato:** 13: cadena o rayo concentrado. 17: interrupción breve o daño sostenido. 20: Ojo de la Tormenta.
- **Riesgo y prueba particular:** Los rebotes no multiplican sin límite ni golpean accidentalmente compañeros.

**C06-S5 · Invocador / Summoner — DMG · CONTROL**

- **Bucle aprobado:** Combina dos entidades de repertorio mixto. Actúan automáticamente sobre la presa marcada; una orden conjunta consume la acción correspondiente.
- **Desarrollo candidato:** 13: potencia individual o coordinación. 17: persistencia o cambio táctico acotado. 20: **Convergencia** potencia temporalmente las dos entidades.
- **Riesgo y prueba particular:** Máximo dos también al 20. Cambiar repertorio fuera de combate; no curar gratis retirando/reinvocando.

**C06-S6 · Cronomante / Chronomancer — CONTROL · DEFF**

- **Bucle aprobado:** Retrasa una amenaza futura y altera reutilización de una técnica dentro de límites. Anticipar vale más que daño inmediato.
- **Desarrollo candidato:** 13: aplazar amenaza o proteger ventana. 17: eficiencia o intervención fuerte. 20: Instante Suspendido.
- **Riesgo y prueba particular:** No rebobina estado persistido, no regala turnos infinitos, no reduce su propia reutilización en bucle.


### 6.7 Druida / Druid

**Identidad:** Maná y adaptación natural; cuerpo, regeneración o ciclos de descomposición.

**C07-S1 · Cambiaformas / Shapeshifter — DMG · DEFF**

- **Bucle aprobado:** Combate mayoritariamente transformado. Forma resistente y forma ofensiva sustituyen acciones principales; cambiar tiene coste.
- **Desarrollo candidato:** 13: especializar forma ofensiva o defensiva. 17: transición eficiente o permanencia fuerte. 20: Forma Primordial.
- **Riesgo y prueba particular:** No duplicar vida cada transformación. Equipo y recurso siguen reglas explícitas.

**C07-S2 · Guardián del Bosque / Grove Warden — DEFF · HEAL**

- **Bucle aprobado:** Corteza, raíces y regeneración preparan supervivencia. Puede consumir parte de su protección para un ataque.
- **Desarrollo candidato:** 13: corteza o regeneración. 17: raíces o liberación ofensiva. 20: Corazón del Bosque.
- **Riesgo y prueba particular:** Diferencia de Vida: prevención y regeneración, no solo curación inmediata.

**C07-S3 · Círculo de Esporas / Circle of Spores — DMG · CONTROL**

- **Bucle aprobado:** Siembra esporas y elige propagarlas, mantenerlas o hacerlas florecer. Desgaste que se acelera con una decisión.
- **Desarrollo candidato:** 13: propagación o concentración. 17: debilitamiento o detonación. 20: Floración Fúngica.
- **Riesgo y prueba particular:** No depender de matar enemigos para funcionar contra uno solo.


### 6.8 Bardo / Bard

**Identidad:** Resonancia; interpreta y cambia el ritmo, con efectos resueltos por el motor.

**C08-S1 · Cantor de Guerra / War Chanter — DMG · HEAL**

- **Bucle aprobado:** Mantiene melodía ofensiva o restauradora; construye Resonancia para un estribillo. Cambiar de melodía no consume un turno inútil.
- **Desarrollo candidato:** 13: cadencia ofensiva o restauradora. 17: mantener canción o transición. 20: Gran Estribillo.
- **Riesgo y prueba particular:** Afecta a sí mismo en solo; no crea canciones apiladas simultáneas.

**C08-S2 · Ilusionista / Illusionist — CONTROL · DEFF**

- **Bucle aprobado:** Señuelos, distracción y réplicas. Decide entre reducir amenaza y preparar castigo.
- **Desarrollo candidato:** 13: señuelo o distracción. 17: réplica o protección. 20: Teatro de Espejos.
- **Riesgo y prueba particular:** Resolución determinista; no convencer a Gemini de que una ilusión gana el combate.


### 6.9 Brujo / Warlock

**Identidad:** Esencia; pactos, condiciones y maldiciones. Poder prestado con restricciones legibles.

**C09-S1 · Demonólogo / Demonologist — DMG · DEFF**

- **Bucle aprobado:** Un servidor poderoso con nombre e identidad permanente. Alimenta el vínculo, ordena una técnica y se protege mediante él.
- **Desarrollo candidato:** 13: ofensiva del servidor o protección del vínculo. 17: evolución de ataque o defensa. 20: Ascensión del Pacto.
- **Riesgo y prueba particular:** El mismo ser evoluciona/cambia de forma; no es una colección reemplazable. Derrota no borra nombre ni progreso.

**C09-S2 · Filo Maldito / Hexblade — DMG · CONTROL**

- **Bucle aprobado:** Maldice y combate de cerca. Los golpes desarrollan la maldición; consumirla sirve para dañar o debilitar.
- **Desarrollo candidato:** 13: maldición larga o explosiva. 17: debilitamiento o recuperación acotada. 20: Hoja del Pacto.
- **Riesgo y prueba particular:** Evitar multiplicar cada golpe extra por todas las marcas sin límite.

**C09-S3 · Nigromante / Necromancer — DMG · CONTROL**

- **Bucle aprobado:** Genera vestigios con sus técnicas, los gasta en poder funerario o sirviente temporal. No exige cadáver externo.
- **Desarrollo candidato:** 13: vestigios eficientes o fuertes. 17: maldición o sirviente. 20: Cortejo de Sombras.
- **Riesgo y prueba particular:** Límite de entidades; la culminación puede ser efecto agregado, no diez turnos extra.


### 6.10 Explorador / Ranger

**Identidad:** Foco; observar, preparar y explotar patrones de una presa.

**C10-S1 · Tirador / Sharpshooter — DMG · CONTROL**

- **Bucle aprobado:** Disparos rápidos frente a tiros preparados. Marca un punto débil o interrumpe una amenaza visible.
- **Desarrollo candidato:** 13: preparación rápida o precisión. 17: interrupción o daño. 20: Disparo Certero.
- **Riesgo y prueba particular:** No volver trivial cualquier jefe por daño automático; tiros preparados tienen coste de oportunidad.

**C10-S2 · Señor de Bestias / Beastmaster — DMG · DEFF**

- **Bucle aprobado:** Un compañero animal estable y ataques coordinados. Ordena atacar o ayudar a protegerse.
- **Desarrollo candidato:** 13: bestia ofensiva o protectora. 17: coordinación o resistencia. 20: Cacería Conjunta.
- **Riesgo y prueba particular:** No exigir comprar/reponer animales; identidad estable separada del catálogo del Invocador.


### 6.11 Monje / Monk

**Identidad:** Foco; técnicas corporales con secuencias cortas de dos pasos.

**C11-S1 · Puño de Hierro / Iron Fist — DMG · CONTROL**

- **Bucle aprobado:** Una técnica abre un remate que golpea, desequilibra o interrumpe. La interfaz muestra la oportunidad.
- **Desarrollo candidato:** 13: impacto o apertura. 17: remate eficiente o potente. 20: Golpe del Horizonte.
- **Riesgo y prueba particular:** Defensa sin armadura necesita reglas reales; no sumar gratuitamente armadura y bonos de monje.

**C11-S2 · Danzante de Sombras / Shadow Dancer — DEFF · DMG**

- **Bucle aprobado:** Evasión y desplazamiento abstracto preparan contraataques. Tiene técnica alternativa para crear oportunidad.
- **Desarrollo candidato:** 13: evasión o réplica. 17: movilidad defensiva o remate. 20: Danza del Eclipse.
- **Riesgo y prueba particular:** No depender completamente del azar de esquivar. No necesita cuadrícula ni sigilo narrativo arbitrario.


### 6.12 Artífice / Artificer

**Identidad:** Carga; configurar dispositivos de clase, independiente de oficios y recetas.

**C12-S1 · Armero Rúnico / Runic Armorer — DEFF · DMG**

- **Bucle aprobado:** Armadura con modo defensivo y ofensivo. Distribuye Carga entre protección y golpes.
- **Desarrollo candidato:** 13: barrera o impacto. 17: transición o especialización de modo. 20: Sobrecarga Rúnica.
- **Riesgo y prueba particular:** La armadura de clase no produce una pieza vendible ni duplica toda la CA del equipo.

**C12-S2 · Artillero / Artillerist — DMG · CONTROL**

- **Bucle aprobado:** Un arma desplegada dispara automáticamente. El héroe administra munición abstracta, recarga o aprovecha el blanco.
- **Desarrollo candidato:** 13: disparo concentrado o área. 17: munición disruptiva o potencia. 20: Salva de Asedio.
- **Riesgo y prueba particular:** Una torreta activa; no requerir munición fabricada para que funcione el kit básico.

**C12-S3 · Catalizador / Catalyst — HEAL · DMG**

- **Bucle aprobado:** Un aparato aplica reactivos: corrosivo, espuma protectora, pulso restaurador y catalización que consume residuos. Usa Carga, no inventario.
- **Desarrollo candidato:** 13: restauración inmediata o sostenida. 17: reacción ofensiva o protección al catalizar. 20: Reacción Maestra.
- **Riesgo y prueba particular:** No fabricar pociones con habilidades, no exigir oficio Alquimia, no gastar materias primas en cada combate.

**C12-S4 · Maestro de Constructos / Construct Master — DEFF · CONTROL**

- **Bucle aprobado:** Un autómata configurado antes del combate protege e interviene. Función distinta de un cañón estacionario.
- **Desarrollo candidato:** 13: protección o perturbación. 17: estabilidad o respuesta. 20: Protocolo del Guardián.
- **Riesgo y prueba particular:** No turnos humanos extra ni curación gratuita reconstruyéndolo durante el encuentro.


### 6.13 Chamán / Shaman

**Identidad:** Maná y un vínculo/tótem activo; transición elemental y presencia ancestral.

**C13-S1 · Elementalista / Elementalist — DMG · CONTROL**

- **Bucle aprobado:** Prepara con un elemento y activa combinación con otro. Su identidad es alternar, no especializarse en fuego o hielo.
- **Desarrollo candidato:** 13: combinación rápida o potente. 17: extensión o concentración. 20: Confluencia Elemental.
- **Riesgo y prueba particular:** Dos pasos legibles; no cuatro barras ni decenas de combinaciones ocultas.

**C13-S2 · Guardián Ancestral / Ancestral Guardian — DEFF · CONTROL**

- **Bucle aprobado:** Tótem y presencia ancestral protegen y responden a agresiones. Mantener vínculo o consumirlo es la decisión.
- **Desarrollo candidato:** 13: protección o represalia. 17: persistencia o intervención. 20: Vigilia Ancestral.
- **Riesgo y prueba particular:** Un tótem activo y efecto agregado; no invocar un ejército de ancestros.

**C13-S3 · Tejedor de Mareas / Tideweaver — HEAL · DMG**

- **Bucle aprobado:** Flujo favorece restaurar; reflujo descargar poder. Puede adaptar el ciclo sin depender de un aliado.
- **Desarrollo candidato:** 13: restauración o descarga. 17: ciclo flexible o fase reforzada. 20: Marea Viva.
- **Riesgo y prueba particular:** No obligar a esperar una fase inútil ni permitir regeneración infinita sin coste.


### 6.14 Caballero de la Muerte / Death Knight

**Identidad:** Poder rúnico; convierte golpes, vitalidad y marcas en presión. Su origen se adapta al lore de Aetherfall.

**C14-S1 · Sangre / Blood — DEFF · DMG**

- **Bucle aprobado:** Absorbe vitalidad y responde a daño reciente con protección o recuperación personal.
- **Desarrollo candidato:** 13: absorción o barrera. 17: respuesta inmediata o reserva. 20: Corazón Carmesí.
- **Riesgo y prueba particular:** No se clasifica HEAL de grupo. Sacrificar vida, si entra, no puede matarlo por costes ocultos.

**C14-S2 · Escarcha / Frost — DMG · CONTROL**

- **Bucle aprobado:** Ataques cercanos acumulan marcas rúnicas; golpes de escarcha las rompen para presionar y debilitar.
- **Desarrollo candidato:** 13: marcas rápidas o fuertes. 17: ruptura o debilitamiento. 20: Marcha del Invierno.
- **Riesgo y prueba particular:** Diferenciarlo de Criomante mediante armas, recurso generado y presión cercana.

<a id="companeros"></a>
## 7. Invocaciones, compañeros y formas

### 7.1 Modelo mínimo común

Reutilizar el estado serializable de encuentro. Cada entidad tiene propietario, tipo, plantilla, duración si procede, PV si puede recibir daño y comportamiento determinista. Mantener dos bandos no significa que todas las entidades sean personajes humanos.

Orden recomendado por turno:
1. Resolver acción del héroe y costes.
2. Resolver entidades que deben actuar en ese turno, una vez por ciclo completo del héroe.
3. Resolver estados y expiraciones conforme al contrato.
4. Pasar al siguiente combatiente.
5. Persistir estado y logs antes de presentar el resultado.

La acción bonus o consultar un menú no debe disparar otro ataque automático. Guardar en estado el marcador de ciclo ya resuelto.

Distinguir:
- **Persistencia de identidad:** servidor del Demonólogo y compañero del Explorador.
- **Persistencia de configuración:** constructo y repertorio del Invocador.
- **Estado de encuentro:** PV, duración, estados, objetivo y orden temporal.
- **Propiedad económica:** ninguna entidad es un objeto que se venda o duplique.

### 7.2 Invocador

Dos espacios máximos. Repertorio inicial propuesto:
- Espada Astral / Astral Blade: daño concentrado.
- Ascua Errante / Wandering Ember: desgaste y área acotada.
- Guardián de Piedra / Stone Guardian: protección limitada.
- Polilla del Velo / Veil Moth: perturbación.

Mostrar coste, función, limitaciones y sinergia. Configuraciones recomendadas explican ventajas; no eligen automáticamente por el jugador. Cambiar repertorio fuera de combate, sin restaurar recursos por abrir/cerrar configuración.

**Convergencia al 20:** potencia temporalmente las dos entidades existentes; duración y cooldown por balance. No crea tercera entidad ni duplica inmediatamente sus turnos. Si falta una, el efecto se aplica a la que existe sin compensación abusiva por dejar espacio vacío.

### 7.3 Demonólogo y otros auxiliares

Servidor permanente con nombre validado como texto de usuario, sin instrucciones incrustadas en prompts. Evoluciones cambian forma y técnica, no borran identidad. Si cae en combate, establecer recuperación visible y limitada; nunca perderlo definitivamente por una tirada de tutorial.

Señor de Bestias usa una bestia estable y coordinación; no el catálogo de invocaciones. Maestro de Constructos modifica configuración; Artillero despliega un arma. Nigromante tiene sirvientes temporales con límite estricto; la culminación puede representarse como un efecto agregado.

### 7.4 Cambiaformas

La forma cambia acciones efectivas, iconos y reglas defensivas. Definir conversión de PV explícita: conservar vida proporcional o una reserva temporal acotada, sin curar al alternar. El recurso y los objetos compatibles se declaran. No eliminar el personaje original del estado ni perder equipo.

Pruebas: cambiar dos veces no restaura PV; morir transformado no evade derrota; reiniciar preserva forma; ficha y simulador ven las mismas habilidades; no equipar armadura incompatible para conservar doble defensa.

<a id="campana"></a>
## 8. Misiones y campaña inicial

### 8.1 Entrega de misiones

Estados nuevos recomendados: locked → available/active → ready_to_turn_in → completed. Failed solo donde exista recuperación definida.

- Objetivos cumplidos: marcar lista para entregar, mostrar PNJ y ruta.
- Entrega: comprobar personaje, lugar, PNJ, objetivos y materiales que se deban consumir.
- Cobrar, consumir, fijar hito y desbloquear siguiente misión en la misma transacción.
- Aceptar doble clic como resultado ya resuelto, nunca segundo premio.
- Si el objetivo es fabricar, la evidencia puede ser el hecho de fabricar; si además hay que entregar la pieza, declararlo y validar posesión.
- No permitir vender un objeto obligatorio y quedar bloqueado sin reposición o receta accesible.
- No bloquear campaña durante horas reales por el horario de su dador: disponibilidad especial o delegado explícito.
- Hablar no entrega silenciosamente varias misiones: botón de entrega identifica misión y recompensa.

**Necesidad del motor:** ampliar QuestStage/QuestObjective y sus validadores. Los objetivos actuales no cubren equipar, aprender oficio, retirar del cofre, usar humo, elegir rama o modificador. Añadir tipos explícitos con eventos, no reconocer frases de Gemini.

### 8.2 Trama común y mentor

Contrato: nuevo mentor cálido, aventurero y memorable; aprendemos como reclutas. No hacer obligatorio un campamento distinto por clase.

Propuesta de trabajo: **Los nombres que faltan / The Missing Names**. Órdenes falsas desvían cargamentos de Crownreach; varias entregas del gremio terminan en lugares peligrosos. El Recaudador coordina la red local. Su mercancía está relacionada con la alteración de fauna que culmina en el Ciervo.

El mentor:
- Presenta objetivos con una razón humana y una instrucción breve.
- Recuerda hechos verificables: primer regreso, oficio elegido, retirada y entrega.
- Al principio acompaña mediante consejos; al final confía una tarea real.
- No resuelve las victorias del jugador ni concede poder fuera del motor.
- Tiene textos base escritos ES/EN; Gemini puede variar tono sin inventar pasado.
- Nombre, biografía, linaje y vínculo con el gremio quedan en N01; escribirlos antes del texto final de campaña.

Vale puede conservar otra función compatible; no borrar un PNJ reutilizable solo por sustituir al mentor. Actualizar saludos y pistas para que no existan dos tutores principales dando órdenes contradictorias.

### 8.3 Estructura implementable

Los títulos siguientes son propuestas editoriales; las funciones de aprendizaje sí forman el alcance.

| Acto | Nivel orientativo | Misiones/escenas | Resultado |
|---|---|---|---|
| I. Tu nombre en el libro | 1–3 | Alistamiento; entrega sospechosa; primer combate; comparar/equipar botín; regreso y entrega | Primera sesión completa y pista de falsificación. |
| II. Un techo ganado | 3–4 | Recoger madera, refinar, montar cama y cofre, guardar y recuperar un objeto, descansar | Habitación real; integrar recetas existentes. |
| III. Las manos de Crownreach | 4–6 | Elegir oficio; aprender; resolver tres misiones específicas; comprar componente faltante; usar o vender resultado | Un oficio elegido conscientemente; ninguna clase impone profesión. |
| IV. Lo que falta en los caminos | 6–8 | Caza, rastreo, desuello, hierbas, minería, pesca/cocina; comparar hechos y rumor; preparar consumibles | Sistemas practicados con razones narrativas, sin ocho aprendizajes artesanales. |
| V. Volver también es vencer | 8–9 | Recuperar prueba y escapar con humo; sanar; preparar equipo; seguir cargamento | La retirada es objetivo válido, no derrota fingida con recompensa infinita. |
| VI. El Recaudador de Ceniza | Hasta 9 antes de la puerta | Investigación por botones/acciones escritas predefinidas; combate; regresar con prueba | Entrega habilita nivel 10, sujeto a XP. |
| VII. Tu camino | 10 | Menú de ramas, detalle, confirmar; preparar T1 accesible y recursos | Especialización real, sin prueba prestada ni investidura extra. |
| VIII. El Ciervo de Hierro | 10 | Rastrear señales, prepararse, vencer, entregar y graduarse | Estrenar poderes y abrir región cercana. |

El número de misiones se ajusta al tiempo medido. Semilla: 24–32 misiones significativas de iniciación, con objetivos cortos agrupados, no 32 recados de ir y volver. Si con contenido real no se alcanza duración objetivo, ampliar acontecimientos y decisiones deterministas antes que cantidades de farmeo.

Los tres encargos de cada oficio reutilizan una estructura, pero productos y motivos cambian. Son misiones de campaña, no un sistema procedural general. Resolver rutas de suministro para los ocho oficios antes de publicar el acto.

### 8.4 Matriz de enseñanza y evidencia

| Sistema | Práctica obligatoria | Evidencia y protección |
|---|---|---|
| Mapa y viaje | Ir a destino y volver al dador; usar ruta de objetivo | Visita efectiva; no basta abrir mapa. |
| Diálogo | Hablar con mentor y maestro; seleccionar un servicio | Interacción validada; no puntuar simpatía arbitraria de IA. |
| Combate | Ataque básico, técnica de recurso y respuesta defensiva | Eventos del encuentro; tutorial se adapta a clase. |
| Recursos | Gastar recurso y recuperarlo mediante vía válida | No exigir gastar Maná a un Bárbaro. |
| Equipo | Comparar, equipar y usar una mejora | Evento equip; entregar pieza apta para clase. |
| Comercio | Comprar algo útil y vender excedente | Transacción; sin obligar a vender material crítico. |
| Recolección | Muestras de minería, tala, hierbas, desuello y rastreo | Trabajo completado; herramientas asequibles. |
| Refinado | Transformar material en estación del gremio | XP de maestría correcta; no oficio obligatorio. |
| Oficio | Aprender uno y completar tres tareas | Un oficio activo; cambio pagado compatible con seguimiento de misión. |
| Conocimiento | Técnica y lectura de un plano accesible | Aprendizaje mecánico; plano de la disciplina elegida. |
| Ramas de campo | Elegir al menos una al rango requerido | No exigir especializar todas las maestrías para graduarse. |
| Herramientas | Elegir herramienta mejorada cuando sea accesible | Preferencia, posesión en mochila y snapshot. |
| Aficiones | Pescar y cocinar algo útil | Captura y fabricación; sin plaza profesional. |
| Habitación | Montar cama/cofre, depositar y retirar | Objeto conservado sin duplicación. |
| Descanso y curación | Descanso corto/largo y uso de curación | Sin acelerar tiempos ni forzar autolesión. |
| Huida | Usar humo y salir con objetivo | Resultado de huida y consumo real; reintento con reposición controlada. |
| Diario | Seguir objetivo y retomar misión | Acción de seguimiento; no premiar abrir veinte menús. |
| Bestiario | Consultar amenaza conocida y prepararse | Consulta más respuesta mecánica; no examen memorístico. |
| Logros y títulos | Conseguir logro introductorio y equipar título | Concesión por hechos y selección persistida. |
| Rumores y reputación | Contrastar pista y hacer una decisión escrita | Rama determinista y cambio de reputación explícito. |
| Especialización | Elegir rama y usar su mecánica frente al Ciervo | Selección + combate; no se exige usar todos sus botones. |

La obligación es aprender sistemas, no completar cada variante. No exigir todas las recetas, los ocho oficios o las 41 ramas. Si un hecho previo sirve, reconocerlo mediante evidencia versionada; hechos que deben ocurrir en una misión se marcan prospectivos.

### 8.5 Evitar bloqueos

- Mantener una fuente recuperable de humo, curación y material de misión; sin reventa abusiva.
- Dar una receta/plano correspondiente al oficio realmente activo o permitir elegir entre opciones válidas.
- Si el jugador cambia oficio durante sus tres tareas, conservar evidencia de aprendizaje y regenerar solo tareas incompatibles, sin pagar premios ya recibidos.
- No basar objetivos obligatorios en un drop raro o una hora real inaccesible.
- No poner al Recaudador detrás de nivel 10 ni al objeto necesario para vencerlo detrás de T1.
- La XP de ruta principal debería acercar al umbral; ofrecer secundarias apropiadas si falta, sin repetir al jefe.
- Conservar el diario como punto de reanudación después de desconectarse.

<a id="jefes"></a>
## 9. Dos jefes con funciones distintas

### 9.1 El Recaudador de Ceniza / The Ash Collector

**Aprobado:** primer jefe principal, misión que abre nivel 10 con XP suficiente. Mecánicas: ballesta, recarga visible, protección desgastable y ataques anunciados.

Diseño:
1. Inicio protegido: disparos normales y una placa/guardia degradable por ataques. Toda clase puede erosionarla.
2. Señal: prepara un disparo fuerte; el panel muestra intención y respuestas disponibles.
3. Descarga y recarga: tras disparar queda una ventana ofensiva.
4. Al perder protección, cambia patrón de forma comprensible, sin ataque sorpresa inevitable.
5. Botín/prueba única → entregar al PNJ → hito + recompensa de XP → reevaluar nivel.

Respuestas universales: defenderse, usar protección/curación preparatoria, humo donde corresponda. Interrumpir es ventaja de ciertas ramas/clases, nunca única solución. El encuentro se equilibra para clase base y equipo T0 de final de tramo.

Recompensa orientativa: prueba de falsificación, oro de preparación y pieza/plano apropiado. No fijar premio de 80 oro por heredar Viejo Colmillo. Si se conserva ese animal como caza opcional, revisar el plano de daga que hoy suelta.

### 9.2 El Ciervo de Hierro / The Iron Stag

**Aprobado:** primer jefe tras elegir especialización, aún en nivel 10. Mecánicas: carga anunciada, defensa endurecida y ventanas de vulnerabilidad.

Diseño:
1. Cornamenta/corteza endurecida mitiga; no vuelve invulnerable.
2. Preparación de carga visible durante un turno.
3. Respuesta: defensa, debilitamiento o técnica propia; todas las ramas tienen salida viable.
4. Tras la carga se expone un núcleo/placa: oportunidad para daño, maldición, invocación o preparación.
5. En la segunda parte combina patrones ya enseñados, sin exigir habilidad nueva no disponible.

No exigir tener todo el conjunto T1. Entregar o hacer asequible una mejora inicial; probar T0 bien preparado y T1 básico. Una rama HEAL gana por sostenerse y aprovechar ventanas, no por curar a un NPC obligatorio.

**Cierre:** entrega de prueba, graduación y pista hacia región cercana. Recuperar estado tras derrota, sin repetir toda la campaña ni perder especialización.

### 9.3 Telemetría de jefes

Registrar nivel, clase/rama, equipo, consumibles, semillas, respuesta a señales, turnos y motivos de derrota. Diferenciar no entender la señal de tener estadísticas insuficientes. No ajustar únicamente PV del jefe para ocultar falta de herramientas en una clase.

<a id="region"></a>
## 10. Región cercana y aventuras 11–20

### 10.1 Alcance aprobado y propuesta geográfica

Aprobado: región nueva, próxima a Crownreach y con motivo narrativo real; Crownreach mantiene servicios centrales. **Nombre y lore siguientes son propuesta, no canon confirmado.**

**Valle de la Fragua Gris / Greyforge Vale**: cuenca de bosques, canteras y puestos de transporte conectada por una desviación del Camino del Viejo Rey. Abastece materiales a Crownreach. Las órdenes falsas permitieron mover componentes de antiguos reguladores arcanos; su extracción altera vetas y fauna. El Recaudador es una pieza local de una red mayor.

No convertir toda la comarca en malvada ni obligar a importar cosmología de otro juego. Revisar `content/world/world.yaml`, continente, facciones y Possibilium antes de redactar lore final. El origen exacto del Ciervo y del Caballero de la Muerte debe encajar en esa revisión.

### 10.2 Nodos candidatos

| Nodo | Uso | Conexión jugable |
|---|---|---|
| Cruce de los Carreteros | Entrada y regreso | Conexión al Camino del Viejo Rey; viaje directo al descubrir. |
| Puesto del Vado | Refugio pequeño | Curación/suministros básicos; no sustituye a Crownreach. |
| Cantera de Ceniza | Enemigos y materiales | Relación con cargamentos; combate al aire libre. |
| Bosque de las Astas | Fauna alterada | Rastreo, encuentros y consecuencias del Ciervo. |
| Aserradero Silencioso | Investigación y rescate | Madera y herramientas; localización abierta, no mazmorra por salas. |
| Taller del Regulador | Escenario de aventura | Mecanismo accesible por acciones explícitas; sin IA obligatoria. |
| Ribera del Vidrio | Pesca, hierbas y anomalías | Materiales T1 y decisiones de preparación. |
| Alto de las Balizas | Cierre regional | Jefe/amenaza final individual y retorno a Crownreach. |

### 10.3 Arcos de progresión

- **11–13, Seguir la carga:** descubrir rutas y comunidades; usar especialización; primer modificador al 13.
- **14–16, Lo que sostiene el valle:** elegir cómo resolver problemas locales mediante opciones escritas; nuevos patrones de enemigos; equipo lateral T1.
- **17–19, Las balizas rotas:** consecuencias conectadas, segundo modificador, encuentros exigentes y proyecto artesanal ligado a aventura.
- **20, Culminación:** desbloquear técnica final y ofrecer una prueba/aventura que permita usarla. No terminar todo el contenido justo antes de conseguirla.

Semilla de volumen: 18–24 misiones principales/regionales más secundarias y contratos escritos repetibles de baja presión. Medir duración real; no presentar esos números como contenido ya producido. Recompensas únicas separadas de repetibles, sin dailies obligatorias.

### 10.4 Vida al 20

Aventuras cortas de veterano, variantes de enemigos, desafíos de clase, colección de planos T1 especiales, herramientas y habitación, reputación y títulos. Equipo horizontal o mejoras limitadas; no subir de tier por cada jefe.

No incluir raids, gremios de jugadores, mercado entre usuarios, contratos con custodia o jefes compartidos. El gremio PNJ de aventureros no es el sistema de guilds multijugador.

<a id="economia"></a>
## 11. Oficios, tiers, equipo y economía

### 11.1 Conservar F15

Reutilizar ocho oficios y maestros, técnicas, planos, refinado de maestrías, herramientas, habitación y 60 recetas base. Mantener independencia del nivel del personaje: fabricar depende del rango; equipar depende del nivel.

T0 rango 0–2: inicio, consumos económicos y componentes. T1 rango 3–5: equipo de combate desde nivel 10 hasta 20, herramientas y muebles según disciplina. **T2 21–30 queda para expansión**; no añadir rangos 6+ ahora por analogía.

Auditar diferencias entre receta T1, rareza, calidad y nivel de uso. No convertir cada objeto raro en otro tier.

### 11.2 Cobertura de las 14 clases

Construir matriz clase × arma × armadura × atributo × receta/tienda/botín:
- Ninguna clase empieza sin ataque gratuito válido.
- Monje tiene reglas sin armadura y arma/cuerpo apropiadas.
- Hechicero y Clérigo no dependen de armas incompatibles.
- Artífice no necesita oficio para usar su aparato.
- Armero no suma doble defensa de armadura de clase y objeto.
- Cada clase dispone de mejoras T0 y T1 alcanzables en solitario.
- Componentes de otros oficios accesibles mediante maestros; no exigir segunda cuenta.
- Pociones, pergaminos y bombas compatibles con recursos nuevos; migrar `restore_spell_charge` hacia efecto adecuado sin confundir Maná con usos.

### 11.3 Catalyst frente a Alquimia

| Catalyst, clase | Alquimia, oficio |
|---|---|
| Aparato con Carga y habilidades de reacción. | Recetas y materiales que producen objetos persistentes. |
| Corrosivo, espuma, pulso restaurador y catalizar. | Pociones almacenables y vendibles. |
| Recupera recurso según reglas de combate/descanso. | Consume ingredientes y concede XP artesanal. |
| No exige profesión ni crea unidades comerciables. | Disponible para cualquier clase. |

Prueba de frontera: usar Pulso restaurador no añade ni quita pociones; fabricar una poción no recarga gratis el aparato. El título y guías explican esa diferencia en ES/EN.

### 11.4 Precios y sumideros

- Retirar pociones a 1 oro y curación gratuita de beta donde corresponda; localizar reglas reales antes de cambiar.
- Cama propia sigue gratis en oro, pero tarda el descanso normal.
- Mantener cambio de oficio pagado y cambio de rama artesanal pagado, sin confundirlos con rama de clase fija.
- Ajustar compra/venta para impedir arbitraje de ingredientes, refinado y lotes.
- Recompensas iniciales cubren herramientas, primera profesión y consumibles esenciales.
- Medir oro neto por acto y coste de una derrota; no dejar a un recluta sin medios de recuperarse.
- No introducir desgaste/reparaciones solo para crear sumideros: sigue como nota futura.
- Balancear herramientas rápidas/selectivas/productivas con sus porcentajes relativos reales y una tirada rara por actividad.

### 11.5 Fuentes que desaparecen con la cripta

Buscar en recetas, botín y logros todas las dependencias de `crypt`, `reliquary`, Holt, Aldren y títulos asociados. Reubicar materiales especiales en jefe, región o maestro. Eliminar rutas activas y referencias colgantes; conservar historial Git. No borrar imágenes históricas por necesidad técnica si basta retirarlas del catálogo activo.

<a id="tiempos"></a>
## 12. Tiempo, descanso y actividades compatibles

Valores aprobados como dirección de calibración; no resultados demostrados:

| Acción | Valor inicial |
|---|---|
| Movimiento urbano | Inmediato. |
| Viaje conocido | Ágil, conservando peligro e interrupción; no añadir espera por calle. |
| Recolección normal | 3–5 minutos. |
| Expedición larga | 12–15 minutos. |
| Rastreo | 2–4 minutos. |
| Desuello | 10–30 segundos según presa. |
| Refinado y fabricación común | Inmediatos por lote. |
| Descanso corto | 2–3 minutos, recuperación parcial limitada. |
| Descanso largo | 15–20 minutos, lugar seguro. |
| Menús, aprender, selección, cofre | Sin temporizador propio; validar localización para acción física. |

Implementación:
- Centralizar duración y recuperación; reglamento y panel leen la misma configuración.
- Preservar instantáneas de actividad. Una actualización no cambia lo ya iniciado.
- Desactivar `beta_instant_rest` y `beta_instant_tutorial`, además del atajo residual `tutorial_boost`.
- No restaurar todo al iniciar descanso: recompensa al completarlo.
- Cancelar no concede parte del descanso salvo regla explícita posterior.
- Descanso corto debe tener límite/coste para evitar repetir tres veces y equivaler siempre al largo. Semilla: usos limitados por descanso largo; validar en campaña.
- No convertir 15–20 días en una espera obligatoria mediante cooldown de historia.
- Especificar segundos reales: el reloj del mundo actualmente no equivale al reloj real.

### 12.1 Matriz de acciones durante actividad

| Acción | ¿Permitida? | Condición |
|---|---|---|
| Diario, recetas, bestiario, ficha y reglamento | Sí | Solo lectura, sin alterar el trabajo. |
| Seguir logro/objetivo, seleccionar título | Sí | Gestión no física. |
| Comparar equipo | Sí | Consulta. |
| Cambiar equipo de combate | Sí, recomendado | Solo fuera de encuentro; no modifica herramienta/snapshot. |
| Elegir otra herramienta para actividad en marcha | No | Su perfil ya quedó fijado; puede cambiar al terminar. |
| Vender o guardar herramienta comprometida | No, recomendado | Evita consumir/mover el instrumento durante su uso. |
| Viajar, cazar, iniciar combate voluntario, fabricar, descansar | No | Requiere terminar o abandonar la actividad. |
| Conversar/comerciar con PNJ lejano | No | No hay teletransporte social. |
| Depositar o retirar del cofre | No durante trabajo de campo | Requiere habitación y estado compatible. |
| Consumir poción | Revisar compatibilidad | Permitida si no contradice descanso/actividad; no cambia recompensa ni duplica recuperación. |

Herramienta requerida en mochila, no equipada. Si solo está en cofre no cuenta. La preferencia de herramienta especializada ya tiene una base en F15; conservar selección por disciplina y snapshot, sin sumar bonos de todas las que llevas.

### 12.2 Derrota y huida

Campaña inicial: retorno seguro, pérdida temporal y penalización económica pequeña con tope. Semilla para probar: porcentaje de oro disponible con mínimo cero y tope bajo por tramo, sin deuda. No fijar cifra definitiva sin presupuesto de recompensas.

No quitar equipo equipado ni destruir compañero permanente. Reponer medios mínimos mediante recuperación controlada, no oro infinito. Huir conserva el tratamiento de botín que tenga el encuentro/actividad; explicar antes de confirmar. Una misión de retirada cuenta huida válida con humo y prueba recuperada, no cualquier derrota.

<a id="interfaz"></a>
## 13. Interfaz, aprendizaje e IA

### 13.1 Selección directa de clase y rama

Creación: familias/filtros visuales para 14 clases, con descripción corta, recurso, dificultad orientativa y ramas. No ocultar clase tras un examen. Clérigo y Hechicero reemplazan nombres visibles antiguos. **Decidido en 0.10.23 (Josue):** se renombran también los ids, `priest` → `cleric` y `mage` → `sorcerer`, en lugar de conservarlos. Se parte de cero y no hay partidas que proteger, así que no vale la pena cargar con dos nombres para lo mismo.

Nivel 10: aviso → gremio → ramas de tu clase → ficha comparativa → confirmación definitiva. La confirmación evita error de botón; no es prueba ni misión. Mostrar claramente que no hay cambio libre y que cambios sustanciales de balance permiten reelección excepcional.

Ficha de rama: rol principal/secundario, bucle, recurso, habilidad de nivel 10, futuras elecciones 13/17 y culminación. No mostrar como seleccionable una rama incompleta.

### 13.2 Panel de combate

- PV, recurso principal y contador auxiliar necesario.
- Intención visible del jefe.
- Ataque básico, técnica destacada, acciones y objetos.
- Resumen compacto de compañero o forma.
- 💡 ¿Qué hago? contextual, reglas y plantillas, sin IA.
- Informe completo separado del resultado breve.
- Actualizar mensaje existente siguiendo F01; no un mensaje por entidad o por tick.
- Explicar rechazos: falta recurso, cooldown, objetivo inválido; sin gastar acción por rechazo.

### 13.3 Idiomas e imágenes

Todos los nombres aprobados ES/EN en catálogo; costos/efectos derivados de datos. Igualdad de marcadores i18n validada. Comandos permanecen en inglés.

Retratos de seis clases nuevas y actualización visible de nombres de Hechicero/Clérigo; reutilizar dirección visual gouache vigente. Cada activo integrado con media.yaml y prompt adjunto según AGENTS. No bloquear pruebas mecánicas por falta de arte provisional, pero no anunciar retratos que no existen.

### 13.4 IA y memoria

Gemini sigue interpretando y narrando. Campaña principal, jefes, ayuda, selección y entregas funcionan con textos escritos y respaldos. Contexto del PNJ incluye objetivo real, servicios y fase de relación; nunca inventar que vendió o entregó algo.

Notas fuera de alcance: enseñar acciones libres y resolver misiones de múltiples maneras mediante IA. No eliminar capacidades existentes de texto libre sin motivo; simplemente no exigirlas para graduarse.

<a id="fases"></a>
## 14. Roadmap de implementación

Las fases se publican en siguientes parches 0.10.x disponibles. El usuario recibe una gran actualización coherente al superar la puerta de salida; los incrementos internos no obligan a exponer contenido incompleto. No reservar 0.10.20 como número definitivo sin volver a leer la rama.

### Dependencias

B00 auditoría → B01 contratos → B02 progreso/entrega → B03 recursos/motor.
B03 → B04 catálogo efectivo y selección → B05 entidades → B06 clases base → B07 ramas.
B02 + B03 → B08 tiempos/economía.
B06 + B08 → B09 campaña hasta Recaudador.
B07 + B09 → B10 Ciervo.
B10 → B11 región y contenido 11–20.
B07 + B08 + B11 → B12 balance integral → B13 limpieza/documentación → B14 lanzamiento.

El simulador y pruebas se amplían junto a cada fase, no solo en B12. No hacen falta subagentes ni implementar toda la arquitectura antes de una primera prueba vertical.

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
- [ ] Catálogo usado por ficha, motor, descanso, simulador y reportes.
- [ ] Selección directa al 10 con confirmación y validación de clase.
- [ ] Modificadores fijos al 13/17 y entrenamientos 5/12/18.
- [ ] Reelección excepcional por cambio sustancial de versión, de un solo uso.
- [ ] Eliminar anuncio antiguo de especialización al 5.
**Archivos:** class_build propuesto, class_specializations service propuesto, characters, render, handlers, locales.
**Pruebas:** dos ramas elegidas concurrentemente, rama ajena, elección repetida, elección pendiente al saltar niveles.
**Terminado:** la selección altera habilidades y recursos en todas las vistas y no recarga reservas gratuitamente.

### B05 · Compañeros, formas y dispositivos

**Objetivo:** base para ramas complejas antes de multiplicar implementaciones.
- [ ] Auxiliar automático con propietario y frecuencia de acción.
- [ ] Identidad permanente de servidor y bestia; configuración de constructo.
- [ ] Dos entidades del Invocador y Convergencia.
- [ ] Transformación que sustituye acciones sin crear vida.
- [ ] Logs agregados legibles y comportamiento al huir/derrota.
**Archivos:** engine/combat, encounter state, services/combat_service, modelos/versionado, schemas.
**Pruebas:** objetivos muertos, doble actuación, muerte del dueño, carga desde JSON, límite dos, transformaciones sucesivas.
**Terminado:** Demonólogo, Invocador y Cambiaformas tienen un recorrido técnico completo en escenarios de prueba.

### B06 · Rediseñar 14 clases base y nivel 1–9

**Objetivo:** todas juegan bien antes de especializarse.
- [ ] Hechicero fusionado y seis clases nuevas. *El renombrado de ids y nombres visibles de Clérigo y Hechicero ya está hecho (0.10.23).*
- [ ] Kit de inicio y curva por clase.
- [ ] Equipo recomendado, atributos y recurso descritos.
- [ ] No anticipar toda la especialización: conservar identidad base.
- [ ] Enseñanza adaptada a recurso y opciones de cada clase.
**Orden recomendado:** Guerrero/Bárbaro/Paladín/Pícaro/Monje; Clérigo/Hechicero/Druida/Bardo; Brujo/Explorador/Artífice/Chamán/Caballero.
**Pruebas:** 14 clases a niveles 1, 3, 5 y 9; encuentros individuales, grupos y varios combates sin descanso completo.
**Terminado:** ninguna necesita rama, oficio o compañero de otro jugador para superar iniciación.

### B07 · Entregar las 41 ramas por familias

**Objetivo:** cumplir el catálogo completo, sin publicar nombres vacíos.
- [ ] Lote A: daño directo, marcas, defensa y maniobras.
- [ ] Lote B: curación, regeneración, melodías, reacciones y control.
- [ ] Lote C: entidades, formas, tótems y tiempo.
- [ ] Para cada rama: pasiva/técnica 10, desarrollo fijo, dos elecciones y culminación.
- [ ] Separar Catalyst de Alquimia en reglas y guías.
- [ ] Crear prueba que demuestre una decisión característica de cada rama.
**Archivos:** classes.yaml, class_specializations propuesto, efectos del motor, simulador, i18n.
**Pruebas:** cuatro combinaciones 13×17 por rama (164 configuraciones al 20), con casos por mecánica y barridos de simulación.
**Terminado:** las 41 ramas son seleccionables solo cuando tienen recorrido 10–20 y material ES/EN completo.

### B08 · Tiempos, descanso, derrota y economía

**Objetivo:** dejar de equilibrar con ayudas de beta.
- [ ] Aplicar tabla §12; retirar aceleración residual del tutorial.
- [ ] Descanso corto y largo con interrupción segura.
- [ ] Matriz de acciones busy; permitir consulta y gestión compatibles.
- [ ] Herramientas en mochila y selección ya implementada preservadas.
- [ ] Precios normales, stock crítico y cobertura T0/T1 de clases.
- [ ] Derrota inicial con coste limitado y retorno seguro.
**Archivos:** activities.py, inventory.py, home.py, crafting.py, config.py, items/recipes/professions, render/rulebook.
**Pruebas:** reiniciar temporizador, cambiar/vender herramienta comprometida, doble claim, descanso cancelado, arbitraje de lotes, ausencia de oro.
**Terminado:** sesión de 60–90 minutos funcional sin atajos ni bloqueos económicos.

### B09 · Campaña común hasta el Recaudador

**Objetivo:** aprender sistemas mediante la historia.
- [ ] Escribir lore del mentor y texto ES/EN.
- [ ] Actos I–VI con eventos y objetivos verificables.
- [ ] Ocho variantes de las tres tareas de oficio.
- [ ] Habitación, plano, maestrías, pesca/cocina, diario, reputación, huida.
- [ ] Recaudador con señales, protección y recarga.
- [ ] Entrega que establece el hito 10; camino para XP faltante.
**Archivos:** quests.yaml, npcs.yaml, monsters.yaml, content/world, fallbacks, quest service, media.
**Pruebas:** todas las clases; cada ruta de oficio; jugador que vende material o cambia oficio; falta/exceso de XP.
**Terminado:** primera sesión completa y campaña sin callejones hasta la selección al 10.

### B10 · Ciervo y graduación

**Objetivo:** culminar aprendizaje usando la rama escogida.
- [ ] Selección directa integrada con el gremio.
- [ ] Preparación T1 asequible sin exigir conjunto completo.
- [ ] Ciervo: endurecimiento, carga y vulnerabilidad.
- [ ] Entrega de graduación y apertura de región.
- [ ] Ayuda contextual con respuestas válidas por clase.
**Pruebas:** 41 ramas al nivel 10; victoria, derrota, huida y retorno; ayuda sin revelar resultados futuros.
**Terminado:** todas las ramas superan el encuentro con preparación razonable y el diario explica el paso siguiente.

### B11 · Región y aventuras 11–20

**Objetivo:** que diez niveles nuevos tengan contenido.
- [ ] Validar lore y nombre de región cercana.
- [ ] Grafo conectado, viajes directos, refugio y relación con Crownreach.
- [ ] Cuatro actos, secundarias, criaturas con patrones y fuentes T1.
- [ ] Contextos para modificadores 13/17 y culminación 20.
- [ ] Actividades de veterano sin multijugador ni mazmorra.
**Archivos:** mundo, NPC, misiones, monstruos, botines, recetas especiales, logros, arte.
**Pruebas:** rutas, recursos accesibles, contenido según nivel, objetivos alcanzables, regreso a ciudad.
**Terminado:** recorrido continuo hasta 20 y aventuras donde usar técnica final.

### B12 · Balance integral

**Objetivo:** medir campaña, no solo un jabalí.
- [ ] Simulador usa builds efectivos, equipo y decisiones de recursos.
- [ ] Escenarios §15 y políticas informadas por rama.
- [ ] Runs de dos sesiones diarias para medir ritmo.
- [ ] Ajustar XP, daño, recuperación, tiempos y economía por datos.
- [ ] Resolver diferencias de duración entre HEAL/DEFF/DMG/CONTROL.
**Terminado:** informe de balance con versión/semillas, defectos resueltos y limitaciones explícitas.

### B13 · Retirar cripta, corregir documentación y preparar reset

**Objetivo:** eliminar contradicciones antes de lanzar.
- [ ] Revisar referencias de mundo, objetos, logros y pruebas a cripta.
- [ ] Sustituir misiones antiguas y logros incompatibles de la nueva edición.
- [ ] Actualizar resúmenes, TODO, roadmap e iter.
- [ ] Crear procedimiento de reinicio que conserve preferencias.
- [ ] Ensayo de backup/restore y proceso en staging.
**Terminado:** cero referencias activas rotas y reinicio ensayado sin tocar datos reales.

### B14 · Candidato y lanzamiento

**Objetivo:** publicar solo al completar puerta de salida.
- [ ] Suite completa según AGENTS.
- [ ] Concurrencia PostgreSQL real; tgtest ES/EN.
- [ ] Copia de seguridad y mantenimiento.
- [ ] Migraciones, reinicio aprobado del estado de juego y nueva época.
- [ ] Smoke test de alta, combate, entrega, oficio, actividad y diario.
- [ ] Borradores de anuncios ES/EN con cambios y aviso de reinicio.
**Terminado:** juego accesible desde nivel 1, sin estado antiguo ni trabajos que vuelvan a pagar. Preparar anuncios no implica enviarlos automáticamente.

<a id="validacion"></a>
## 15. Plan de balance y validación

### 15.1 Matriz mínima

| Dimensión | Cobertura |
|---|---|
| Clase base | 14 clases; niveles 1, 3, 5 y 9. |
| Rama | 41 ramas; niveles 10, 13, 17 y 20. |
| Modificadores | Dos opciones por elección; cuatro combinaciones finales por rama. |
| Equipo | T0 inicial/final, T1 básico y T1 avanzado razonable. |
| Encuentro | Rival débil, estándar, élite, pareja/grupo, jefe y secuencia de encuentros. |
| Estrategia | Básico, política informada, uso conservador y uso explosivo de recursos. |
| Recuperación | Descanso corto/largo, pociones, sesión con recursos parciales. |
| Entidades | Invocador, servidor, bestia, constructo, torreta, tótem y forma. |
| Idioma | ES/EN; marcadores, botones y textos de ayuda. |
| Infraestructura | Reintentos, reinicio, clicks antiguos, concurrencia PostgreSQL. |

No usar el mismo bot simple de prioridades para declarar mala una rama que necesita preparación. Comparar política básica con política competente y registrar decisiones disponibles. Muestreos con semillas reproducibles; acompañar porcentajes con tamaño de muestra e incertidumbre.

### 15.2 Métricas

- Victoria, derrota, huida y timeout.
- Rondas y duración real de interacción.
- Daño y recuperación efectivos; daño prevenido; turnos enemigos afectados.
- Recurso inicial/final, tiempo sin acción útil, consumibles.
- Uso de acciones dominantes y diversidad de decisiones.
- PV finales, dependencia de crítico y sensibilidad al equipo.
- Oro neto, materiales/minuto, coste de descanso y progresión artesanal.
- Tiempo activo, espera, AFK y sesión total por misión.
- XP bloqueada por hito y tiempo en puerta.
- Reintentos por jefe y porcentaje que responde correctamente a señales.
- Coste/latencia de IA por sesión, sin confundir narración con reglas.

### 15.3 Objetivos experimentales

Semillas, no promesas:
- Encuentros introductorios razonables: alta probabilidad de victoria con política básica y herramientas enseñadas.
- Jefes: la política informada mejora claramente resultados frente a ignorar señales.
- HEAL/DEFF no deben duplicar sistemáticamente duración de DMG en misiones comunes; investigar diferencias persistentes.
- Ninguna rama requiere consumibles raros para el Ciervo.
- No hay acción básica inútil por agotamiento de recurso.
- No es posible controlar a un jefe para que nunca actúe.
- Ninguna configuración domina simultáneamente daño, defensa, control y economía de recurso.
- Ritmo de dos sesiones/día compatible con 5–10 días de iniciación y 15–20 acumulados al 20.

Definir umbrales numéricos finales con datos de sesiones; una victoria del 95 % contra un enemigo débil no prueba balance de campaña.

### 15.4 Casos de integridad obligatorios

- Premio, hito y nivel en una transacción.
- Doble selección de rama/modificador; una sola queda aplicada.
- Reclamar actividad tras reinicio y cambio de contenido conserva snapshot.
- Pociones no restauran a la vez usos antiguos y recurso nuevo por error.
- Transformar/invocar/cambiar configuración no cura gratis.
- Catálogo efectivo idéntico en ficha, motor y simulador.
- Modificadores no duplicados al recargar.
- Entidad no actúa dos veces por bonus o reintento.
- XP en cap preservada y desbloqueada correctamente.
- Objetos de misión recuperables sin explotación de venta.
- Postgres prueba carreras; SQLite solo lógica compatible.
- Reset deja preferencias y elimina efectos de juego, incluidos rumores y trabajos pendientes.

### 15.5 Comandos y evidencia

Comandos existentes a adaptar, no ejecutados para producir este documento:
- pytest por área y contenido durante cambios.
- Suite completa antes de commits según AGENTS.
- `oath simulate --level 1-20`: ampliar primero las reglas y políticas del simulador; el argumento por sí solo no crea contenido de niveles altos.
- Añadir opciones propuestas de rama/modificadores/equipo/secuencia al simulador.
- `oath tutorial-stats`: conservar reporte actual, añadir métricas de sesión/actividad; no llamar tiempo activo a diferencia de timestamps.
- tgtest ES/EN con cuenta de prueba y bot real.
- Informe de resultados con SHA de código, versión de contenido, semilla y configuración.

<a id="lanzamiento"></a>
## 16. Reinicio limpio y lanzamiento

**Autorizado como decisión de lanzamiento; no ejecutado al generar este roadmap.** No reiniciar durante la escritura del plan ni al instalar una migración.

### 16.1 Datos

Eliminar/reiniciar:
- Personajes, habilidades entrenadas, progresión, ramas, modificadores y compañeros.
- Mochila, cofre, propiedad artesanal y vivienda.
- Misiones, logros, títulos, reputación y memoria relacional derivada de partidas.
- Encuentros, actividades, premios pendientes y notificaciones de estado antiguo.
- Rumores/hechos del mundo producidos por esas partidas.
- Preferencias de UI que apuntan a ids de personaje/objetivo desaparecidos.

Conservar:
- Identidad de cuenta y preferencias no ligadas a personaje: idioma y ajustes generales.
- Registros técnicos necesarios, separados del mundo jugable.
- Contadores de seguridad/cuota de IA que no deben poder reiniciarse por reset de personajes.
- Copia de seguridad previa con retención definida.

### 16.2 Procedimiento

1. Ensayar en staging con copia controlada y conteos por tabla.
2. Crear backup y verificar restauración.
3. Mantenimiento: detener nuevas acciones y workers de actividades.
4. Aplicar migraciones compatibles; no llamar delete_player masivo porque elimina User.
5. Ejecutar servicio administrativo de reset con alcance y conteos; preservar cuentas/preferencias.
6. Invalidar época de jobs, callbacks, anuncios y hechos anteriores.
7. Eliminar/regenerar consecuencias compartidas; conservar datos estáticos de mundo.
8. Verificar integridad referencial y ausencia de estados activos huérfanos.
9. Reiniciar workers y crear personaje de prueba.
10. Smoke test ES/EN y abrir acceso.

Ante fallo previo a apertura, restaurar copia completa de estado compatible. Después de reabrir, no restaurar silenciosamente perdiendo partidas nuevas: procedimiento de incidencia separado.

<a id="trazabilidad"></a>
## 17. Trazabilidad con TODO y planning

Este documento desarrolla el nuevo alcance, sin sustituir íntegramente el roadmap general ni borrar su trabajo histórico.

| Tema de TODO.md / ficha | Aplicación aquí |
|---|---|
| Especialización a nivel 5 / F19 | Sustituida por nivel 10 directo; B04/B07. |
| Siguientes clases Explorador y Artificiero / F14 | Ampliado a las seis nuevas y fusión Mago/Hechicero; B06. |
| Campamento opcional / F13 | Nota N04; no requisito de esta entrega. |
| Más misiones después del nivel 5 / F12 | Campaña completa y región 11–20; B09–B11. |
| Entregar al PNJ / F12 | Estado de entrega y recompensa atómica; B02. |
| Descanso corto / F07 | Recuperación calibrada; B08. |
| Tiers y recetas / F15 | Conservar T0/T1 ya entregados, ampliar cobertura para clases; B08/B11. |
| Cofre y habitación / F06/F15 | Ya entregados; integrar nueva questline, no rehacer. |
| Ramas de maestría y herramientas / F15 | Ya entregadas; preservar contrato separado de clases. |
| Tutorial y balance / F13 | Campaña verificable, dos jefes y métricas de sesión. |
| Monstruos / F09/F18 | Patrones, telegráficos, control y balance por rama. |
| Segunda región / F10 | Ahora alcance aprobado en 0.10.x, próxima a Crownreach. |
| Cripta / F10/F12 | Retirada activa, referencias y recompensas reubicadas. |
| Logros / F04 | Actualizar edición/condiciones de mundo nuevo; no construir otro motor. |
| Facciones, rumores / F17 | Enseñanza individual y consecuencias verificables; sin crisis global multiplayer. |
| Cooperativo, gremios jugadores y PvP / F18 | 0.11; no habilitados aquí. |
| IA / F20 | Conservar Gemini y respaldos; ayuda y progresión sin IA. |

### Archivos que deben actualizarse al implementar

- `planning/ordines.md`: 14 clases, 41 ramas, recursos y nivel 10.
- `planning/progressio.md`: 1–20, híbrido, entrenamientos, elecciones y reinicio.
- `planning/pugna.md`: recursos, control de jefes, auxiliares, descanso y derrota.
- `planning/mundus.md`: mentor, nueva campaña, jefes, región y retirada de cripta.
- `planning/bestiarium.md`: patrones, nuevas criaturas y criterios de dificultad.
- `planning/opificia.md` y `roadmap-profesiones.md`: compatibilidad con nuevos niveles; no duplicar F15.
- `planning/mercatura.md`: precios, T1, consumibles y suministros.
- `planning/facies.md`: selección, recursos, busy, ayuda y mensajes.
- `planning/narratio.md`: contexto de mentor, fallback y límites.
- `planning/ars.md`, `TODO-images.md`: nuevas clases, jefes, mentor y región.
- `planning/README.md`: enlace a este documento.
- `planning/roadmap.md`, `planning/iter.md`: reemplazar alcance viejo y números orientativos ocupados.
- `planning/Possibilium.md`: estados de ideas afectadas, sin reescribir anexos históricos.
- `TODO.md`: cerrar solo trabajo demostrado; conservar ideas futuras.
- `tests/features.md`: checklist reproducible de campaña, ramas y recuperación.
- `CHANGELOG.md` y `oathforge/__init__.py`: versión real por incremento.
- `README.md`: actualización final de presentación cuando corresponda al cierre solicitado; no afirmar funciones antes de estar listas.

No marcar implementado por incorporar una idea a este documento. No publicar anuncios sin autorización de envío.

<a id="salida"></a>
## 18. Puerta de salida

### Producto

- [ ] 14 clases distintas y completas, sin duplicado Mago/Hechicero.
- [ ] 41 ramas con selección al 10, modificaciones 13/17 y culminación al 20.
- [ ] Catalyst claramente separado de oficio Alquimia.
- [ ] Invocador limitado a dos y Convergencia; Demonólogo con identidad persistente.
- [ ] Nivel 10 exige XP e hito del Recaudador; no bloqueo circular.
- [ ] Ciervo posterior a selección, vencible por todas las ramas.
- [ ] Primera sesión enseña ciclo básico; campaña practica todos los sistemas definidos.
- [ ] Un oficio obligatorio, tres misiones coherentes y cambio pagado compatible.
- [ ] Nueva región cercana con contenido 11–20 y Crownreach central.
- [ ] Aventuras al 20 para usar poder final.
- [ ] Cripta y mazmorras fuera de contenido activo.
- [ ] Tiempos normales, sin aceleraciones de beta ocultas.

### Integridad y operación

- [ ] Entregas, recursos, elecciones y recompensas idempotentes.
- [ ] Timers y encuentros sobreviven a reinicios.
- [ ] Ninguna elección o cambio de forma genera curación/recarga infinita.
- [ ] Snapshot artesanal preservado.
- [ ] Esquemas, referencias y ES/EN válidos.
- [ ] Pruebas PostgreSQL y tgtest completadas y documentadas.
- [ ] Reset ensayado, preferencias preservadas, época antigua invalidada.

### Balance

- [ ] Curva y ritmo medidos sobre dos sesiones diarias.
- [ ] Ramas defensivas y sanadoras viables sin tedio excesivo.
- [ ] Control útil sobre jefes sin bloqueo permanente.
- [ ] Fuentes T0/T1 y economía accesibles para todas las clases.
- [ ] Ayuda y campaña completas sin llamadas a IA obligatorias.
- [ ] Riesgos conocidos documentados; no declarar equilibrado lo no probado.

<a id="fuentes"></a>
## 19. Fuentes y límites de revisión

Lectura directa de GitHub en el SHA fijado. Se inspeccionaron README, AGENTS, índice de planning, ordines, progressio, opificia, mundus, pugna, roadmap, TODO, CHANGELOG y versión; además progression, characters, quests, specializations, activities, combat_service, combat, schemas, models, config, admin, simulate, classes/quests YAML y tests/features. La relación completa de archivos del árbol permitió localizar dominios; listar un archivo no equivale a leerlo.

Fuentes fijadas:
- [Versión](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/__init__.py)
- [Changelog](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/CHANGELOG.md)
- [Invariantes](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/AGENTS.md)
- [Oficios 0.10.19](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/planning/opificia.md)
- [Progresión actual](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/engine/progression.py)
- [Aplicación de XP](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/services/characters.py)
- [Misiones](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/services/quests.py)
- [Especializaciones artesanales](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/services/specializations.py)
- [Modelo de datos](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/database/models.py)
- [Combate](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/engine/combat.py)
- [Actividades](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/services/activities.py)
- [Administración](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/services/admin.py)
- [Simulador](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/oathforge/tools/simulate.py)
- [TODO](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/TODO.md)
- [Roadmap general](https://github.com/JD3M0N/Oathforge/blob/107ccacba523004a0059a3f3b1be796c3591ee65/planning/roadmap.md)

Esta revisión no ejecutó el bot, no abrió la BD de producción, no corrió el simulador ni certificó tests. Las validaciones aquí descritas son trabajo de implementación. Los enlaces fijados permiten distinguir cambios posteriores de esta base.

<a id="notas"></a>
## 20. Notas e ideas futuras — conservar al final

### N01 · Lore del mentor y encaje de la campaña — pendiente necesario

Escribir un personaje nuevo cálido, aventurero y emblemático. Su nombre, género, linaje y edad no se han fijado. No asumir que Rowan Ashford o Merrin Valehart están aprobados. Darle motivación, límites, voz y una relación progresiva con el recluta. Encajarlo con el gremio, Vale, maestros y hechos de Aetherfall antes de producir texto final. No convertirlo en protagonista que gana por el jugador.

### N02 · Nombre e historia definitiva de la región — pendiente necesario

La cercanía a Crownreach y la función 11–20 sí están aprobadas. Greyforge Vale es una propuesta de este documento. Verificar geografía, rutas, facciones, materiales y causa de fauna alterada; explicar por qué la ciudad necesita esa comarca y por qué el personaje viaja allí.

### N03 · Cambio de especialización — futuro

No disponible libremente ahora. En una versión posterior valorar instructor, oro, condiciones y conservación de progreso. Nunca recargar recursos ni duplicar habilidades al cambiar. Diferenciar de la reelección gratuita por cambios de balance, que sí entra ahora.

### N04 · Varios personajes y salto de iniciación — futuro

Mantener un personaje por cuenta en esta entrega. Más adelante decidir número de plazas, progreso compartido, títulos y derecho a saltar campaña tras completarla una vez. El primer personaje actual debe jugarla. No añadir multiclase como consecuencia automática.

### N05 · Campamento y misiones específicas de clase — idea futura

La campaña es común. Las antiguas 3–5 misiones de entrenamiento por clase quedan como ampliación, no requisito de lanzamiento. Podrían profundizar identidad después de graduarse, pero no sustituir la selección directa aprobada.

### N06 · Acciones libres y soluciones alternativas con IA — futuro

Enseñar a investigar, negociar o improvisar mediante lenguaje natural y resolver un conflicto de varias formas sigue siendo deseable. No es objetivo obligatorio de esta campaña. Mantener motor determinista, intenciones tipadas, costes y evidencias; no permitir que el narrador adjudique éxito, objetos o hitos.

### N07 · Utilidad fuera del combate — aprobada en principio, alcance acotado

Ventajas ocasionales, no requisito para completar historias. Ejemplos candidatos: Explorador reconoce un rastro; Artífice comprende una avería; Hechicero detecta una anomalía; Bardo identifica una contradicción en un rumor. Deben existir rutas alternativas y no monopolizar recursos. Diseñar algunas donde tengan sentido; no inventar una profesión paralela para cada clase.

### N08 · Expansiones de diez niveles y T2 — futuro aprobado como dirección

Siguiente techo 30; T2 cubre 21–30. No implementar ahora rangos artesanales nuevos, umbrales ni habilidades 21–30. Revisar cómo ampliar rango/tier sin romper independencia entre artesano y nivel del personaje.

### N09 · Multijugador — 0.11

Grupos, roles hacia aliados humanos, sincronización de turnos, escalado, comercio entre jugadores, gremios de jugadores, PvP y eventos compartidos. Las ramas funcionan solas ahora. Tener entidades aliadas automáticas no implica haber implementado cooperativo.

### N10 · Mazmorras y retorno de la cripta — futuro

Cripta retirada de contenido activo. Puede volver rediseñada cuando se aprueben mazmorras. Conservar ideas e historial; no dejar misiones, materiales o logros necesarios dependiendo de ella.

### N11 · Números de XP, tiempos y economía — calibración pendiente

Mantener los rangos artesanales 0–5. Curva de personaje, XP de oficio/maestría, costes, recuperación y duración se calibran con datos. Las tablas son semillas; no marcarlas equilibradas. Medir tiempo de pared por separado de sesiones, especialmente con dos sesiones diarias.

### N12 · Evolución de invocaciones y compañeros — limitado ahora

Invocador: dos espacios y Convergencia, no tercera invocación al 20. La tercera fue descartada para este diseño, no debe quedar como tarea obligatoria. Más variedad de repertorio puede añadirse después. Demonólogo conserva identidad personal del mismo servidor; evoluciones no son cambio permanente de personaje.

### N13 · Lore de clases y diferenciación — pendiente de contenido

Definir origen de Brujo, Chamán y Caballero de la Muerte en Aetherfall. No importar de otro juego pactos, deidades o cosmología completos. Preservar diferencias Paladín/Clérigo, Guerrero/Bárbaro, Criomante/Escarcha y las cuatro familias de compañeros.

### N14 · Ideas previas de profesiones — mantener en su contrato original

No perder las notas del roadmap-profesiones: revisar Rastreo como maestría/afición; experimentar Cocina; herramientas y porcentajes; variantes de diseños, calidad, reciclaje, experimentación de ingredientes, proyectos personales y encargos; aficiones nuevas, encantamiento, durabilidad, cebos, vetas, clima y fauna. No quedan aprobadas para esta entrega por mencionarlas aquí. Consultar sus N01–N13 y trasladar solo dependencias necesarias, conservando la explicación original.

Los tres pedidos narrativos del oficio en la campaña son contenido escrito. No equivalen a aprobar un sistema abierto de encargos personalizados ni proyectos personales.

### N15 · Revisión de identidad sin inflar menús — criterio permanente

Si dos ramas toman las mismas decisiones cambiando solo daño elemental, revisar su bucle antes de añadir más botones. Máximo una barra principal y un contador auxiliar necesario. Textos breves arriba, explicación mecánica bajo demanda. No confundir profundidad con cantidad de estados.

### N16 · Valores todavía no fijados — resolver durante implementación

- Fórmula exacta de XP y posibles hitos posteriores al Ciervo.
- Magnitudes de recursos, maná recuperado, regeneración y cooldowns.
- Coste/tope económico de derrota; número de descansos cortos por largo.
- Poderes y nombres definitivos de culminaciones excepto Convergencia.
- Contenido exacto de las dos opciones de cada modificador.
- Especies y apariencia de la bestia; formas del servidor.
- Catálogo de equipo y recompensas por clase.
- Número final de misiones según duración probada.

Estas decisiones no bloquean escribir el roadmap, pero sí bloquean declarar completa la fase correspondiente. No ocultarlas como supuestos ya aprobados.

---

**Estado de este documento:** diseño preparado sobre 0.10.19 y decisiones de la conversación. No se ha modificado el repositorio ni reiniciado ningún personaje. Al incorporarlo al proyecto, mantener esta base histórica y actualizar el seguimiento de fases con evidencias reales.
