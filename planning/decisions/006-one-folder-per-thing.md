# ADR 006 — Una carpeta por cosa en content/

**Estado:** vigente

## Contexto

Una clase, un monstruo o una ciudad estaban repartidos en cinco o seis YAML planos.

## Decisión

Cada entidad tiene su carpeta con su ficha, imágenes y prompts (`classes/<clase>/`, `monsters/<id>/`, `items/<tipo>/<id>/`, `world/<continente>/<zona>/…`). El cargador es genérico (`load_folder`) y los locales van por dominio.

## Consecuencias

Un archivo no pasa de 800 líneas (`.py`) ni de 40 KB (YAML): `tests/test_sizes.py`. El contenido nuevo se crea con `oath new` y su skill. Detalle: `structura.md`.
