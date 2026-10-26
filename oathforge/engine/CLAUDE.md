# engine/ — reglas puras

- **Sin E/S**: aquí no se importa nada de `database`, `services`, `bot`, `ai` ni Telegram. Solo datos de entrada y resultados. Lo comprueba `lint-imports` (contratos en `pyproject.toml`).
- **Todo azar pasa por `dice.py`** con un `random.Random` inyectado. Nunca uses `random` a nivel de módulo: los tests y el simulador fijan la semilla.
- El estado de un combate es un modelo Pydantic serializable (`EncounterState`). Lo guarda `services/combat_service.py`, no el motor.
- **`combat/`** es un paquete, un módulo por etapa: `state` (constantes, modelos y consultas), `resolve` (salvaciones, ataques, daño, estados y curación), `entities` (invocaciones y formas), `turns` (inicio, flujo de turnos y turno de los enemigos) y `actions` (el turno del jugador). Las dependencias van en ese orden y nunca hacia atrás.
  - `combat/__init__.py` reexporta lo público (`combat.player_act`, `combat.EncounterState`…) y los pasos privados que usan los tests de `tests/engine/` (`cb._apply_damage`…). Si un test necesita otro paso privado, añádelo allí.
- Un cambio de reglas o de números se comprueba con `tests/engine/` y con `oath simulate --level 1-5` (y `oath balance` si toca la campaña).
