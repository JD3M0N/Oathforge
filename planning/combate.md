# Combate

## Estado actual

Motor puro en `oathforge/engine/combat.py`, persistido como JSON en `encounters.state`.

- Iniciativa d20 + DES. Cada turno: acción, acción adicional y movimiento.
- Filas: vanguardia y retaguardia. El cuerpo a cuerpo solo alcanza la retaguardia enemiga si la vanguardia está vacía; disparar desde la vanguardia con enemigos delante da desventaja.
- Críticos (20 natural; 19–20 con Crítico Mejorado), ventaja/desventaja, ataque furtivo.
- Estados: sangrado, quemadura, envenenado, asustado, aturdido, vulnerable, oculto, defendiendo y bendecido.
- Objetos del escenario (empujar un carro, tirar una lámpara) con prueba de habilidad.
- Huir: Atletismo o Acrobacias contra 10 + 2 por enemigo.
- **v0.2.0, tipos de daño y criaturas**: los monstruos tienen tipo (humanoide, bestia, no-muerto), resistencias (½ daño), vulnerabilidades (×2) e inmunidades. El panel avisa «¡débil!» o «resiste». Los esqueletos sufren el doble con contundente y radiante; el Guardián de la Cripta, con radiante, y resiste necrótico y frío. El daño extra de otro tipo (Golpe Consagrado, Golpe Divino) se aplica aparte para que cuente la debilidad.
- Enemigos: atacan al jugador con menos PV con su primer ataque válido; los cobardes huyen con ¼ de PV.
- **v0.5.0, cripta más fácil**: en la partida del 11/10 hubo 4 muertes en 4 combates en la sala de los juramentos (2 esqueletos contra nivel 1). Esqueleto: 11 PV, +3, 1d6+1. Guardián: 40 PV, +4, 1d8+2 y miedo al 25 %. Descanso gratis en el osario antes del santuario. Con la cadena de misiones se llega a la cripta a nivel 3–4.
- **v0.5.0, botones a prueba de doble clic**: cada botón de combate lleva `<encounter.version>.<turn_index>.<nonce>`; si la versión o el turno ya no coinciden, se vuelve a pintar el panel sin actuar.
- **v0.5.8, panel más legible**: cada combatiente muestra ❤️ PV, barra y 🛡️ CA. Cada acción es un bloque: la línea del ataque (🗡️ acierto, 💥 crítico en negrita, 💨 fallo, con «🎲 14 +5 = 19 vs 🛡️ 13») y, sangradas debajo, sus consecuencias (🩸 daño con los PV que le quedan al objetivo, 💀 cae, salvaciones, estados). Separador «── Ronda N ──»: el motor deja una entrada `combat.round` al empezar cada ronda. El daño guarda `hp` y `max_hp` del objetivo. Los golpes ya no se repiten en el mensaje de viñetas: solo salen en el panel.
- **v0.5.9, informe de batalla**: botón «📜 Informe» en el panel final y `/report` (la última batalla terminada). Página de resumen (resultado, rondas, daño hecho y recibido, aciertos, críticos, curación, derrotados y recompensas) y una página por ronda con todas las tiradas, con el mismo formato que el panel. Se reconstruye desde `combat_actions`: además de una fila por acción del jugador, ahora se guardan la apertura (`actor="start"`: iniciativa y turnos enemigos antes del primero del jugador) y el final (`actor="end"`: XP, oro, botín, subidas de nivel o la penalización por derrota). Sin migración. Las batallas anteriores a v0.5.9 salen incompletas (sin apertura ni recompensas).

- **v0.7.22**: ronda 0 con la iniciativa (cada d20 y su DES); con ventaja o desventaja, los dos d20 y el que cuenta; «📊 Resumen» y «📜 Informe» (todas las rondas seguidas, en varios mensajes si hace falta); botones por clase: los ataques y una habilidad destacada 🌟 (`signature` en `classes.yaml`, la primera disponible) en la primera fila, y «✨ Acciones» con el resto de poderes.

