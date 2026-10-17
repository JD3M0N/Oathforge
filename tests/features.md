# Checklist de features

Lo que hay que probar **siempre** tras una feature grande, jugando de punta a punta con la cuenta de prueba (`oath tgtest send|press|show`). Cada feature grande nueva añade aquí sus casillas.

Cada pasada se hace con una clase distinta (la que menos se haya probado) y se anota el tiempo de cada misión del tutorial.

## Personaje
- [ ] `/start` sin personaje: elegir idioma, clase, linaje y trasfondo, nombre
- [ ] Ficha 🧝 Héroe: stats, PV, maná/recursos, habilidades de la clase
- [ ] Todo el texto sale en el idioma elegido (sin claves de i18n crudas)

## Teclado fijo y escena
- [ ] 📍 Lugar · 🧝 Héroe · 🗺 Mapa / 🎒 Inventario · 📖 Diario
- [ ] `/start` y `/look` enseñan la escena; en combate, el combate
- [ ] La escena no repite botones del teclado fijo

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
- [ ] Jefes del tutorial (Guardián de la cripta, Viejo Colmillo) ganables por la clase más frágil sin esperar un descanso largo
- [ ] Aviso de poca vida al cazar/rastrear/expedición

## Actividades
- [ ] Cazar y rastrear (texto propio del lugar)
- [ ] Recolectar hierbas, minar
- [ ] Descanso largo en la taberna
- [ ] Fabricar (estofado, poción de maná con ala de murciélago)
- [ ] El atajo del tutorial al desollar no deja sin la carne que pide la misión siguiente
- [ ] Poción de maná: qué conjuro recupera

## Comercio e inventario
- [ ] Tienda por categorías; tras comprar sigues en la categoría
- [ ] Fichas `/item_…`
- [ ] Inventario: equipado primero, iconos de hueco en equipar/quitar

## NPCs y misiones
- [ ] Aceptar y entregar misiones; al cumplir un objetivo, aviso del siguiente
- [ ] Saludo de regreso (`greeting_return`) tras terminar una misión del NPC
- [ ] Sin IA: el NPC recuerda la pista de la misión activa
- [ ] Las 11 misiones del tutorial se completan; anotar minutos de cada una

## Diario y reglas
- [ ] 📖 Diario: misiones activas/hechas, 📈 Estadísticas
- [ ] `/rulebook` (Viajar y explorar, Actividades)

## Herramientas
- [ ] `oath tutorial-stats` refleja la partida
