# content/ — reglas al tocar contenido

- **Busca en `content/INDEX.md`** (una línea por id con su archivo) antes de abrir un YAML grande (`class_specializations`, `quests`, `classes`, `items`…). Lee por rangos.
- **Ids en inglés y ASCII** (`[a-z0-9_]`), únicos en su tipo. Las carpetas y los archivos, igual.
- **Todo texto visible lleva `{es: …, en: …}`** con los mismos marcadores (`{monster}`, `{loot}`…) en los dos idiomas.
- **El mundo es una carpeta por nodo**: `world/<continente>/<zona>/<lugar>/place.yaml`. El id del lugar es el nombre de su carpeta.
- **Imágenes**: van en una carpeta `images/` dentro de su nodo, su clase (`classes/<id>/images/`) o su monstruo (`monsters/<id>/images/`), con `media.yaml` (créditos y licencia) y `<nombre>.prompt.md` al lado de cada archivo. `.night` y `.male`/`.female` en el nombre marcan las variantes.
- **Respaldos de IA** (`fallbacks/`): 12 textos distintos por clave e idioma, sin modificadores de formato y solo con los marcadores permitidos.
- **No toques ni leas `officina/`**: es el laboratorio de imágenes de Josue.
- Al editar un `.yaml` aquí, un hook ejecuta `oath validate` y reescribe `INDEX.md`. Si devuelve errores, arréglalos antes de seguir. Antes del commit: `.venv\Scripts\python -m pytest tests/test_content.py -q`.
- Lo que valida cada campo está en `oathforge/content/schemas.py`, y las referencias cruzadas, en `validate_references` de `oathforge/content/loader.py`.
