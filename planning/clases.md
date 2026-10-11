# Clases

## Estado actual

Cada clase vive en `content/classes.yaml`: dado de golpe, característica principal, reparto de atributos, competencias, equipo inicial y habilidades por nivel (1–5). A nivel 5 se anuncia la especialización, pero aún no se puede elegir.

| Clase | Rol | Dado | Principal | Fila | Identidad |
|---|---|---|---|---|---|
| Paladín | Tanque sagrado | d10 | FUE | Vanguardia | Golpe Consagrado (radiante), Imposición de Manos, Aura de Resolución, Ataque Extra |
| Pícaro | Daño oportunista | d8 | DES | Retaguardia | Ataque Furtivo, Esconderse, Esquiva Asombrosa |
| Guerrero (v0.2.0) | Combatiente puro | d10 | FUE | Vanguardia | Segundo Aliento, Estilo Defensa, Oleada de Acción, Crítico Mejorado, Ataque Extra |
| Sacerdote (v0.2.0) | Sanador y azote de no-muertos | d8 | SAB | Retaguardia | Llama Sagrada, Palabra Sanadora, Expulsar No-muertos, Bendición, Golpe Divino |
| Mago (v0.4.0) | Daño de área y control | d6 | INT | Retaguardia | Rayo de Fuego, Armadura de Mago, Dormir, Bola de Fuego, Proyectil Mágico |
| Druida (v0.4.0) | Control, curación y forma de bestia | d8 | SAB | Retaguardia | Látigo de Espinas, Curar Heridas, Enredar, Forma Salvaje, Furia Elemental |
| Bardo (v0.4.0) | Apoyo, burla e hipnosis | d8 | CAR | Retaguardia | Burla Cruel, Inspiración Bárdica, Canción Sanadora, Patrón Hipnótico, Palabras Cortantes |

Desde v0.4.0 hay **tiradas de salvación**: la CD de conjuro es 8 + competencia + característica de la clase, y los monstruos salvan con DES o SAB (las únicas que tienen). Las habilidades `save` afectan a un objetivo o a toda su fila (`area: row`).

Especializaciones previstas (nivel 5):

- Paladín: Venganza, Guardián Sagrado, Redentor, Inquisidor.
- Pícaro: Asesino, Espía, Duelista, Trampero.
- Guerrero: Campeón, Maestro de Batalla, Guardián, Berserker.
- Sacerdote: Vida, Luz, Guerra, Tumba.
- Mago: Piromante, Criomante, Arcanista, Cronomante.
- Druida: Cambiaformas, Guardián, Invocador, Esporas.
- Bardo: Ilusionista, Diplomático, Cantor de Guerra, Embaucador.

## Ideas

- **Explorador**: enemigo predilecto por tipo de criatura (los monstruos ya tienen `type`), compañero animal, ventaja en el bosque.
- **Bardo en grupo**: cuando llegue el combate en grupo, la Inspiración debería darse a un aliado; fuera de combate, ventaja en diálogo con NPC.
- **Forma Salvaje** completa: hoy son PV temporales; podría cambiar los ataques por los de una bestia.
- **Brujo**: pacto con una facción (Sindicato Carmesí), poderes que cambian con la reputación.
- Especializaciones con una decisión real: cada una cambia una habilidad o añade un recurso, no solo números.
- Multiclase: probablemente no; mejor especializaciones profundas.
- Rasgos de linaje que interactúen con la clase (orco + guerrero, enano + sacerdote).

### Visión a largo plazo: 12 clases (GDD §4.3)

El GDD imagina 12 clases con 4 especializaciones cada una. Es una **visión**, no un plan: el propio GDD avisa de que no hay que programar 48 caminos antes de tener un combate divertido. Los nombres de especialización ya decididos en Oathforge (arriba) mandan sobre los del GDD.

| Clase | Especializaciones (GDD) | Identidad | En Oathforge |
|---|---|---|---|
| Paladín | Venganza, Protección, Redención, Inquisición | Juramentos, auras, primera línea | ✅ |
| Guerrero | Berserker, Maestro de Armas, Centinela, Gladiador | Dominio marcial y control | ✅ |
| Pícaro | Asesino, Espía, Duelista, Trampero | Precisión, información, movilidad | ✅ |
| Clérigo | Oráculo, Sacerdote de Guerra, Sanador, Exorcista | Apoyo y símbolos sagrados | ✅ como **Sacerdote** |
| Mago | Piromante, Criomante, Arcanista, Cronomante | Hechizos, área, preparación | ✅ |
| Explorador | Cazador, Francotirador, Acechador, Trampero Salvaje | Rastreo, distancia, terreno | idea |
| Bardo | Ilusionista, Diplomático, Cantor de Guerra, Embaucador | Inspiración, conversación, engaño | ✅ |
| Brujo | Pactista Infernal, Nigromante, Hexblade, Vacío | Pactos, maldiciones, riesgo | idea |
| Druida | Cambiaformas, Guardián, Invocador, Esporas | Naturaleza, formas, control | ✅ |
| Monje | Puño de Hierro, Espiritual, Sombra, Elemental | Recursos internos y combos | nueva |
| Hechicero | Sangre Dracónica, Magia Salvaje, Tormenta, Astral | Poder innato | nueva |
| Artífice | Ingeniero, Alquimista, Forjador Rúnico, Autómata | Objetos y dispositivos; encaja con profesiones | nueva |

### Especializaciones del Paladín con talentos (GDD §4.4)

Sirven de plantilla para diseñar las del resto:

- **Venganza** (≈ nuestro *Venganza*): marca un objetivo y cambia defensa por daño. Talentos: *Juramento Implacable* (bonificación al perseguir), *Castigo Resonante* (daño condicionado), *Último Veredicto* (ejecución con coste).
- **Protección** (≈ *Guardián Sagrado*): escudos, intercepción, provocación. Talentos: *Muro de Fe*, *Guardia Compartida*, *Fortaleza del Juramento*. En solitario debe conservar opciones ofensivas.
- **Redención** (≈ *Redentor*): cura, purifica y abre rutas diplomáticas. Talentos: *Palabra de Tregua*, *Gracia Persistente*, *Segundo Aliento*.
- **Inquisición** (≈ *Inquisidor*): detecta corrupción y debilita. Talentos: *Sello de Silencio*, *Juicio Radiante*, *Lectura de Herejía*. Detectar mentiras no debe resolver solo todos los misterios.

### Recursos de clase (GDD §4.5)

Concentración, furia, fe, maná, preparación o inspiración. **Como máximo dos recursos por clase** para no saturar el panel de Telegram, y con recuperación clara: por turno, por encuentro, en descanso corto, en descanso largo o por día del mundo.

## Preguntas abiertas

- ¿Nivel máximo 5 o ampliamos a 10 antes de añadir más clases?
- ¿Los conjuros usan espacios (estilo D&D) o una barra de fe/maná más simple para Telegram?
- ¿Cuántos botones caben en el panel de combate antes de que sea incómodo? (hoy ~8–10)
- ¿Qué clase entra después: Explorador (aprovecha los tipos de criatura) o Brujo (pactos con facciones)?
- ¿Entran algún día Monje, Hechicero o Artífice, o nos quedamos en 9 clases?
- ¿Cada especialización tiene un árbol de 3 talentos (como en el GDD) o un único cambio fuerte?
