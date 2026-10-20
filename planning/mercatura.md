# Mercatura — comercio, economía y equipo

Resumen de [Possibilium §17–18](Possibilium.md#s17).

## Estado actual (0.8.2)

- Tiendas en NPC (`content/npcs.yaml`, campo `shop`), abiertas por categorías (⚔️ Armas, 🛡️ Armaduras, 🧪 Consumibles, 🧰 Herramientas…) con la ficha `/item_` de cada objeto.
- Compra: valor base ±25 % según la reputación con la facción del NPC (−100..100). Venta: 50 %, ajustado igual; todo lo que vale ≥ 1 se vende por ≥ 1 (`services/inventory.py`).
- Stock con bloqueo de fila: dos jugadores no compran a la vez la última poción.
- **Beta**: pociones de vida y de maná a 1 de oro; Ysolde cura gratis; el descanso no cobra tiempo.
- Entradas de oro: trasfondo, botín, misiones, venta de materiales, robos. Salidas: tiendas, descanso, cambio de oficio y el 10 % al ser derrotado.
- El relicario se puede vender al Sindicato Carmesí (decisión con reputación).
- **Equipo**: 4 ranuras (principal, distancia, secundaria/escudo, cuerpo); lo equipado sale primero en el inventario; `crafted_by` en lo fabricado.

## Decidido

- Moneda única: oro.
- El precio y la cantidad se recalculan siempre en el servidor.
- Antes de comercio entre jugadores: cero duplicados en 1.000 repeticiones automatizadas.

## Próximo

- **Cofre, planos y maestros** ([F15](roadmap.md#F15), [contrato](roadmap-profesiones.md)): el cofre personal (**EQU-07**) vive en la habitación del Gremio, con depositar y retirar atómicos, capacidad por espacios y mejoras de Carpintería; cada maestro de oficio vende las herramientas de su oficio, los componentes de terceros que sus recetas piden y planos; los planos son objetos comerciables que enseñan una receta especial y se gastan una sola vez.
- **ECO-01** pedido de fabricación con custodia (materiales + comisión, aceptación única, cancelación/caducidad que devuelve una vez); tickets CRAFT-01/02.
- **ECO-05** pedidos PNJ con demanda limitada (herramienta, lote de pociones, comida de expedición).
- **ECO-02..04** órdenes de compra, listados a precio fijo con comisión, intercambio seguro.
- Sumideros: reparaciones, tasas, viajes seguros, recetas avanzadas, almacén.
- Revisar robos PNJ repetibles sin bolsa ni cooldown (ticket ECO-01) y márgenes de joyería.
- Libro de economía: oro creado/destruido, riqueza mediana, precios básicos.
- **EQU-01..10**: comparar antes de equipar, más ranuras (cabeza, manos, pies, cuello, 2 anillos, capa), rareza con función, un afijo, sets de dos, procedencia visible, cofre/almacén, protección de mala suerte.
- Mercado negro, regateo, caravanas (**ECO-06..12**) más adelante.

## Preguntas abiertas

- ¿Cómo evitamos que el oro sobre a nivel 5? Medir oro por hora en `artifacts/events/`.
- ¿El comercio entre jugadores exige estar en el mismo lugar?
- ¿Precio fijo, pedidos o intercambio como primera economía compartida?
- ¿Cuántas ranuras caben en `/sheet`?
