# Planning

Puntos de partida para las ideas del juego. No es documentación del código (eso está en el `README.md` raíz) ni un registro de cambios (eso es `CHANGELOG.md`): aquí se piensa **qué** queremos construir y **por qué**.

| Archivo | Tema |
|---|---|
| [roadmap.md](roadmap.md) | Qué entra en cada versión |
| [clases.md](clases.md) | Clases, habilidades, especializaciones y clases futuras |
| [combate.md](combate.md) | Sistema de batalla: qué hay y hacia dónde va |
| [comercio.md](comercio.md) | Tiendas, precios, economía y mercado entre jugadores |
| [progresion.md](progresion.md) | Niveles, habilidades por uso, equipo |
| [mundo-y-misiones.md](mundo-y-misiones.md) | Lugares, misiones, facciones, eventos del mundo |
| [bestiario.md](bestiario.md) | Criaturas, fichas que se desbloquean y cómo ampliarlo |
| [multijugador.md](multijugador.md) | Grupos, combate cooperativo, PvP |
| [ia-y-narracion.md](ia-y-narracion.md) | Qué hace Gemini y qué nunca debe hacer |
| [interfaz-telegram.md](interfaz-telegram.md) | Cómo se ve el juego en el chat: escenas, botones, comandos, sesiones |
| [audiovisual.md](audiovisual.md) | Imágenes, música, voces, mapas, stickers y licencias |
| [referencias/](referencias/README.md) | PDFs de diseño (GDD *Aetherfall Chronicles* y guía audiovisual) y dónde se recoge cada capítulo |

## Cómo usarla

- Cada archivo tiene tres partes: **Estado actual** (lo que ya existe), **Ideas** (lo que podríamos hacer) y **Preguntas abiertas** (lo que hay que decidir).
- Cuando una idea se implementa, pásala a *Estado actual* y anota la versión (`v0.2.0`).
- Las ideas que vienen de los PDF citan su sección (`GDD §5.5`, `Guía §3`). Son propuestas: lo ya decidido en Oathforge manda (ver las diferencias en [referencias/](referencias/README.md)).
- Las ideas de los testers llegan por `TODO-<nombre>.md`; las que se aceptan se copian aquí. La lista de tareas general está en [`TODO.md`](../TODO.md).
- Para ver cómo se juega de verdad, mira `artifacts/` en local (conversaciones, combates y llamadas a la IA; no se sube a GitHub).
