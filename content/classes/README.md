# classes/ — una carpeta por clase

```
classes/<clase>/
  class.yaml            la ficha (sale de lo que fue classes.yaml); el id es el nombre de la carpeta
  specializations.yaml  las ramas de clase de esa clase: {rama: ficha, …}
  images/               retratos (portrait.male.jpg, portrait.female.jpg) con media.yaml y .prompt.md
```

- `order: N` al final de `class.yaml` fija la posición de la clase en los menús (no es un campo del modelo: el cargador lo
  quita). Sin `order`, las clases van detrás, por id.
- Las catorce clases (roadmap_balance §6). Cada una tiene su propia barra de recurso (`content/progression.yaml`) y
  habilidades de nivel 1 a 9; la rama de clase llega al 10 (`specializations.yaml` de su carpeta).
- Costes y cifras son SEMILLAS para medir (B12). El ataque básico nunca cuesta nada.

## Ramas de clase (`specializations.yaml`)

Las 41 ramas de clase (planning/roadmap_balance.md §6). Una por personaje, elegida al nivel 10 en el Gremio.
No confundir con `content/specializations.yaml`, que son las ramas de maestría de campo.

roles: dmg (daño), deff (defensa), heal (recuperación), control (alterar lo que puede hacer el rival).
El primero es el principal.

Cada rama LISTA tiene su recorrido entero: una pasiva y una técnica al 10, desarrollo fijo al 15, dos
modificadores en el 13 y otros dos en el 17 (el jugador elige uno de cada par) y una técnica culminante
al 20. Una rama sin recorrido sigue con `ready: false` y no se puede elegir. Todas las cifras son SEMILLAS
para medir (B12). Las descripciones cuentan el efecto; el coste, el enfriamiento y las cifras que un
modificador cambia salen de los datos y se muestran en la ficha de cada habilidad.
