# Ordines — clases y especializaciones

Resumen de [Possibilium §5–7](Possibilium.md#s05).

## Estado actual (0.8.2)

> **En revisión (0.10-I, desde 0.10.22; las catorce clases base, hechas en 0.10.31).** El [contrato de clases y progresión](roadmap_balance.md) sustituye lo que sigue: pasan a ser **14 clases** (Mago y Hechicero se fusionan en Hechicero y Sacerdote pasa a Clérigo —ya renombrados, ids `sorcerer` y `cleric`, en 0.10.23—, y entran Bárbaro, Explorador, Monje, Artífice, Chamán y Caballero de la Muerte), cada una con **su propia barra** en vez de usos por descanso —ya en el motor desde 0.10.25, con el Guerrero (Foco) y el Hechicero (Maná) como pilotos—, y **41 ramas que se eligen al nivel 10**, no al 5. El catálogo ya está en `content/class_specializations.yaml` y los recursos en `content/progression.yaml`; ninguna rama es elegible todavía (`ready: false`) hasta que B07 le escriba su recorrido de 10 a 20. La tabla de abajo describe las ocho clases tal y como están hoy.


Cada clase vive en `content/classes.yaml`: dado de golpe, atributo principal, reparto recomendado, competencias, equipo inicial, **su propia barra de recurso**, habilidades de nivel 1 a 9, `signature` (habilidad destacada 🌟 en combate) y `details` (texto largo de `/skill_<clave>`). Del nivel 10 en adelante lo da la rama ([`content/class_specializations.yaml`](../content/class_specializations.yaml)).

| Clase | Rol | Dado | Principal | Recurso | Identidad (niveles 1–9) |
|---|---|---|---|---|---|
| Guerrero | Combatiente puro | d10 | FUE | Foco | Golpe Poderoso, Segundo Aliento, Oleada de Acción, Embestida de Escudo, Ataque Extra, Golpe de Gracia |
| Bárbaro | Presión y vitalidad | d12 | FUE | Furia | Golpe Temerario, Furia, Golpe de Barrido, Asalto Implacable, Golpe Salvaje, Pisotón Atronador |
| Paladín | Tanque sagrado | d10 | FUE | Convicción | Castigo Divino, Imposición de Manos, Aura de Resolución, Favor Divino, Cólera Sagrada, Luz Purificadora |
| Pícaro | Daño oportunista | d8 | DES | Energía | Ataque Furtivo, Esconderse, Golpe Bajo, Zancadilla, Acción Astuta, Filo Mortal |
| Monje | Técnicas del cuerpo | d8 | DES | Foco | Ráfaga de Golpes, Golpe Aturdidor, Desviar Golpes, Respiración Serena, Mil Puños, Ola Arrolladora |
| Clérigo | Sanador y azote de no-muertos | d8 | SAB | Maná | Llama Sagrada, Palabra Sanadora, Expulsar No-muertos, Bendición, Plegaria Sanadora, Columna de Luz |
| Hechicero | Área y control | d6 | INT | Maná | Rayo de Fuego, Armadura de Mago, Dormir, Bola de Fuego, Lanza de Hielo, Cono de Frío |
| Druida | Control, curación y forma | d8 | SAB | Maná | Látigo de Espinas, Curar Heridas, Enredar, Forma Salvaje, Piel de Corteza, Rebrote |
| Bardo | Apoyo, burla e hipnosis | d8 | CAR | Resonancia | Burla Cruel, Inspiración Bárdica, Patrón Hipnótico, Susurros Disonantes, Acorde Estremecedor, Bis |
| Brujo | Maldiciones y daño sostenido | d8 | CAR | Esencia | Estallido Sobrenatural, Maleficio, Armadura de Sombras, Susurros del Vacío, Drenar Vida, Desgarro de Alma |
| Explorador | Cazador a distancia | d10 | DES | Foco | Disparo Certero, Marca de Presa, Paso del Bosque, Lluvia de Flechas, Disparo Doble, Tormenta de Flechas |
| Artífice | Aparato que carga y descarga | d8 | INT | Carga | Descarga del Aparato, Pulso Restaurador, Reactivo Corrosivo, Espuma Protectora, Sobrecarga, Gran Descarga |
| Chamán | Fuerza de los elementos | d8 | SAB | Maná | Chispa Elemental, Piel de Piedra, Marea Sanadora, Agarre de Tierra, Cadena de Tormenta, Llamada de la Tempestad |
| Caballero de la Muerte | Runas de muerte y escarcha | d10 | FUE | Poder rúnico | Golpe de Muerte, Sorber Vitalidad, Cadenas de Escarcha, Hoja Rúnica, Aniquilar, Ráfaga Aullante |

- **Todas pagan con su barra** (ver [pugna](pugna.md)); ya no hay usos por descanso. El ataque básico es siempre gratis y útil.
- Las barras que empiezan vacías (Furia, Convicción, Resonancia, Poder rúnico) se construyen atacando; las otras se recuperan por turno o al ganar.
- CD de conjuro: 8 + competencia + atributo de la clase (el Monje y el Explorador usan SAB). Los monstruos salvan con DES o SAB. Habilidades `save` a un objetivo o a toda su fila (`area: row`).
- `kind: curse`: estado sin salvación. El Maleficio deja `hexed` (1d6 necrótico por golpe); la Marca de presa del Explorador deja `marked` (1d6 perforante).
- Un `strike` con `ranged` usa el arma a distancia: así dispara el Explorador.
- **Calendario de poderes** (roadmap_balance §5.2): en el 1 hay ataque básico, técnica distintiva y el recurso; del 2 al 4, una herramienta defensiva o de preparación; en el 5, refuerzo de identidad; del 6 al 9, una o dos mejoras. Los nombres, costes y cifras son semillas para medir.
- `tests/engine/test_class_roster.py` exige a **cada** clase lo mismo: barra propia, técnica desde el nivel 1, nada que dependa de una rama o un aliado, victoria sobre un bandido (niveles 1, 3, 5 y 9) y sobre una pareja de goblins (5 y 9).
- Los retratos del Bárbaro, el Monje, el Explorador, el Artífice, el Chamán y el Caballero de la Muerte están pendientes ([TODO-images](../TODO-images.md)).
- `extra_attack` está en Guerrero, Paladín, Bárbaro, Monje, Explorador y Caballero (con claves propias en las nuevas, para que cada página de habilidad hable de su clase).
- Ramas: 41 declaradas; **32 elegibles desde 0.10.33** (lotes A y B de B07) con su recorrido del 10 al 20. Las ramas comparten una docena de mecánicas pequeñas (gastar un estado, responder a una herida, robar vida acotado, enfriamientos, barreras, entidades y formas) y `tests/engine/test_branches.py` exige que dos ramas de una clase no hagan las mismas decisiones.

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
