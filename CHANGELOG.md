# Changelog

Todos los cambios relevantes de Oathforge. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado `0.x.y` (ver `planning/roadmap.md`).

Cada versión corresponde a un commit cuyo asunto es `vX.Y.Z: resumen` y cuyo cuerpo repite esta lista.

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
