---
name: new-city
description: Crear una ciudad o zona nueva de Oathforge entera (carpeta de zona, grafo de lugares, PNJ con sus 12 respaldos por idioma, tiendas, misiones, monstruos, imágenes de día y noche con su prompt, balance por rango y recorrido de prueba). Úsala cuando Josue pida una ciudad, una zona, una región, una mazmorra o varios lugares nuevos.
---

# Nueva ciudad (o zona)

Una ciudad es una carpeta con todo dentro: `content/world/<continente>/<zona>/`. Lee antes `content/world/README.md` y, para el tono, la zona más parecida (`crownreach`, `greyforge_vale`, `thornwood`).

1. **Zona**: `.venv\Scripts\oath new zone <id> --continent terra_coronata --kind <city|wilds|dungeon> --name "…" --desc "…"`. Crea `zone.yaml` y `images/` con los prompts de la panorámica de día y de noche.
2. **Lugares**: uno por sitio (plaza, taberna, puestos…) con `.venv\Scripts\oath new place <id> --zone <zona> [--to <lugar>]`. El primero de la ciudad lleva `hub: true` (la plaza: única salida de la ciudad); los siguientes se conectan al hub por defecto y `oath new` añade la vuelta en el otro lugar. Después añade las rutas con el resto del mundo (con los mismos minutos, yardas y peligro en los dos sentidos) y, según el sitio: `stations`, `teaches`, `home`, `rest_cost`, `healer`, `hunting`, `encounters`, `gathering`.
3. **PNJ** (skill `new-npc`): un `oath new npc` por personaje, con `--place` si no está en el hub. Cada uno necesita sus 12 respaldos de diálogo distintos por idioma en `dialogue.fallback.yaml`.
4. **Tiendas**: en el `shop` del `npc.yaml` del vendedor; los objetos que venda tienen que existir (skill `new-item`).
5. **Misiones** (skill `new-quest`): `oath new quest <id> --zone <zona> --giver <pnj>`. Encadénalas con `after` y comprueba que el diario las ordena bien.
6. **Monstruos** (skill `new-monster`): los de sus alrededores, en `encounters` de los lugares salvajes.
7. **Imágenes**: panorámica de día y de noche de la zona (y de los lugares que quieras) con el prompt ya escrito. La de noche sale de la de día aprobada. Skill `new-image` cuando haya imagen.
8. **Balance del rango de niveles**: `.venv\Scripts\oath simulate --level <rango>` y `.venv\Scripts\oath balance --quick`; el equipo y la XP de la zona tienen que encajar con la progresión de `planning/roadmap_balance.md` (solo la fase que toca).
9. **Pruebas**: `.venv\Scripts\oath validate`; `.venv\Scripts\python -m pytest tests/test_content.py tests/test_coherence.py -q` (rutas de ida y vuelta, todo PNJ colocado, todo monstruo en un lugar); añade las casillas de la zona a `tests/features.md` y recórrela con `.venv\Scripts\oath tgtest send "/start"` (en Git Bash, `MSYS_NO_PATHCONV=1`).
10. **Cierre**: actualiza `planning/mundus.md` (Estado actual), CHANGELOG, `iter.md` si cambia el plan, y commit (skill `release`). Tras el merge a `main`, `/graphify . --update`.

Lista de cierre: zona con hub · rutas de ida y vuelta · PNJ con 12 respaldos en es y en · tiendas con ids reales · misiones encadenadas · monstruos colocados · imágenes de día y noche con prompt · `oath simulate` revisado · `tests/features.md` ampliado · recorrido con `tgtest`.
