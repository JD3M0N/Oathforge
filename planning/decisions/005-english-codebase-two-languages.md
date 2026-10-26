# ADR 005 — Base en inglés, texto visible en es y en

**Estado:** vigente

## Contexto

El juego se juega en español e inglés, y el código lo tocan agentes y personas.

## Decisión

Ids, variables, archivos, claves y subcomandos van en inglés; los ids y rutas de `content/` son ASCII en minúsculas. Todo texto que ve el jugador está en los dos idiomas: `{es, en}` en el contenido y `i18n/locales/{es,en}/<dominio>.yaml` en la interfaz, con los mismos marcadores.

## Consecuencias

`tests/test_content.py` lo comprueba. El diseño de `planning/` sigue en español, con nombres latinos.
