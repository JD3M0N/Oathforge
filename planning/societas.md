# Societas — multijugador, gremios y PvP

Resumen de [Possibilium §12 y §24](Possibilium.md#s12).

## Estado actual (0.8.2)

- Solo en solitario. Las tablas para grupos existen (`parties`, `party_members`, `encounter_participants`), pero el servicio de combate sincroniza y recompensa a un solo personaje (`p1`).
- Los jugadores se afectan de forma indirecta mediante rumores.
- Canales de anuncios: https://t.me/OathForge (inglés) y https://t.me/OathForge_es (español), publicados a mano.

## Decidido

- Primera prueba: dos amigos en una aventura corta del Valle de la Fragua Gris (PKG-02; la Cripta Hundida se retiró en 0.10.41), ampliable a cuatro.
- PvP solo con consentimiento y sin pérdidas permanentes.
- Nunca usar el personaje de un ausente sin consentimiento; mostrar nombres de personaje, no datos de Telegram.

## Próximo

- **COO-01** cripta compartida: escena e iniciativa comunes, cura/protección aliada, recompensas individuales, recuperación tras reinicio.
- Reglas antes del menú: un grupo activo por personaje, invitaciones con token y caducidad, roster congelado al empezar combate, actor derivado del usuario autenticado, premio único por participante (tickets COOP-01..08).
- Ritmo: sesión rápida (90 s por turno, hipótesis) o campaña lenta (6–24 h); deadline persistido en BD y despertado por JobQueue.
- Panel común en el grupo; ficha, inventario y secretos por privado.
- `/party` y `/resume`.
- Después: gremios pequeños (**GRE-01..05**), duelo amistoso, arena normalizada, competición de facciones.

| Espacio de Telegram | Para qué |
|---|---|
| Chat privado | Personaje, exploración, secretos |
| Grupo de expedición | Combate y escenas en grupo |
| Grupo de gremio | Organización y reclutamiento |
| Comunidad con temas | Mercado, taberna global, anuncios |
| Canal de noticias | *Herald of Aetherfall* y grandes eventos |
| Mini App (futuro) | Mapa, talentos, mercado; validar `initData` |

## Preguntas abiertas

- ¿Panel en el chat del grupo o privado por jugador?
- ¿Cómo evitamos que el grupo espere a un jugador lento?
- ¿Tamaño: 2–4 o 2–5?
- ¿Qué botín se comparte y qué se entrega por personaje?
- ¿Abrimos el canal de noticias antes de tener grupos?
