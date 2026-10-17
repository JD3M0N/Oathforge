# Oathforge

RPG narrativo multijugador para Telegram, ambientado en **Aetherfall**. Un Dungeon Master con IA (Gemini) narra; un motor d20 determinista decide.

> Regla de oro: **la IA nunca decide resultados.** Convierte el texto libre en una intención estructurada; el motor la valida, tira los dados y guarda el resultado; después la IA narra *exactamente* lo que pasó.

## Estado: beta en solitario

Qué cambió en cada versión está en [CHANGELOG.md](CHANGELOG.md); qué viene, en [planning/iter.md](planning/iter.md). Aquí solo la idea del proyecto.

- Creación de personaje: hombre o mujer, 4 linajes, 12 trasfondos (o uno propio revisado por la IA), 8 clases (Paladín, Pícaro, Guerrero, Sacerdote, Mago, Druida, Bardo, Brujo) con habilidades hasta nivel 5, atributos por compra de puntos (27, como en D&D) y retrato por clase y sexo.
- Crownreach (plaza, taberna La Corona Rota, mercado, Barrio de Oficios, Capilla del Alba), el Camino del Viejo Rey, el Bosque de los Susurros, el Prado de los Colmillos, la Mina del Paso Viejo, la Arboleda Antigua, el Claro de la Raíz Roja, la Ribera de Silverbrook y la Cripta Hundida.
- Viaje en un toque a cualquier lugar conocido (`/map`), con una tirada de emboscada por viaje y un botón 📜 al objetivo de la misión.
- Actividades de campo que terminan solas aunque estés desconectado: minar, talar, recolectar hierbas y pescar, expediciones largas con emboscada, rastreo y desuello, con 5 maestrías que suben de rango. Se fabrica en 7 oficios (dos activos a la vez: herrería, alquimia, carpintería, peletería, joyería, escribanía e ingeniería) y 2 aficiones (cocina y pesca). Cada actividad termina con una crónica personal escrita por la IA (con presupuesto diario y textos genéricos cuando se agota).
- Tutorial de 10 misiones con la sargenta Vale (hablar, ciudad, tiendas, caza, desuello, recolección, cocina, minería, curación y descanso, y el Viejo Colmillo como jefe), después la misión ramificada «El relicario sellado» y la cripta. Diario con misiones, registro, bestiario, rumores y estadísticas.
- Combate por turnos: iniciativa, acción/acción adicional/movimiento, vanguardia/retaguardia, críticos, ataque furtivo, conjuros, salvaciones, área por filas, PV temporales, estados, objetos del escenario, pergaminos y bombas, e informe de batalla.
- Tipos de daño y de criatura: resistencias, vulnerabilidades e inmunidades (los esqueletos temen el contundente y lo radiante).
- NPC con memoria (Vale, Bram, Mira, Holt, Tessa, Ysolde), confianza, reputación con dos facciones, robos que se recuerdan y tiendas con precios según reputación.
- Rumores del mundo: cuando alguien derrota al guardián, las tabernas lo cuentan a los demás jugadores.
- Consulta dentro del juego: `/rulebook`, `/classes`, `/skill_…`, `/item_…`, `/monster_…`, `/professions`.
- Español e inglés desde el primer día (`/settings`).
- Tablas preparadas para grupos (`parties`, `party_members`, `encounter_participants`); el juego cooperativo es el siguiente paso.

## Puesta en marcha (Windows)

1. **PostgreSQL**
   ```powershell
   winget install PostgreSQL.PostgreSQL.17
   # luego, con la contraseña elegida durante la instalación:
   & "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres oathforge
   & "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres oathforge_test
   ```
