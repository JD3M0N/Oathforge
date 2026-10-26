# monsters/ — una carpeta por criatura

```
monsters/<criatura>/
  monster.yaml   la ficha; el id es el nombre de la carpeta
  images/        retrato (portrait.jpg) con media.yaml y .prompt.md
```

`order: N` al final de `monster.yaml` fija su posición en las listas (no es un campo del modelo). Sin `order`, por id.
