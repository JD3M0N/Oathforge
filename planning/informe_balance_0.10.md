# Informe de balance de la serie 0.10-I (B12)

> Generado con `oath balance --n 32 --seed 7` sobre la versión **0.10.40** (el commit base de las tablas es el que sigue a `db38079`: se generó con los cambios de esta versión aún sin confirmar). Es reproducible: mismo comando, mismas semillas, mismos números. Las tablas completas están al final; aquí van las conclusiones, lo que se cambió por los datos y lo que queda sin resolver. Los umbrales («suelos») son semillas de este informe, no promesas del juego (roadmap §15.3).

## Conclusiones

1. **Las señales de los jefes se recompensan, pero sólo donde duelen.** Responder (defenderse al aviso, beber pociones, guardar el recurso para la ventana expuesta) sube las victorias contra el Ciervo de Hierro +9 puntos de media y +15 en clases frágiles contra el Recaudador (Clérigo 58 → 73 %); contra el Custodio, +3,5. En el centinela del taller y para el promedio de las 14 clases contra el Recaudador la diferencia es nula: las clases con buena defensa pueden ignorar las señales. Es un hallazgo de diseño, no un defecto que se cure con números.
2. **Los lanzadores son la cola del reparto.** De los 52 defectos que encuentra el informe, 35 son parejas del mismo nivel (sobre todo Pirómano, Criomante, Arcanista, Tormentista, Elementalista, Luz, Tejemareas y Chamán) y a nivel 20 sólo cuatro ramas quedan por debajo del suelo contra el Custodio: Luz, Pirómano, Tirador y Tejemareas (16–22 % frente al 35 %). Pierden casi cuatro veces más vida por ronda que un Vengador. No se ha tocado su diseño en esta fase; sólo se ha medido y documentado.
3. **El rol no duplica la duración.** Rondas medias en combates estándar y de élite: DMG 7,4 · curación 8,8 · control 9,1 · defensa 9,6. Defensa tarda un 30 % más que daño, no el doble (objetivo del roadmap §15.3).
4. **Hueco de contenido entre los niveles 6 y 10.** Sólo existían criaturas hasta 40 PV: un héroe de nivel 9 las aplastaba sin gastar nada. Se añadieron tres (sabueso de ceniza, cobrador del peaje y sargento del peaje) en el Puesto de Peaje Abandonado.
5. **El ritmo es el problema grande.** En el modelo, la campaña dirigida (tutorial, campaña y valle) se recorre en **≈ 6 horas de juego activo, unos 2,4 días a dos sesiones** de 75 minutos, frente a los 5–10 días de iniciación y 15–20 acumulados al nivel 20 que pide el roadmap. La XP de las misiones por sí sola lleva al nivel 18 y a la puerta del nivel 10 con menos de 900 de XP de diferencia. No se ha inventado contenido para cubrir el hueco: faltan misiones secundarias, contratos repetibles y actividades de veterano (B11 dejó 11 de las 18–24 misiones previstas). Hay que decidir si se amplía el contenido, se alargan los tiempos o se baja la meta.
6. **Nivel 1 frente a un lobo gris (élite).** Hechicero 16 %, Druida 19 %, Chamán 47 %, Clérigo 50 % de victorias; el Guerrero, 91 %. Es un combate opcional, no un cuello de botella del tutorial, pero confirma que los lanzadores empiezan frágiles.

## Qué se cambió por los datos

- **Simulador** (`oath simulate`): política *básica* frente a *informada*, kit T1 (una pieza de nivel 10), pociones mayores desde el nivel 10, secuencias de combates con descansos cortos y herencia de vida y recurso.
- **Nueva herramienta** `oath balance`: matriz de clases y ramas, intervalos de Wilson, jefes con y sin política, secuencias, duración por rol, defectos con suelos y modelo de ritmo; escribe un informe con versión, commit y semilla.
- **Criaturas**: tres nuevas para los niveles 6–9; el Custodio de las Balizas baja de 230 a 200 PV y de daño (por ganar 0 % las ramas de lanzador); el Recaudador de Ceniza sube su descarga (4d6+5) para que ignorar la señal duela.
- **XP de las misiones del valle** a un 70 %: dejaban casi todo el camino al nivel 20 sin cazar; así la caza cubre una quinta parte del camino al 20.
- Las ayudas de beta (tiempos, atajos, precios) ya se habían retirado en B08.

## Lo que queda sin resolver (honestamente)

- Luz, Pirómano, Tirador y Tejemareas a nivel 20 no alcanzan el suelo del 35 % contra el Custodio con la política informada, y 35 parejas quedan por debajo del 55 %; el problema es de la clase (defensa y daño sostenido), no de un número del jefe.
- El **ritmo** (punto 5) es un modelo con tiempos supuestos y sin datos de jugadores; debe contrastarse con sesiones reales (`oath tutorial-stats` y `tgtest`).
- No hay barrido de las 164 configuraciones 13×17 ni de las estrategias de uso conservador y explosivo de recursos; sí hay política básica e informada.
- Sin infraestructura medida (concurrencia con PostgreSQL, reintentos): las pruebas de integridad de §15.4 siguen siendo las de la suite.
- El coste y la latencia de IA por sesión no se mide en este informe.

