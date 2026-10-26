---
name: new-image
description: Integrar una imagen nueva en Oathforge (prompt, preparación con tools/prepare_image.py, media.yaml con créditos y .prompt.md). Úsala cuando Josue aporte o pida una imagen de un lugar, criatura, clase o zona.
---

# Nueva imagen

Las pruebas viven en `content/officina/` (el laboratorio de Josue: no lo leas ni lo toques salvo que lo pida). Solo se integra una imagen aprobada.

1. **Prompt**: `oath new …` ya escribe `images/<nombre>.prompt.md` con el estilo común (`content/_templates/prompts/style.md`, de `planning/ars.md` §5). Orden: qué es y desde dónde se ve → detalles → luz en una frase → estilo. Sin nombres ni texto dentro de la imagen. La de noche sale de la de día aprobada, cambiando solo la frase de luz.
2. **Prepara el archivo**: `.venv\Scripts\python tools/prepare_image.py <original> <destino> --kind <panorama|portrait|icon|sticker>` (1280×720, 768×1024, 128×128, 512×512; recorta, escala y quita metadatos). `--trim-bottom N` quita una franja inferior con firmas o texto falsos de la IA.
3. **Dónde va**: en `images/` del nodo — `world/<cont>/<zona>/images/`, `<lugar>/images/`, `classes/<clase>/images/` o `monsters/<id>/images/`. Nombres: `panorama.jpg`, `panorama.night.jpg`, `portrait.jpg`, `portrait.male.jpg`, `portrait.female.jpg`. `.night`, `.male` y `.female` marcan la variante; el catálogo (`oathforge/content/media.py`) las lee solo.
4. **Créditos**: la entrada del archivo en `images/media.yaml` (`author`, `source`, `license`, `notes` con el tamaño original y el recorte). No inventes datos que no conozcas.
5. **Cierra el `.prompt.md`**: herramienta, fecha, tamaño original y el prompt realmente usado (borra la línea que dice que aún no hay imagen).
6. **Comprueba**: `.venv\Scripts\python -m pytest tests/test_content.py -q` (exige `media.yaml` y `.prompt.md` junto a cada imagen) y mira la imagen en el bot (`oath tgtest`: «🖼️ Ver lugar», bestiario, retrato en la ficha). Solo versiones de entrega optimizadas van a git.
7. CHANGELOG y commit (skill `release`).

Lista de cierre: tamaño de entrega · variante de noche con su prompt · entrada en `media.yaml` · `.prompt.md` completo · se ve en el bot.
