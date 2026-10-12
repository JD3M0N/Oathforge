# Changelog

Todos los cambios relevantes de Oathforge. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado `0.x.y` (ver `planning/roadmap.md`).

Cada versión corresponde a un commit cuyo asunto es `vX.Y.Z: resumen` y cuyo cuerpo repite esta lista.

## [0.5.3] - 2026-10-12

### Añadido
- **Test estadístico de los dados** (`tests/engine/test_dice_fairness.py`): chi-cuadrado sobre 200 000 tiradas del d20 (uniforme), de la ventaja y la desventaja (máximo y mínimo de dos d20), de 1d6 y de 2d6; frecuencia de 20 y 1 naturales (≈ 5 %) y medias (10,5 / 13,825 / 7,175). Usa semillas fijas, así que no falla por azar, y una prueba con el RNG real del bot.

## [0.5.2] - 2026-10-12

### Arreglado
- **Ya no se puede repetir la misma tirada hasta que salga.** Una prueba de habilidad libre (escrita) se puede intentar una vez por habilidad y lugar al día de juego (4 h reales). Se desbloquea al día siguiente o al subir de nivel. Si se repite, sale «Ya intentaste {habilidad} aquí hoy».
  - Investigar: cada secreto que se falla queda bloqueado hasta el día siguiente; si todos los pendientes están bloqueados, sale «Ya has registrado este lugar hoy».
  - Con las tiradas manuales activadas, una tirada bloqueada no pide el dado.
  - Prueba de habilidad e interacción con el entorno comparten bloqueo (misma habilidad, mismo lugar).
  - Nueva columna `characters.checks_tried` (migración `0005`); guarda solo los intentos del día actual.

## [0.5.1] - 2026-10-11

### Añadido
- **`/roll` y tiradas manuales**, opcionales por jugador (`users.settings.manual_rolls`).
  - Sin tirada pendiente, `/roll` las activa o desactiva.
  - Con ellas activadas, la prueba de habilidad espera a que el jugador haga `/roll` o pulse «🎲 Tirar el dado». Afecta a investigar, a las acciones de misión con prueba y a las acciones escritas que piden tirada (prueba de habilidad, interacción con el entorno, inspeccionar o acción de misión).
  - Al tirar, sale el dado animado de Telegram y después el resultado del motor: d20 + bonificador contra la CD. El dado de Telegram solo va de 1 a 6, así que es decorativo.
  - El combate no espera a `/roll`.
  - Si el jugador se ha movido antes de tirar, la tirada se anula.
- **Retratos de hombre y de mujer** para las 8 clases: Bardo, Maga y Mago, Druida y Druidesa, Guerrera, Pícara, Sacerdotisa y Paladina. La barda aún no tiene retrato y usa el del bardo. Se quitó la franja inferior con texto falso de la IA.

### Cambiado
- Los retratos neutros de Paladín, Sacerdote, Pícaro y Guerrero eran de hombre: pasan a `portrait.male.jpg`.
- Las pruebas de habilidad se muestran con 🎲 delante.
- Las acciones escritas se separan en interpretar (`handle_free_text`) y resolver (`execute_free_text`), para poder resolverlas después de `/roll`.

## [0.5.0] - 2026-10-11

### Añadido
- **Sistema de misiones**: cadena automática de 6 misiones que lleva a nivel 5 (Bienvenido a Crownreach, Colmillos en el prado, Alas al anochecer, El relicario sellado, Huesos inquietos y El Viejo Colmillo). Al completar una se abre la siguiente (`after` o `unlock_flag`). Los objetivos (matar N, hablar con, ir a) cuentan solos y dan su recompensa. El avance se guarda en `quest_progress.counters` (migración `0004`) y los personajes antiguos reciben las misiones nuevas sin perder su progreso.
- **Diario renovado**: muestra las misiones en curso con su avance y tiene tres secciones. En «📜 Misiones» se toca cada misión para ver quién la da, el resumen, los objetivos (`2/3`), una pista de dónde ir y la recompensa. Las otras dos son «📖 Bestiario» y «🗣️ Rumores». Nuevo comando `/quests`.
- **Prado de los Colmillos**, zona de caza a 20 minutos de la plaza y sin peligro en el camino. Con el botón «🏹 Cazar» salen **jabalíes de día** y **murciélagos de noche** (`night_encounters`, también en las emboscadas). El jefe **Viejo Colmillo** aparece con la misión 6. Botín vendible: colmillos de jabalí y alas de murciélago.
- **Bestiario** (`characters.bestiary`): cuenta las criaturas vistas y derrotadas. Su ficha se desbloquea por partes: al verla, descripción, historia y hábitat; a la primera derrota, PV, CA y ataques; a la tercera, puntos débiles, XP y botín. Los monstruos tienen `lore`, `habitat` y `active` (día o noche).
- **Compra de atributos por puntos** al crear el personaje: todos empiezan en 8 y hay 27 puntos (14→15 cuesta 2), con botones ➖/➕. «⭐ Recomendado» carga el array de la clase y «🔄 Reiniciar» vuelve a empezar. Cada atributo explica para qué sirve (`effect` en `content/abilities.yaml`) y se ve la vida resultante.
- Emojis en XP (✨), oro (🪙), subidas de nivel (🎉) y habilidades nuevas (🌟).

