# Progressio — personaje, progresión y juramentos

Resumen de [Possibilium §8–9](Possibilium.md#s08) (y equipo en [mercatura](mercatura.md)).

## Estado actual (0.8.2)

- **Creación**: nombre, hombre o mujer, 4 linajes (humano, elfo, enano, orco), trasfondo (4 básicos como botón, 12 en total, o uno propio revisado por Gemini con 2 habilidades a elegir), clase y compra de 27 puntos (todo en 8; 14→15 cuesta 2; «⭐ Recomendado» carga el array de la clase). `/lineage`, `/background` y `/classes` ayudan a mitad de la creación.
- **Niveles 1–5**: 0 / 200 / 500 / 1000 / 1800 XP (`engine/progression.py`). PV: dado completo a nivel 1, después media + 1 + CON. Nivel 4: +2 a la principal. Subida de nivel en un mensaje propio.
- **Competencias** 0–3 que mejoran con el uso, con rendimientos decrecientes si se repite lo mismo en 24 h.
- Una prueba de habilidad se intenta una vez por habilidad, lugar y día de juego (4 h reales); se desbloquea al día siguiente o al subir de nivel (`characters.checks_tried`).
- El tutorial (10 misiones, unos 750 XP de misión) lleva a nivel 3–4; relicario y cripta llevan a 5.
- Reputación con dos facciones; títulos, juramentos y logros no existen todavía.

## Decidido

- Linaje no determina moralidad ni clase «correcta».
- Cambiar un rasgo o atributo ofrece revisión gratuita o compensación.
- Sin multiclase antes de especializaciones.

## Próximo

- **PRO-02** XP por lo que importa (peligros, descubrimientos, decisiones), no por spam.
- **PRO-03** nivel 4 con elección de atributo o dote.
- **PRO-06** campamento de entrenamiento por clase tras el tutorial, opcional.
- **PRO-07** ampliar a 6–8 solo con un arco de contenido.
- **JUR-01** un juramento verificable (Guard the Witness o Return What Was Taken), por eventos, sin juicio moral de la IA (ticket OATH-01).
- **REL-01..05** favores concretos, rivales, títulos y cicatrices, legado, vínculos de grupo.
- **LIN-01..06** linajes nuevos (Ashborn, Tidekin…) tras revisar humano (+1 a todo) y enano (inmune a veneno).
- Imagen de cada linaje en `/lineage` ([ars](ars.md)); sistema de logros ([mundus](mundus.md)).

## Preguntas abiertas

- ¿Horas de juego por nivel? Medir con `artifacts/events/`.
- ¿Competencias 0–3 visibles con 0–100 por debajo?
- ¿Qué se comparte por cuenta si hay varios personajes?
