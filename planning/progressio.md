# Progressio — personaje, progresión y juramentos

Resumen de [Possibilium §8–9](Possibilium.md#s08) (y equipo en [mercatura](mercatura.md)).

## Estado actual (0.10.8)

> **En revisión (0.10-I, desde 0.10.22).** El [contrato de clases y progresión](roadmap_balance.md) lleva el techo de nivel 5 a **20** y hace la subida **híbrida**: la XP demuestra experiencia y un hito narrativo abre la frontera, y hacen falta las dos cosas. La tabla de 20 umbrales, las dos puertas (el Recaudador al 10 y el Ciervo para el resto) y los recursos de clase viven ya en `content/progression.yaml`; el cálculo puro, en `engine/class_build.py`. **Conectado al juego en 0.10.24 (B02)**: el nivel es ya el menor entre el que da la XP y el que permiten los hitos, la XP no se pierde esperando en una puerta y la ficha dice cuál falta; las misiones con `turn_in_stage` se cobran al entregárselas a quien las dio, con recompensa, hito y nivel en la misma transacción. Queda por conectar la mejora de atributo del nivel 4, que sustituyen tres entrenamientos en 5, 12 y 18, y los modificadores de rama del 13 y el 17 (B04). Lo que sigue describe el resto de la progresión vigente.


- **Creación**: nombre, hombre o mujer, 4 linajes (humano, elfo, enano, orco), trasfondo (4 básicos como botón, 12 en total, o uno propio revisado por Gemini con 2 habilidades a elegir), clase y compra de 27 puntos (todo en 8; 14→15 cuesta 2; «⭐ Recomendado» carga el array de la clase). `/lineage`, `/background` y `/classes` ayudan a mitad de la creación.
- **Niveles 1–20** (0.10.24): la tabla vive en `content/progression.yaml` y los cinco primeros umbrales siguen siendo 0 / 200 / 500 / 1000 / 1800 XP. PV: dado completo a nivel 1, después media + 1 + CON. Nivel 4: +2 a la principal. Subida de nivel en un mensaje propio.
- **Competencias** 0–3 que mejoran con el uso, con rendimientos decrecientes si se repite lo mismo en 24 h.
- Una prueba de habilidad se intenta una vez por habilidad, lugar y día de juego (4 h reales); se desbloquea al día siguiente o al subir de nivel (`characters.checks_tried`).
- El tutorial (10 misiones, unos 750 XP de misión) lleva a nivel 3–4; relicario y cripta llevan a 5.
- Reputación con dos facciones; los juramentos siguen pendientes.
- **Logros**: 34 individuales y dos metalogros, por personaje (dos de ellos ocultos hasta conseguirlos); puntos de logro sin poder ni uso económico. Edición fija v0_9 y concesiones atómicas con evidencia. En la interfaz se llaman «Logros», nunca «hazañas».
- **Identidad**: cinco títulos desbloqueables, uno equipado, tres logros destacados y tres objetivos seguidos. El título se ve en `/hero`, en `/sheet` y en la cabecera del Libro del Héroe, y va como dato al narrador y a los PNJ, que pueden saludarte por él; concederlo sigue siendo solo del motor. El progreso anterior se reconoce solo cuando hay evidencia persistida.
- Los retos de 1 PV, combate contra varios y ausencia de consumibles usan parejas repetibles de lobos o murciélagos a nivel inicial 3–5; no dependen de repetir jefes únicos.
- **Crónica de hechos** (`hero_facts`, 0.10.7): cada hecho que el motor registra se guarda una vez por personaje (el mismo registro que deduplica los logros, antes `achievement_event_receipts`) con su tipo, sus datos y el día de juego. Los que merecen entrada van marcados `notable`: siempre misión, decisión, logro, nivel, derrota, secreto y descubrimiento; solo la primera vez cada lugar, receta, criatura y rango; nunca lo repetido. De ahí salen el diario, las estadísticas verificables y, más adelante, el resumen narrado y el *Heraldo*. Hechos nuevos: nivel alcanzado, rango de oficio y misión aceptada.

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
- Imagen de cada linaje en `/lineage` ([ars](ars.md)); ampliar logros cuando haya contenido que los justifique ([mundus](mundus.md)).

## Preguntas abiertas

- ¿Horas de juego por nivel? Medir con `artifacts/events/`.
- ¿Competencias 0–3 visibles con 0–100 por debajo?
- ¿Qué se comparte por cuenta si hay varios personajes?
