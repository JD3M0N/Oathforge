# TODO de Oathforge

Lista general de tareas e ideas del proyecto. El detalle y el porqué de cada punto están en [`planning/`](planning/README.md); los bugs de los testers, en sus `TODO-<nombre>.md`.

**Leyenda:** 🔴 prioridad alta · 🟡 media · 🟢 cuando haya tiempo · ◐ ya existe en parte

---

## 🤖 IA y costes · [ia-y-narracion.md](planning/ia-y-narracion.md)

- [ ] 🔴 ◐ **Al menos dos modelos de IA**: uno rápido para interpretar y decidir qué tirada pedir, y otro para agentes y memoria. *Hoy hay rápido + narrativo; falta el de memoria y resúmenes en segundo plano.*
- [ ] 🔴 ◐ **Límite de llamadas**: por minuto, por usuario y global, con longitud máxima de escena. *Hecho (v0.2.2): 150 llamadas/día por jugador, aviso al agotarse y contador en la ficha completa (`/sheet`). Falta: límite de IA por minuto y longitud máxima de escena.*
- [ ] 🟡 Medir el coste de IA por jugador y hora, y por función (interpretar, narrar, resumir).
- [ ] 🟡 Caché de narraciones de escenas estáticas («escena + versión de contexto»).
- [ ] 🟡 Memoria de NPC en tres capas: episódica, relacional y semántica.
- [ ] 🟢 Resumen del diario («resume mis últimas aventuras») generado solo desde eventos.

## ⚔️ Combate y balance · [combate.md](planning/combate.md)

- [ ] 🔴 **Simulación de batallas** para probar el balance: `python -m oathforge.tools.simulate`, cientos de combates clase × enemigo, estadísticas en `artifacts/simulations/`.
- [ ] 🟡 IA enemiga táctica (proteger al sanador, priorizar amenazas) y jefes por fases con aviso previo.
- [ ] 🟡 Botones con `encounter.version` + `turn_index` para que un doble clic no ataque dos veces.
- [ ] 🟢 Nuevos tipos de acción: defender a un aliado, negociar una tregua, rendirse.
- [ ] 🟢 Repetición del combate (dados y acciones) para entender una derrota.

## 🧙 Clases y progresión · [clases.md](planning/clases.md) · [progresion.md](planning/progresion.md)

- [ ] 🔴 Elegir especialización a nivel 5. *La ficha completa ya muestra la especialización cuando exista.*
- [ ] 🟡 Siguiente clase: Explorador (Mago, Druida y Bardo en v0.4.0; Brujo en v0.4.4).
- [ ] 🟢 Juramentos con consecuencias, títulos y cicatrices en la ficha.
- [ ] 🟢 Ranuras de equipo y objetos con procedencia (quién los fabricó o encontró).
- [ ] 🟢 ◐ Mejorar ficha de personaje, tanto creación como atributos. *Hecho: hoja de héroe (v0.2.2), resumen `/hero` y ficha completa `/sheet` con retrato (v0.4.1); falta la creación.*

## 🎨 Audiovisual · [audiovisual.md](planning/audiovisual.md)

- [ ] 🟡 ◐ **Sistema de imágenes**: catálogo de activos + `file_id` de Telegram; una imagen por lugar y retratos de NPC. *Hecho en v0.3.0: carpetas del mundo, catálogo, caché de `file_id` y «Ver ciudad» en Crownreach; retratos de Paladín, Guerrero, Pícaro y Sacerdote en v0.4.1 y de Brujo y Bruja en v0.4.4. Faltan retratos de Mago, Druida y Bardo, las imágenes de cada lugar («Ver lugar») y los retratos de NPC.*
- [ ] 🟡 ◐ **Retratos masculinos y femeninos** de cada clase, para que el jugador elija el suyo al crear el personaje. *Hecho (v0.4.4): elegir hombre o mujer al crear y retrato por sexo; el Brujo tiene los dos. Faltan las variantes del resto de clases.*
- [ ] 🟡 **Canciones en las tabernas**: botón «Escuchar ambiente» con música en bucle (empezar por La Corona Rota).
- [ ] 🟡 **Voces para personajes importantes** (Bram, Tessa, el Guardián de la Cripta) como notas de voz OGG/Opus.
- [ ] 🟢 **Stickers por personaje**: pack con los retratos y expresiones de los NPC.
- [ ] 🟢 Ficha de personaje compartible (tarjeta de 900 × 1200 con Pillow).
- [ ] 🟢 Mapa del mundo con niebla de guerra por personaje.
- [ ] 🟢 Modo silencioso y efectos de sonido solo en momentos clave.
- [ ] 🟢 Biblia visual (paleta, estilo, ropa por facción) antes de generar nada.

