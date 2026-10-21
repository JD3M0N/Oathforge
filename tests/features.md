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
- [ ] 🎒 Inventario: resumen con lo puesto y cuántos de cada tipo; pestañas con una línea por objeto e icono
- [ ] Equipar desde ⚔️ Equipo y usar desde 🧪 Consumibles vuelven a su pestaña; `/item_` de algo tuyo trae su botón
- [ ] Botín, recetas y tiendas con el icono de cada objeto

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

## 0.10.7 — El Libro del Héroe (F03)
- [x] 📖 Diario por pestañas: la activa entre «• … •» y el mismo mensaje se edita (Telegram, ES y EN).
- [x] 📖 Ahora: objetivo de misión con botón de ruta; sin misiones, botón hacia quien las da (Telegram).
- [ ] 📖 Ahora con una actividad en marcha y con un viaje interrumpido (Telegram).
- [x] 🕯️ Crónica: entradas por día, «Antes de este libro» para lo retroactivo (Telegram, ES y EN); paginación de 8 (automático).
- [x] Una visita o fabricación repetida no añade entrada pero sí cuenta (automático); rango 0 no es entrada (automático).
- [x] 📜 Misiones incluye las terminadas; el botón «Registro» de un menú viejo abre la Crónica (automático).
- [x] 📈 Estadísticas: contadores de la crónica junto a los antiguos, cada bloque con su «desde» (Telegram).
- [x] Abrir el diario no genera llamadas a Gemini (`artifacts/ai/`).
- [x] `/rulebook`: descanso y emboscada con las cifras del motor y la frase de beta (Telegram); cada marcador tiene valor (automático).
- [x] Migración 0010 en una base de prueba: los recibos se conservan como `legacy`, y `downgrade` los devuelve.
- [ ] Un logro nuevo durante la partida aparece en la Crónica como «🏆 Logro: …» (Telegram).

## 0.10.8 — Logros auditados (F04)
- [x] Toda la interfaz dice «Logros» y «puntos de logro» (Telegram, ES).
- [x] El título sale junto al nombre en `/sheet` y en la cabecera del Libro (render con un personaje con título).
- [x] El título llega al narrador y a los PNJ como dato (automático).
- [x] Una expedición o rastreo perdido no cuenta como actividad (automático).
- [x] Destacar o seguir con la clave «-» se rechaza (automático).
- [ ] «Héroe de Crownreach» al llegar a nivel 5, con su título (Telegram).
- [ ] «Oficial del gremio» al alcanzar rango 2 en un oficio (Telegram).
- [ ] Los dos ocultos no aparecen en Pendientes y sí al conseguirlos (Telegram).

## 0.10.9–0.10.18 — Oficios, maestrías y aficiones (F15)

Recorrido completo, con la cuenta de prueba, en ES y EN. Lo marcado (automático) ya lo cubre la suite.

### El mundo nuevo
- [ ] La plaza enseña por dónde se va al Gremio de Aventureros, y Vale alista allí (Telegram).
- [ ] El mapa de la ciudad cabe en una pantalla: los puestos salen bajo «Barrio de Oficios» con «🛠️ Puestos (8)» (Telegram).
- [x] Cada oficio se aprende solo en su puesto; en otro, dice a cuál ir (automático).
- [ ] Tessa está de día en su forja y de noche en la taberna, y sigue vendiendo herramientas (Telegram).
- [ ] Los ocho maestros responden al hablarles, con y sin IA (Telegram, ES y EN).

### Refinar y fabricar
- [x] Fundir, aserrar, curtir y limpiar fibra en el Gremio sin tener oficio, con XP de la maestría (automático).
- [x] El lote comprueba todos los materiales antes de gastar uno (automático).
- [ ] 🔨 Fabricar: ingredientes con tengo/necesito y botón solo con todo completo (Telegram).
- [ ] `/recipes` con sus cinco pestañas, `/r_<receta>` con el origen de lo que falta y `/craft_<receta> 5` (Telegram, ES y EN).
- [ ] Reenviar el mismo `/craft_` dos veces no fabrica dos veces (Telegram).

