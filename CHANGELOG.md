# Changelog

Todos los cambios relevantes de Oathforge. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado `0.x.y` (ver `planning/roadmap.md`).

Cada versión corresponde a un commit cuyo asunto es `vX.Y.Z: resumen` y cuyo cuerpo repite esta lista.

## [0.2.2] - 2026-10-11

### Añadido
- **Hoja de héroe**: el botón «🦸 Héroe» y el nuevo comando `/hero` (`/sheet` sigue funcionando) muestran una ficha detallada con barras de PV y XP, atributos en tabla (★ en el principal de la clase), equipo con daño y CA, competencias con su bonificador, habilidades de clase con usos y las de niveles futuros bloqueadas, reputación con etiqueta (hostil, neutral, amistoso…) y rasgo del linaje. Botones directos a Inventario y Diario.
- La hoja muestra las llamadas al Dungeon Master usadas hoy y las que quedan.
- Aviso al jugador cuando agota su presupuesto diario de IA, en acciones libres y en conversaciones.

### Cambiado
- Límite de IA en la fase de testeo: **150 llamadas al día por jugador** (antes 200).

## [0.2.1] - 2026-10-11

### Añadido
- `planning/referencias/` con los documentos de diseño: el GDD *Aetherfall Chronicles* y la guía de recursos audiovisuales (PDF), más un índice que indica en qué archivo de planning se recoge cada capítulo y en qué difieren de lo ya decidido.
- `planning/audiovisual.md`: imágenes, música de taberna, voces de NPC, mapas, stickers, envío por Telegram, catálogo de activos y licencias.
- `planning/interfaz-telegram.md`: escenas, botones, comandos, estados de acción y sesiones.

### Cambiado
- Planning ampliado con ideas del GDD: 12 clases y talentos del Paladín (`clases.md`), tipos de acción, estados e IA enemiga (`combate.md`), proficiencias, equipo y juramentos (`progresion.md`), profesiones, contratos y libro mayor (`comercio.md`), regiones, eventos, misiones, facciones y rumores (`mundo-y-misiones.md`), espacios de Telegram, expediciones y PvP (`multijugador.md`), roles del DM, memoria y control de calidad (`ia-y-narracion.md`) y visión a largo plazo (`roadmap.md`).
- `TODO.md` reorganizado por temas con prioridades y enlaces a planning, con nuevas tareas sacadas de los PDF.

## [0.2.0] - 2026-10-11

### Añadido
- Clase **Guerrero** (d10, FUE, vanguardia): Segundo Aliento, Estilo Defensa, Oleada de Acción (N2), Crítico Mejorado 19–20 (N3), Ataque Extra (N5).
- Clase **Sacerdote** (d8, SAB, retaguardia, lanza con SAB): Llama Sagrada (ataque de conjuro a distancia, ilimitado), Palabra Sanadora, Expulsar No-muertos (N2), Bendición +2 a impactar (N3), Golpe Divino +1d8 radiante (N5).
- Tipos de daño y de criatura: los monstruos tienen `type` (humanoide, bestia, no-muerto), `resist` (½), `vulnerable` (×2) e `immune_damage`. El panel muestra «¡débil!», «resiste» o «inmune».
- Esqueletos vulnerables a contundente y radiante; el Guardián de la Cripta vulnerable a radiante y resistente a necrótico y frío; los no-muertos son inmunes al veneno.
- Nuevos tipos de habilidad en el motor: `spell`, `turn`, `buff`, `surge`; campos `heal_dice`/`heal_add`, `crit_range`, `bonus_damage`; estado `blessed`.
- Objetos: martillo de guerra, maza, hacha de mano (arrojadiza) y cota de escamas; a la venta en la tienda de Tessa.

### Cambiado
- El daño extra de otro tipo (Golpe Consagrado, Golpe Divino) se aplica por separado para que cuenten las resistencias y debilidades.
- Una tirada dentro del rango de crítico siempre impacta.
- Las habilidades ilimitadas ya no muestran «(None)» en el botón.

### Arreglado
- Un enemigo sin ataques ya no rompe el turno enemigo.
- `/help` (v0.1.1): error de sintaxis en el pie de versión que impedía arrancar el bot.

## [0.1.1] - 2026-10-11

### Añadido
- Versionado: `oathforge.__version__` es la única fuente (pyproject la lee); se muestra al arrancar el bot y al pie de `/help`.
- `CHANGELOG.md` y convención de commits `vX.Y.Z: resumen`.
- Carpeta `planning/` con los puntos de partida: clases, combate, comercio, progresión, mundo y misiones, multijugador, IA y roadmap.
- Registro de partidas en `artifacts/` (ignorado por git) para depurar y analizar: conversaciones jugador ↔ bot, eventos en JSONL, combates turno a turno (.md legible + .json), cada llamada a Gemini (prompt, respuesta, modelo, tokens, latencia) y errores. Se controla con `ARTIFACTS_ENABLED` y `ARTIFACTS_DIR`.

## [0.1.0] - 2026-10-10

### Añadido
- Vertical slice en solitario: creación de personaje (4 linajes, 4 trasfondos, Paladín y Pícaro con habilidades hasta nivel 5).
- Crownreach, el Camino del Viejo Rey, el Bosque de los Susurros y la Cripta Hundida (5 salas + jefe).
- Combate por turnos: iniciativa, acción/adicional/movimiento, filas, críticos, ataque furtivo, estados y objetos del escenario.
- Misión ramificada «El relicario sellado», NPC con memoria, reputación con facciones, tiendas con precios por reputación y rumores entre jugadores.
- Gemini como Dungeon Master: interpreta texto libre y narra; el motor decide. Presupuesto diario, plantillas de respaldo y fallback al modelo rápido.
- Español e inglés.
- Flujo de colaboración: ramas por persona y TODO de testers sincronizados a `main`.
