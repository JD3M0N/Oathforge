# Pugna — combate, derrota y descanso

Resumen de [Possibilium §10–11](Possibilium.md#s10).

## Estado actual (0.8.2)

> **En revisión (0.10-I, desde 0.10.25).** El [contrato](roadmap_balance.md) sustituye los usos por descanso por **una barra propia de cada clase**, con generación, coste y enfriamientos contados en turnos de combate (nunca en segundos reales). Ya en el motor: **Guerrero con Foco** y **Hechicero con Maná** son los pilotos; las otras doce clases siguen con usos hasta B06 y las dos formas conviven. El **ataque básico es gratis y siempre útil**, un estado **se refresca y no se acumula**, y el **control duro no encadena a un jefe**: le dura un turno y el resto lo deja vulnerable, dicho en el registro. **Desde 0.10.28 (B05)** hay aliados que combaten solos —invocaciones, servidor, bestia, constructo, torreta y tótem—, cada uno una vez por turno de su dueño, y formas que sustituyen los ataques sin curar al alternar. Lo que falta de la ficha: los tiempos de descanso y la derrota calibrados (B08) y los contadores de apoyo por rama (B07).


Motor puro en `oathforge/engine/combat.py`, persistido como JSON en `encounters.state`.

- **Ronda 0** con iniciativa (d20 + DES); cada turno: acción, acción adicional y movimiento.
- **Filas**: vanguardia y retaguardia. El cuerpo a cuerpo alcanza la retaguardia solo si la vanguardia está vacía; disparar desde la vanguardia con enemigos delante da desventaja.
- Críticos (20; 19–20 con Crítico Mejorado), ventaja/desventaja con los dos d20 visibles, ataque furtivo, salvaciones DES/SAB, PV temporales.
- **Estados**: sangrado, quemadura, envenenado, asustado, aturdido, vulnerable, oculto, defendiendo, bendecido, dormido, apresado, inspirado, maldito, forma salvaje. Se refrescan, no se acumulan: al repetir uno gana la duración más larga (0.10.25).
- **Tipos de daño y criatura**: resistencias (½), vulnerabilidades (×2) e inmunidades; el daño extra de otro tipo se aplica aparte. El panel avisa «¡débil!» o «resiste».
- Objetos del escenario con prueba; pergaminos y bombas desde «🎒 Objetos»; poción si quedan.
- Huir: Atletismo o Acrobacias contra 10 + 2 por enemigo.
- **Enemigos**: atacan al de menos PV con su primer ataque válido; los cobardes huyen con ¼ de PV.
- **Botones** a prueba de doble clic: `<encounter.version>.<turn_index>.<nonce>`; uno viejo vuelve a pintar el panel.
- Botones por clase: ataques + habilidad 🌟 en la primera fila, «✨ Acciones» con el resto.
- **Panel**: ❤️ PV y barra, 🛡️ CA; bloques por acción (🗡️ acierto, 💥 crítico, 💨 fallo, «🎲 14 +5 = 19 vs 🛡️ 13»); separador por ronda.
- **Informe**: «📊 Resumen» (resultado, daño, aciertos, críticos, curación, recompensas, páginas por ronda) y «📜 Informe» completo; `/report`. Se reconstruye desde `combat_actions` (`actor="start"` y `actor="end"`).
- **Derrota** (tope de 15 de oro por nivel desde 0.10.35): pierdes el 10 % del oro y quedas «herido» (techo del 50 % de PV) hasta descansar o curarte.
- **Descanso** (0.10.35, tiempos en `engine/timings.py`): largo en la posada (5 de oro, 15 min reales; recompensa al terminar, abandonar no da nada); **corto** en cualquier sitio (3 min, gratis, 30 % de PV sin pasar del tope de heridas, parte de la barra; dos entre dos largos); osario de la cripta gratis (se retira en B13); tónico del reposo como descanso corto (enfriamiento 4 h); Ysolde cura por 3 de oro (quien lleva menos paga lo que tenga).
- Simulador: `oath simulate --level 1-5` (200 combates por clase × enemigo × nivel).

## Decidido

- La IA no tira dados ni decide daño; la narración recibe la bitácora resuelta.
- Sin LLM para la IA enemiga.
- Derrota recuperable durante la beta; sin muerte permanente.

## Próximo

- **COM-01..10**: proteger aliado, ayudar, empujar entre filas, cobertura, romper entorno, interrumpir ritual, negociar o rendirse, retirada organizada, reacción preseleccionada, entrenamiento seguro.
- Estados nuevos (ralentizado, derribado, silencio, concentración) con `source`, `duration`, `stacking_rule` y `dispel_type`; inmunidad temporal tras control.
- IA enemiga táctica y jefes por fases con aviso previo; roles de enemigo.
- **REC-01** caído antes que derrotado; **REC-03** descanso corto sin poción; **REC-06** campamento.
- Simulador: grupos por zona, políticas alternativas, composiciones de grupo.

## Preguntas abiertas

- ¿Cuánto dura un combate normal? Objetivo tentativo 3–5 rondas.
- ¿La derrota debe costar más que oro y «herido»?
- ¿Cobertura como tercera posición?
- ¿Qué enemigo estrena la IA táctica: capitán bandido o esqueletos?
- ¿El osario debe tardar como la posada al cerrar la beta?