2. **Bot de Telegram**: habla con [@BotFather](https://t.me/BotFather), `/newbot`, copia el token.
3. **Clave de Gemini**: <https://aistudio.google.com/apikey>. Sin clave el juego funciona igual, pero sin narración ni acciones libres.
4. **Configuración**
   ```powershell
   copy .env.example .env   # rellena BOT_TOKEN, DATABASE_URL y GEMINI_API_KEY
   py -3.12 -m venv .venv
   .venv\Scripts\pip install -e ".[dev]"
   .venv\Scripts\alembic upgrade head
   ```
5. **Jugar**
   ```powershell
   .venv\Scripts\oath bot
   ```
   Abre tu bot en Telegram y escribe `/start`. `.venv\Scripts\oath help` lista todos los comandos de consola (con el venv activado basta `oath help`; `oathforge` es el nombre largo).

## Tests

```powershell
.venv\Scripts\python -m pytest
```

Usan `TEST_DATABASE_URL` (Postgres) si está disponible; si no, SQLite. La prueba de concurrencia (dos compras simultáneas de la última poción) solo corre con Postgres.

## Arquitectura

```
oathforge/
  engine/     reglas puras: dados, pruebas, combate, progresión (sin E/S, RNG inyectable)
  services/   las ÚNICAS escrituras de estado; transacciones con SELECT … FOR UPDATE + versión
  ai/         cliente Gemini con presupuesto, intérprete de intenciones, narrador, diálogo de NPC
  bot/        handlers de Telegram, teclados y render HTML
  i18n/       locales es/en
  database/   modelos SQLAlchemy y sesión
content/      todo el contenido del juego en YAML validado al arrancar
  world/      mundo → continente → zona → lugar, con images/ y audio/ en cada carpeta
  officina/   laboratorio de imágenes y prompts (fuera del juego y de git, salvo su README)
tools/        utilidades (prepare_image.py: escala y optimiza imágenes)
migrations/   Alembic
```

Flujo de una acción libre:

```
leer contexto (tx corta) → Gemini interpreta → bloquear + validar + resolver (tx) → Gemini narra
```

Nunca se mantiene un bloqueo de fila mientras se espera al modelo.

**Seguridad y robustez**
- El texto del jugador va delimitado como datos (`<player_text>`), nunca dentro de las instrucciones.
- Los ids que propone la IA deben existir en el contexto; si no, la acción pasa a `narrate_only`.
- Las dificultades sugeridas por la IA se limitan a un rango permitido.
- Cada botón lleva un nonce: un doble toque o un menú antiguo no ejecuta la acción dos veces (`action_logs.idempotency_key`).
- Presupuesto diario de IA por usuario y global, comprobado **antes** de cada llamada (`ai_usage`).
- Si la IA falla o se agota el presupuesto, el juego sigue con textos de plantilla.
- Límite de frecuencia por usuario y registro auditable de cada acción.

## Añadir contenido

Todo vive en `content/*.yaml`. Cada texto visible es `{es: ..., en: ...}`. Al arrancar se validan las referencias cruzadas (objetos, lugares, NPC, etapas de misión). Si algo está mal, el bot no arranca y dice qué es. `pytest tests/test_content.py` hace la misma comprobación.

Las misiones son máquinas de estados: `stages`, `actions` (botones o acciones libres con tirada opcional) y `triggers` (p. ej. derrotar a un monstruo). Los efectos disponibles son `give_item`, `take_item`, `gold`, `xp`, `reputation`, `set_flag`, `npc_memory`, `trust`, `damage` y `world_rumor`.

## Versiones, planning y artifacts

- **Versión** en `oathforge/__init__.py`; cambios en [CHANGELOG.md](CHANGELOG.md). Cada commit sube la versión (`0.1.1 → 0.1.2`; `0.2.0` para features grandes) y su asunto empieza por `vX.Y.Z:`.
- **[planning/](planning/README.md)**: [Possibilium](planning/Possibilium.md) (el libro de ideas) y un resumen por tema con nombre latino (`ordines`, `pugna`, `opificia`, `mundus`…); la hoja de ruta es [`iter.md`](planning/iter.md).
- **[AGENTS.md](AGENTS.md)**: cómo trabajar en el repo (invariantes, mapa de módulos, pruebas) gastando pocos tokens.
- **`artifacts/`** (local, no se sube): cada partida queda registrada para depurar y analizar.
  - `conversations/<día>/<telegram_id>.md`: lo que escribe el jugador y lo que responde el bot.
  - `battles/<día>/<id>-<lugar>.md` y `.json`: combates turno a turno con tiradas y resultado.
  - `ai/<día>/…json`: cada llamada a Gemini con prompt, respuesta, modelo, tokens y latencia.
  - `events/<día>.jsonl` (todo en crudo, incluidos los cambios de estado), `errors/<día>.log` y `logs/<día>.log` (avisos).
  - Cada cambio de estado (PV, oro, objetos, misiones, memorias de PNJ, acciones de botón…) aparece también como «⚙️ estado» dentro de la conversación.
  - Se desactiva con `ARTIFACTS_ENABLED=false` en `.env`.
- **Ronda de pruebas limpia:** para el bot y ejecuta `.venv\Scripts\oath reset-players --yes` (sin `--yes` solo muestra qué borraría). Para borrar a un solo jugador, `oath delete-player <nombre|id> --yes`; sin argumentos lista los jugadores.
- **Probar desde Telegram:** `.venv\Scripts\oath tgtest send "/start"` y `tgtest press "Investigar"` juegan con el bot desde una cuenta de prueba (Telethon). Configuración y login en `oathforge/tools/tgtest.py`. En Git Bash, exporta `MSYS_NO_PATHCONV=1` para que `/start` no se convierta en una ruta.
- **Balance:** `.venv\Scripts\oath simulate --level 1-5` lanza 200 combates por clase × enemigo × nivel (sin base de datos ni IA) y guarda la tabla en `artifacts/simulations/` (JSON y CSV). Opciones: `--classes`, `--monsters` (grupos con `+`, p. ej. `bandit+bandit`), `--n`, `--seed`, `--no-abilities`.

## Canales de Telegram

- Inglés: https://t.me/OathForge
- Español: https://t.me/OathForge_es

Cada versión se anuncia en los dos con el mismo formato (título `🛡 Oathforge vX.Y.Z: …`, bloques con emoji y viñetas); el de español es la traducción del inglés.

## Cómo colaborar

Cada persona trabaja el código en su rama: `josue-development`, `rayko-development` o `edian-development`.

- **TODO de testers:** edita tu `TODO-<nombre>.md` directamente en `main` y haz `git push`. Es lo único que se empuja a `main` sin pull request.
- **Código:** abre un pull request de tu rama a `main`. Necesita la aprobación de Josue.
- **Mantente al día:** `git fetch` y `git merge origin/main` en tu rama antes de empezar.

```powershell
git clone https://github.com/JD3M0N/Oathforge.git
cd Oathforge
git switch main
git pull
# ...edita TODO-rayko.md...
git commit -am "todo: bugs de la cripta"
git push
```

## Pendiente (siguientes pasos)

Detalle y orden en [planning/iter.md](planning/iter.md):

- Grupos cooperativos y combate en grupo; después PvP con consentimiento.
- Elección de especialización a nivel 5 (los datos ya existen).
- Encargos entre jugadores, mercado y sumideros de oro.
- Eventos mundiales encadenados (la crisis del hierro) y una segunda región.
- Imágenes de lugares y NPC, música de taberna y voces (planning/ars.md); Mini App.
