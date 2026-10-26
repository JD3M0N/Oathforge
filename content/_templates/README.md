# _templates/ — plantillas para crear contenido

El cargador ignora las carpetas que empiezan por `_`. Cada plantilla refleja lo que crea: `oath new <tipo> <id> …` copia
`_templates/<tipo>/` a su sitio, cambia los marcadores `__x__` y escribe los prompts de imagen con el estilo de
`prompts/style.md`.

| Quiero crear… | Comando | Se crea en | Skill |
|---|---|---|---|
| un objeto | `oath new item <id> --category weapon` | `items/<categoría>/<id>/item.yaml` | `new-item` |
| una criatura | `oath new monster <id>` | `monsters/<id>/monster.yaml` + `images/` | `new-monster` |
| un PNJ | `oath new npc <id> --zone <zona>` | `world/<cont>/<zona>/npcs/<id>/` | `new-npc` |
| una misión | `oath new quest <id> --zone <zona> [--giver <pnj>]` | `world/<cont>/<zona>/quests/<id>.yaml` | `new-quest` |
| una zona / ciudad | `oath new zone <id> [--continent terra_coronata] [--kind city]` | `world/<cont>/<id>/` | `new-city` |
| un lugar | `oath new place <id> --zone <zona> [--to <lugar>]` | `world/<cont>/<zona>/<id>/` | `new-city` |
| una clase | `oath new class <id>` | `classes/<id>/` | `new-class` |

Opciones comunes: `--name "English name"` y `--desc "English description"` rellenan la ficha y el prompt de imagen.

- Lo que queda por escribir lleva la marca `TODO(new)`; `tests/test_content.py` falla mientras quede alguna en `content/`.
- Cada plantilla es una ficha válida: el bot arranca con ella tal cual. Los comentarios dicen qué campos hay y sus rangos;
  bórralos si no los usas.
- `prompts/style.md` es el estilo común de las imágenes (sale de `planning/ars.md` §5); `prompts/prompt.md` y
  `prompts/night.md`, el esqueleto de cada `<nombre>.prompt.md`.