## Datos del informe generado · Oathforge 0.10.40

- Commit de código: `db38079` · versión de contenido: 0.10.40 · generado 2026-10-25 17:08
- Semilla base: 7 · combates por celda: 32 (intervalo de Wilson al 95 % entre corchetes)
- Linaje humano, trasfondo soldado, entrenamientos y modificadores por defecto (`simulate.default_choices`).
- Política **básica**: prioridades fijas, ignora avisos y pociones. **Informada**: se defiende cuando el jefe apunta y bebe pociones por debajo del 40 % de vida.
- Equipo: **T0** = el inicial de la clase. **T1** = además la pieza de nivel 10 que presta el gremio (niveles ≥ 10).

## Clases base · niveles 1, 3, 5 y 9 (política informada, equipo T0)

| Nivel | Clase | weak | standard | elite | pair | boss |
|---|---|---|---|---|---|---|
| 1 | warrior | 100 [89–100] | 100 [89–100] | 91 [76–97] | 100 [89–100] | — |
| 1 | barbarian | 100 [89–100] | 100 [89–100] | 72 [55–84] | 100 [89–100] | — |
| 1 | paladin | 100 [89–100] | 100 [89–100] | 75 [58–87] | 100 [89–100] | — |
| 1 | rogue | 100 [89–100] | 100 [89–100] | 59 [42–74] | 100 [89–100] | — |
| 1 | monk | 100 [89–100] | 100 [89–100] | 78 [61–89] | 94 [80–98] | — |
| 1 | cleric | 100 [89–100] | 100 [89–100] | 50 [34–66] | 97 [84–99] | — |
| 1 | sorcerer | 100 [89–100] | 97 [84–99] | 16 [7–32] | 69 [51–82] | — |
| 1 | druid | 100 [89–100] | 100 [89–100] | 19 [9–35] | 72 [55–84] | — |
| 1 | bard | 100 [89–100] | 100 [89–100] | 50 [34–66] | 88 [72–95] | — |
| 1 | warlock | 100 [89–100] | 100 [89–100] | 62 [45–77] | 91 [76–97] | — |
| 1 | ranger | 100 [89–100] | 100 [89–100] | 81 [65–91] | 97 [84–99] | — |
| 1 | artificer | 100 [89–100] | 100 [89–100] | 59 [42–74] | 97 [84–99] | — |
| 1 | shaman | 100 [89–100] | 100 [89–100] | 47 [31–64] | 97 [84–99] | — |
| 1 | death_knight | 100 [89–100] | 100 [89–100] | 78 [61–89] | 100 [89–100] | — |
| 3 | warrior | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | — |
| 3 | barbarian | 100 [89–100] | 97 [84–99] | 94 [80–98] | 100 [89–100] | — |
| 3 | paladin | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | — |
| 3 | rogue | 100 [89–100] | 100 [89–100] | 97 [84–99] | 100 [89–100] | — |
| 3 | monk | 100 [89–100] | 100 [89–100] | 97 [84–99] | 100 [89–100] | — |
| 3 | cleric | 100 [89–100] | 88 [72–95] | 81 [65–91] | 91 [76–97] | — |
| 3 | sorcerer | 100 [89–100] | 88 [72–95] | 62 [45–77] | 81 [65–91] | — |
| 3 | druid | 100 [89–100] | 78 [61–89] | 59 [42–74] | 88 [72–95] | — |
| 3 | bard | 100 [89–100] | 56 [39–72] | 69 [51–82] | 97 [84–99] | — |
| 3 | warlock | 100 [89–100] | 88 [72–95] | 66 [48–80] | 81 [65–91] | — |
| 3 | ranger | 100 [89–100] | 100 [89–100] | 88 [72–95] | 100 [89–100] | — |
| 3 | artificer | 100 [89–100] | 97 [84–99] | 100 [89–100] | 97 [84–99] | — |
| 3 | shaman | 100 [89–100] | 78 [61–89] | 56 [39–72] | 88 [72–95] | — |
| 3 | death_knight | 100 [89–100] | 97 [84–99] | 100 [89–100] | 97 [84–99] | — |
| 5 | warrior | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | barbarian | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | paladin | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | rogue | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | monk | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | cleric | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | sorcerer | 100 [89–100] | 91 [76–97] | 100 [89–100] | 94 [80–98] | 100 [89–100] |
| 5 | druid | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | bard | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | warlock | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | ranger | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | artificer | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 5 | shaman | 100 [89–100] | 97 [84–99] | 100 [89–100] | 94 [80–98] | 100 [89–100] |
| 5 | death_knight | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 9 | warrior | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 9 | barbarian | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 9 | paladin | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 9 | rogue | 100 [89–100] | 100 [89–100] | 100 [89–100] | 97 [84–99] | 100 [89–100] |
| 9 | monk | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] |
| 9 | cleric | 100 [89–100] | 100 [89–100] | 78 [61–89] | 88 [72–95] | 75 [58–87] |
| 9 | sorcerer | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 78 [61–89] |
| 9 | druid | 100 [89–100] | 100 [89–100] | 84 [68–93] | 81 [65–91] | 88 [72–95] |
| 9 | bard | 100 [89–100] | 100 [89–100] | 100 [89–100] | 75 [58–87] | 100 [89–100] |
| 9 | warlock | 100 [89–100] | 97 [84–99] | 94 [80–98] | 72 [55–84] | 88 [72–95] |
| 9 | ranger | 100 [89–100] | 100 [89–100] | 100 [89–100] | 100 [89–100] | 97 [84–99] |
| 9 | artificer | 100 [89–100] | 100 [89–100] | 100 [89–100] | 97 [84–99] | 100 [89–100] |
| 9 | shaman | 100 [89–100] | 97 [84–99] | 50 [34–66] | 47 [31–64] | 28 [16–45] |
| 9 | death_knight | 100 [89–100] | 100 [89–100] | 100 [89–100] | 94 [80–98] | 97 [84–99] |

