# ⚔️ Oathforge

**Un RPG de fantasía que se juega en Telegram.** Tú decides qué hace tu héroe, los dados deciden si lo consigue y un Dungeon Master con IA te cuenta lo que pasó.

> Escribe «me agacho junto a las huellas y busco señales de emboscada». El motor tira el d20, la IA lo narra y el mundo de **Aetherfall** lo recuerda.

## Qué te espera

- 🛡️ **Ocho clases**, de Paladín a Brujo, cada una con su retrato, sus habilidades y su forma de pelear.
- 🎲 **Combate por turnos** al estilo D&D: iniciativa, filas, críticos, conjuros, estados y objetos del escenario.
- 🗺️ **Un mundo para explorar**: la ciudad de Crownreach, bosques, minas, ríos y la Cripta Hundida.
- ⛏️ **Oficios de verdad**: minas, talas, cazas y pescas, y con lo que traes forjas, preparas pociones o cocinas.
- 📜 **Misiones con decisiones**: un tutorial con la sargenta Vale y aventuras con más de un final.
- 🗣️ **Personajes que te recuerdan**: lo que haces cambia cómo te tratan y llega a las tabernas en forma de rumor.
- 🌍 En **español e inglés** desde el primer día.

## La regla de oro

**La IA nunca decide los resultados.** Interpreta lo que escribes, pero las tiradas, el oro y las consecuencias los decide un motor justo y verificable. Libertad para intentar cualquier cosa; reglas para que importe.

## Síguelo

- Canal en español: https://t.me/OathForge_es
- Canal en inglés: https://t.me/OathForge

Estamos en beta y cada partida de prueba hace mejor el juego. Si juegas, cuéntanos lo que veas en los canales.

## Para quien construye

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
copy .env.example .env      # BOT_TOKEN, DATABASE_URL y GEMINI_API_KEY
.venv\Scripts\alembic upgrade head
.venv\Scripts\oath bot      # oath help lista todo lo demás
```

- Cómo trabajar en el código: [AGENTS.md](AGENTS.md).
- Qué queremos construir: [planning/](planning/README.md).
- Qué ha cambiado: [CHANGELOG.md](CHANGELOG.md).