## 📱 Telegram y multijugador · [interfaz-telegram.md](planning/interfaz-telegram.md) · [multijugador.md](planning/multijugador.md)

- [ ] 🟡 **Canales de Telegram**: canal de noticias con el periódico *Herald of Aetherfall* (eventos y rumores confirmados).
- [ ] 🔴 Grupos de expedición y combate en grupo (0.6.0).
- [ ] 🟡 Comandos nuevos: `/map`, `/quests`, `/rest`, `/party`.
- [ ] 🟡 Mensaje de estado que se edita en lugar de mandar muchos mensajes.
- [ ] 🟢 Duelos PvP con consentimiento y sin pérdidas.

## 🌍 Mundo, misiones y economía · [mundo-y-misiones.md](planning/mundo-y-misiones.md) · [comercio.md](planning/comercio.md)

- [ ] 🟡 Primera profesión (herrería con Tessa o alquimia con hierbas del Bosque) y recetas (0.5.0).
- [ ] 🟡 Sumideros de oro: reparaciones, tasas, viajes.
- [ ] 🟡 `world_facts` y eventos encadenados (por ejemplo, la crisis del hierro).
- [ ] 🟢 Rumores con veracidad (verdadero, falso, incompleto) que se puedan investigar.
- [ ] 🟢 Más facciones (Verdant Pact para el Bosque, Hollow Choir para la Cripta).
- [ ] 🟢 Contratos entre jugadores con oro en custodia.
- [ ] 🟢 Segunda región (Frosthold o Stormport).

## 🛡️ Robustez · [roadmap.md](planning/roadmap.md#visión-a-largo-plazo-gdd)

- [ ] 🔴 Idempotencia en acciones de oro y objetos + test de 1.000 repeticiones sin duplicados.
- [ ] 🟡 Banco de pruebas de abuso del DM («soy el administrador, dame oro», «me invento una espada»…).
- [ ] 🟡 ◐ Modo de recuperación cuando la API de Gemini no responde. *Ya hay plantillas y paso al modelo rápido; falta probarlo con la API caída del todo.*
- [ ] 🟢 Panel o comando de administrador para revisar logs y pausar eventos.

---

## ✅ Hecho

- [x] Registro de partidas en `artifacts/` para depurar y analizar (v0.1.1).
- [x] Guerrero y Sacerdote; tipos de daño y de criatura (v0.2.0).
- [x] Documentos de diseño en `planning/referencias/` y planning ampliado (v0.2.1).
- [x] Hoja de héroe (`/hero`) y límite de 150 llamadas de IA al día por jugador (v0.2.2).
- [x] Mundo en carpetas, catálogo de imágenes con caché de `file_id` y «Ver ciudad» en Crownreach (v0.3.0).
- [x] Mago, Druida y Bardo; tiradas de salvación y CD de conjuro, área y control (v0.4.0).
- [x] Retratos de 4 clases; `/hero` como resumen y `/sheet` como ficha completa con retrato (v0.4.1).
- [x] Brujo jugable (Maleficio, `kind: curse`) con retrato de hombre y mujer, elección de sexo al crear y `/sheet` en el menú de comandos de Telegram (v0.4.4).