## Ramas · niveles 10, 13, 17 y 20 (política informada, equipo T1)

| Nivel | Rama | Rol | weak | standard | elite | pair | boss |
|---|---|---|---|---|---|---|---|
| 10 | avenger | dmg | 100 | 100 | 100 | 97 | 100 |
| 10 | sacred_warden | deff | 100 | 100 | 100 | 100 | 100 |
| 10 | redeemer | heal | 100 | 100 | 97 | 91 | 100 |
| 10 | inquisitor | control | 100 | 100 | 97 | 94 | 100 |
| 10 | battle_master | dmg | 100 | 100 | 100 | 100 | 100 |
| 10 | bulwark | deff | 100 | 100 | 100 | 100 | 100 |
| 10 | berserker | dmg | 100 | 100 | 100 | 91 | 100 |
| 10 | colossus | deff | 100 | 100 | 100 | 100 | 100 |
| 10 | assassin | dmg | 100 | 100 | 100 | 72 | 100 |
| 10 | duelist | dmg | 100 | 100 | 100 | 97 | 100 |
| 10 | saboteur | control | 100 | 100 | 100 | 78 | 100 |
| 10 | life_domain | heal | 97 | 100 | 72 | 22 | 81 |
| 10 | light_domain | dmg | 100 | 100 | 84 | 22 | 84 |
| 10 | war_domain | dmg | 100 | 100 | 91 | 69 | 94 |
| 10 | pyromancer | dmg | 100 | 100 | 78 | 9 | 75 |
| 10 | cryomancer | control | 100 | 100 | 84 | 12 | 84 |
| 10 | arcanist | dmg | 100 | 100 | 84 | 12 | 88 |
| 10 | stormcaller | dmg | 100 | 100 | 100 | 44 | 97 |
| 10 | summoner | dmg | 100 | 100 | 97 | 22 | 100 |
| 10 | chronomancer | control | 100 | 100 | 97 | 28 | 94 |
| 10 | shapeshifter | dmg | 100 | 100 | 94 | 66 | 100 |
| 10 | grove_warden | deff | 100 | 100 | 97 | 47 | 97 |
| 10 | circle_of_spores | dmg | 100 | 100 | 100 | 84 | 100 |
| 10 | war_chanter | dmg | 100 | 100 | 100 | 59 | 100 |
| 10 | illusionist | control | 100 | 100 | 100 | 94 | 100 |
| 10 | demonologist | dmg | 100 | 100 | 100 | 97 | 100 |
| 10 | hexblade | dmg | 100 | 100 | 100 | 47 | 97 |
| 10 | necromancer | dmg | 100 | 100 | 100 | 50 | 100 |
| 10 | sharpshooter | dmg | 100 | 100 | 97 | 75 | 100 |
| 10 | beastmaster | dmg | 100 | 100 | 100 | 88 | 100 |
| 10 | iron_fist | dmg | 100 | 100 | 100 | 91 | 100 |
| 10 | shadow_dancer | deff | 100 | 100 | 100 | 100 | 100 |
| 10 | runic_armorer | deff | 100 | 100 | 100 | 88 | 100 |
| 10 | artillerist | dmg | 100 | 100 | 100 | 94 | 100 |
| 10 | catalyst | heal | 100 | 100 | 100 | 62 | 100 |
| 10 | construct_master | deff | 100 | 100 | 100 | 100 | 100 |
| 10 | elementalist | dmg | 100 | 100 | 100 | 47 | 100 |
| 10 | ancestral_guardian | deff | 100 | 100 | 100 | 97 | 100 |
| 10 | tideweaver | heal | 100 | 100 | 84 | 25 | 100 |
| 10 | blood | deff | 100 | 100 | 100 | 94 | 100 |
| 10 | frost | dmg | 100 | 100 | 100 | 75 | 100 |
| 13 | avenger | dmg | 100 | 100 | 100 | 100 | — |
| 13 | sacred_warden | deff | 100 | 100 | 100 | 100 | — |
| 13 | redeemer | heal | 100 | 100 | 100 | 94 | — |
| 13 | inquisitor | control | 100 | 100 | 100 | 94 | — |
| 13 | battle_master | dmg | 100 | 100 | 100 | 94 | — |
| 13 | bulwark | deff | 100 | 100 | 100 | 100 | — |
| 13 | berserker | dmg | 100 | 100 | 100 | 94 | — |
| 13 | colossus | deff | 100 | 100 | 100 | 100 | — |
| 13 | assassin | dmg | 100 | 100 | 100 | 81 | — |
| 13 | duelist | dmg | 100 | 100 | 100 | 100 | — |
| 13 | saboteur | control | 100 | 100 | 100 | 75 | — |
| 13 | life_domain | heal | 100 | 100 | 97 | 50 | — |
| 13 | light_domain | dmg | 100 | 100 | 97 | 44 | — |
| 13 | war_domain | dmg | 100 | 97 | 97 | 72 | — |
| 13 | pyromancer | dmg | 100 | 100 | 100 | 22 | — |
| 13 | cryomancer | control | 100 | 100 | 100 | 22 | — |
| 13 | arcanist | dmg | 100 | 100 | 100 | 34 | — |
| 13 | stormcaller | dmg | 100 | 100 | 100 | 28 | — |
| 13 | summoner | dmg | 100 | 100 | 100 | 59 | — |
| 13 | chronomancer | control | 100 | 100 | 100 | 41 | — |
| 13 | shapeshifter | dmg | 100 | 100 | 100 | 66 | — |
| 13 | grove_warden | deff | 100 | 100 | 100 | 50 | — |
| 13 | circle_of_spores | dmg | 100 | 100 | 100 | 84 | — |
| 13 | war_chanter | dmg | 100 | 100 | 100 | 47 | — |
| 13 | illusionist | control | 100 | 100 | 100 | 100 | — |
| 13 | demonologist | dmg | 100 | 100 | 100 | 97 | — |
| 13 | hexblade | dmg | 100 | 100 | 97 | 59 | — |
| 13 | necromancer | dmg | 100 | 100 | 100 | 56 | — |
| 13 | sharpshooter | dmg | 100 | 100 | 100 | 19 | — |
| 13 | beastmaster | dmg | 100 | 100 | 100 | 88 | — |
| 13 | iron_fist | dmg | 100 | 100 | 100 | 97 | — |
| 13 | shadow_dancer | deff | 100 | 100 | 100 | 100 | — |
| 13 | runic_armorer | deff | 100 | 100 | 100 | 97 | — |
| 13 | artillerist | dmg | 100 | 100 | 100 | 100 | — |
| 13 | catalyst | heal | 100 | 100 | 100 | 53 | — |
| 13 | construct_master | deff | 100 | 100 | 100 | 81 | — |
| 13 | elementalist | dmg | 100 | 100 | 100 | 47 | — |
| 13 | ancestral_guardian | deff | 100 | 100 | 100 | 97 | — |
| 13 | tideweaver | heal | 100 | 100 | 100 | 38 | — |
| 13 | blood | deff | 100 | 100 | 100 | 94 | — |
| 13 | frost | dmg | 100 | 100 | 100 | 47 | — |
| 17 | avenger | dmg | 100 | 100 | 100 | 100 | 100 |
| 17 | sacred_warden | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | redeemer | heal | 100 | 100 | 100 | 94 | 100 |
| 17 | inquisitor | control | 100 | 100 | 100 | 97 | 100 |
| 17 | battle_master | dmg | 100 | 100 | 100 | 100 | 100 |
| 17 | bulwark | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | berserker | dmg | 100 | 100 | 100 | 84 | 100 |
| 17 | colossus | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | assassin | dmg | 100 | 100 | 100 | 75 | 100 |
| 17 | duelist | dmg | 100 | 100 | 100 | 91 | 100 |
| 17 | saboteur | control | 100 | 100 | 100 | 56 | 100 |
| 17 | life_domain | heal | 100 | 100 | 100 | 91 | 100 |
| 17 | light_domain | dmg | 100 | 100 | 100 | 59 | 88 |
| 17 | war_domain | dmg | 100 | 100 | 100 | 72 | 100 |
| 17 | pyromancer | dmg | 100 | 100 | 100 | 22 | 88 |
| 17 | cryomancer | control | 100 | 100 | 100 | 47 | 94 |
| 17 | arcanist | dmg | 100 | 100 | 100 | 75 | 88 |
| 17 | stormcaller | dmg | 100 | 100 | 100 | 38 | 97 |
| 17 | summoner | dmg | 100 | 100 | 100 | 59 | 100 |
| 17 | chronomancer | control | 100 | 100 | 100 | 97 | 100 |
| 17 | shapeshifter | dmg | 100 | 100 | 100 | 78 | 100 |
| 17 | grove_warden | deff | 100 | 100 | 100 | 97 | 100 |
| 17 | circle_of_spores | dmg | 100 | 100 | 100 | 91 | 100 |
| 17 | war_chanter | dmg | 100 | 100 | 100 | 56 | 100 |
| 17 | illusionist | control | 100 | 100 | 100 | 97 | 100 |
| 17 | demonologist | dmg | 100 | 100 | 100 | 100 | 100 |
| 17 | hexblade | dmg | 100 | 100 | 100 | 75 | 84 |
| 17 | necromancer | dmg | 100 | 100 | 100 | 91 | 100 |
| 17 | sharpshooter | dmg | 100 | 100 | 100 | 28 | 88 |
| 17 | beastmaster | dmg | 100 | 100 | 100 | 84 | 100 |
| 17 | iron_fist | dmg | 100 | 100 | 100 | 100 | 100 |
| 17 | shadow_dancer | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | runic_armorer | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | artillerist | dmg | 100 | 100 | 100 | 94 | 100 |
| 17 | catalyst | heal | 100 | 100 | 100 | 50 | 100 |
| 17 | construct_master | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | elementalist | dmg | 100 | 100 | 100 | 50 | 94 |
| 17 | ancestral_guardian | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | tideweaver | heal | 100 | 100 | 97 | 66 | 84 |
| 17 | blood | deff | 100 | 100 | 100 | 100 | 100 |
| 17 | frost | dmg | 100 | 100 | 97 | 69 | 100 |
| 20 | avenger | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | sacred_warden | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | redeemer | heal | 100 | 100 | 100 | 97 | 100 |
| 20 | inquisitor | control | 100 | 100 | 100 | 100 | 100 |
| 20 | battle_master | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | bulwark | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | berserker | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | colossus | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | assassin | dmg | 100 | 100 | 100 | 91 | 97 |
| 20 | duelist | dmg | 100 | 100 | 100 | 97 | 100 |
| 20 | saboteur | control | 100 | 100 | 100 | 94 | 91 |
| 20 | life_domain | heal | 100 | 100 | 100 | 100 | 100 |
| 20 | light_domain | dmg | 100 | 100 | 100 | 81 | 19 |
| 20 | war_domain | dmg | 100 | 100 | 100 | 100 | 44 |
| 20 | pyromancer | dmg | 100 | 100 | 97 | 81 | 22 |
| 20 | cryomancer | control | 100 | 100 | 100 | 97 | 50 |
| 20 | arcanist | dmg | 100 | 100 | 97 | 59 | 38 |
| 20 | stormcaller | dmg | 100 | 100 | 100 | 94 | 44 |
| 20 | summoner | dmg | 100 | 100 | 100 | 100 | 69 |
| 20 | chronomancer | control | 100 | 100 | 100 | 97 | 100 |
| 20 | shapeshifter | dmg | 100 | 100 | 100 | 100 | 84 |
| 20 | grove_warden | deff | 100 | 100 | 100 | 100 | 91 |
| 20 | circle_of_spores | dmg | 100 | 100 | 100 | 100 | 88 |
| 20 | war_chanter | dmg | 100 | 100 | 100 | 81 | 100 |
| 20 | illusionist | control | 100 | 100 | 100 | 100 | 100 |
| 20 | demonologist | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | hexblade | dmg | 100 | 100 | 94 | 84 | 66 |
| 20 | necromancer | dmg | 100 | 100 | 100 | 97 | 84 |
| 20 | sharpshooter | dmg | 100 | 100 | 100 | 84 | 16 |
| 20 | beastmaster | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | iron_fist | dmg | 100 | 100 | 100 | 100 | 100 |
| 20 | shadow_dancer | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | runic_armorer | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | artillerist | dmg | 100 | 100 | 100 | 97 | 97 |
| 20 | catalyst | heal | 100 | 100 | 100 | 97 | 100 |
| 20 | construct_master | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | elementalist | dmg | 100 | 100 | 100 | 100 | 66 |
| 20 | ancestral_guardian | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | tideweaver | heal | 100 | 100 | 97 | 81 | 19 |
| 20 | blood | deff | 100 | 100 | 100 | 100 | 100 |
| 20 | frost | dmg | 100 | 100 | 100 | 94 | 94 |

