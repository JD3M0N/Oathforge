---
name: new-class
description: Crear una clase nueva de Oathforge (ficha, habilidades, barra de recurso, ramas de clase o especializaciones y progresión de niveles 1-20), o una rama nueva de una clase que ya existe. Úsala cuando Josue pida una clase, una rama o una especialización de clase.
---

# Nueva clase o rama de clase

Empieza por `planning/roadmap_balance.md` §6 (solo la ficha de esa clase, por rangos) y `planning/ordines.md`. Los ejemplos de Josue con el Paladín valen para todas las clases.

## Clase

1. **Ficha**: `.venv\Scripts\oath new class <id> --name "…" --desc "…"`. Crea `content/classes/<id>/class.yaml`, `specializations.yaml` (una rama con `ready: false`) e `images/` con los prompts de retrato de hombre y de mujer.
2. **Habilidades de nivel 1 a 9**: `abilities` con `kind` (strike, spell, turn, buff, heal, summon…), `level`, `cost`/`uses`, `details` en es y en. El ataque básico nunca cuesta nada. Si la clase tiene barra propia (`resource`), defínela en `content/progression.yaml` (`resources`) y usa `cost`/`generates` en vez de `uses`. Cifras: semillas.
3. **Equipo inicial**: `items` y `equip` con ids que existen; `array` con las seis características, `skills` y `signature`.
4. **Fuera de `content/`**: el emoji de la clase en `CLASS_ICONS` de `oathforge/bot/render/character.py`, y el retrato con la skill `new-image`.
5. **Ramas**: la clase tiene varias (`specializations.yaml`, ids únicos en todo el juego, prefijados con la clase). Cada rama lista lleva su recorrido entero: pasiva y técnica al 10, desarrollo fijo al 15, dos modificadores en el 13 y otros dos en el 17 (se elige uno de cada par) y una técnica culminante al 20. Mira `content/classes/paladin/specializations.yaml`. Hasta entonces, `ready: false`.
6. **Progresión 1-20**: XP, hitos, entrenamientos y niveles sin habilidad nueva siguen `content/progression.yaml` (`xp`, `training_levels`, `modifier_levels`, `milestones`) y el calendario de poderes de `roadmap_balance.md` §5. Una clase nueva tiene que cubrir cada nivel con algo: habilidad, entrenamiento o modificador.
7. **Balance**: `.venv\Scripts\oath balance --n 16` (varios minutos) y `.venv\Scripts\oath simulate --level 1-5`; la clase no puede quedar claramente por encima ni por debajo de las demás. Anota el resultado en `planning/informe_balance_0.10.md` o en el plan de la serie.

## Rama de una clase que ya existe

Añade la rama a `content/classes/<clase>/specializations.yaml` con `class_key`, `name`, `description`, `roles` (el primero es el principal) y `ready: false`; pásala a `true` solo cuando tenga todo su recorrido 10-20. Si cambia mucho cómo juega una rama ya elegida, sube su `revision`.

## Cierre

`.venv\Scripts\oath validate` · `.venv\Scripts\python -m pytest tests/test_content.py tests/test_balance.py tests/test_campaign.py -q` · actualizar el **Estado actual** de `planning/ordines.md` y `progressio.md` · CHANGELOG y commit (skill `release`).

Lista de cierre: ficha en es y en · sin `TODO(new)` · recurso definido · emoji en `CLASS_ICONS` · ramas con su recorrido o `ready: false` · progresión sin niveles vacíos · balance medido · retratos con prompt.
