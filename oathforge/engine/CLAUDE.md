# engine/ — reglas puras

- **Sin E/S**: aquí no se importa nada de `database`, `services`, `bot`, `ai` ni Telegram. Solo datos de entrada y resultados.
- **Todo azar pasa por `dice.py`** con un `random.Random` inyectado. Nunca uses `random` a nivel de módulo: los tests y el simulador fijan la semilla.
- El estado de un combate es un modelo Pydantic serializable (`EncounterState`). Lo guarda `services/combat_service.py`, no el motor.
- `combat.py` es grande: localiza la función con Grep y lee unas decenas de líneas alrededor.
- Un cambio de reglas o de números se comprueba con `tests/engine/` y con `oath simulate --level 1-5` (y `oath balance` si toca la campaña).