## Qué aporta responder a las señales (jefes: informada + T1 frente a básica + T0)

| Jefe | Nivel | Básica T0 | Informada T1 | Mejora (puntos) |
|---|---|---|---|---|
| ash_collector | 9 | 90.0 | 89.3 | -0.7 |
| iron_stag | 10 | 88.2 | 97.3 | +9.1 |
| regulator_sentinel | 17 | 98.0 | 97.6 | -0.4 |
| beacon_keeper | 20 | 78.8 | 82.3 | +3.5 |

## Secuencias de combates (estándar, élite, estándar y jefe; dos descansos cortos entre ellos)

| Nivel | Rama | Rol | Superan toda la secuencia |
|---|---|---|---|
| 10 | life_domain | heal | 0 % [0–19] (16) |
| 10 | light_domain | dmg | 0 % [0–19] (16) |
| 10 | pyromancer | dmg | 0 % [0–19] (16) |
| 10 | cryomancer | control | 6 % [1–28] (16) |
| 10 | arcanist | dmg | 6 % [1–28] (16) |
| 10 | summoner | dmg | 6 % [1–28] (16) |
| 10 | chronomancer | control | 6 % [1–28] (16) |
| 10 | tideweaver | heal | 6 % [1–28] (16) |
| 10 | grove_warden | deff | 12 % [4–36] (16) |
| 10 | hexblade | dmg | 12 % [4–36] (16) |
| 10 | stormcaller | dmg | 19 % [7–43] (16) |
| 10 | war_domain | dmg | 25 % [10–50] (16) |
| 10 | necromancer | dmg | 31 % [14–56] (16) |
| 10 | shapeshifter | dmg | 38 % [18–61] (16) |
| 10 | elementalist | dmg | 44 % [23–67] (16) |
| 10 | sharpshooter | dmg | 50 % [28–72] (16) |
| 10 | catalyst | heal | 75 % [50–90] (16) |
| 10 | ancestral_guardian | deff | 75 % [50–90] (16) |
| 10 | demonologist | dmg | 81 % [57–93] (16) |
| 10 | circle_of_spores | dmg | 88 % [64–96] (16) |
| 10 | beastmaster | dmg | 88 % [64–96] (16) |
| 10 | construct_master | deff | 88 % [64–96] (16) |
| 10 | berserker | dmg | 94 % [72–99] (16) |
| 10 | runic_armorer | deff | 94 % [72–99] (16) |
| 10 | artillerist | dmg | 94 % [72–99] (16) |
| 10 | frost | dmg | 94 % [72–99] (16) |
| 10 | avenger | dmg | 100 % [81–100] (16) |
| 10 | sacred_warden | deff | 100 % [81–100] (16) |
| 10 | redeemer | heal | 100 % [81–100] (16) |
| 10 | inquisitor | control | 100 % [81–100] (16) |
| 10 | battle_master | dmg | 100 % [81–100] (16) |
| 10 | bulwark | deff | 100 % [81–100] (16) |
| 10 | colossus | deff | 100 % [81–100] (16) |
| 10 | assassin | dmg | 100 % [81–100] (16) |
| 10 | duelist | dmg | 100 % [81–100] (16) |
| 10 | saboteur | control | 100 % [81–100] (16) |
| 10 | war_chanter | dmg | 100 % [81–100] (16) |
| 10 | illusionist | control | 100 % [81–100] (16) |
| 10 | iron_fist | dmg | 100 % [81–100] (16) |
| 10 | shadow_dancer | deff | 100 % [81–100] (16) |
| 10 | blood | deff | 100 % [81–100] (16) |
| 13 | pyromancer | dmg | 56 % [33–77] (16) |
| 13 | light_domain | dmg | 62 % [39–82] (16) |
| 13 | tideweaver | heal | 62 % [39–82] (16) |
| 13 | life_domain | heal | 75 % [50–90] (16) |
| 13 | summoner | dmg | 75 % [50–90] (16) |
| 13 | chronomancer | control | 75 % [50–90] (16) |
| 13 | shapeshifter | dmg | 75 % [50–90] (16) |
| 13 | grove_warden | deff | 75 % [50–90] (16) |
| 13 | cryomancer | control | 81 % [57–93] (16) |
| 13 | arcanist | dmg | 81 % [57–93] (16) |
| 13 | elementalist | dmg | 81 % [57–93] (16) |
| 13 | stormcaller | dmg | 88 % [64–96] (16) |
| 13 | sharpshooter | dmg | 88 % [64–96] (16) |
| 13 | beastmaster | dmg | 88 % [64–96] (16) |
| 13 | berserker | dmg | 94 % [72–99] (16) |
| 13 | war_domain | dmg | 94 % [72–99] (16) |
| 13 | hexblade | dmg | 94 % [72–99] (16) |
| 13 | avenger | dmg | 100 % [81–100] (16) |
| 13 | sacred_warden | deff | 100 % [81–100] (16) |
| 13 | redeemer | heal | 100 % [81–100] (16) |
| 13 | inquisitor | control | 100 % [81–100] (16) |
| 13 | battle_master | dmg | 100 % [81–100] (16) |
| 13 | bulwark | deff | 100 % [81–100] (16) |
| 13 | colossus | deff | 100 % [81–100] (16) |
| 13 | assassin | dmg | 100 % [81–100] (16) |
| 13 | duelist | dmg | 100 % [81–100] (16) |
| 13 | saboteur | control | 100 % [81–100] (16) |
| 13 | circle_of_spores | dmg | 100 % [81–100] (16) |
| 13 | war_chanter | dmg | 100 % [81–100] (16) |
| 13 | illusionist | control | 100 % [81–100] (16) |
| 13 | demonologist | dmg | 100 % [81–100] (16) |
| 13 | necromancer | dmg | 100 % [81–100] (16) |
| 13 | iron_fist | dmg | 100 % [81–100] (16) |
| 13 | shadow_dancer | deff | 100 % [81–100] (16) |
| 13 | runic_armorer | deff | 100 % [81–100] (16) |
| 13 | artillerist | dmg | 100 % [81–100] (16) |
| 13 | catalyst | heal | 100 % [81–100] (16) |
| 13 | construct_master | deff | 100 % [81–100] (16) |
| 13 | ancestral_guardian | deff | 100 % [81–100] (16) |
| 13 | blood | deff | 100 % [81–100] (16) |
| 13 | frost | dmg | 100 % [81–100] (16) |
| 17 | pyromancer | dmg | 6 % [1–28] (16) |
| 17 | cryomancer | control | 19 % [7–43] (16) |
| 17 | arcanist | dmg | 25 % [10–50] (16) |
| 17 | light_domain | dmg | 31 % [14–56] (16) |
| 17 | sharpshooter | dmg | 38 % [18–61] (16) |
| 17 | elementalist | dmg | 38 % [18–61] (16) |
| 17 | stormcaller | dmg | 44 % [23–67] (16) |
| 17 | hexblade | dmg | 44 % [23–67] (16) |
| 17 | tideweaver | heal | 44 % [23–67] (16) |
| 17 | summoner | dmg | 50 % [28–72] (16) |
| 17 | shapeshifter | dmg | 56 % [33–77] (16) |
| 17 | war_domain | dmg | 75 % [50–90] (16) |
| 17 | grove_warden | deff | 81 % [57–93] (16) |
| 17 | circle_of_spores | dmg | 81 % [57–93] (16) |
| 17 | necromancer | dmg | 88 % [64–96] (16) |
| 17 | artillerist | dmg | 88 % [64–96] (16) |
| 17 | catalyst | heal | 88 % [64–96] (16) |
| 17 | berserker | dmg | 94 % [72–99] (16) |
| 17 | beastmaster | dmg | 94 % [72–99] (16) |
| 17 | avenger | dmg | 100 % [81–100] (16) |
| 17 | sacred_warden | deff | 100 % [81–100] (16) |
| 17 | redeemer | heal | 100 % [81–100] (16) |
| 17 | inquisitor | control | 100 % [81–100] (16) |
| 17 | battle_master | dmg | 100 % [81–100] (16) |
| 17 | bulwark | deff | 100 % [81–100] (16) |
| 17 | colossus | deff | 100 % [81–100] (16) |
| 17 | assassin | dmg | 100 % [81–100] (16) |
| 17 | duelist | dmg | 100 % [81–100] (16) |
| 17 | saboteur | control | 100 % [81–100] (16) |
| 17 | life_domain | heal | 100 % [81–100] (16) |
| 17 | chronomancer | control | 100 % [81–100] (16) |
| 17 | war_chanter | dmg | 100 % [81–100] (16) |
| 17 | illusionist | control | 100 % [81–100] (16) |
| 17 | demonologist | dmg | 100 % [81–100] (16) |
| 17 | iron_fist | dmg | 100 % [81–100] (16) |
| 17 | shadow_dancer | deff | 100 % [81–100] (16) |
| 17 | runic_armorer | deff | 100 % [81–100] (16) |
| 17 | construct_master | deff | 100 % [81–100] (16) |
| 17 | ancestral_guardian | deff | 100 % [81–100] (16) |
| 17 | blood | deff | 100 % [81–100] (16) |
| 17 | frost | dmg | 100 % [81–100] (16) |
| 20 | light_domain | dmg | 0 % [0–19] (16) |
| 20 | pyromancer | dmg | 0 % [0–19] (16) |
| 20 | stormcaller | dmg | 0 % [0–19] (16) |
| 20 | sharpshooter | dmg | 0 % [0–19] (16) |
| 20 | tideweaver | heal | 0 % [0–19] (16) |
| 20 | cryomancer | control | 6 % [1–28] (16) |
| 20 | arcanist | dmg | 6 % [1–28] (16) |
| 20 | summoner | dmg | 6 % [1–28] (16) |
| 20 | shapeshifter | dmg | 6 % [1–28] (16) |
| 20 | elementalist | dmg | 12 % [4–36] (16) |
| 20 | grove_warden | deff | 19 % [7–43] (16) |
| 20 | circle_of_spores | dmg | 19 % [7–43] (16) |
| 20 | catalyst | heal | 19 % [7–43] (16) |
| 20 | war_domain | dmg | 25 % [10–50] (16) |
| 20 | hexblade | dmg | 25 % [10–50] (16) |
| 20 | necromancer | dmg | 31 % [14–56] (16) |
| 20 | saboteur | control | 50 % [28–72] (16) |
| 20 | beastmaster | dmg | 50 % [28–72] (16) |
| 20 | assassin | dmg | 56 % [33–77] (16) |
| 20 | artillerist | dmg | 62 % [39–82] (16) |
| 20 | life_domain | heal | 75 % [50–90] (16) |
| 20 | chronomancer | control | 81 % [57–93] (16) |
| 20 | war_chanter | dmg | 81 % [57–93] (16) |
| 20 | berserker | dmg | 94 % [72–99] (16) |
| 20 | illusionist | control | 94 % [72–99] (16) |
| 20 | frost | dmg | 94 % [72–99] (16) |
| 20 | avenger | dmg | 100 % [81–100] (16) |
| 20 | sacred_warden | deff | 100 % [81–100] (16) |
| 20 | redeemer | heal | 100 % [81–100] (16) |
| 20 | inquisitor | control | 100 % [81–100] (16) |
| 20 | battle_master | dmg | 100 % [81–100] (16) |
| 20 | bulwark | deff | 100 % [81–100] (16) |
| 20 | colossus | deff | 100 % [81–100] (16) |
| 20 | duelist | dmg | 100 % [81–100] (16) |
| 20 | demonologist | dmg | 100 % [81–100] (16) |
| 20 | iron_fist | dmg | 100 % [81–100] (16) |
| 20 | shadow_dancer | deff | 100 % [81–100] (16) |
| 20 | runic_armorer | deff | 100 % [81–100] (16) |
| 20 | construct_master | deff | 100 % [81–100] (16) |
| 20 | ancestral_guardian | deff | 100 % [81–100] (16) |
| 20 | blood | deff | 100 % [81–100] (16) |