### Sastrería, técnicas y planos
- [x] Fibra → fibra limpia → hilo → tela → jubón; el sedal a rango 2 (automático).
- [ ] Al subir de rango sale «📘 Técnica aprendida: …» con sus recetas (Telegram).
- [x] Un plano se gasta una vez, no se gasta si ya la conoces y no se olvida al cambiar de oficio (automático).
- [ ] El plano del Viejo Colmillo cae al derrotarlo y su ficha trae «Aprender la receta» (Telegram).

### La habitación
- [ ] La misión «Un cuarto propio» de punta a punta: talar, aserrar, cofre, tela y cama (Telegram, ES y EN).
- [x] Las recetas de iniciación solo existen durante la misión y no se hacen por lotes (automático).
- [x] Dormir en tu cama no cuesta oro y mantiene las reglas del descanso largo (automático).
- [x] El cofre mueve la misma fila: nada se duplica, nada se pierde, y lo guardado no se gasta ni se vende (automático).
- [ ] `/room`, `/stash_<objeto> 5` y `/take_<objeto> 5` (Telegram).
- [ ] Pedir la tela dos veces: el botón no está mientras la llevas o ya tienes la cama (Telegram).
- [ ] Migración 0012 en una base de prueba, con su `downgrade`.

### Ramas y herramientas
- [x] Rango 1 rechazado, rango 2 permitido; la primera rama gratis y el cambio cobrado una vez (automático).
- [x] La rama pausada no suma y no se pierde (automático).
- [x] Rama y herramienta quedan fijadas al empezar; con un trabajo en marcha no se cambian (automático).
- [ ] 🌿 Especializaciones y 🧰 Herramientas desde Oficios → Maestrías (Telegram, ES y EN).
- [x] Una caña rápida convierte 300 s en 270 s; 10 % × 1,05 = 10,5 %; el extra se tira una vez (automático).
- [ ] El reglamento explica el porcentaje relativo frente a los puntos (Telegram, ES y EN).

### T1 y economía
- [x] Ningún ingrediente sin origen y ninguna receta que pida lo que produce (automático).
- [x] Comprar los componentes a un maestro y vender lo fabricado nunca da beneficio (automático).
- [x] El equipo T1 se fabrica a nivel bajo y no se equipa ni se bebe sin nivel 10 (automático).
- [ ] Un personaje de rango 4 encuentra hierro profundo, corazón de roble y fibra sedosa (Telegram o simulación).

### Concurrencia (PostgreSQL, `TEST_DATABASE_URL`)
- [ ] Doble toque en «Fabricar» con los materiales justos: una sola pieza.
- [ ] Depositar y retirar a la vez el mismo objeto: ni duplicado ni perdido.
- [ ] Dos lecturas del mismo plano: se gasta uno solo.

## 0.10-I · Progresión híbrida y entrega al PNJ (B02, v0.10.24)

### Nivel por XP e hito
- [x] Con la XP del nivel 12 y sin el hito del Recaudador, el héroe se queda en 9 y conserva toda su XP (automático).
- [x] El hito solo no da niveles; al llegar la XP sube sin repetir al jefe (automático).
- [x] Un hito se concede una vez y uno inventado no se concede nunca (automático).
- [x] La segunda puerta deja en 10 hasta el Ciervo (automático).
- [x] La puerta sobrevive a una transacción nueva (automático).
- [x] La ficha dice qué falta: ✨ la barra llena y 🔒 el hito que cierra el paso (Telegram, ES y EN).

### Entregar la misión a quien la dio
- [x] Abatir al Viejo Colmillo no paga: la misión queda «lista» y Bram debe la recompensa (automático).
- [x] Sin el dador delante no se entrega (automático).
- [x] Entregar dos veces paga una (automático y Telegram: el botón desaparece).
- [x] Una misión sin terminar no se entrega (automático).
- [x] Premio, hito y nivel en la misma transacción (automático).
- [x] «📜 Entregar: …» en la escena y en el panel del PNJ (Telegram, ES y EN).
- [x] El diario y `/quests` la muestran ✅ con el PNJ al que se le debe (Telegram).
- [ ] Doble toque simultáneo sobre «Entregar» con PostgreSQL: un solo pago.
- [ ] Migración 0013 en una base de prueba, con su `downgrade`.
