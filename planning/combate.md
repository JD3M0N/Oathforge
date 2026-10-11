# Combate

## Estado actual

Motor puro en `oathforge/engine/combat.py`, persistido como JSON en `encounters.state`.

- Iniciativa d20 + DES. Cada turno: acción, acción adicional y movimiento.
- Filas: vanguardia y retaguardia. El cuerpo a cuerpo solo alcanza la retaguardia enemiga si la vanguardia está vacía; disparar desde la vanguardia con enemigos delante da desventaja.
- Críticos (20 natural; 19–20 con Crítico Mejorado), ventaja/desventaja, ataque furtivo.
- Estados: sangrado, quemadura, envenenado, asustado, aturdido, vulnerable, oculto, defendiendo y bendecido.
- Objetos del escenario (empujar un carro, tirar una lámpara) con prueba de habilidad.
- Huir: Atletismo o Acrobacias contra 10 + 2 por enemigo.
- **v0.2.0, tipos de daño y criaturas**: los monstruos tienen tipo (humanoide, bestia, no-muerto), resistencias (½ daño), vulnerabilidades (×2) e inmunidades. El panel avisa «¡débil!» o «resiste». Los esqueletos sufren el doble con contundente y radiante y resisten el perforante.
- Enemigos: atacan al jugador con menos PV con su primer ataque válido; los cobardes huyen con ¼ de PV.

## Ideas

- **Tiradas de salvación y CD de conjuro**: base para el Mago y los efectos de área.
- **IA enemiga**: elegir ataque según resistencias del jugador, habilidades propias (curarse, multiataque, pedir refuerzos), cambiar de fila, proteger al jefe.
- **Jefes por fases**: el Guardián de la Cripta cambia de comportamiento a mitad de PV.
- **Descubrir debilidades**: Religión/Arcanos para conocer tipo y resistencias antes de golpear.
- **Simulador de batallas**: `python -m oathforge.tools.simulate` para lanzar cientos de combates clase × enemigo y guardar estadísticas en `artifacts/simulations/`.
- **Descanso corto** que recupere algunas habilidades (Segundo Aliento, Oleada de Acción).
- **Temporizador de turno** (JobQueue) cuando haya grupos.
- Salvaciones contra muerte en vez de derrota inmediata.

## Preguntas abiertas

- ¿Cuánto debe durar un combate normal? Objetivo tentativo: 3–5 rondas. Medirlo con `artifacts/battles/`.
- ¿La derrota debe costar más que oro y el estado «herido»?
- ¿Mostrar siempre los números de la tirada o solo en un modo detallado?