## Duración por rol (rondas medias en encuentros estándar y élite, política informada)

| Rol | Ramas | Rondas medias |
|---|---|---|
| control | 5 | 9.05 |
| deff | 9 | 9.58 |
| dmg | 23 | 7.41 |
| heal | 4 | 8.77 |

## Defectos que el informe encuentra

| Nivel | Quién | Encuentro | Victorias % | Suelo % |
|---|---|---|---|---|
| 1 | bard | elite | 50 | 55 |
| 1 | cleric | elite | 50 | 55 |
| 1 | druid | elite | 19 | 55 |
| 1 | shaman | elite | 47 | 55 |
| 1 | sorcerer | elite | 16 | 55 |
| 3 | bard | standard | 56 | 75 |
| 9 | shaman | boss | 28 | 35 |
| 9 | shaman | elite | 50 | 55 |
| 9 | shaman | pair | 47 | 55 |
| 10 | arcanist | pair | 12 | 55 |
| 10 | chronomancer | pair | 28 | 55 |
| 10 | cryomancer | pair | 12 | 55 |
| 10 | elementalist | pair | 47 | 55 |
| 10 | grove_warden | pair | 47 | 55 |
| 10 | hexblade | pair | 47 | 55 |
| 10 | life_domain | pair | 22 | 55 |
| 10 | light_domain | pair | 22 | 55 |
| 10 | necromancer | pair | 50 | 55 |
| 10 | pyromancer | pair | 9 | 55 |
| 10 | stormcaller | pair | 44 | 55 |
| 10 | summoner | pair | 22 | 55 |
| 10 | tideweaver | pair | 25 | 55 |
| 13 | arcanist | pair | 34 | 55 |
| 13 | catalyst | pair | 53 | 55 |
| 13 | chronomancer | pair | 41 | 55 |
| 13 | cryomancer | pair | 22 | 55 |
| 13 | elementalist | pair | 47 | 55 |
| 13 | frost | pair | 47 | 55 |
| 13 | grove_warden | pair | 50 | 55 |
| 13 | life_domain | pair | 50 | 55 |
| 13 | light_domain | pair | 44 | 55 |
| 13 | pyromancer | pair | 22 | 55 |
| 13 | sharpshooter | pair | 19 | 55 |
| 13 | stormcaller | pair | 28 | 55 |
| 13 | tideweaver | pair | 38 | 55 |
| 13 | war_chanter | pair | 47 | 55 |
| 17 | catalyst | pair | 50 | 55 |
| 17 | cryomancer | pair | 47 | 55 |
| 17 | elementalist | pair | 50 | 55 |
| 17 | pyromancer | pair | 22 | 55 |
| 17 | sharpshooter | pair | 28 | 55 |
| 17 | stormcaller | pair | 38 | 55 |
| 20 | light_domain | boss | 19 | 35 |
| 20 | pyromancer | boss | 22 | 35 |
| 20 | sharpshooter | boss | 16 | 35 |
| 20 | tideweaver | boss | 19 | 35 |

