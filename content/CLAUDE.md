# content/ — reglas al tocar contenido

- **Busca en `content/INDEX.md`** (una línea por id con su archivo) antes de abrir una ficha: dice en qué archivo vive cada id. Lee por rangos los archivos grandes.
- **Ids en inglés y ASCII** (`[a-z0-9_]`), únicos en su tipo. Las carpetas y los archivos, igual.
- **Todo texto visible lleva `{es: …, en: …}`** con los mismos marcadores (`{monster}`, `{loot}`…) en los dos idiomas.
- **Una carpeta por cosa** (el id es el nombre de la carpeta o del archivo; el esquema de cada una está en su `README.md`):
  - `classes/<clase>/class.yaml` + `specializations.yaml` (sus ramas) + `images/`
  - `monsters/<id>/monster.yaml` + `images/`
  - `items/<tipo>/<id>/item.yaml` y `items/<tipo>/recipes.yaml` (las recetas de lo que produce ese tipo)
  - `world/<continente>/<zona>/<lugar>/place.yaml`, `npcs/<pnj>/npc.yaml` (+ `dialogue.fallback.yaml`) y `quests/<misión>.yaml`: una ciudad es una carpeta con todo dentro
  - Las carpetas que empiezan por `_` (plantillas) se ignoran. `order: N` al final de una ficha fija su posición en los menús (clases, criaturas, PNJ).
  - Para crear una, copia una ficha parecida y cambia el id; un id repetido o un error de esquema nombra el archivo.
- **Imágenes**: van en una carpeta `images/` dentro de su nodo, su clase (`classes/<id>/images/`) o su monstruo (`monsters/<id>/images/`), con `media.yaml` (créditos y licencia) y `<nombre>.prompt.md` al lado de cada archivo. `.night` y `.male`/`.female` en el nombre marcan las variantes.
- **Respaldos de IA** (`fallbacks/`): 12 textos distintos por clave e idioma, sin modificadores de formato y solo con los marcadores permitidos.
- **No toques ni leas `officina/`**: es el laboratorio de imágenes de Josue.
- Al editar un `.yaml` aquí, un hook ejecuta `oath validate` y reescribe `INDEX.md`. Si devuelve errores, arréglalos antes de seguir. Antes del commit: `.venv\Scripts\python -m pytest tests/test_content.py -q`.
- Lo que valida cada campo está en `oathforge/content/schemas/<dominio>.py`, y las referencias cruzadas, en `oathforge/content/validation/<dominio>.py` (`validate_references` las corre todas).
