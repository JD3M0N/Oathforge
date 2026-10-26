---
name: new-npc
description: Crear un PNJ nuevo de Oathforge con ficha en es/en, horario, persona para Gemini, tienda opcional y sus 12 respaldos de diálogo por idioma. Úsala cuando Josue pida un personaje, un PNJ, un tendero o un maestro de oficio.
---

# Nuevo PNJ

1. **Ficha**: `.venv\Scripts\oath new npc <id> --zone <zona> [--place <lugar>] --name "…"`. Crea `content/world/<continente>/<zona>/npcs/<id>/npc.yaml` y `dialogue.fallback.yaml`. Por defecto está en el hub de la zona; con `--place`, en otro lugar.
2. **Horario**: `schedule: {day: <lugar>, night: <lugar>}` con lugares que existen (de noche suele estar en la taberna, como Bram o Tessa).
3. **Persona para Gemini**: `persona`, `goals`, `secrets` y `knowledge` van en inglés y dicen cómo habla, qué quiere y qué sabe. Gemini narra lo que el motor decide: no le des poder de dar oro, objetos ni confianza en la ficha. Coherencia con el mundo: lee `content/world/guide.yaml` y los PNJ de la zona.
4. **Textos visibles**: `name`, `title`, `greeting` (y `greeting_return` si cambia tras una misión) en es y en. No inventes rasgos permanentes del rostro sin que Josue los apruebe (`planning/ars.md`, «NPC»).
5. **12 respaldos**: `dialogue.fallback.yaml` lleva 12 textos distintos por idioma, sin modificadores de formato y solo con `{npc}` y `{name}`. Se usan cuando Gemini falla o se agota el presupuesto.
6. **Opcional**: `shop: {items: […], buys: true}` (los objetos tienen que existir), `faction`, `steal_gold`, `passive_perception`, `order`. Si enseña un oficio, el `teaches` va en su lugar, no en la ficha.
7. **Cierre**: `.venv\Scripts\oath validate`, `.venv\Scripts\python -m pytest tests/test_content.py tests/test_coherence.py -q` (todo PNJ tiene horario y lugar), habla con él con `.venv\Scripts\oath tgtest`, CHANGELOG y commit (skill `release`).

Lista de cierre: es y en · sin `TODO(new)` · horario con lugares reales · persona en inglés · 12 respaldos distintos por idioma · tienda con ids reales.
