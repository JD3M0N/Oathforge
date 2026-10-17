# Bestiarium — criaturas

Resumen de [Possibilium §20](Possibilium.md#s20).

## Estado actual (0.8.2)

- Diario → «🐉 Bestiario». Cada personaje guarda en `characters.bestiary` cuántas veces ha visto y derrotado cada criatura (`services/bestiary.py`).
- La ficha se desbloquea con la experiencia:
  - **vista**: nombre, tipo, descripción, historia (`lore`), hábitat y si sale de día o de noche (`active`);
  - **1 derrota**: PV, CA y ataques;
  - **3 derrotas**: vulnerabilidades, resistencias, inmunidades, XP y botín.
- 10 criaturas en `content/monsters.yaml`: bandido, capitán bandido, goblin explorador, lobo gris, esqueleto de la cripta, Guardián de la Cripta (Ser Aldren), jabalí, murciélago de cueva, Viejo Colmillo y rata gigante. Icono propio (`icon`) e ilustración en `content/monsters/<criatura>/images/portrait.jpg` («🖼️ Ver ilustración», `/monster_<clave>`).
- Bestias con `harvest` y `skin_seconds` para el desuello.
- **Balance del tutorial**: jabalí, bandido y esqueleto 7 PV, +2, 1d4; murciélago 5 PV, +3, 1d4; capitán 26 PV, +4, 1d8+1; Viejo Colmillo 18 PV, CA 11, +3, 1d8+1 (el mago de nivel 4 gana el 89 % en el simulador). Las parejas salen por `min_level`: prado desde nivel 2, mina y camino desde 3, capitán desde 4, lobos desde 3 y parejas de lobos desde 4.

## Decidido

- Toda criatura nueva lleva `lore`, `habitat`, `active`, `icon` e ilustración con su `media.yaml` y `.prompt.md`.
- Mago y druida a nivel 1 deben ganar casi siempre 1 contra 1 a las criaturas del tutorial.

## Próximo

- **BES-01** debilidades descubiertas antes con Religión, Arcanos o Naturaleza.
- **BES-02** rarezas de encuentro (10–15 %), después por hora y clima.
- **BES-03/04** tamaño y peso de presas, récords y desuello por peso.
- **BES-08** logros por bestiario de zona y siluetas «???».
- Lobo gris a nivel 1 (la pícara gana ~40 %, el druida ~20 %) y la tabla del camino con el capitán.
- «Algo brilla» en la mina como descubrimiento con recompensa.

## Preguntas abiertas

- ¿Mostrar las no vistas como «???»?
- ¿Recompensa por completar el bestiario (oro, título, objeto)?
