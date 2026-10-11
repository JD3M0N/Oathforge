# Progresión

## Estado actual

- Niveles 1–5 por XP (`oathforge/engine/progression.py`: 0, 300, 900, 2700, 6500).
- PV: dado de golpe completo a nivel 1; después, media + 1 + CON por nivel.
- Mejora de característica a nivel 4 (+2 a la principal).
- Habilidades de clase nuevas por nivel; los usos se recuperan al descansar.
- Las habilidades (skills) mejoran con el uso, con rendimientos decrecientes si repites lo mismo en 24 h (rango 0–3).

## Ideas

- Elegir especialización a nivel 5 (pantalla con descripción y botones).
- Equipo mágico con propiedades (+1, daño extra de un tipo, resistencia).
- Títulos y logros en la ficha (p. ej. «Azote de la Cripta»).
- Ampliar a nivel 10 con un segundo arco de contenido.

## Preguntas abiertas

- ¿Cuántas horas de juego por nivel? Medirlo con `artifacts/events/`.
- ¿La mejora de nivel 4 debería ser elegible (dote o característica)?