### Cambiado
- **Curva de XP comprimida**: los niveles 2–5 piden 200 / 500 / 1.000 / 1.800 XP (antes 300 / 900 / 2.700 / 6.500).
- **La Cripta Hundida es más fácil**:
  - esqueleto: 11 PV, +3, 1d6+1;
  - Guardián: 40 PV, +4, 1d8+2, miedo al 25 %;
  - descanso gratis en el osario antes del santuario.
- «El relicario sellado» empieza bloqueado hasta completar «Alas al anochecer». Sus finales dan 300 XP y abren la misión del Viejo Colmillo.
- **Botones de combate a prueba de doble clic**: cada botón lleva `<encounter.version>.<turn_index>.<nonce>`. Un botón de un panel viejo o de otro turno ya no actúa: vuelve a pintar el panel.

### Arreglado
- `TimedOut` al subir retratos: el bot tiene ahora timeouts de 30 s, y 60 s para subir fotos. Si una imagen falla por red, se registra un aviso y se sigue con la vista sin mostrar el error genérico.
- Reintentos inútiles a Gemini con la cuota diaria agotada: ante un 429 se respeta el `retryDelay` de Google (si la cuota es diaria, se salta ese modelo hasta que vuelva, como máximo 24 h). Se deja de llamar y de avisar cada 2 minutos.

## [0.4.4] - 2026-10-11

### Añadido
- **Brujo** (d8, CAR, retaguardia): Estallido Sobrenatural (1d10 de fuerza, ilimitado), Maleficio (acción adicional: maldice a un enemigo 3 turnos sin salvación y cada golpe que recibe suma 1d6 necrótico), Armadura de Sombras (2d4 + CAR PV temporales), Susurros del Vacío (salvación de SAB de toda una fila: 2d6 psíquico, la mitad si salva, miedo a quien falla) y Estallido Agónico (+CAR al daño de conjuros). Especializaciones previstas: Pactista Infernal, Nigromante, Filo Maldito y Vacío.
- Habilidades de maldición (`kind: curse`): ponen un estado a un enemigo elegido, sin tirada de salvación; estado `hexed` (🕯️).
- **Hombre o mujer** al crear el personaje (paso nuevo tras el nombre): se guarda en `characters.gender` (migración `0003`), sale en el resumen de creación y en la ficha, y la IA lo recibe para narrar con el género correcto.
- Retratos por sexo: `portrait.male.jpg` / `portrait.female.jpg` en `content/classes/<clase>/images/`; `/sheet` envía el del personaje, o el neutro (`portrait.jpg`) si no hay. Retratos de Brujo y Bruja (768 × 1024).

### Arreglado
- `/sheet` no aparecía en el menú de comandos de Telegram (`MENU_COMMANDS` en `oathforge/main.py`).

## [0.4.3] - 2026-10-11

### Añadido
- **Comandos de consola** `oathforge` (`oathforge/cli.py`, también `python -m oathforge`): `oathforge help` lista los comandos con una descripción breve, `oathforge bot` arranca el bot y `oathforge reset-players [--yes]` borra los jugadores.

### Cambiado
- `scripts/reset_players.py` pasa a ser `oathforge reset-players`.

## [0.4.2] - 2026-10-11

### Añadido
- **Cambios de estado en `artifacts/`**: cada cambio confirmado en la BD (PV, oro, XP, nivel, ubicación, flags, recursos, objetos, habilidades, misiones, relaciones y memorias de PNJ, reputación, rumores y acciones de botón del registro de auditoría) se guarda como diff en `events/` (`kind: state`) y como bloque «⚙️ estado» en la conversación del jugador, venga del camino que venga. Lo revertido no se registra.
- `artifacts/logs/<día>.log`: avisos y errores de cualquier logger (reintentos y JSON inválido de Gemini, presupuesto de IA…), que antes solo salían por consola.
- Evento `boot` al arrancar el bot con versión, commit, modelos y base de datos.
- Las conversaciones registran también stickers, fotos, voz y demás mensajes que no son texto.
- `scripts/reset_players.py`: borra todos los jugadores y sus datos para empezar una ronda de pruebas limpia (sin `--yes` solo muestra qué borraría); conserva `media_files`.

