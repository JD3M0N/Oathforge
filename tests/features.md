# Checklist de features

Lo que hay que probar **siempre** tras una feature grande, jugando de punta a punta con la cuenta de prueba (`oath tgtest send|press|show`). Cada feature grande nueva añade aquí sus casillas.

Cada pasada se hace con una clase distinta (la que menos se haya probado) y se anota el tiempo de cada misión del tutorial.

## Personaje
- [ ] `/start` sin personaje: elegir idioma, clase, linaje y trasfondo, nombre
- [ ] Ficha 🧝 Héroe: stats, PV, maná/recursos, habilidades de la clase
- [ ] Todo el texto sale en el idioma elegido (sin claves de i18n crudas)

## Teclado fijo y escena
- [ ] 📍 Lugar · ⚒ Actividades · 🗺 Mapa / 🧝 Héroe · 🎒 Inventario · 📖 Diario (los jugadores viejos reciben el teclado nuevo)
- [ ] `/start` y `/look` enseñan la escena; en combate, el combate
- [ ] La escena no repite botones del teclado fijo
- [ ] La escena solo tiene Viajar, Investigar, Hablar, Comerciar, ⚒ Actividades (n) y lo de la misión
- [ ] ⚒ Actividades: cada actividad con duración y qué falta; sin pico, «🛒 Pico · ir a Mercado» lleva al mercado
- [ ] ⚒ Actividades mientras trabajas: el panel de la actividad; en combate: el combate
- [ ] 🛠️ Oficios desde Héroe y desde Actividades, con sus pestañas
- [ ] Investigar, cazar o abandonar: un solo mensaje con el resultado y los botones; el panel viejo se queda sin botones
- [ ] Un botón viejo o un doble toque: ventanita «Ese menú ya no vale» y el mensaje pasa a la vista actual, sin gastar nada
- [ ] Un rechazo («Necesitas un pico», sin oro): ventanita, sin mensaje nuevo
- [ ] Pulsar la misma vista dos veces no manda un mensaje repetido
- [ ] Comprar, equipar, aprender o fabricar: el resultado encima del mismo menú
- [ ] Una actividad que termina sola trae los botones del lugar en el mismo mensaje
- [ ] Investigar: «🎲 Percepción: 12 + 2 = 14 vs CD 12 · ✅ Éxito»
- [ ] «Llegas al Mercado», «a la Taberna», «por el Camino del Viejo Rey» (en inglés, «the Old Pass Mine»)
- [ ] Informe de un combate de una ronda: «1 ronda»
- [ ] `/sheet` explica ● ○ · y ★

## Mapa y viaje (0.8.0)
- [ ] Mapa: dónde estás · 📜 objetivo · esta zona · otras zonas · 🌫️ Sin explorar
- [ ] Viaje directo a un lugar conocido, también entre zonas, en un toque
- [ ] El camino no atraviesa salas con combate fijo pendiente
- [ ] 📜 al objetivo lleva al siguiente paso de cada misión activa sin revelar sitios desconocidos
- [ ] 📜 respeta la hora: de día no manda a cazar criaturas que solo salen de noche
- [ ] 📜 aparece también en misiones con decisiones (relicario: buscar, entregar a Holt, guardián)
- [ ] Tramos ⚠️: emboscada con una sola tirada; «▶️ Seguir hacia…» termina el viaje
- [ ] Al llegar sin más que contar, el mapa se convierte en la escena («Llegas a X…»)
- [ ] Solo distancias en yardas, sin tiempos
- [ ] `/map` estando ocupado avisa en vez de enseñar caminos

## Combate
- [ ] Ataque básico y habilidades de la clase (maná/recursos se gastan bien)
- [ ] Informe de batalla: rondas correctas, «🏆 Victoria» una sola vez
- [ ] Botín y crónica en el mismo mensaje
- [ ] Huida
- [ ] Derrota → heridas graves; Ysolde las cura gratis (beta)
- [ ] El jefe del tutorial (Viejo Colmillo) es ganable por la clase más frágil
- [ ] Aviso de poca vida al cazar/rastrear/expedición

## Actividades
- [ ] Cazar y rastrear (texto propio del lugar); las misiones de caza cuentan de día y de noche
- [ ] Beta: en el tutorial las actividades terminan al momento; el descanso largo es instantáneo
- [ ] Recolectar hierbas, minar
- [ ] Descanso largo en la taberna
- [ ] Fabricar (estofado, poción de maná con ala de murciélago)
- [ ] El atajo del tutorial al desollar no deja sin la carne que pide la misión siguiente
- [ ] Poción de maná: con varios conjuros gastados, deja elegir cuál recupera
- [ ] Beta: pociones de vida y de maná a 1 de oro

## Comercio e inventario
- [ ] Tienda por categorías; tras comprar sigues en la categoría
- [ ] Fichas `/item_…`
- [ ] Inventario: equipado primero, iconos de hueco en equipar/quitar

## NPCs y misiones
- [ ] Aceptar y entregar misiones; al cumplir un objetivo, aviso del siguiente
- [ ] Saludo de regreso (`greeting_return`) tras terminar una misión del NPC
- [ ] Sin IA: el NPC recuerda la pista de la misión activa
- [ ] Las 10 misiones del tutorial se completan sin pasar por la cripta; anotar minutos de cada una

## Diario y reglas
- [ ] 📖 Diario: misiones activas/hechas, 📈 Estadísticas
- [ ] `/rulebook` (Viajar y explorar, Actividades)

## Herramientas
- [ ] `oath tutorial-stats` refleja la partida

## 0.9 — Logros e identidad

Validación 2026-10-17: suite automatizada con PostgreSQL y recorrido real con la cuenta de prueba. «Automático» identifica los casos que no se han forzado en la partida real.

- [x] /achievements: portada, pendientes y obtenidos en español e inglés (Telegram); categorías y paginación (automático).
- [x] Condición y progreso (Telegram); revelar una pista sin conceder el logro (automático).
- [x] Seguir tres objetivos y sustituir uno (automático); seguimiento en el diario (Telegram).
- [x] Equipar/quitar título y límite de destacados (automático); destacado en /hero (Telegram).
- [x] Actividad automática con un único anuncio agrupado (automático); anuncio retroactivo agrupado (Telegram).
- [x] 1.000 repeticiones, concurrencia y rollback sin duplicados (automático, PostgreSQL).
- [x] Reinicio conserva destacados (Telegram); recuperación de anuncio tras fallo y vencimiento de lease (automático).
- [x] Backfill en simulación y aplicado en la base local; segunda ejecución sin nuevas concesiones.
- [x] Personaje nuevo: fabricación, victoria y decisiones concedidas por el motor sin IA (automático).

La cuenta de prueba conserva su idioma original y quedó sin los destacados ni objetivos temporales usados en el recorrido.
