---
name: new-monster
description: Crear una criatura o jefe nuevo de Oathforge con ficha en es/en, estadísticas según su nivel, dónde aparece, botín, prompt del retrato y comprobación con el simulador. Úsala cuando Josue pida un monstruo, una criatura, un enemigo o un jefe.
---

# Nueva criatura

1. **Crea la ficha**: `.venv\Scripts\oath new monster <id> --name "English name" --desc "English description"`. Hace `content/monsters/<id>/monster.yaml` y `images/portrait.prompt.md` (+ `media.yaml`). Ábrela y quita cada `TODO(new)`: nombre, `indefinite`, descripción, hábitat y `lore` en es y en. El `icon` (emoji) no puede repetirse entre criaturas.
2. **Estadísticas según su nivel**: no tienen nivel propio; el rival previsto por nivel está en `STANDARDS` de `oathforge/tools/balance.py`. Parte de una criatura parecida (`content/INDEX.md`) del mismo rango y ajusta `hp`, `ac`, `to_hit`, `damage` y `xp`. Los números son semillas: se miden en el paso 5.
3. **Dónde aparece**: añádela a `encounters` (o `night_encounters`) del `place.yaml` que toque, con `weight` y `min_level` (las manadas empiezan más tarde), o a un `fixed_encounters` si es un jefe de una sola vez. `tests/test_coherence.py` falla si ninguna tabla la usa.
4. **Botín y despiece**: `loot` (objeto, probabilidad, cantidad), `gold` y `harvest` (lo que da desollarla, pide cuchillo). Los objetos tienen que existir (`content/INDEX.md`). Un jefe lleva `boss: true` y `pattern` (placa, ataque pesado que avisa); mira `ash_collector` y `beacon_warden`.
5. **Mídela**: `.venv\Scripts\oath simulate --level <rango>` con el rango donde aparece; las clases deben poder ganar sin que sea un paseo ni una pared. Un jefe también se mira con `oath balance --quick`.
6. **Retrato**: el prompt ya está en `images/portrait.prompt.md` (estilo gouache común). Si Josue aporta la imagen, skill `new-image`; el bestiario la muestra sola.
7. **Cierre**: `.venv\Scripts\oath validate`, `.venv\Scripts\python -m pytest tests/test_content.py tests/test_coherence.py -q`, bestiario en `planning/bestiarium.md` si es una criatura nueva de diseño, CHANGELOG y commit (skill `release`).

Lista de cierre: es y en · sin `TODO(new)` · aparece en algún lugar · botín con ids reales · `oath simulate` revisado · prompt del retrato listo.