## [0.4.1] - 2026-10-11

### Añadido
- **Retratos de clase** (768 × 1024) para Paladín, Guerrero, Pícaro y Sacerdote en `content/classes/<clase>/images/`, con créditos en `media.yaml`; el catálogo de medios los carga (`class_images`) y rechaza carpetas de clases que no existen.
- **Ficha completa** con `/sheet` y el botón «📜 Ficha completa»: envía el retrato de la clase (si lo hay, con caché de `file_id`) y debajo la ficha con descripción y especialización de la clase, dado de golpe, ataques con bonificador al impacto y daño, conjuros (característica, ataque y CD), percepción pasiva, inmunidades, todas las competencias (● competente, ○ practicada, · sin entrenar), habilidades de clase, reputación, rasgo del linaje y trasfondo, y el uso de IA del día.

### Cambiado
- `/hero` y el botón «🦸 Héroe» muestran ahora un **resumen** (PV, XP, CA, atributos, equipo y habilidades desbloqueadas) con un botón a la ficha completa; `/sheet` deja de ser un alias de `/hero`.
- `services/characters.py`: `spell_stats` e `immunities` calculan la CD de conjuro y las inmunidades en un solo sitio (combate y ficha).
- Ayuda y descripciones de comandos mencionan `/sheet`.

## [0.4.0] - 2026-10-11

### Añadido
- **Mago** (d6, INT): Rayo de Fuego, Armadura de Mago (+3 CA sin armadura), Dormir, Bola de Fuego (toda una fila, mitad si salva), Proyectil Mágico (nunca falla).
- **Druida** (d8, SAB): Látigo de Espinas, Curar Heridas, Enredar (toda una fila), Forma Salvaje (PV temporales), Furia Elemental (+SAB al daño de conjuros).
- **Bardo** (d8, CAR): Burla Cruel, Inspiración Bárdica (+1d6 al próximo ataque), Canción Sanadora, Patrón Hipnótico (toda una fila), Palabras Cortantes.
- **Tiradas de salvación** (DES y SAB) contra la CD de conjuro (8 + competencia + característica); habilidades `save` contra un objetivo o contra toda su fila.
- Estados `asleep` (pierde el turno, despierta al recibir daño), `restrained` (ventaja contra él, desventaja en sus ataques), `inspired` y `wild_shape`.
- **PV temporales**: absorben el daño primero y se ven en el panel de combate como `(+N)`.
- Tipos de daño `force` (fuerza) y `psychic` (psíquico).
- Objetos: bastón y estoque (tienda de Tessa).

### Cambiado
- Los monstruos usan su modificador de SAB para las salvaciones.
- Las habilidades `save` piden objetivo a distancia como los conjuros.

## [0.3.0] - 2026-10-11

### Añadido
- **Mundo en carpetas**: `content/world/<continente>/<zona>/<lugar>/place.yaml`, con `world.yaml`, `continent.yaml` y `zone.yaml` (zona = ciudad, territorio salvaje o mazmorra). Primer continente: **Terra Coronata**, con Crownreach, Thornwood y la Cripta Hundida.
- **Catálogo de imágenes** por convención: cada carpeta puede tener `images/` (el sufijo `.night` marca la variante nocturna) y un `media.yaml` opcional con créditos y licencia (`oathforge/content/media.py`).
- **Caché de `file_id` de Telegram** por bot y checksum (tabla `media_files`, migración `0002`, `services/media.py`): cada imagen se sube una sola vez y se vuelve a subir sola si cambia el archivo.
- Botón **«🏙️ Ver ciudad»** en la plaza de Crownreach (lugar `hub`), solo si la ciudad tiene imágenes: envía la panorámica con su descripción de día o de noche y vuelve a mostrar la escena.
- Panorámica de Crownreach (1280 × 720).
- `tools/prepare_image.py` (Pillow, extra `dev`): recorta, escala y optimiza imágenes a la escala del juego.

### Cambiado
- `content/locations.yaml` se reparte en la nueva estructura; los ids de lugar no cambian.

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