Suelos usados (semillas, no promesas): weak 90 %, standard 75 %, elite 55 %, pair 55 %, boss 35 %.

## Ritmo de la campaña (modelo, no medición)

Supuestos: 3 min por criatura derrotada, 1.5 min por unidad recogida o fabricada, 2 min por paso o visita; 2 sesiones diarias de 75 min. Sólo cuenta lo que piden las misiones, en orden.

| Misión | XP acumulada | Min acumulados | Nivel por XP | Día (2 sesiones) |
|---|---|---|---|---|
| tut_chapel | 510 | 66 | 3 | 0.4 |
| camp_order | 1260 | 82 | 4 | 0.5 |
| camp_collector | 4660 | 202 | 7 | 1.3 |
| camp_stag | 8910 | 224 | 9 | 1.5 |
| reg_arrive | 9310 | 232 | 9 | 1.5 |
| reg_trial | 44230 | 364 | 18 | 2.4 |

| Hito | Nivel que abre/pide | XP necesaria | XP de las misiones | Falta | Min de caza para cubrirlo |
|---|---|---|---|---|---|
| camp_collector | 9 | 7600 | 4660 | 2940 | 74 |
| camp_stag | 10 | 9800 | 8910 | 890 | 10 |
| reg_trial | 20 | 56500 | 44230 | 12270 | 66 |

## Limitaciones

- El simulador no modela huida, objetos de combate más allá de la poción de curación, ni la decisión de qué rama o modificador escoger: usa las opciones por defecto.
- Un solo linaje y trasfondo; no se barren las 164 configuraciones 13×17 por rama (cuatro por rama): sólo la primera de cada elección.
- Las criaturas de nivel 11–20 se midieron una a una o en parejas, no en las mezclas de las tablas de encuentros reales.
- El ritmo es un modelo con tiempos supuestos; las sesiones reales (tgtest, `oath tutorial-stats`) lo desmentirán o confirmarán.
- No se mide la latencia ni el coste de la IA (la narración no decide reglas).
