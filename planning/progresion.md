# Progresión

## Estado actual

- Niveles 1–5 por XP (`oathforge/engine/progression.py`: 0, 200, 500, 1000, 1800). **v0.5.0**: curva comprimida para que la cadena de 6 misiones lleve a nivel 5 en una tarde (la curva de D&D, 6.500 XP, pedía decenas de combates).
- Atributos al crear (**v0.5.0**): compra por puntos de D&D (todo en 8, 27 puntos, 14→15 cuesta 2) con botón «Recomendado» que carga el array de la clase (15/14/13/12/10/8 cuesta justo 27) y una línea por atributo que explica para qué sirve (`content/abilities.yaml`, `effect`).
- PV: dado de golpe completo a nivel 1; después, media + 1 + CON por nivel.
- Mejora de característica a nivel 4 (+2 a la principal).
- Habilidades de clase nuevas por nivel; los usos se recuperan al descansar.
- Las habilidades (skills) mejoran con el uso, con rendimientos decrecientes si repites lo mismo en 24 h (rango 0–3).
- **v0.5.2**: una prueba de habilidad no se repite hasta que salga. Cada habilidad se puede intentar una vez por lugar y día de juego (4 h reales); cada secreto de Investigar, una vez al día. Se desbloquea al día siguiente o al subir de nivel (`characters.checks_tried`, `exploration.tried`).

## Ideas

- Elegir especialización a nivel 5 (pantalla con descripción y botones).
- Equipo mágico con propiedades (+1, daño extra de un tipo, resistencia).
- Títulos y logros en la ficha (p. ej. «Azote de la Cripta»).
- Ampliar a nivel 10 con un segundo arco de contenido.

### Del GDD

- **XP por lo que importa** (§4.5): peligros resueltos, descubrimientos, misiones y decisiones narrativas, no el spam de diálogos ni repetir enemigos débiles. Cada nivel da mejoras predecibles y, cada cierto número de niveles, una elección de talento.
- **Proficiencias más finas** (§4.6): puntuación 0–100 con cinco rangos (Novato, Aprendiz, Competente, Experto, Maestro). Hoy usamos 0–3; se podría mapear sin romper nada (0–3 como rango visible y 0–100 por debajo). Incluye oficios: minería, cocina, herrería, cartografía, comercio.
- **Maestros que enseñan** (§4.6, idea 14): técnicas que no se compran, solo se aprenden de un NPC bajo condiciones (Tessa podría enseñar una técnica de herrería).
- **Ranuras de equipo** (§4.7): arma principal, secundaria/escudo, casco, torso, manos, botas, amuleto, anillos y consumibles. Rarezas común → legendaria, pero la rareza no decide sola el poder.
- **Objetos con historia** (§4.7, idea 65): los objetos fabricados guardan fabricante, materiales y fecha; los únicos, quién los encontró, sus dueños y sus batallas. Registro inmutable para evitar duplicados.
- **Juramentos** (§4.8, idea 13): promesas voluntarias con consecuencias publicadas («No abandonaré a mis compañeros»). Cumplirlas da reputación; romperlas abre una historia de redención, no arruina el personaje. Encaja con el Paladín.
- **Títulos y cicatrices** (§4.8, idea 18): títulos cosméticos o de acceso social; cicatrices que cambian diálogos, nunca penalizaciones permanentes.

## Preguntas abiertas

- ¿Cuántas horas de juego por nivel? Medirlo con `artifacts/events/`.
- ¿La mejora de nivel 4 debería ser elegible (dote o característica)?
- ¿Ampliamos las habilidades a 0–100 o mantenemos 0–3, que es más legible en Telegram?
- ¿Cuántas ranuras de equipo caben en `/sheet` sin que se vuelva pesado?
