# world/ — una carpeta por nodo del mundo

```
world/world.yaml, guide.yaml
world/<continente>/continent.yaml
world/<continente>/<zona>/zone.yaml
world/<continente>/<zona>/<lugar>/place.yaml          (+ images/)
world/<continente>/<zona>/npcs/<pnj>/npc.yaml         la ficha; el id es el nombre de la carpeta
world/<continente>/<zona>/npcs/<pnj>/dialogue.fallback.yaml   los 12 respaldos por idioma (lista de textos es/en)
world/<continente>/<zona>/quests/<misión>.yaml        una misión por archivo; el id es el nombre del archivo
```

Una ciudad nueva es una carpeta de zona con todo dentro. Las tiendas son del PNJ: van en `shop` de su `npc.yaml`.
La zona de un PNJ es la de su lugar de día; la de una misión, la de quien la da (`giver`).
Las carpetas que empiezan por `_` (plantillas) se ignoran.

`order: N` al final de `npc.yaml` fija la posición del PNJ en las listas (no es un campo del modelo). Las misiones
usan su propio `order` (el diario las ordena por él).

## Misiones

Las que tienen `objectives` se completan solas al cumplirlos (muertes, charlas, lugares, objetos recogidos,
desollados o fabricados, descansos, curaciones) y dan `rewards`; la siguiente se desbloquea con `after` (misión
completada) o `unlock_flag`. El diario las ordena por `order`.
1-10: el tutorial (Vale, Bram): hablar, ciudad, tiendas, cazar, desollar, recolectar, cocinar, minar, curarse y
descansar, y un jefe en el prado. Sin mazmorras. Después viene la campaña (camp_*) y el valle (reg_*).
`tutorial`: misión del tutorial (cuenta en `oath tutorial-stats`). Sus actividades llevan su tiempo real.
`legacy_done`: quien completó alguna de esas misiones antiguas empieza con esta completada (sin recompensa).

## PNJ

Un maestro por puesto del Barrio de Oficios: enseña y cambia su oficio y explica sus técnicas.
De noche se los encuentra en la taberna, como a Tessa.
