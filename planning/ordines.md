# Ordines — clases y especializaciones

Resumen de [Possibilium §5–7](Possibilium.md#s05).

## Estado actual (0.8.2)

> **En revisión (0.10-I, desde 0.10.22).** El [contrato de clases y progresión](roadmap_balance.md) sustituye lo que sigue: pasan a ser **14 clases** (Mago y Hechicero se fusionan en Hechicero y Sacerdote pasa a Clérigo —ya renombrados, ids `sorcerer` y `cleric`, en 0.10.23—, y entran Bárbaro, Explorador, Monje, Artífice, Chamán y Caballero de la Muerte), cada una con **su propia barra** en vez de usos por descanso, y **41 ramas que se eligen al nivel 10**, no al 5. El catálogo ya está en `content/class_specializations.yaml` y los recursos en `content/progression.yaml`; ninguna rama es elegible todavía (`ready: false`) hasta que B07 le escriba su recorrido de 10 a 20. La tabla de abajo describe las ocho clases tal y como están hoy.


Cada clase vive en `content/classes.yaml`: dado de golpe, atributo principal, reparto recomendado, competencias, equipo inicial, habilidades por nivel (1–5), `signature` (habilidad destacada 🌟 en combate) y `details` (texto largo de `/skill_<clave>`).

| Clase | Rol | Dado | Principal | Fila | Identidad |
|---|---|---|---|---|---|
| Paladín | Tanque sagrado | d10 | FUE | Vanguardia | Golpe Consagrado, Imposición de Manos, Aura de Resolución, Ataque Extra |
| Pícaro | Daño oportunista | d8 | DES | Retaguardia | Ataque Furtivo, Esconderse (nivel 1), Esquiva Asombrosa |
| Guerrero | Combatiente puro | d10 | FUE | Vanguardia | Segundo Aliento, Estilo Defensa, Oleada de Acción, Crítico Mejorado, Ataque Extra |
| Clérigo | Sanador y azote de no-muertos | d8 | SAB | Retaguardia | Llama Sagrada, Palabra Sanadora, Expulsar No-muertos, Bendición, Golpe Divino |
| Hechicero | Área y control | d6 | INT | Retaguardia | Rayo de Fuego, Armadura de Mago, Dormir, Bola de Fuego, Proyectil Mágico |
| Druida | Control, curación y forma | d8 | SAB | Retaguardia | Látigo de Espinas, Curar Heridas, Enredar, Forma Salvaje (PV temporales), Furia Elemental |
| Bardo | Apoyo, burla e hipnosis | d8 | CAR | Retaguardia | Burla Cruel, Inspiración Bárdica, Canción Sanadora, Patrón Hipnótico, Palabras Cortantes |
| Brujo | Maldiciones y daño sostenido | d8 | CAR | Retaguardia | Estallido Sobrenatural, Maleficio, Armadura de Sombras, Susurros del Vacío, Estallido Agónico |

- CD de conjuro: 8 + competencia + atributo de la clase. Los monstruos salvan con DES o SAB. Habilidades `save` a un objetivo o a toda su fila (`area: row`).
- `kind: curse`: estado sin salvación; el Maleficio deja `hexed` 3 turnos y suma 1d6 necrótico a cada golpe con tirada.
- Usos por descanso en `Character.resources`; no hay maná.
- `extra_attack` en Paladín y Guerrero. «⚙️ Cómo funciona» de `/skill_<clave>` se genera desde los campos (`render.ability_mechanics`).
- Especializaciones (nivel 5): 32 nombres en el YAML; **todavía no se pueden elegir**.

## Decidido

- Ocho clases; ninguna clase nueva antes de especializaciones y cooperativo.
- Como máximo dos recursos por clase; recuperación clara (turno, encuentro, descanso).
- Nombres de especialización actuales mandan sobre los del GDD.

## Próximo

- **ESP-01** paquete por rama: pasiva, activa, interacción narrativa y misión de desbloqueo; una funcional por clase primero (Protection, Duelist, Battle Master, Life, Cryomancer, Warden, War Chanter, Hexblade como candidatas).
- **ESP-03** reentrenamiento en ciudad con coste; **ESP-05** desbloqueo por identidad.
- Catálogo efectivo clase + especialización para motor, descanso, ficha y simulador (ticket SPEC-01).
- **CLA-01** Explorador como siguiente clase; **CLA-05** Artífice (distinto del oficio Ingeniería). Monje, Bárbaro, Hechicero, Chamán y Caballero de la muerte, reserva.
- Renombrar el golpe base del Paladín a **Castigo divino**.
- Inspiración del Bardo a un aliado cuando haya grupos; Forma Salvaje completa; pacto de facción del Brujo.

## Preguntas abiertas

- ~~¿Sacerdote, Clérigo o ambos?~~ Resuelto (0.10.23): **Clérigo** (`cleric`), y el Mago pasa a **Hechicero** (`sorcerer`) al fusionarse las dos fantasías (NOM-01..03, Possibilium §6).
- ¿Nivel máximo 5 o ampliar a 10 antes de más clases?
- ¿Usos actuales o barra de fe/maná?
- ¿Una o dos especializaciones iniciales por clase? ¿Árbol de 3 talentos o un cambio fuerte?
- ¿Cuántos botones caben en el panel de combate?
