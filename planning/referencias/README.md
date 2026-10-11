# Referencias

Documentos de diseño externos de los que salen muchas ideas de `planning/`. Son **propuestas**, no decisiones: las cifras de balance, los nombres y el alcance hay que validarlos contra lo que ya existe en Oathforge.

| PDF | Qué es |
|---|---|
| [gdd-aetherfall-chronicles.pdf](gdd-aetherfall-chronicles.pdf) | *Aetherfall Chronicles*, documento de diseño ampliado (v1.0, oct. 2026, 34 págs.): mundo, clases, combate, oficios, economía, facciones, tabernas, DM con IA, mundo vivo, misiones, multijugador, arquitectura, costes, MVP y roadmap. Incluye un banco de 84 ideas. |
| [guia-recursos-audiovisuales.pdf](guia-recursos-audiovisuales.pdf) | Guía de recursos audiovisuales gratuitos (oct. 2026, 12 págs.): música, voces, retratos, mapas, efectos, cómo enviarlo por Telegram, catálogo de activos y licencias. |

## Dónde se recoge cada capítulo

### GDD

| Capítulo | Archivo de planning |
|---|---|
| §1 Visión, §17 MVP y roadmap, §19 Riesgos, §20 Recomendación final | [roadmap.md](../roadmap.md) |
| §2 Experiencia en Telegram | [interfaz-telegram.md](../interfaz-telegram.md), [multijugador.md](../multijugador.md) |
| §3 Mundo y exploración, §11 Mundo vivo, §12 Misiones | [mundo-y-misiones.md](../mundo-y-misiones.md) |
| §4 Personajes y progresión | [clases.md](../clases.md), [progresion.md](../progresion.md) |
| §5 Combate, PvE y PvP | [combate.md](../combate.md), [multijugador.md](../multijugador.md) |
| §6 Profesiones, §7 Economía | [comercio.md](../comercio.md) |
| §8 Facciones y política, §9 Tabernas y rumores | [mundo-y-misiones.md](../mundo-y-misiones.md) |
| §10 DM artificial, §16 Costes de IA | [ia-y-narracion.md](../ia-y-narracion.md) |
| §13 Multijugador | [multijugador.md](../multijugador.md) |
| §14 Banco de 84 ideas | repartidas por tema; las más concretas, en [`TODO.md`](../../TODO.md) |
| §15 Arquitectura técnica | Ya cubierta por el código (ver `README.md` raíz); las ideas de idempotencia, en [combate.md](../combate.md) y [comercio.md](../comercio.md) |

### Guía audiovisual

Toda en [audiovisual.md](../audiovisual.md).

## Diferencias con lo que ya está decidido

El GDD se escribió como visión general y no siempre coincide con Oathforge:

- **Clases**: el GDD habla de *Clérigo*; nosotros tenemos **Sacerdote** con especializaciones propias (Vida, Luz, Guerra, Tumba). Del Guerrero propone Berserker, Maestro de Armas, Centinela y Gladiador; las nuestras son Campeón, Maestro de Batalla, Guardián y Berserker.
- **Niveles**: el GDD propone 1–20; hoy el máximo es **5**.
- **Habilidades**: el GDD propone 0–100 con 5 rangos; hoy el rango es **0–3**.
- **Facciones**: el GDD propone 8; hoy hay **2** (Pacto de Plata y Sindicato Carmesí), equivalentes a *The Silver Covenant* y *The Crimson Syndicate*.
- **Regiones**: el GDD propone 7 regiones; hoy Aetherfall tiene Crownreach, el Camino del Viejo Rey, el Bosque de los Susurros (≈ Thornwood) y la Cripta Hundida.
- **Proveedor de IA**: el GDD sugiere un adaptador multiproveedor; el proyecto usa **Gemini** y no se cambia sin que Josue lo pida.
