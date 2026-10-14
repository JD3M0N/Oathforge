# Bestiario

## Estado actual

- **v0.5.0**: Diario → «📖 Bestiario». Cada personaje guarda en `characters.bestiary` cuántas veces ha visto y derrotado cada criatura (`oathforge/services/bestiary.py`).
- La ficha se desbloquea con la experiencia, como un manual de monstruos que el jugador va rellenando:
  - **vista**: nombre, tipo, descripción, historia (`lore`), hábitat y si sale de día o de noche (`active`);
  - **1 derrotada**: PV, CA y ataques;
  - **3 derrotadas**: vulnerabilidades, resistencias, inmunidades, XP y botín.
- 10 criaturas: bandido, capitán bandido, goblin explorador, lobo gris, esqueleto de la cripta, Guardián de la Cripta, jabalí, murciélago de cueva, el Viejo Colmillo y la rata gigante.
- **v0.7.3**: icono propio por criatura (`icon` en `content/monsters.yaml`; si falta, el de su tipo) e ilustración en `content/monsters/<criatura>/images/portrait.jpg` (768 × 1024), que se ve con «🖼️ Ver ilustración» en la ficha de una criatura ya vista.

## Ideas

- Añadir criaturas poco a poco, siempre con `lore`, `habitat` y `active` en `content/monsters.yaml`.
- Descubrir puntos débiles antes de tiempo con una tirada de Religión, Arcanos o Naturaleza.
- Logros por completar el bestiario de una zona («Cazador del Prado»).
- Criaturas raras o nocturnas con poca probabilidad, para que valga la pena volver.

## Preguntas abiertas

- ¿Mostrar las criaturas no vistas como «???» para que el jugador sepa cuántas faltan?
- ¿Recompensa por completar el bestiario (oro, título, objeto)?
