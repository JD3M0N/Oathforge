# items/ — una carpeta por objeto

```
items/<categoría>/<objeto>/item.yaml    la ficha; el id es el nombre de la carpeta
items/<categoría>/recipes.yaml          las recetas que producen objetos de esa categoría: {receta: ficha, …}
```

- La categoría es el `type` del objeto (`weapon`, `armor`, `material`, …); un test comprueba que coinciden.
- Una receta va en la categoría de su primer producto; las que no producen objetos (muebles que se instalan en el
  cuarto) van en `furniture/recipes.yaml`.
- Los iconos (`images/icon.jpg`, `icon.prompt.md`, `media.yaml`) se pueden poner junto a la ficha; el catálogo de
  imágenes todavía no los lee.

## Recetas (`recipes.yaml`)

Disciplina (un oficio, una afición o una maestría), rango mínimo en ella, ingredientes → productos y XP de esa
disciplina. Sin `station`, se fabrica en la del oficio (`content/professions.yaml`).
El refinado (mena → lingote, tronco → tablón, piel → cuero, fibra → fibra limpia) pertenece a la maestría:
no ocupa plaza de oficio, da XP de maestría y se hace en las estaciones del Gremio de Aventureros.
Fabricar es inmediato, y se puede fabricar por lotes (CRAFT_BATCH_MAX).

Notas que estaban entre las recetas:
- Recetas de iniciación de la misión de la habitación: no piden oficio ni plaza, solo esa misión en curso, y lo que
  hacen se queda instalado en el cuarto. No abren la puerta a fabricar muebles sin ser carpintero.
- Herramientas especializadas: la herrería las forja; las cañas, la carpintería. Las mejoradas piden una pieza de
  otro oficio (mango, empuñadura o sedal): se compran a su maestro.
- Catálogo T1 (rango 3-5): el equipo de combate pide nivel 10 para llevarse; se fabrica ya y se equipa cuando el mundo
  llegue ahí. Lo demás (refinado, herramientas, muebles) se usa por rango.
