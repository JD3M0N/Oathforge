# Officina — laboratorio de imágenes

Espacio para probar imágenes y prompts antes de meterlos en el juego. **El bot no lee esta carpeta** (el catálogo solo recorre `world/`, `classes/` y `monsters/`) y **git solo guarda este README**: lo demás queda en tu equipo.

## Cómo usarla

Una subcarpeta por prueba y, por cada imagen, su prompt al lado con el mismo nombre:

```text
content/officina/
  estilos/                 # p. ej. comparar los estilos A–E de planning/ars.md
    01-crownreach-a.jpg
    01-crownreach-a.prompt.md
  bram/
    bram-neutral-v3.png
    bram-neutral-v3.prompt.md
```

No crees una subcarpeta `images/` aquí: esa convención es la de los activos integrados.

## Plantilla de `<nombre>.prompt.md`

```markdown
# <nombre>

- Herramienta / modelo: Leonardo AI, <modelo y versión>
- Fecha: AAAA-MM-DD
- Proporción y tamaño: 16:9 1344×768 / 3:4 …
- Semilla: <si existe>
- Referencia usada: <imagen o ninguna>
- Estado: borrador / candidata / descartada / aprobada

## Prompt

<prompt positivo>

## Negativo

<si el modelo tiene campo negativo>

## Notas

<qué funcionó, qué cambiar en la siguiente versión>
```

## Cuando una imagen se aprueba

1. Prepara la versión de entrega con `tools/prepare_image.py` (1280×720 para escenas, 768×1024 para retratos).
2. Cópiala a su sitio, por ejemplo `content/world/.../<lugar>/images/cover.jpg` o `content/monsters/<criatura>/images/portrait.jpg`, junto con su `.prompt.md`.
3. Añade su entrada en el `media.yaml` de esa carpeta (autor, herramienta, licencia).
4. `.venv\Scripts\python -m pytest tests/test_content.py` comprueba que no falta nada.

Formatos, estilos y flujo completo: [planning/ars.md](../../planning/ars.md) §14.
