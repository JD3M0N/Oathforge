---
name: release
description: Cerrar una versión de Oathforge: subir la versión, escribir el CHANGELOG, actualizar iter.md, hacer el commit vX.Y.Z y preparar el anuncio en inglés y su traducción al español. Úsala cuando Josue pida cerrar, versionar, commitear o anunciar un cambio.
---

# Cerrar una versión

Se trabaja en `josue-development` (`git branch --show-current`). Nunca se hace commit en `main`; a `main` solo se lleva trabajo cuando Josue lo pide, y la CI tiene que estar en verde.

1. **Pruebas**: `.venv\Scripts\python -m pytest -q`, `.venv\Scripts\python -m ruff check .`, `.venv\Scripts\lint-imports` y `.venv\Scripts\pyright`. Si tocaste `content/`, `.venv\Scripts\oath validate`. Si no pasan, no se cierra.
2. **Versión**: solo en `oathforge/__init__.py`. Parche para arreglos y cambios pequeños, menor para una feature grande; `1.0.0` está reservado.
3. **CHANGELOG.md**: una entrada nueva arriba (`## [X.Y.Z] - AAAA-MM-DD`) con una frase de resumen y las secciones Añadido / Cambiado / Arreglado / Eliminado que haga falta. Lee solo las primeras entradas para copiar el tono.
4. **Planning**: una fila en `planning/iter.md` si cambia el plan; el **Estado actual** del resumen latino del tema (`planning/structura.md`, `ordines.md`…) si implementaste o decidiste algo. `README.md` raíz no se toca.
5. **Commit**: `git add` de lo que toca y asunto `vX.Y.Z: resumen corto`; el cuerpo repite la lista del CHANGELOG. Sin `Co-Authored-By` ni atribución a Claude. El hook de pre-commit comprueba la versión, la entrada y el asunto; si falla, arréglalo y haz un commit nuevo (no `--no-verify`). Un commit que solo formatea va a `.git-blame-ignore-revs`.
6. **Anuncio** (si la versión es para jugadores): `planning/releases/X.Y.Z.md` con dos borradores, el inglés primero y el español como su traducción, en el formato de los canales [inglés](https://t.me/OathForge) y [español](https://t.me/OathForge_es): título `🛡 Oathforge vX.Y.Z: …`, una frase de apertura, bloques con emoji y viñetas, y un cierre. Copia el formato de `planning/releases/0.9.1.md`. Márcalos «borrador, no enviado»: publicar en los canales lo hace Josue.
7. **Tras un merge a `main`** (solo si Josue lo pide): `/graphify . --update`.

Lista de cierre: suite, ruff, imports y pyright en verde · versión subida · CHANGELOG · `iter.md` · asunto `vX.Y.Z: …` sin atribución · anuncio en es y en si procede.
