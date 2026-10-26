---
name: new-item
description: Crear un objeto nuevo de Oathforge (arma, armadura, escudo, consumible, herramienta, material, baratija u objeto de misión) con su ficha en es/en, nivel y precio, procedencia, prompt del icono y entrada en el CHANGELOG. Úsala cuando Josue pida un objeto, un arma, una poción, un material…
---

# Nuevo objeto

1. **Crea la ficha**: `.venv\Scripts\oath new item <id> --category <weapon|armor|shield|consumable|tool|quest|material|trinket> --name "English name" --desc "English description"`. Hace `content/items/<categoría>/<id>/item.yaml` con la plantilla, y `images/icon.prompt.md` (+ `media.yaml`) con el prompt del icono ya escrito. El id es inglés, ASCII y en minúsculas. Un `blueprint` se escribe a mano (necesita una receta especial que enseñar).
2. **Escribe los textos** en `es` y `en` (los dos, siempre) y quita cada `TODO(new)`. Elige un emoji propio para `icon` salvo que el del tipo valga.
3. **Nivel y precio**: busca objetos parecidos en `content/INDEX.md` y ábrelos para comparar. En equipo, `min_level` y `value` crecen con el nivel (un test lo comprueba dentro de un mismo tipo y ranura). Para armas y armaduras mira el rival del rango con `.venv\Scripts\oath balance --quick`.
4. **De dónde sale** (si no, `tests/test_coherence.py` falla): una `shop` de un `npc.yaml`, el `loot` o `harvest` de una criatura, una receta en `content/items/<categoría>/recipes.yaml` (disciplina, rango, ingredientes → productos), un `gathering` de un lugar, una recompensa de misión (`give_item`) o el equipo inicial de una clase.
5. **Efectos** si los lleva: `heal`/`effects` en consumibles, `combat` en bombas y pergaminos, `tool` en herramientas de recolección. El esquema está en `oathforge/content/schemas/items.py`.
6. **Imagen del icono**: el catálogo todavía no lee iconos de objetos. Deja el prompt; si Josue aporta la imagen, usa la skill `new-image`.
7. **Cierre**: `.venv\Scripts\oath validate` (el hook ya lo hace al editar), `.venv\Scripts\python -m pytest tests/test_content.py tests/test_coherence.py tests/test_new.py -q`, entrada en `CHANGELOG.md`, versión de parche y commit `vX.Y.Z: …` (skill `release`).

Lista de cierre: ficha en es y en · sin `TODO(new)` · precio comparado · se consigue de alguna forma · `INDEX.md` al día (lo reescribe el hook) · tests de contenido en verde.