## Ideas

- **Tiradas de salvación y CD de conjuro**: base para el Mago y los efectos de área.
- **IA enemiga**: elegir ataque según resistencias del jugador, habilidades propias (curarse, multiataque, pedir refuerzos), cambiar de fila, proteger al jefe.
- **Jefes por fases**: el Guardián de la Cripta cambia de comportamiento a mitad de PV.
- **Descubrir debilidades**: Religión/Arcanos para conocer tipo y resistencias antes de golpear.
- **Simulador de batallas**: *hecho en v0.5.4* (`oathforge simulate`, ver README). Siguientes pasos: grupos de enemigos por defecto (los de cada zona), políticas alternativas (huir, pociones) y comparar dos versiones del contenido.
- **Descanso corto** que recupere algunas habilidades (Segundo Aliento, Oleada de Acción).
- **Temporizador de turno** (JobQueue) cuando haya grupos.
- Salvaciones contra muerte en vez de derrota inmediata.

### Del GDD

- **Tipos de acción** (§5.3.1). Ya tenemos ataque, habilidad, interacción y huida; faltan:

  | Tipo | Ejemplos | Validación |
  |---|---|---|
  | Defensa | Bloqueo, esquiva preparada, proteger a un aliado | Coste de acción, posición |
  | Apoyo | Curar, inspirar, quitar veneno | Aliado válido, recursos |
  | Social | Intimidar, negociar una tregua, rendirse | Disposición del enemigo, tirada |
  | Retirada | Cubrir la retirada, rendirse | Ruta, amenaza, consecuencias |

- **Cobertura** como tercera posición junto a vanguardia y retaguardia (§5.3): reduce la probabilidad de impacto. Más elementos del escenario: barriles, puertas, puentes, cuerdas (ejemplo de la lámpara sobre los goblins, §5.8).
- **Estados nuevos** (§5.4): ralentizado, derribado, silenciado y concentración. Cada estado con `source`, `duration`, `stacking_rule`, `dispel_type` y momento en que se activa. Evitar bloqueos infinitos: inmunidad temporal tras un control.
- **IA enemiga en tres niveles** (§5.5), sin LLM, con reglas o árboles de comportamiento:
  - *Básica*: ataca lo que alcanza, huye con poca vida, usa una habilidad según el contexto (lo que hay hoy).
  - *Táctica*: protege al sanador, busca cobertura, prioriza amenazas y aprovecha estados.
  - *Jefe*: fases, **avisos previos** del ataque fuerte («el Guardián alza la espada…»), entorno que cambia y objetivos alternativos.
- **Roles de enemigo** (§5.6): tanque, atacante, invocador, sanador y controlador, para que los encuentros premien la cooperación.
- **Botín** (§5.6): botín por jugador como base; los objetos únicos de evento, con reglas anunciadas antes del combate.
- **Anti-duplicado** (§15.5): `encounter.version` + `turn_index` en cada botón para que un callback viejo o un doble clic no ejecute dos ataques en el mismo turno.
- **Repetición de combates** (idea 78): historial de dados y acciones legible por el jugador para entender una derrota. La base ya está en `artifacts/battles/`.
- Críticos, ventaja, desventaja y reacciones con una única especificación y tests; no deben depender de cómo redacte la IA.

## Preguntas abiertas

- ¿Cuánto debe durar un combate normal? Objetivo tentativo: 3–5 rondas. Medirlo con `artifacts/battles/`.
- ¿La derrota debe costar más que oro y el estado «herido»?
- ¿Mostrar siempre los números de la tirada o solo en un modo detallado?
- ¿Añadimos la cobertura como tercera posición o basta con vanguardia y retaguardia?
- ¿Qué enemigo estrena la IA táctica: el capitán bandido (proteger a los suyos) o los esqueletos de la Cripta (rodear al sanador)?
