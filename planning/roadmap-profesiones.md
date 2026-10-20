# Roadmap de profesiones, maestrías y aficiones (F15)

Documento de diseño e implementación de la ficha [F15](roadmap.md#F15). Alcance: ocho oficios, dos aficiones, cinco maestrías con refinado y ramas, herramientas especializadas, tiers T0/T1, la calle de los oficios con un puesto por oficio, el Gremio de Aventureros y la habitación propia.

**Base auditada:** `josue-development`, versión **0.10.8**, 20 de octubre de 2026. Lo que aquí se marca como implementado está verificado en el código; el resto es propuesta hasta que se cierre su fase.

**Objetivo:** un sistema artesanal entretenido en Telegram, con actividades propias de cada oficio, colaboración opcional, refinado significativo, herramientas especializadas y conexión con la aventura. Quien quiera puede dedicarse sobre todo a la artesanía, aunque el mundo y sus recursos inviten a salir.

## Índice

1. [Estados y decisiones](#1-estados-y-decisiones)
2. [Auditoría y discrepancias](#2-auditoría-y-discrepancias)
3. [Arquitectura de progresión y tiers](#3-arquitectura-de-progresión-y-tiers)
4. [Maestrías, refinado y especializaciones](#4-maestrías-refinado-y-especializaciones)
5. [Herramientas y probabilidades](#5-herramientas-y-probabilidades)
6. [Ocho profesiones y dos aficiones](#6-ocho-profesiones-y-dos-aficiones)
7. [Recetas, técnicas y planos](#7-recetas-técnicas-y-planos)
8. [El Gremio, la calle de los oficios y la habitación](#8-el-gremio-la-calle-de-los-oficios-y-la-habitación)
9. [Contratos técnicos y datos](#9-contratos-técnicos-y-datos)
10. [Interfaz y comandos](#10-interfaz-y-comandos)
11. [Fases de entrega](#11-fases-de-entrega)
12. [Pruebas y criterios de salida](#12-pruebas-y-criterios-de-salida)
13. [Documentación y trazabilidad](#13-documentación-y-trazabilidad)
14. [Fuentes e investigación](#14-fuentes-e-investigación)
15. [Notas finales: experimentos, balance y futuro](#15-notas-finales-experimentos-balance-y-futuro)

## 1. Estados y decisiones

Convenciones: **Acordado** = decisión explícita de Josue; **Implementado** = verificado en la base; **Propuesta técnica** = forma recomendada de realizar una decisión; **Pendiente** = valor o comportamiento no confirmado; **Futuro/experimental** = no convertir automáticamente en requisito de lanzamiento.

| ID | Estado | Regla |
|---|---|---|
| D01 | Acordado | Dos profesiones activas. Maestrías libres. Cocina y Pesca son aficiones sin plaza. |
| D02 | Acordado | Carpintería es un oficio completo. Sastrería se incorpora como octavo oficio. |
| D03 | Acordado | **T0 y T1 entran en 0.10.** El tier se deduce del rango de la receta: T0 = rangos 0–2, T1 = rangos 3–5. No hace falta un campo nuevo ni ampliar el nivel de personaje para empezar. |
| D04 | Acordado | T1 supera a T0; T0 mantiene usos económicos y productivos. |
| D05 | Acordado | El oficio permite fabricar por rango; el personaje equipa por nivel. Un artesano de nivel bajo puede fabricar para personajes superiores. |
| D06 | Acordado | Se conservan rangos artesanales 0–5. La curva de XP y su ritmo quedan para balance posterior (N11). |
| D07 | Acordado | Refinado básico pertenece a la maestría y concede XP de esa maestría. Menas → lingotes; troncos → tablones; pieles → cuero; plantas → fibra limpia. |
| D08 | Acordado | Dos especializaciones iniciales por maestría y también por Pesca. Elección en rango 2. |
| D09 | Acordado | Cambio de especialización en el Gremio, pagando oro. La anterior queda pausada y puede reactivarse sin borrarse. |
| D10 | Acordado experimental | Rastreo se prueba como maestría; documentar la posibilidad de convertirlo en afición o eliminarlo (N01). |
| D11 | Acordado | Herramientas con diseños especializados; Carpintería fabrica cañas. Sin desgaste actualmente. |
| D12 | Acordado | Los bonos de raro son relativos. El bono de unidad extra se evalúa por actividad completa. |
| D13 | Acordado | Versiones básicas autónomas; mejoradas pueden pedir componentes de otros oficios. |
| D14 | Acordado | Equipo artesanal y botín equivalentes dentro del mismo nivel/tier, con utilidades distintas; las piezas excepcionales combinan aventura y fabricación. |
| D15 | Acordado | **El Gremio de Aventureros es un lugar nuevo junto a la plaza**: Vale y el alistamiento, las estaciones de refinado, un fogón, las especializaciones y la habitación. Sustituye la idea de reunir allí todos los talleres. |
| D16 | Acordado | **La habitación entra dentro del tutorial.** Una misión nueva: conseguir madera, aserrarla en el Gremio, montar el cofre y montar la cama con tela que entrega el Gremio. Descansar allí no cuesta oro. Las mejoras del cofre requieren Carpintería. |
| D17 | Acordado | Instructor/rango + aventura para aprender. Técnicas comunes desbloqueadas al subir rango; recetas especiales individuales. |
| D18 | Acordado | Diseños de recetas fijos inicialmente. Planos especiales comerciables antes de aprenderlos. |
| D19 | Futuro | Experimentación de ingredientes, proyectos personales y encargos: notas explicadas, no requisitos de esta entrega (N08, N09, N10). |
| D20 | Experimental | Cocina: rama Chef de calidad y rama de ración adicional, pendientes de prueba y aprobación de sus números (N03). |
| D21 | Acordado | **Todo el catálogo T1 se publica en 0.10**, aunque el nivel máximo siga en 5: las armas, armaduras y consumibles de combate T1 llevan requisito de nivel y se fabrican, venden y guardan sin poder equiparse todavía. |
| D22 | Acordado | **La calle de los oficios se refactoriza en ocho puestos**, cada uno un lugar del mapa con su estación y su maestro. El Barrio de Oficios (`crownreach_workshops`) conserva su id y pasa a ser la calle de la que cuelgan. |
| D23 | Acordado | **Un maestro PNJ por puesto**: enseña y cambia su oficio, explica sus técnicas y vende herramientas básicas, componentes de otros oficios y planos. |
| D24 | Acordado | **Tessa es la maestra de Herrería** y su puesto de día pasa a la Forja. Sigue vendiendo lo que vendía. |
| D25 | Acordado | Comandos nuevos al estilo de Chat Wars: `/recipes`, `/r_<id>`, `/craft_<id> [n]`, `/guild`, `/room` y `/stash`. |

No confundir cambio de **oficio** con cambio de **especialización de maestría**. El precio actual de 25 de oro corresponde al primero; el segundo tiene su propio precio configurable.

### Números provisionales

Son valores semilla para que el sistema se pueda jugar y medir. Ninguno está aprobado como balance final (N11).

| Qué | Valor inicial | Dónde vive |
|---|---|---|
| Cambiar de rama de maestría | 50 de oro | `config.py` |
| Capacidad del cofre | 20 espacios, +10 por mejora | `config.py` |
| Lote máximo de fabricación | 10 | `config.py` |
| Herramienta rápida | −10 % de duración | catálogo de objetos |
| Herramienta selectiva | +5 % relativo de hallazgo raro | catálogo de objetos |
| Herramienta productiva | 5 % de una unidad extra por actividad | catálogo de objetos |
| Requisito de nivel del equipo de combate T1 | 10 | catálogo de objetos |

## 2. Auditoría y discrepancias

### 2.1 Base real (0.10.8)

- **Oficios y aficiones**: siete oficios con estación propia y dos aficiones (`content/professions.yaml`). Cambiar de oficio cuesta 25 de oro y conserva la XP (`services/professions.py`, `SLOTS = 2`, `SWAP_COST = 25`).
- **Maestrías**: no están en YAML. Son una tupla en `engine/gathering.py` (`MASTERIES`), con los iconos en `bot/render.py` y la lista de crónicas en `content/schemas.py`. Tres sitios que hay que tocar a la vez para añadir una.
- **Rangos**: `RANK_XP = (0, 80, 240, 500, 900, 1500)`, 0–5, compartidos por oficios, aficiones y maestrías.
- **Recetas**: 26 en `content/recipes.yaml`, con `profession`, `min_rank`, `ingredients`, `outputs` y `xp`. Nada más: no hay técnica, plano, estación ni tier.
- **Estación**: sale del **oficio**, no de la receta (`services/crafting.py`). Por eso hoy no se puede representar fundición libre, una receta de misión ni dos puestos para una misma disciplina.
- **Refinado**: el lingote es de Herrería (3 menas + 1 carbón, 10 XP), el tablón de Carpintería (3 troncos → 2 tablones, 8 XP) y el cuero de Peletería. Son valores heredados, no un balance aprobado.
- **Herramientas**: un objeto de tipo `tool`, sin campos propios. La herramienta de cada actividad es una cadena del lugar (`Gathering.tool`) y basta tenerla en el inventario.
- **Bono de rango**: +4 % por rango, tope 20 %, una tirada en trabajo corto y tres en expedición, y la unidad extra es siempre del recurso de más peso. No equivale al bono de herramienta que se propone.
- **Actividades**: se guarda la semilla y el momento, pero **no la tabla**: `claim` lee el contenido vigente. Es la casilla pendiente de F08 que este plan resuelve.
- **Equipo**: cuatro ranuras y ningún requisito de nivel para equipar.
- **Almacenamiento**: no existe cofre, alijo ni banco.
- **Mundo**: el Barrio de Oficios es un solo nodo con las siete estaciones, `guild: true` y **ningún PNJ**. Se aprende un oficio pulsando un botón, no hablando con nadie. El fogón está en la taberna. Tessa vende las herramientas en el mercado.
- **Tutorial**: diez misiones; la única de fabricación es el estofado (afición Cocina, fogón de la taberna). Ninguna pide aprender un oficio.
- **Progresión**: nivel máximo 5 (`engine/progression.py`).

### 2.2 Cambios de dirección que quedan expresos

| Dirección anterior | Decisión de este documento |
|---|---|
| Afinidades a rango 3 (`MIN-01..04`) | Especializaciones a rango 2, dos ramas por disciplina |
| Recetas por tier T1–T3 (TODO) | T0 y T1, deducidos del rango de la receta |
| Talleres reunidos en el Gremio | El Gremio tiene refinado, especializaciones y habitación; los talleres son ocho puestos en la calle de los oficios |
| Un único lugar «Barrio de Oficios» con siete estaciones | La calle conserva su id y de ella cuelgan ocho puestos, cada uno con su maestro |
| Se aprende el oficio con un botón en la calle | Se aprende con el maestro de ese oficio, en su puesto |
| Fundición en el yunque del herrero | Horno en el Gremio, accesible por Minería, con XP de Minería |
| Tablones exclusivos del carpintero | Aserradero en el Gremio, con XP de Tala; Carpintería fabrica productos elaborados |
| Armas artesanales no superiores a las de tienda | Equivalencia con el botín del mismo tramo, con utilidades propias |
| Cofre personal en la ciudad (F06) | El cofre es parte de la habitación del Gremio y lo cubre la fase 5 de este plan |
| Encargos como expansión prioritaria | Idea futura (N10), no condición para terminar |

El «Estado actual (0.8.2)» de [opificia.md](opificia.md) está desfasado; prevalece el código auditado.

## 3. Arquitectura de progresión y tiers

### 3.1 Cuatro variables independientes

1. **Nivel de personaje** (1–5 hoy, 20 como objetivo lejano): aptitud de combate y requisitos de equipo.
2. **Rango de disciplina** (0–5): recursos, refinados y recetas accesibles.
3. **Especialización activa**: enfoque de una maestría o de Pesca; se desbloquea a rango 2.
4. **Conocimiento**: técnicas comunes y recetas especiales aprendidas.

### 3.2 T0 y T1 por rango

El tier no es un campo nuevo que haya que mantener a mano: **una receta de rango 0–2 es T0 y una de rango 3–5 es T1**. Así el tier siempre coincide con lo que de verdad limita el acceso, y un oficio entero sube de tier a medida que el artesano progresa, sin esperar a la expansión del nivel de personaje.

Consecuencias:

- Los **materiales T1** salen de donde ya hay recursos con `min_rank` 3+ (gemas, musgo del reposo, trucha plateada), de nuevos recursos de rango 3–5 en los mismos lugares, de jefes y de la cripta, y de lo que venden los maestros.
- Las **herramientas, los muebles y las mejoras de cofre T1** se usan por rango de maestría: se notan desde el primer momento.
- Las **armas, armaduras y consumibles de combate T1** llevan requisito de nivel 10. Se fabrican, se venden y se guardan, y no se equipan ni se usan hasta que exista la progresión 10–20. El reglamento y la ficha del objeto lo dicen con claridad; no es un error ni una promesa vacía.
- T0 conserva sus usos: menor coste, consumo cotidiano y componentes comunes dentro de las recetas T1.

Separar tier de rareza y de calidad: una comida mejor no crea un tier nuevo.

### 3.3 Lo que no se decide aquí

La curva de XP, la ampliación del nivel de personaje a 20 y la XP de personaje por artesanía quedan para [F05](roadmap.md#F05) y para la nota N11. Este documento no las resuelve y no depende de ellas para entregarse.

## 4. Maestrías, refinado y especializaciones

### 4.1 Cadena de materiales

| Disciplina | Materia prima | Refinado básico (XP de maestría) | Fabricación posterior |
|---|---|---|---|
| Minería | Mena + combustible | Lingote, en el **horno** | Herrería: herramientas, herrajes, armas y armaduras; Joyería: monturas |
| Tala | Troncos | Tablones, en el **aserradero** | Carpintería: cañas, muebles, arcos, bastones, armazones |
| Herboristería | Plantas, fibras | Fibra limpia y hierbas preparadas, en la **mesa de preparación** | Alquimia: fórmulas; Sastrería: hilo y tela |
| Desuello | Pieles | Cuero preparado, en el **secadero** | Peletería: correas, fundas y armaduras ligeras |
| Rastreo | Señales | No produce refinado | Localiza presas; el combate y el desuello dan los recursos |
| Pesca (afición) | Capturas | No necesita refinado | Cocina: platos y raciones |

Las cuatro estaciones de refinado están en el Gremio, abiertas a cualquiera: refinar no ocupa plaza de oficio. Hilar y tejer son Sastrería; formular pociones es Alquimia; forjar herrajes es Herrería. No se traslada toda la producción de un oficio a una maestría.

Una sola etapa de refinado antes del producto cuando basta. Las hierbas frescas pueden seguir entrando directamente en recetas fijas; el carbón es combustible y no se funde.

### 4.2 Dos ramas por disciplina

Las ramas están acordadas; estos nombres y efectos son propuesta de contenido para la fase 7.

| Disciplina | Rama A | Rama B | Límite |
|---|---|---|---|
| Minería | Extracción: más recurso común | Prospección: favorece los raros disponibles | No crea gemas ausentes ni ignora el rango |
| Tala | Producción: más madera común | Selección forestal: madera especial y resinas | Que B no gane en volumen y en valor a la vez |
| Herboristería | Cosecha abundante | Botánica selectiva | Comparar utilidad y suministro real |
| Desuello | Aprovechamiento: más cuero común | Extracción cuidadosa: componentes especiales | Solo lo que la criatura tiene |
| Rastreo | Rastro seguro: presa común más fiable | Rastro selectivo: especie o ejemplar especial | No garantiza jefes infinitos ni bloquea misiones |
| Pesca | Pesca abundante | Pesca selectiva | Catálogo por lugar y rango |

Una especialización activa por disciplina, y las disciplinas no comparten plaza: se puede especializar Minería y Tala a la vez. Al cambiar se conserva la elección anterior y su progreso; las ramas pausadas no suman efectos.

Primera versión: rango compartido de la disciplina y estados aprendido / activo / pausado. Sin segunda barra de XP y sin árbol (N02).

Flujo del cambio: mostrar rama actual, nueva, efectos y coste → confirmar → bloquear y revalidar → cobrar una vez → activar y pausar → informar. No se cobra por volver a pulsar la rama activa, y el cambio se rechaza con una actividad en curso.

### 4.3 Rastreo experimental

Un panel con la familia de presa y el peligro aproximado, con las especies elegibles de esa zona, hora y condiciones. Las señales llevan a un encuentro del motor; Gemini no inventa ni concede presas. El desuello sigue siendo otra actividad. Se mide la elección real frente a Cazar, el tiempo hasta una presa objetivo y el uso de las dos ramas. Si resulta una espera redundante, se evalúa convertirlo en afición o integrarlo en Cazar, conservando XP y logros (N01).

## 5. Herramientas y probabilidades

### 5.1 Diseños fijos especializados

Cada herramienta especializada tiene su propia receta fija. Lo que queda fuera es elegir componentes o afijos al fabricar.

| Herramienta | Fabricante | Base autónoma | Mejorada colaborativa |
|---|---|---|---|
| Caña | Carpintería | Materiales de maestrías | Sedal de Sastrería |
| Pico | Herrería | Metal refinado y materiales comunes | Mango preparado por Carpintería |
| Hacha | Herrería | Ídem | Mango de Carpintería |
| Hoz | Herrería | Ídem | Mango o empuñadura de otro oficio |
| Cuchillo de desollar | Herrería | Ídem | Empuñadura de Peletería o Carpintería |

Tres diseños T1: rápido, selectivo y productivo, con los valores semilla de la sección 1. No se declaran equilibrados: es posible que +5 % relativo sea demasiado pequeño; se mantiene la semántica y se ajusta la magnitud tras medir.

Se selecciona una herramienta por disciplina; tener tres no suma sus efectos. El servidor valida pertenencia y compatibilidad, y la herramienta queda fijada al iniciar la actividad.

No hay durabilidad, roturas ni mantenimiento (N06).

### 5.2 Semántica inequívoca

Con una probabilidad base del 10 %:

- **+5 % relativo:** `0,10 × 1,05 = 0,105` → 10,5 %.
- **+5 puntos porcentuales:** `0,10 + 0,05 = 0,15` → 15 %.
- Se usa la primera para los bonos de raro. La ayuda muestra base y resultado, no solo «+5 %».
- Tiempo: `duración_base × (1 − reducción)`; cinco minutos con −10 % son 270 segundos. Redondeo y duración mínima únicos y configurables.
- Unidad extra: una oportunidad por actividad completa, nunca por unidad ni por notificación. Máximo una unidad, sin XP adicional.

### 5.3 Adaptación de las tablas actuales

La tabla vigente sortea cada unidad por peso. Multiplicar el peso de los raros por 1,05 y normalizar no equivale a subir un 5 % relativo la probabilidad de raro de la actividad.

**Propuesta técnica:** definir un hallazgo raro por actividad. Separar comunes y raros elegibles; calcular la probabilidad de hallazgo raro de la actividad; aplicar el multiplicador relativo; si tiene éxito, sustituir una unidad base por un raro de la tabla. Mantiene la cantidad y hace comprensible el porcentaje. Sin raros elegibles, probabilidad cero y aviso claro. Las expediciones pueden tener otra base, pero una sola evaluación del bono de herramienta.

Antes de adoptarla se compara la distribución con la del sistema anterior, para no mover economía ni misiones en silencio. El bono de rango heredado no cambia: se auditan juntos rango, rama y herramienta, sumando mejoras relativas compatibles dentro de una categoría, aplicándolas una vez y limitando la probabilidad a 1. No mezclar puntos porcentuales y multiplicadores en el mismo campo.

En la actividad se guarda: modo, tabla (instantánea reproducible), rango, especialización, herramienta, modificadores, tiempos y semilla. Un reinicio o un cambio de catálogo no recalcula un premio ya iniciado con otras reglas.

## 6. Ocho profesiones y dos aficiones

### 6.1 Identidad y catálogo de arranque

Los objetos siguientes son candidatos concretos, no un inventario aprobado.

| Oficio | Bucle propio repetible | Productos T0 candidatos | Productos T1 candidatos | Aporte a otros |
|---|---|---|---|---|
| Herrería | Herramientas, componentes y equipo | Herrajes, pico, hacha, hoz, cuchillo, arma y armadura básicas | Herramientas especializadas, equipo superior | Bisagras, cierres, carcasas |
| Alquimia | Consumibles de aventura | Curación, maná, preparado sencillo | Consumibles mejores o situacionales | Reactivo, aceite o resina |
| Carpintería | Componentes, equipo y mobiliario | Mangos, caña, bastón, mejora de cofre | Cañas especializadas, muebles y mejoras T1 | Armazones y mangos |
| Peletería | Correas, equipo de campo y armaduras | Correas, funda, armadura ligera | Equipo reforzado y forros | Correas y empuñaduras |
| Joyería | Monturas y piezas especiales | Engaste, joya decorativa | Accesorio útil | Engastes para otros oficios |
| Escribanía | Pergaminos consumibles | Tinta, pergamino, pergaminos actuales | Pergaminos del tramo alto | Inscripción prevista en receta fija |
| Ingeniería | Consumibles y mecanismos | Mechas, pólvora, bombas básicas | Dispositivos y bombas superiores | Cerraduras y mecanismos |
| Sastrería | Hilo, tela y prendas | Hilo, tela, prenda acolchada, sedal | Tejidos y prendas mejores, sedal avanzado | Componentes textiles de herramientas y muebles |

Cada oficio debe tener al menos una receta útil repetible sin necesitar otro oficio, y un producto colaborativo con consumidor identificado. No se promete demanda infinita: los encargos estructurados quedan en N10.

### 6.2 Sastrería y recursos

Se usan Herboristería para las fibras vegetales y Desuello para los materiales animales: no hace falta una maestría nueva. Primera cadena: fibra común (T0) y fibra fina (T1) → fibra limpia (maestría) → hilo y tela (Sastrería) → prenda, sedal o componente. Sin cargar el lanzamiento con algodón, lino, lana y seda a la vez.

Peletería trabaja cuero y resistencia; Sastrería trabaja tejidos y prendas. Si las dos hacen bolsas, se les dan funciones o costes distintos. Vendas, estandartes y accesorios quedan como candidatos: no se aprueban curaciones nuevas ni ranuras nuevas por omisión.

### 6.3 Aficiones

- **Pesca:** progreso por actividad, sin plaza, cañas de Carpintería y dos ramas a rango 2. Su catálogo tiene capturas que Cocina usa de verdad.
- **Cocina:** recetas comunes por rango y especiales por aventura o plano; consumo útil fuera de combate con las reglas de efectos actuales. La especialización Chef y la producción extra siguen experimentales (N03).
- No se añade hambre obligatoria ni se obliga a pescar a todo cocinero.

### 6.4 Interdependencia sin bloqueo

Ejemplos: caña T1 = piezas de Carpintería + sedal de Sastrería; coraza = lingotes + correas de Peletería; cofre reforzado = armazón de Carpintería + bisagras de Herrería.

Mientras el juego es individual, el **maestro de cada oficio vende los componentes de su oficio** a precio revisado. En 0.11 los jugadores pueden competir con ese suministro. Nadie necesita una segunda cuenta, cambiar de oficio continuamente ni esperar al único artesano conectado.

Se comprueba el grafo completo: ninguna receta básica depende de otro oficio sin alternativa, ningún ciclo exige fabricar primero su propio ingrediente y todo componente tiene procedencia accesible.

## 7. Recetas, técnicas y planos

### 7.1 Aprendizaje

- El **maestro de cada puesto** enseña su oficio y explica sus técnicas. Las recetas comunes nuevas se aprenden automáticamente al alcanzar el rango.
- Una **técnica** agrupa varias recetas comunes. Desbloquearla no exige comprar cada receta ni hacer un encargo.
- Las **recetas especiales** son individuales y se obtienen por aventura; un **plano** es el objeto comerciable que permite aprenderlas.
- Aprender un plano gasta ese ejemplar una vez y conserva el conocimiento. Si ya se conoce, no se gasta: se puede guardar para venderlo.
- El conocimiento no permite fabricar sin oficio activo, rango y estación. Se puede guardar un plano hasta cumplir los requisitos.
- Al cambiar de oficio se conservan XP, técnicas y recetas aprendidas.
- Por personaje, no por cuenta.

### 7.2 Diseños fijos

Cada receta tiene ingredientes y productos exactos. No hay afijos, material alternativo libre ni calidad aleatoria en este alcance. Las cañas rápida, selectiva y productiva son tres diseños fijos, no un constructor modular. La futura experimentación no habilita a Gemini a inventar efectos (N07, N08).

### 7.3 Datos y presentación

Ficha de receta: nombre ES/EN, disciplina, tier, rango, técnica o plano, estación y dónde está, ingredientes con `tengo/necesito` y el origen de los que faltan, cantidad producida, XP y para qué sirve.

Filtros: «Puedo fabricar», «Faltan materiales», «Por aprender» y T0/T1. La ficha explica cómo aprender una receta bloqueada y no revela contenido secreto sin su pista.

Fabricación por lotes: 1, 5 o el máximo permitido, con tope de servidor y coste total antes de confirmar. No produce una parte y pierde el resto. La resolución sigue siendo inmediata: no se añaden temporizadores de fabricación.

### 7.4 Autonomía y equipo excepcional

Las recetas esenciales de un oficio no dependen de un plano aleatorio. Para una pieza excepcional: materiales comunes trabajados + componente de aventura + receta especial. Hay que evitar que la mejor opción de todas las clases exija una sola profesión; las bombas y los pergaminos se comparan con las habilidades de clase, no solo por su coste.

## 8. El Gremio, la calle de los oficios y la habitación

### 8.1 Gremio de Aventureros

Institución PNJ (distinta de los gremios de jugadores de 0.11), en un lugar nuevo junto a la plaza de Crownreach. Reúne:

- **Vale** y el alistamiento: ahí empieza el tutorial y ahí se reciben las misiones.
- **Refinado**: horno, aserradero, mesa de preparación y secadero, abiertos a cualquiera.
- Un **fogón** para la Cocina (la taberna conserva el suyo).
- **Especializaciones** de maestría y de Pesca.
- **Mi habitación**: cama y cofre.

Panel: `[🔨 Refinar] [🌿 Especializaciones] [🏠 Mi habitación] [💬 Hablar]`. «Encargos» no aparece hasta que exista esa expansión.

### 8.2 La calle de los oficios, un puesto por oficio

`crownreach_workshops` conserva su id y su nombre (Barrio de Oficios / Craftsmen's Row) y pasa a ser la calle: de ella cuelgan ocho puestos, cada uno un lugar del mapa con su estación, su maestro y su descripción de día y de noche.

| Puesto | Estación | Oficio |
|---|---|---|
| Forja de Tessa | anvil | Herrería |
| Botica del alquimista | alchemy_table | Alquimia |
| Taller del carpintero | carpenter_bench | Carpintería |
| Curtiduría | tannery | Peletería |
| Banco del joyero | jeweler_bench | Joyería |
| Escritorio del escriba | scribe_desk | Escribanía |
| Taller del ingeniero | workbench | Ingeniería |
| Telar | loom | Sastrería |

Cada oficio **se aprende y se cambia en su puesto**, con su maestro, no con un botón genérico en la calle. El mapa muestra los puestos sangrados bajo la calle para que la ciudad no sea una lista interminable. Los logros de ciudad y exploración ya publicados no cambian de condición.

### 8.3 La misión de la habitación

Entra en el tutorial, después de «Hierro para la Guardia»:

1. Vale ofrece un cuarto en el Gremio a quien se lo gane.
2. El jugador consigue madera talando y la asierra en el Gremio (XP de Tala).
3. Monta el **cofre** con sus tablones.
4. El Gremio entrega la **tela**, una sola vez, y repone si se pierde mientras la cama no esté montada.
5. Monta la **cama**; desde entonces hay descanso gratis y almacenamiento.

Las dos recetas de iniciación son excepciones limitadas a esa misión: no obligan a aprender Carpintería ni Sastrería y no abren la puerta a fabricar muebles profesionales. La tela es material de misión no vendible. Quien ya terminó el tutorial recibe la misión igual, sin acelerón y sin duplicar recompensas.

### 8.4 Descanso y almacenamiento

- **Cama**: descanso sin coste de oro, con las mismas reglas de recuperación, estados y duración. Gratis no significa instantáneo fuera de la beta, y no se puede descansar en combate ni durante una actividad incompatible.
- **Cofre**: inventario personal persistente, con depositar y retirar atómicos y capacidad por espacios. Conserva identidad, `crafted_by` y propiedades de los objetos no apilables, y no mezcla objetos con efectos distintos.
- **Ampliación**: consume una mejora fabricada por Carpintería y sube la capacidad una vez, mostrando el antes y el después. El carpintero fabrica la suya; los demás la compran al maestro carpintero.
- Sin alquiler, deterioro ni borrado por ausencia. La sede comunitaria futura (N12) no es requisito de la habitación.

## 9. Contratos técnicos y datos

### 9.1 Evolución mínima del modelo

| Área | Cambio | Ubicación |
|---|---|---|
| Recetas | Disciplina de acceso y destino de XP, estación por receta, técnica/plano, receta de misión | `content/schemas.py`, `loader.py`, `content/recipes.yaml` |
| Conocimiento | Técnicas y recetas aprendidas, con migración de las comunes ya accesibles | `database/models.py`, migración, `services/professions.py` |
| Especialización | Una activa por disciplina, aprendidas y pausadas | `Character.crafting` |
| Herramientas | Perfil tipado de efectos, disciplina, requisito de rango, selección por disciplina | `Item.tool`, inventario, `engine/gathering.py` |
| Actividad | Instantánea de reglas y modificadores; premio resuelto persistido | `WorldActivity.result`, `services/activities.py` |
| Habitación | Acceso, cama instalada, nivel del cofre y contenido almacenado | `Character.home`, `ItemInstance.container` |
| Planos | Relación objeto → receta, con consumo y aprendizaje atómicos | `Item.teaches`, `services/crafting.py` |
| Equipo por tier | Requisito de nivel para equipar, separado del rango de fabricación | `Item.min_level`, `services/inventory.py` |

El campo `Tier` que ya existe para las pruebas d20 **no se reutiliza** para T0/T1: son cosas distintas. Se separan la disciplina de acceso y la disciplina que recibe la XP, para que una receta de misión no eluda las reglas profesionales por tener XP cero. Los ids de objeto existentes se conservan mientras signifiquen lo mismo.

### 9.2 Operación de fabricar y refinar

Entrada: personaje autenticado, id de receta, cantidad acotada y nonce. El cliente no envía costes ni resultados.

Secuencia: bloquear → comprobar estado y nonce → revalidar conocimiento, rango y estación → comprobar materiales y capacidad → consumir → producir → conceder la XP correspondiente → actualizar desbloqueos, misión y logro → registrar → commit → mostrar o narrar.

Un fallo revierte todo. Repetir el mismo nonce no produce de nuevo. Nunca se llama a Gemini ni a Telegram con un lock abierto. Toda escritura vive en `oathforge/services/`; `engine/` calcula sin BD y con azar inyectable.

### 9.3 Migración sin perder progreso

- Se conserva la XP de oficios y maestrías. No se duplica históricamente la XP de fundición en Minería.
- Las recetas de refinado se reclasifican para las acciones futuras; no se reconvierten objetos ya guardados ni se vuelve a premiar.
- Se conceden las técnicas comunes que correspondan al rango ya alcanzado: un personaje migrado y uno nuevo llegan al mismo acceso.
- Siguen dos profesiones activas y las aficiones libres. Sastrería no ocupa plaza automáticamente.
- Quien ya tiene rango 2+ puede elegir rama; no se elige por él.
- Las actividades antiguas en curso se resuelven con las reglas heredadas: sin instantánea, el comportamiento es el de hoy. No se inventan instantáneas retrospectivas.
- Las habitaciones empiezan bloqueadas salvo evidencia de la misión; sin recompensas duplicadas.
- La migración se ejecuta sobre una copia y se comparan oro, cantidades, objetos, XP, misiones y logros.

### 9.4 Telegram e IA

Paneles paginados y botones con ids breves y nonce, dentro del límite de 64 bytes del `callback_data`. Se reutilizan `render` y `keyboards`. Todo en ES y EN, con los mismos marcadores.

Gemini interpreta peticiones libres y narra hechos ya resueltos: no decide planos, precios, XP, rareza ni calidad. Fabricar y refinar funcionan con plantillas, sin llamada obligatoria; la crónica es opcional para los hitos y dentro del presupuesto vigente.

## 10. Interfaz y comandos

Referencias de [facies.md](facies.md): Chat Wars (teclado corto, comandos clicables en el texto, duración en el propio botón) y AshWars (ingredientes con `tengo/necesito`, línea de «te falta», coste visible aunque la receta esté bloqueada, selector de origen de materiales 🎒/📦).

- **🛠️ Oficios** sigue siendo la puerta: pestañas de oficios, maestrías y aficiones, más la ficha de cada uno.
- **Fabricar** muestra los ingredientes con `tengo/necesito`, el icono de cada material, la línea de lo que falta y botones ×1 · ×5 · máx con el coste total. El botón de fabricar solo aparece con los materiales completos; cuando falta algo, se ve el coste y de dónde sale.
- **Selector de origen** 🎒 Mochila / 📦 Cofre en el panel de fabricación, cuando haya cofre.
- Comandos nuevos, en inglés y sin alias:
  - `/recipes`: lista paginada con los filtros Puedo fabricar · Faltan · Por aprender · T0 · T1.
  - `/r_<id>`: la ficha de una receta.
  - `/craft_<id> [n]`: fabricar escribiendo; sin cantidad abre la ficha.
  - `/guild`: el panel del Gremio.
  - `/room`: la habitación.
  - `/stash`: el cofre, con `/stash_<objeto> n` y `/take_<objeto> n`.
- Cada puesto de la calle enseña en su escena el oficio que se aprende allí y su maestro, igual que la taberna enseña su fogón.

## 11. Fases de entrega

Cada fase es un parche 0.10.x con una experiencia comprobable, su CHANGELOG, su entrada en `planning/iter.md` y las casillas de F15 marcadas. Las referencias `ART-*` del plan original se agrupan aquí.

| Fase | Versión | Qué entrega | Cubre |
|---|---|---|---|
| 0 | 0.10.9 | Este documento y las fichas de planning | ART-001..005 |
| 1 | 0.10.10 | Contrato de recetas: estación por receta, disciplina de XP, tier por rango, receta de misión, plano, `min_level` y lotes | ART-010..014 |
| 2 | 0.10.11 | Gremio de Aventureros, calle con ocho puestos, ocho maestros, Tessa en la Forja, Vale en el Gremio y tutorial adaptado | ART-020 |
| 3 | 0.10.12 | Refinado de maestrías (horno, aserradero, secadero, mesa), lotes en la interfaz y `/recipes`, `/r_<id>`, `/craft_<id>` | ART-021..025 |
| 4 | 0.10.13 | Sastrería, técnicas por rango, planos y catálogo T0 autónomo de los ocho oficios | ART-030..035 |
| 5 | 0.10.14 | Habitación en el tutorial: cama, descanso gratis, cofre, mejoras y `/room`, `/stash` | ART-060..064 |
| 6 | 0.10.15 | Instantánea de reglas al iniciar una actividad y hallazgo raro por actividad | ART-052, pendiente de F08 |
| 7 | 0.10.16 | Dos ramas por maestría y Pesca a rango 2, cambio con oro y piloto de Rastreo | ART-040..044 |
| 8 | 0.10.17 | Herramientas especializadas con perfil tipado, una por disciplina, y la ayuda de porcentajes | ART-050..055 |
| 9 | 0.10.18 | Catálogo T1: materiales de rango 3–5, equipo con requisito de nivel y precios revisados | ART-070..073 |
| 10 | 0.10.19 | Cierre: `tests/features.md`, partida ES/EN con `tgtest`, simulación y estados de planning | ART-080..082 |

Lo que queda fuera y por qué: encargos con custodia y transferencia de planos entre jugadores son 0.11 (ART-083); la construcción de sedes de gremio, también (ART-084, N12). La artesanía individual no espera a que existan sedes compartidas.

## 12. Pruebas y criterios de salida

### 12.1 Escenarios obligatorios

| Área | Caso y resultado esperado |
|---|---|
| Acceso | Dos profesiones; maestrías y aficiones sin plaza; Sastrería sí ocupa plaza |
| Independencia | Un personaje de nivel bajo fabrica T1 con rango y materiales, y no equipa equipo de combate T1 sin nivel |
| Refinado | Fundir y aserrar dan XP de maestría, nunca de oficio |
| Conocimiento | El rango desbloquea la técnica; cambiar de oficio conserva el conocimiento; un plano repetido no se pierde |
| Especialización | Rango 1 rechazado y rango 2 permitido; el oro se cobra una vez; pausar y reactivar conserva el estado |
| Probabilidades | Casos base 0 y 1, sin raros elegibles, +5 % relativo y extra por actividad |
| Persistencia | Reiniciar el bot o reintentar la resolución conserva el premio; una actualización de catálogo no cambia una actividad iniciada |
| Inventario | Un lote sin materiales o sin espacio no consume nada; depositar y retirar en paralelo no duplica |
| Habitación | Misión única; los materiales se recuperan sin explotación; el descanso gratis no ignora combate ni heridas |
| Economía | No hay ciclo positivo comprando componentes al maestro y revendiéndolos |
| Experiencia | Las dos ramas tienen uso; T0 sigue siendo útil; las recetas básicas no obligan a otro oficio |
| Idioma | Todos los textos en ES y EN con los mismos marcadores |

Pruebas puras para las fórmulas, de servicio para permisos y atomicidad y PostgreSQL real para la concurrencia: doble clic, callbacks viejos, consumo simultáneo y aprendizaje concurrente del mismo plano. Simulaciones con semilla y márgenes estadísticos, no pruebas frágiles que exijan un número exacto de raros.

### 12.2 Puerta de salida de F15

- [ ] Ocho oficios con dos plazas, dos aficiones y cinco maestrías, con Rastreo marcado experimental.
- [ ] Refinado accesible sin oficio y con la XP correcta.
- [ ] Dos ramas por maestría y Pesca a rango 2, con cambio en el Gremio y sin pérdida.
- [ ] Herramientas especializadas y fórmulas por actividad verificadas.
- [ ] Técnicas comunes automáticas y planos persistentes.
- [ ] Cada oficio con productos útiles autónomos y colaboración accesible en solitario.
- [ ] Habitación inicial, cama gratuita y cofre ampliable con Carpintería.
- [ ] La migración conserva el progreso: sin duplicados ni pérdidas.
- [ ] El catálogo T1 está publicado y su equipo de combate dice con claridad que pide nivel 10.
- [ ] Los comentarios experimentales y las notas de decisiones futuras están donde corresponde.

## 13. Documentación y trazabilidad

### 13.1 Archivos que cambian

| Documento | Contenido |
|---|---|
| Este archivo | Contrato principal de F15 |
| [roadmap.md](roadmap.md) F15 | Casillas por fase y enlace aquí |
| [opificia.md](opificia.md) | Estado actual, maestrías y refinado, ocho oficios, ramas, herramientas y recetas |
| [mundus.md](mundus.md) | Gremio, calle con puestos, misión de la habitación y recursos |
| [mercatura.md](mercatura.md) | Componentes de los maestros, planos, cofre y comercio futuro |
| [facies.md](facies.md) | Paneles, comandos y navegación |
| [progressio.md](progressio.md) | Independencia artesanal; la curva de XP queda pendiente |
| [societas.md](societas.md) | Sedes comunitarias futuras |
| [Possibilium.md](Possibilium.md) §§15–18 y 24 | Estados de las ideas; lo futuro sigue futuro |
| [iter.md](iter.md), `CHANGELOG.md` | Alcance y versión de cada fase |
| `content/rulebook.yaml` y locales ES/EN | Reglas visibles: porcentajes, tiers, herramientas, refinado y habitación |
| `tests/features.md` | Recorridos jugables y regresiones |

### 13.2 Relación con ideas existentes

| Referencia previa | Tratamiento |
|---|---|
| `MIN-01..04` | El piloto se reduce a dos ramas; el resto sigue futuro |
| `MAS-01..07` | Herramientas y especialización en alcance; cuadernos, árboles y durabilidad en notas |
| `RECETA-01..07` | Tiers, aprendizaje y lotes en alcance; variantes, experimentación y reciclaje futuros |
| `OFI-01` | Sastrería promovida a decisión de alcance |
| `EQU-07` | El cofre personal se implementa como parte de la habitación, antes del banco comunitario |
| `ECO-01` / `RECETA-06` | Suministro accesible y preparación del comercio; custodia multijugador posterior |
| `ECO-05` | Encargos PNJ como nota (N10) |
| TODO: oficios, portabilidad, afinidades, tiers | Panel unificado y ramas en alcance; portabilidad pendiente; T0/T1 sustituyen a T1–T3 |

## 14. Fuentes e investigación

Las decisiones de Josue prevalecen sobre los referentes externos. La investigación aporta patrones; no demuestra que los porcentajes propuestos estén equilibrados.

- La fuente primaria del estado es el código: `content/professions.yaml`, `content/recipes.yaml`, `oathforge/content/schemas.py`, `oathforge/services/crafting.py`, `oathforge/services/professions.py`, `oathforge/engine/gathering.py`, `oathforge/services/activities.py`, `oathforge/database/models.py` y `content/world/terra_coronata/crownreach/`.
- [Blizzard, *Dragonflight: Making It with Professions*](https://news.blizzard.com/en-us/article/23876529/dragonflight-making-it-with-professions): especializaciones, pedidos y la distinción entre calidad y rareza. Se aprovecha la identidad artesanal y los componentes compartidos; no se copian árboles permanentes ni varias calidades.
- [Guild Wars 2 Wiki: *Recipe*](https://wiki.guildwars2.com/wiki/Recipe) y [*Recipe sheet*](https://wiki-en.guildwars2.com/wiki/Recipe_sheet): separar el conocimiento del producto. No se importa el descubrimiento por mezcla ni el desbloqueo por cuenta.
- [PostgreSQL: *Explicit Locking*](https://www.postgresql.org/docs/current/explicit-locking.html): inventario, aprendizaje y ampliación en transacciones cortas y con orden consistente. Los locks no sustituyen las claves de idempotencia.
- [Telegram Bot API: *InlineKeyboardButton*](https://core.telegram.org/bots/api#inlinekeyboardbutton): identificadores breves, resolución en el servidor y paneles paginados.
- Chat Wars (`@chtwrsbot`) y AshWars (`@AshWarsBot`), partidas de prueba del 18-10-2026: ver [facies.md](facies.md).

## 15. Notas finales: experimentos, balance y futuro

Estas notas quedan tal como se recogieron, al final y sin recortar, para analizarlas y moverlas donde corresponda. **No son tareas aprobadas**: lo único aprobado es documentarlas y preparar la compatibilidad. Los comentarios sugeridos se añaden al código al implementar su módulo; este archivo no afirma que ya estén allí.

### N01 — Rastreo: conservar, convertir en afición o eliminar

**Decisión:** probar como maestría. **Evaluación:** utilidad frente a Cazar, decisiones de presa, satisfacción y redundancia con Supervivencia. Si se reclasifica, preservar XP, conocimiento y logros o definir una compensación explícita.

Comentario sugerido junto a la definición y la resolución de Rastreo:

```python
# DESIGN-N01: Tracking is an experimental mastery. Evaluate keeping it,
# moving it to hobbies, or merging it into hunting. Preserve progress on migration.
```

### N02 — Árbol de especialización futuro

**Ahora:** dos ramas, una activa por disciplina, rango 2, cambio con oro y pausa. **Después:** valorar un árbol con puntos, varias ramas y técnicas, solo si las elecciones iniciales ofrecen diferencias reales. No confundir el progreso general con una barra de rama que aún no existe.

```python
# DESIGN-N02: Start with two switchable branches. Evaluate a skill tree later;
# inactive branches must retain their learned state and any future progress.
```

### N03 — Especializaciones de Cocina a probar

**Chef:** mayor calidad, que modifica uno o varios efectos previstos del plato. **Aprovechamiento:** probabilidad de una ración adicional. No habilitar sin comparar coste, potencia, duración y valor económico. No aumentar todas las estadísticas de todos los platos por defecto.

Definir el alcance del proc en lotes: la regla por actividad aprobada para la recolección no resuelve automáticamente la fabricación. Propuesta a probar: una oportunidad por ejecución elemental de receta, de modo que fabricar cinco en lote equivalga a cinco individuales y no se explote el tamaño del lote. Aclarar las recetas que ya producen varias raciones.

```python
# DESIGN-N03: Cooking quality vs extra-serving branches are experimental.
# Test effect limits, output economics and batch-size invariance before enabling.
```

### N04 — Herramienta acumulativa

**Ahora:** diseños especializados con una ventaja principal. **Futuro:** evaluar una herramienta que combine velocidad, raro y rendimiento. Riesgo: reemplazar todas las elecciones previas. Podría reservarse a contenido excepcional, pero esa solución no está aprobada.

```python
# DESIGN-N04: Tools use fixed specialized designs. Consider cumulative bonuses
# later only if they do not invalidate same-tier choices.
```

### N05 — Porcentaje relativo y puntos porcentuales

**Decisión registrada:** raro relativo; extra por actividad completa. En el reglamento ES/EN incluir 10 % → 10,5 % con +5 % relativo frente a 10 % → 15 % con +5 puntos. Explicar la probabilidad final real, especialmente si la base cambia por lugar o modo. Ajustar la magnitud sin cambiar la semántica en silencio.

```python
# DESIGN-N05: Rare bonuses are relative multipliers, not percentage points.
# Tool extra-output is rolled once per completed field activity, not per item.
```

### N06 — Durabilidad y piedra de afilar

**Ahora:** herramientas sin desgaste. **Futuro:** desgaste solo si aporta decisiones y no un mantenimiento rutinario molesto. La piedra de afilar puede ser un producto recurrente, pero primero hay que definir si restaura durabilidad o concede un beneficio temporal; ninguno de esos efectos está aprobado. No publicar objetos sin utilidad real ni activar desgaste retroactivo sin avisar.

### N07 — Variantes de recetas y componentes

**Ahora:** recetas exactas. **Futuro:** base más variante prevista, sustituciones de ingredientes y, eventualmente, componentes. Distinguirlo de los diseños fijos de cañas ya acordados. Evaluar la claridad del menú, la explosión de inventario y la trazabilidad de las propiedades.

### N08 — Experimentación en Cocina y Alquimia

Idea futura: combinaciones de ingredientes previstas por el motor que descubren recetas. Nunca una IA adjudicando efectos. Definir el coste de experimentar, la protección ante pérdidas y cómo evitar el bloqueo de recetas esenciales. Puede probarse en un catálogo pequeño antes de extenderlo.

### N09 — Proyectos personales artesanales

Idea futura bien delimitada: la historia breve de un instructor o PNJ que propone una obra significativa, por ejemplo equipar una expedición, reparar un mecanismo o amueblar una sala. Fases con materiales, montaje y entrega; recompensa útil o cosmética y técnica especial opcional.

No sustituye los desbloqueos comunes por rango. Puede enseñar una técnica especial o dar contexto a una ya aprendida. Propuesta: un proyecto por hito importante, no una misión por receta. La misión de la habitación sí está en alcance y es independiente de este sistema general.

### N10 — Encargos repetibles de PNJ y de jugadores

Idea futura: entregas cortas de herramientas, comida, suministros o muebles. Los PNJ tienen demanda limitada; el pago y los materiales se validan en el servidor. Medir la creación de oro y evitar el circuito infinito vender-comprar-refabricar.

En multijugador: el cliente deposita materiales y comisión, el artesano acepta una vez y la entrega o cancelación va con custodia y auditoría. No convertir la aceptación en envío automático de mensajes no solicitados. Preparar un diseño aparte cuando exista economía compartida. No depender de estos encargos para conceder las recetas comunes del sistema inicial.

### N11 — XP y ritmo de subida: equilibrar después

**Petición expresa:** conservar como nota de balance. Mantener rangos 0–5; la curva actual es un punto de comparación, no un compromiso nuevo. Revisar la XP de personaje hasta 20, la de maestrías, oficios y aficiones, el refinado, las recetas triviales, las bonificaciones y los tiempos de actividad.

Medir: minutos activos y pasivos hasta rango 2, tiempo hasta el primer producto útil, llegada a T1, coste de subir comprando materiales frente a recolectarlos y efecto de los lotes. El refinado puede enseñar, pero no debe hacer irrelevante toda la recolección. Evitar XP extra por unidades gratuitas y reciclaje infinito. No fijar horas objetivo ni porcentajes definitivos sin pruebas.

La ampliación a 20 necesita una curva antes de publicarse; dejar los números para después no elimina esa tarea. No generar XP de personaje por spam de artesanía sin una decisión específica.

### N12 — Construcción de gremios y ampliación de la vivienda

Carpintería debe tener futuro en sedes, muebles y estructuras. Separar materiales personales de aportes comunitarios; exigir permisos y registro para banco y obras. Sastrería puede aportar textiles, Herrería herrajes e Ingeniería mecanismos. Cantería se valorará solo cuando haya suficiente construcción; por ahora no se añade una maestría nueva.

La habitación inicial se limita a cofre y cama. Decoración, trofeos, talleres privados, bonos de descanso y espacios nuevos se discuten después. No atribuir a la cama inicial bonificaciones superiores al descanso normal.

### N13 — Otras ideas conservadas, sin ampliar el alcance

- Preparación manual o portátil de madera y herramientas portátiles de fabricación: decidir la comodidad y la utilidad del taller antes de introducir dos métodos equivalentes.
- Cuaderno de campo, colecciones de pesca y recetas favoritas: posibles mejoras de interfaz, no necesarias para resolver la economía.
- Cantería y Recuperación como maestrías nuevas: exigen contenido propio y un análisis del reciclaje; Prospección permanece como rama de Minería.
- Ramas de profesión —construcción o arquería en Carpintería, etc.—: distintas de las especializaciones de maestrías; no están aprobadas.
- Vendas, bolsas textiles y ranura de accesorios: resolver con combate e inventario antes de publicar efectos.
- Lotes de refinado y capacidad del cofre: parámetros configurables; confirmar unidades, límites y precios al cerrar el catálogo.
- Cap 20 y límites de tiers: configurables para expansiones; no codificar «T1 es el último para siempre».

**Regla final de mantenimiento:** cada nota que se apruebe pasa a una tarea con reglas, dependencia, prueba y versión. Hasta entonces sigue siendo una nota, no una funcionalidad prometida ni implementada.
