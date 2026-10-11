# Comercio y economía

## Estado actual

- Tiendas en NPC (`content/npcs.yaml`, campo `shop`).
- Compra: valor base ±25 % según la reputación con la facción del NPC (-100..100). Venta: 50 % del valor, ajustado igual (`oathforge/services/inventory.py`).
- Stock con bloqueo de fila: dos jugadores no pueden comprar a la vez la última poción.
- Entradas de oro: trasfondo inicial, botín, misiones, robos. Salidas: tiendas, descansar en la taberna y el 10 % que se pierde al ser derrotado.
- El relicario de la misión se puede vender al Sindicato Carmesí (decisión con consecuencias de reputación).

## Ideas

- **Stock que se repone** con el reloj del mundo; precios que suben si todos compran lo mismo.
- **Mercado entre jugadores**: tablón de ofertas en Crownreach con comisión (sumidero de oro) y entrega asíncrona.
- **Profesiones**: herrería (armas +1), alquimia (pociones con hierbas del bosque), que suben por uso como las habilidades.
- **Sumideros de oro**: reparaciones, alojamiento, sobornos, cuotas de gremio, mejoras de casa.
- **Mercado negro** del Sindicato: objetos robados, mejores precios con reputación criminal y riesgo de que la Guardia te pille.
- **Regateo**: una prueba de Persuasión o Engaño por visita.
- Objetos únicos que solo se ganan en misiones, para que explorar valga la pena.

## Preguntas abiertas

- ¿Moneda única (oro) o oro/plata/cobre? Hoy: oro.
- ¿Cómo evitamos que el oro sobre a nivel 5? Medir en `artifacts/events/` cuánto acumula un jugador por hora.
- ¿El comercio entre jugadores exige estar en el mismo lugar?
