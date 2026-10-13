# Comercio y economía

## Estado actual

- Tiendas en NPC (`content/npcs.yaml`, campo `shop`).
- Compra: valor base ±25 % según la reputación con la facción del NPC (-100..100). Venta: 50 % del valor, ajustado igual (`oathforge/services/inventory.py`).
- Stock con bloqueo de fila: dos jugadores no pueden comprar a la vez la última poción.
- Materiales de recolección (v0.6.0): mena, madera, hierbas, pieles, pescado. Se venden en cualquier tienda que compre; Tessa vende las herramientas (pico, hacha, hoz, cuchillo, caña).
- Entradas de oro: trasfondo inicial, botín, misiones, robos. Salidas: tiendas, descansar en la taberna y el 10 % que se pierde al ser derrotado.
- El relicario de la misión se puede vender al Sindicato Carmesí (decisión con consecuencias de reputación).

## Ideas

- **Stock que se repone** con el reloj del mundo; precios que suben si todos compran lo mismo.
- **Mercado entre jugadores**: tablón de ofertas en Crownreach con comisión (sumidero de oro) y entrega asíncrona.
- **Profesiones**: diseño en [`profesiones.md`](profesiones.md). v0.6.0 trae la recolección (maestrías y materiales); los oficios y las recetas llegan en v0.6.1.
- **Sumideros de oro**: reparaciones, alojamiento, sobornos, cuotas de gremio, mejoras de casa.
- **Mercado negro** del Sindicato: objetos robados, mejores precios con reputación criminal y riesgo de que la Guardia te pille.
- **Regateo**: una prueba de Persuasión o Engaño por visita.
- Objetos únicos que solo se ganan en misiones, para que explorar valga la pena.

### Economía en tres capas (GDD §7.1)

1. **Tiendas NPC de referencia** (lo que hay): precios acotados para que nadie se quede sin herramientas.
2. **Mercado entre jugadores**: órdenes de compra y venta de objetos fungibles.
3. **Encargos personalizados**: intercambio directo, subastas, objetos únicos, contratos de escolta y de fabricación.

Cada región produce y consume cosas distintas (Crownreach necesita hierro de las minas y hierbas del bosque). Los NPC actúan como compradores y vendedores limitados para que el mercado no dependa de cuántos jugadores haya conectados.

### Profesiones (GDD §6)

| Grupo | Profesiones | Producen |
|---|---|---|
| Extracción | Minero, leñador, pescador, cazador, herborista | Menas, madera, pieles, plantas |
| Transformación | Herrero, fundidor, carpintero, sastre, joyero | Armas, lingotes, armaduras, amuletos |
| Consumo | Cocinero, alquimista, cervecero | Comida, tónicos |
| Conocimiento | Cartógrafo, escriba, arqueólogo | Mapas, copias, análisis de reliquias |
| Transporte | Caravanero, guía, escolta | Entregas, menos riesgo en ruta |
| Clandestinas | Ladrón, contrabandista, espía, falsificador | Encargos secretos e información (solo dentro del juego) |

- **Interdependencia** (§6.1): el mineral alimenta la forja, el herrero vende al guerrero y una guerra sube la demanda. Mejor que «minar 20 veces».
- **Vetas** (§6.3): tipo, calidad, cantidad, regeneración y riesgo. Se agotan y reaparecen despacio; sobreexplotar aumenta el peligro de derrumbe. Todo por estados y eventos, nunca improvisado por la IA.
- **Recetas** (§6.4): materiales + estación + nivel de oficio + tiempo. Calidad dentro de un rango pequeño y documentado; el artesano elige («más ligera» o «más resistente»). Ejemplo: espada de acero templado = 3 lingotes + 1 madera noble + forja.
- **Firma del artesano**: los objetos fabricados guardan quién los hizo (ver `progresion.md`).
- **Talleres y pedidos** (§6.5): «cinco escudos antes del domingo», con el pago en custodia.
- **Especializaciones de oficio** (§6.6): herrería (armas / armaduras / artefactos), alquimia (medicina / venenos / transmutación), cartografía (topografía / rutas secretas / mapas del tesoro).

### Contratos, caravanas y seguridad (GDD §7.2–7.6)

- **Contrato con custodia** (§7.5): un alquimista pide 8 lirios por 240 de oro; el motor retiene el oro; quien entrega los 8 lirios cobra en la misma transacción; si caduca, se devuelve.
- **Intercambio seguro**: los dos depositan, confirmación doble, se puede cancelar antes de cerrar.
- **Caravanas** (§7.6): origen, destino, carga, ruta, escolta y hora estimada de llegada; un asalto no puede dar riqueza ilimitada (límites de carga, seguros ficticios).
- **Contrabando** según la ley de cada ciudad (ver `mundo-y-misiones.md`).
- **Fuentes y sumideros** (§7.3): medir oro creado y destruido, mediana de riqueza y precios de lo básico. Sumideros que faltan: reparaciones, tasas de mercado, estaciones de oficio, viajes.
- **Libro mayor e idempotencia** (§7.4): cada transferencia en una transacción, con filas bloqueadas, una clave de idempotencia por operación y un asiento en el libro mayor. El precio se recalcula siempre en el servidor, nunca se fía del botón. Criterio antes de abrir el comercio entre jugadores: **cero duplicados en 1.000 repeticiones** automatizadas (§17.6).

## Preguntas abiertas

- ¿Moneda única (oro) o oro/plata/cobre? Hoy: oro.
- ¿Cómo evitamos que el oro sobre a nivel 5? Medir en `artifacts/events/` cuánto acumula un jugador por hora.
- ¿El comercio entre jugadores exige estar en el mismo lugar?
- ~~¿Cuántas profesiones a la vez?~~ Dos oficios activos de seis; la recolección es libre (ver `profesiones.md`).
- ~~¿Cuánto tarda fabricar?~~ Las recetas básicas son inmediatas; recolectar sí lleva 5 o 15 minutos reales.
