# Ars — Dirección audiovisual de Oathforge

Documento de trabajo para arte, música, voces, mapas, efectos, animaciones y presentación en Telegram. Sustituye a `audiovisual.md` desde la v0.8.3 y desarrolla el capítulo 26 de [Possibilium](Possibilium.md#s26).

**Revisión:** 17 de octubre de 2026, sobre la versión **0.8.2**. La auditoría del inventario se hizo sobre `main` en 0.8.0 (`a1a7687`); entre 0.8.0 y 0.8.2 no cambiaron imágenes ni el catálogo.

**Principio:** los activos representan el mundo, pero la verdad está en la base de datos. La geografía, los NPC presentes y los hechos los decide el motor. Nunca se genera arte ni audio en cada turno: se produce una vez, se revisa, se cataloga y se reutiliza.

## Índice

1. [Cómo interpretar los estados](#1-cómo-interpretar-los-estados)
2. [Auditoría del estado actual](#2-auditoría-del-estado-actual)
3. [Contradicciones y documentación pendiente](#3-contradicciones-y-documentación-pendiente)
4. [Decisiones documentadas vigentes](#4-decisiones-documentadas-vigentes)
5. [Biblia visual propuesta](#5-biblia-visual-propuesta)
6. [Cinco estilos que explorar](#6-cinco-estilos-que-explorar)
7. [Banco de quince prompts](#7-banco-de-quince-prompts)
8. [Consistencia de ciudades, NPC y criaturas](#8-consistencia-de-ciudades-npc-y-criaturas)
9. [Catálogo de contenido por producir](#9-catálogo-de-contenido-por-producir)
10. [Música y ambientes](#10-música-y-ambientes)
11. [Voces y escenas narradas](#11-voces-y-escenas-narradas)
12. [Mapas, iconos, tarjetas y animación](#12-mapas-iconos-tarjetas-y-animación)
13. [Experiencia en Telegram](#13-experiencia-en-telegram)
14. [Producción, formatos y metadatos](#14-producción-formatos-y-metadatos)
15. [Herramientas, procedencia y licencias](#15-herramientas-procedencia-y-licencias)
16. [Costes, prioridades y primera versión](#16-costes-prioridades-y-primera-versión)
17. [Organización documental](#17-organización-documental)
18. [Preguntas abiertas](#18-preguntas-abiertas)
19. [Fuentes y trazabilidad](#19-fuentes-y-trazabilidad)

## 1. Cómo interpretar los estados

- **IMPLEMENTADO:** comprobado en código o archivos versionados. No equivale a haberlo probado en el bot en producción.
- **DECISIÓN DOCUMENTADA:** regla recogida en «Decidido» o en las instrucciones de Josue; no se presupone aprobación de ideas cercanas.
- **PLANIFICADO / PROPUESTA PREVIA:** aparece en ideas, TODO, `iter.md` o en la guía histórica, pero sigue pendiente. Una versión candidata no es una fecha comprometida.
- **PROPUESTA NUEVA:** recomendación de este documento; necesita valoración de Josue.
- **PREGUNTA ABIERTA:** decisión sin resolver.

Este documento no aprueba automáticamente un estilo, proveedor, presupuesto, rediseño de personajes ni integración.

## 2. Auditoría del estado actual

### IMPLEMENTADO

| Recurso o función | Comprobación | Qué recibe el jugador |
|---|---|---|
| Panorámica de Crownreach | Dos JPEG de 1280 × 720 en `content/world/terra_coronata/crownreach/images/`: día y noche (`panorama.night.jpg`), en el estilo aprobado (0.10.4) | «🏙️ Ver ciudad» desde el hub, nocturna de noche |
| Retratos de las ocho clases | 16 JPEG de 768 × 1024: hombre y mujer por clase | Retrato de clase y sexo en `/sheet`; no retrato personal de linaje o equipo |
| Bestiario ilustrado | 10 JPEG de 768 × 1024 | «🖼️ Ver ilustración» en la ficha de una criatura vista |
| Consulta de monstruos | `/monster_<clave>` (0.7.19) | Imagen consultable desde el enlace al comenzar un combate |
| Catálogo de imágenes | `oathforge/content/media.py` | Selección por zona, lugar, continente, clase o monstruo; no todas las categorías tienen interfaz |
| Variantes horarias | Sufijo `.night` y selección `_pick` | Nocturna si existe; si no hay coincidencia, vuelve a todos los activos del conjunto |
| Caché de envío | `services/media.py` y `handlers/common.py` | Reutilización por bot y checksum; nueva subida si el archivo cambia o Telegram rechaza el id |
| Álbumes | `send_photos`, máximo 10 | Una foto o álbum |
| Preparación de imágenes | `tools/prepare_image.py` | Recorte central, escala, `--trim-bottom` y exportación JPEG |
| Procedencia adjunta | `.prompt.md` y `media.yaml` junto a cada imagen; `tests/test_content.py` exige ambos | Metadatos de producción; varios prompts siguen incompletos |
| «Ver lugar» | Botón 🖼️ en cada escena (0.10.5), lee `<lugar>/images/` | La imagen del lugar (de noche, la `.night` si existe); sin imagen, una ventanita «aún no hay pintor» |
| Dado decorativo | Tiradas manuales (`/settings`) | Animación d6 de Telegram; el resultado real lo calcula el d20 del motor |
| Laboratorio | `content/officina/` (0.8.3), fuera del catálogo y de git | Nada: solo para pruebas de Josue |

Inventario binario: **28 imágenes** (16 de clase 1,916 MB; 10 de criaturas 1,064 MB; ciudad de día y de noche 0,30 MB). Lo que falta, con su prompt, está en [`TODO-images.md`](../TODO-images.md).

Las diez criaturas: bandido, capitán bandido, goblin explorador, lobo gris, esqueleto de la cripta, Guardián de la Cripta, jabalí, murciélago de cueva, Viejo Colmillo y rata gigante. El Guardián es **Ser Aldren**, un caballero muerto que custodia el relicario (canon del YAML). Su armadura, rostro y color de brillo necesitan referencia artística aprobada. El Viejo Colmillo es desde la 0.8.2 el jefe final del tutorial: candidato a ilustración de evento.

### PLANIFICADO, TODAVÍA NO IMPLEMENTADO

- Imágenes de los lugares (el botón ya existe); retratos de NPC e integración.
- Música de taberna y ambientes opcionales; banco de voces y TTS de momentos importantes.
- Mapas ilustrados de continente, ciudad y mazmorra con posición y niebla individual.
- Tarjeta compartible de personaje, marcos y pack de stickers.
- Efectos de sonido y animaciones propias.
- Créditos accesibles al jugador (`/credits`) y flujo formal de revisión de activos.
- Imagen de cada linaje en `/lineage`; foto de perfil del bot y de los canales.

No hay archivos de audio en el contenido ni envío de música/voz en los handlers.

## 3. Contradicciones y documentación pendiente

| Hallazgo | Interpretación correcta | Estado |
|---|---|---|
| La antigua `audiovisual.md` decía «faltan Mago, Druida y Bardo» | Superado en 0.5.1 y 0.7.3: hay 16 retratos | Resuelto en 0.8.3: este documento lleva el inventario actual |
| `/monster_<clave>` no figuraba en audiovisual | Existe desde 0.7.19 | Resuelto |
| «Aún no hay imagen por lugar» junto a una panorámica | Zona y lugar son niveles distintos | Solo hay imagen de zona; faltan portadas de lugares |
| Roadmap con pendientes bajo 0.2.x–0.7.x | Versiones candidatas no actualizadas | Resuelto con `iter.md` |
| Guía antigua proponía `assets/` global y tablas `assets`, `location_media` | El proyecto decidió carpetas junto al contenido y DB solo para caché | Se conserva el esquema real |
| Ruta futura de NPC `content/npcs/<npc>/portrait.jpg` | No hay cargador de retratos de NPC | Propuesta: `content/npcs/<npc>/images/portrait.jpg`, a decidir antes de integrar |
| «Telegram siempre reduce las fotos a 1280 px» | La documentación de `sendPhoto` no lo garantiza | 1280 × 720 es estándar propio de entrega |
| `prepare_image.py` usa JPEG calidad 85 | No garantiza ≤ 350 KB ni exporta WebP | Comprobar el peso final; no pasarle `.webp` sin adaptarla |
| Créditos «uso propio» y «generada con IA» | Notas internas, no términos | Completar procedencia, plan y términos |
| Modo silencioso como idea de interfaz | No es un ajuste implementado | Propuesta |
| La guía pone a Elian como tabernero | El tabernero real es Bram | No introducir a Elian como canon |

Los prompts de Paladín no especifican variaciones por sexo; otros archivos son plantillas PENDIENTE. No reconstruir un prompt exacto desde una imagen: si se perdió, guardar «reconstrucción aproximada».

## 4. Decisiones documentadas vigentes

1. La IA interpreta y narra; el motor valida y resuelve. Una imagen nunca abre una puerta, crea una ruta ni prueba que un NPC esté presente.
2. Solo `oathforge/services/` escribe estado, también preferencias multimedia y cachés persistentes.
3. Los activos se producen, revisan y reutilizan; no se generan en cada turno.
4. Los medios van junto al nodo de contenido; los ids de lugar son globales y no dependen de la carpeta.
5. Solo versiones de entrega optimizadas van en git; originales grandes y archivos de edición se guardan fuera (Drive).
6. `media.yaml` recoge créditos/licencia; `<nombre>.prompt.md` acompaña a cada imagen. La DB contiene la caché de `file_id` por bot y checksum (`media_files`).
7. Variantes `.night`, `.male` y `.female` siguen las convenciones existentes.
8. Textos visibles en español e inglés. Cada audio hablado necesita equivalente textual.
9. Sin nombres ni texto dentro del generador: van en el caption o se componen con Pillow/SVG.
10. Gemini sigue siendo el proveedor del DM. Las herramientas de arte o audio no sustituyen al narrador.
11. Las pruebas se hacen en `content/officina/`; solo se integra un activo aprobado.

## 5. Biblia visual propuesta

**DECISIÓN (0.10.4): estilo de libro de rol en gouache.** Josue lo eligió con la nueva Crownreach de día y de noche. Sufijo común de todos los prompts:

```text
Tabletop RPG book illustration in opaque gouache, fine details, earthy colors with jewel-toned accents, subtle painted texture. Full-bleed, no border, no text, no watermark.
```

Orden del prompt: qué es y desde dónde se ve → detalles concretos → luz en una frase → estilo. Las versiones de noche salen de la imagen de día aprobada (Image to Image o edición), cambiando solo la frase de luz. Prompt base, regla de noche y lista de pendientes en [`TODO-images.md`](../TODO-images.md). Los estilos de §6 quedan como histórico de la exploración; las 26 imágenes anteriores se rehacen al nuevo estilo con baja prioridad.

**PROPUESTA NUEVA: fantasía de juramentos, civilización y ruinas**, con lugares habitables y cálidos que contrasten con lo inquietante del exterior. No convertir Aetherfall en una sucesión de oscuridad y calaveras.

| Elemento | Ya existe en contenido | Propuesta estética, pendiente |
|---|---|---|
| Crownreach | Río, catedrales, puentes de piedra, tejados rojos y castillo en la colina | Piedra marfil, cubiertas terracota, río verde azulado, silueta reconocible |
| Catedral de referencia | La ciudad menciona catedrales; el prompt existente una catedral de piedra clara | Una catedral con dos torres y rosetón; no confundirla con la Capilla del Alba |
| La Corona Rota | Taberna de Bram, con fogón y posada | Vigas oscuras, hogar ámbar y emblema de corona rota sin letras |
| Cripta Hundida | Mazmorra, santuario, relicario y Ser Aldren | Piedra húmeda, azul verdoso espectral y luz cálida puntual |
| Pacto y Sindicato | Facciones y NPC existentes | Familias de materiales y emblemas distintos, previa aprobación |
| Clases | Ocho clases con retratos | Marcos y siluetas legibles; igual cuidado para todas |

Paleta candidata: marfil `#D9CEB8`, carbón `#22262A`, terracota `#A8543B`, oro viejo `#B99A55`, verde azulado `#39716F`, luz espectral `#7CBEC6`. Comprobar legibilidad a tamaño móvil.

Cada biblia de zona: imagen maestra aprobada, materiales, clima, paleta, skyline, escala de edificios, vestuario, 3 motivos recurrentes y 3 cosas que evitar. No reutilizar arquitectura real reconocible como referencia libre.

## 6. Cinco estilos que explorar

Todos se prueban con ciudad + criatura + taberna para comparar coherencia, no solo una imagen espectacular.

| Estilo | Qué aporta | Riesgo | Uso recomendado, pendiente |
|---|---|---|---|
| A. Pintura épica semirrealista | Atmósfera, materiales y continuidad con los prompts existentes | Saturación de detalle al reducir | Candidato principal para escenas, héroes y bestiario |
| B. Fantasía estilizada de formas grandes | Siluetas claras, personalidad y lectura móvil | Volverse caricaturesco | Alternativa fuerte para todo el juego |
| C. Óleo gótico tenebrista | Drama, juramentos y ruinas | Oscuridad que oculta información | Cripta, jefes y eventos |
| D. Tinta y acuarela de libro de viajes | Diario, exploración y cercanía artesanal | Poco contraste | Crónicas, mapas decorativos o estilo general |
| E. Pixel art de alta calidad | Identidad retro y potencial de animación | Píxeles incoherentes; limpieza manual | Ruta alternativa completa, sin mezclar con retratos realistas |

**Recomendación pendiente:** probar A y B primero (en `content/officina/estilos/`). Elegir un estilo principal y soportes secundarios con función clara (mapa en pergamino), no cinco estilos en la misma pantalla.

## 7. Banco de quince prompts

Prompts de exploración para Leonardo AI, en inglés, por debajo de 2.000 caracteres. No son prompts históricos de los archivos existentes. El 16:9 o 3:4 debe seleccionarse también en los ajustes del generador. Los detalles nuevos (torres, rosetón, color espectral, distribución de taberna) son propuestas de prueba; en producción prevalece una referencia aprobada.

### A. Pintura épica semirrealista

**01. Ciudad · Crownreach**

```text
Wide elevated view of Crownreach, a medieval fantasy capital along a river, pale stone bridges, dense red tiled roofs, a fortified castle on the hill. One prominent pale stone cathedral with twin square bell towers and a circular rose window near the river. Busy but legible streets, warm late-afternoon sunlight. Landscape 16:9. Painterly semi-realistic high fantasy RPG illustration, visible brushwork, believable materials, cinematic depth, controlled detail, strong focal point, teal shadows and warm gold light. No text, no letters, no logo, no watermark, no UI.
```

**02. Monstruo · Ser Aldren**

```text
Ser Aldren, the undead knight guarding the Sunken Crypt, standing alone in a damp stone sanctuary, ancient battered plate armor, spectral greatsword held point down, faint cold turquoise light in the helmet, solemn oathbound presence. Readable three-quarter figure, entire weapon visible, simple background, no gore. Vertical 3:4. Painterly semi-realistic high fantasy RPG illustration, visible brushwork, believable materials, cinematic depth, controlled detail, strong focal point, teal shadows and warm gold light. No text, no letters, no logo, no watermark, no UI.
```

**03. Lugar · La Corona Rota**

```text
Interior of the Broken Crown tavern in Crownreach, broad oak counter on the right, stone fireplace on the left, heavy dark wooden beams, round tables, amber lanterns, simple broken-crown emblem above the counter without lettering. A few small distant patrons, welcoming lived-in atmosphere, clear central aisle. Landscape 16:9. Painterly semi-realistic high fantasy RPG illustration, visible brushwork, believable materials, cinematic depth, controlled detail, strong focal point, teal shadows and warm gold light. No text, no letters, no logo, no watermark, no UI.
```

### B. Fantasía estilizada

**04. Ciudad · Crownreach**

```text
Wide elevated view of Crownreach, a medieval fantasy capital along a river, pale stone bridges, dense red tiled roofs, a fortified castle on the hill. One prominent pale stone cathedral with twin square bell towers and a circular rose window near the river. Busy but legible streets, warm late-afternoon sunlight. Landscape 16:9. Stylized fantasy RPG illustration, hand-painted textures, bold readable silhouettes, slightly exaggerated proportions, clean shapes, rich restrained colors, soft volumetric light, charming but mature tone. No text, no letters, no logo, no watermark, no UI.
```

**05. Monstruo · Ser Aldren**

```text
Ser Aldren, the undead knight guarding the Sunken Crypt, standing alone in a damp stone sanctuary, ancient battered plate armor, spectral greatsword held point down, faint cold turquoise light in the helmet, solemn oathbound presence. Readable three-quarter figure, entire weapon visible, simple background, no gore. Vertical 3:4. Stylized fantasy RPG illustration, hand-painted textures, bold readable silhouettes, slightly exaggerated proportions, clean shapes, rich restrained colors, soft volumetric light, charming but mature tone. No text, no letters, no logo, no watermark, no UI.
```

**06. Lugar · La Corona Rota**

```text
Interior of the Broken Crown tavern in Crownreach, broad oak counter on the right, stone fireplace on the left, heavy dark wooden beams, round tables, amber lanterns, simple broken-crown emblem above the counter without lettering. A few small distant patrons, welcoming lived-in atmosphere, clear central aisle. Landscape 16:9. Stylized fantasy RPG illustration, hand-painted textures, bold readable silhouettes, slightly exaggerated proportions, clean shapes, rich restrained colors, soft volumetric light, charming but mature tone. No text, no letters, no logo, no watermark, no UI.
```

### C. Óleo gótico tenebrista

**07. Ciudad · Crownreach**

```text
Wide elevated view of Crownreach, a medieval fantasy capital along a river, pale stone bridges, dense red tiled roofs, a fortified castle on the hill. One prominent pale stone cathedral with twin square bell towers and a circular rose window near the river. Busy but legible streets, warm late-afternoon sunlight. Landscape 16:9. Gothic fantasy oil painting, dramatic chiaroscuro, layered oil brushwork, weathered textures, restrained earth colors, luminous focal point, solemn atmosphere, clearly readable forms outside the shadows. No text, no letters, no logo, no watermark, no UI.
```

**08. Monstruo · Ser Aldren**

```text
Ser Aldren, the undead knight guarding the Sunken Crypt, standing alone in a damp stone sanctuary, ancient battered plate armor, spectral greatsword held point down, faint cold turquoise light in the helmet, solemn oathbound presence. Readable three-quarter figure, entire weapon visible, simple background, no gore. Vertical 3:4. Gothic fantasy oil painting, dramatic chiaroscuro, layered oil brushwork, weathered textures, restrained earth colors, luminous focal point, solemn atmosphere, clearly readable forms outside the shadows. No text, no letters, no logo, no watermark, no UI.
```

**09. Lugar · La Corona Rota**

```text
Interior of the Broken Crown tavern in Crownreach, broad oak counter on the right, stone fireplace on the left, heavy dark wooden beams, round tables, amber lanterns, simple broken-crown emblem above the counter without lettering. A few small distant patrons, welcoming lived-in atmosphere, clear central aisle. Landscape 16:9. Gothic fantasy oil painting, dramatic chiaroscuro, layered oil brushwork, weathered textures, restrained earth colors, luminous focal point, solemn atmosphere, clearly readable forms outside the shadows. No text, no letters, no logo, no watermark, no UI.
```

### D. Tinta y acuarela

**10. Ciudad · Crownreach**

```text
Wide elevated view of Crownreach, a medieval fantasy capital along a river, pale stone bridges, dense red tiled roofs, a fortified castle on the hill. One prominent pale stone cathedral with twin square bell towers and a circular rose window near the river. Busy but legible streets, warm late-afternoon sunlight. Landscape 16:9. Fantasy travel-journal illustration in fine ink and watercolor, confident linework, translucent washes, warm ivory paper, selective intricate details, airy composition, vivid readable focal point. No text, no letters, no logo, no watermark, no UI.
```

**11. Monstruo · Ser Aldren**

```text
Ser Aldren, the undead knight guarding the Sunken Crypt, standing alone in a damp stone sanctuary, ancient battered plate armor, spectral greatsword held point down, faint cold turquoise light in the helmet, solemn oathbound presence. Readable three-quarter figure, entire weapon visible, simple background, no gore. Vertical 3:4. Fantasy travel-journal illustration in fine ink and watercolor, confident linework, translucent washes, warm ivory paper, selective intricate details, airy composition, vivid readable focal point. No text, no letters, no logo, no watermark, no UI.
```

**12. Lugar · La Corona Rota**

```text
Interior of the Broken Crown tavern in Crownreach, broad oak counter on the right, stone fireplace on the left, heavy dark wooden beams, round tables, amber lanterns, simple broken-crown emblem above the counter without lettering. A few small distant patrons, welcoming lived-in atmosphere, clear central aisle. Landscape 16:9. Fantasy travel-journal illustration in fine ink and watercolor, confident linework, translucent washes, warm ivory paper, selective intricate details, airy composition, vivid readable focal point. No text, no letters, no logo, no watermark, no UI.
```

### E. Pixel art

**13. Ciudad · Crownreach**

```text
Wide elevated view of Crownreach, a medieval fantasy capital along a river, pale stone bridges, dense red tiled roofs, a fortified castle on the hill. One prominent pale stone cathedral with twin square bell towers and a circular rose window near the river. Busy but legible streets, warm late-afternoon sunlight. Landscape 16:9. High-quality 2D fantasy pixel art, deliberate square pixel clusters, consistent pixel scale, limited 32-color palette, strong silhouettes, crisp hard edges, careful dithering, no blur, no painted gradients. No text, no letters, no logo, no watermark, no UI.
```

**14. Monstruo · Ser Aldren**

```text
Ser Aldren, the undead knight guarding the Sunken Crypt, standing alone in a damp stone sanctuary, ancient battered plate armor, spectral greatsword held point down, faint cold turquoise light in the helmet, solemn oathbound presence. Readable three-quarter figure, entire weapon visible, simple background, no gore. Vertical 3:4. High-quality 2D fantasy pixel art, deliberate square pixel clusters, consistent pixel scale, limited 32-color palette, strong silhouettes, crisp hard edges, careful dithering, no blur, no painted gradients. No text, no letters, no logo, no watermark, no UI.
```

**15. Lugar · La Corona Rota**

```text
Interior of the Broken Crown tavern in Crownreach, broad oak counter on the right, stone fireplace on the left, heavy dark wooden beams, round tables, amber lanterns, simple broken-crown emblem above the counter without lettering. A few small distant patrons, welcoming lived-in atmosphere, clear central aisle. Landscape 16:9. High-quality 2D fantasy pixel art, deliberate square pixel clusters, consistent pixel scale, limited 32-color palette, strong silhouettes, crisp hard edges, careful dithering, no blur, no painted gradients. No text, no letters, no logo, no watermark, no UI.
```

**Negativo opcional**, solo si el modelo ofrece un campo compatible: `text, letters, watermark, logo, UI, blurry focal subject, malformed anatomy, duplicate limbs, cropped weapon, modern objects`. Para pixel art añadir `anti-aliasing, smooth gradients, inconsistent pixel size`. Si no hay campo negativo, conservar las restricciones esenciales en el prompt normal.

Prompts históricos de la guía (tabernas, bosque, jefe, tabernero, paladín de venganza, Crownreach de noche, mapa mundial, taberna interior): en el [anexo de Possibilium](Possibilium.md#anexo-audio).

## 8. Consistencia de ciudades, NPC y criaturas

### Crownreach y la misma catedral

1. Elegir una panorámica maestra. Identificar en ella el río, los puentes, el castillo y la catedral.
2. Guardar el original y un recorte de la catedral como referencia. Un nombre propio y una semilla no garantizan la misma arquitectura en otro plano.
3. Preparar una ficha con número de torres, tejados, rosetón, color de piedra, acceso y posición respecto al río, sacada de la imagen aprobada.
4. Generar el exterior cercano con la referencia visual y un prompt centrado en el edificio. Probar edición localizada o referencia de contenido antes de regenerar todo.
5. Crear noche, lluvia e interior desde esa referencia. Descartar imágenes bonitas que contradigan la geografía.
6. El mapa sigue siendo la fuente espacial del motor. Si una ilustración inventa otro puente, se corrige el arte; no se crea un camino.

No hay porcentajes de referencia universales; ajustar una variable cada vez.

### NPC

Bram: corpulento, calvo, de mediana edad (`npcs.yaml`); no copiar el tabernero barbado de la guía. Mira: informante encapuchada. Vale: veterana robusta y curtida. Holt: oficial rígido y honrado. Tessa: herrera alegre con hollín y quemaduras en los antebrazos. Ysolde: hermana de la Capilla del Alba. No inventar marcas faciales permanentes sin aprobarlas.

Rostro canónico, busto, vestuario y tres expresiones al principio: neutral, preocupado y satisfecho.

### Criaturas y héroes

Una lámina por especie/variante; los estados los muestra la interfaz. Ser Aldren no cambia de armadura entre bestiario y escena especial. El retrato de clase es representativo: no implica el rostro, linaje o equipo del personaje.

## 9. Catálogo de contenido por producir

**PROPUESTA**, por valor de reutilización.

| Familia | Primer lote | Uso |
|---|---|---|
| Ciudad | Revisar Crownreach y producir noche consistente | Vista de zona |
| Lugares | La Corona Rota, plaza, mercado, capilla, Bosque de los Susurros, entrada y santuario de la cripta | Escena visual opcional |
| Actividades | Mina del Paso Viejo, Arboleda Antigua, Claro de la Raíz Roja, Ribera de Silverbrook, Prado de los Colmillos | Minería, tala, hierbas, pesca y caza |
| NPC | Vale (tutorial), Bram, Tessa, Mira; después Holt e Ysolde | Identificación y diálogo |
| Bestiario | Revisar las diez imágenes y completar procedencia | Coherencia sin rehacerlas |
| Eventos | Victoria sobre el Viejo Colmillo (fin del tutorial), un juramento y un descubrimiento | Hitos, no cada ataque |
| Comunidad | Avatar del bot, emblema del canal y fogata del grupo | Tres símbolos legibles en recorte circular |
| Linajes | Humano, elfo, enano y orco para `/lineage` | Creación de personaje |

Banco futuro: taberna clandestina, puerto, regiones de nieve/volcán, biblioteca olvidada y asedios. No producirlos como lugares presentes.

## 10. Música y ambientes

**PROPUESTA PREVIA:** bases instrumentales reutilizables de 60–90 s, dos entregas por pista (`music_only` y `ambience_mix` con fuego, vasos y murmullos CC0). El empalme se prepara en edición: escribir «seamless loop» no garantiza un bucle. El bot entrega una pista a petición («Escuchar ambiente»); Telegram no reproduce música de fondo automáticamente.

Primera pieza: **La Corona Rota**, laúd y flauta de madera, cuerda suave, percusión discreta, fuego y murmullos muy bajos, sin diálogos que revelen rumores inexistentes. Sin voces sirve para ES y EN.

Banco ampliado: 3 tabernas, 4 regiones, 2 mazmorras, 2 combates y 1 tema principal. Plan inicial: 2–3 pistas (taberna, bosque, cripta).

- **Taberna:** `Instrumental medieval fantasy tavern music, warm lute melody, wooden flute, gentle fiddle, light hand percussion, welcoming acoustic room, 80 BPM, no vocals, no electronic instruments, loop-friendly ending.`
- **Clandestina:** `Dark medieval inn instrumental, low fiddle, sparse hammered dulcimer, subdued frame drum, secretive intimate mood, slow tempo, natural instruments, no vocals.`
- **Bosque:** `Ancient fantasy forest exploration instrumental, breathy wooden flute, soft harp, sparse strings, peaceful yet unsettling, spacious gentle dynamics, no vocals.`
- **Jefe:** `Dark fantasy boss battle instrumental, powerful war drums, brass and fast low strings, solemn relentless tension, 140 BPM, no vocals, no lyrics.`

Edición: revisar saturación, quitar clics, suavizar entrada/salida y equilibrar volumen percibido. Guardar mezcla editable y máster antes de exportar.

## 11. Voces y escenas narradas

**PROPUESTA PREVIA:** solo introducciones, juramentos, confesiones, amenazas de jefe y diálogos importantes. Nunca locutar automáticamente cada mensaje de Gemini.

Tres vías: frases pregrabadas y cacheadas; generación excepcional bajo demanda (en cola); voces humanas con consentimiento. Empezar con 4–6 frases por NPC de prueba (30–50 es expansión).

Ficha de voz: NPC, idioma/acento, proveedor, modelo, voz, velocidad, pronunciación de nombres, intención, fecha, permisos y referencia canónica. Bram podría tener voz grave y pausada (velocidad orientativa 0,93).

Flujo: motor resuelve → texto localizado validado → si el jugador pide voz, buscar audio por hash de texto + idioma + voz/modelo/ajustes → reutilizar o generar fuera de la transacción → enviar (`sendVoice`, OGG/Opus: `ffmpeg -i in.mp3 -c:a libopus -b:a 32k out.ogg`). Nunca bloquear una escritura esperando al TTS.

Si una grabación depende de una misión, validar su acceso como el diálogo. ES/EN para frases canónicas importantes; si falta un idioma, texto completo. Nunca narrar en el idioma incorrecto por un fallback silencioso.

Ejemplo:

- ES: «Bram baja la voz. “Esta noche hay alguien esperando en la trastienda.”» + «🔊 Escuchar voz».
- EN: “Bram lowers his voice. ‘Someone is waiting in the back room tonight.’” + “🔊 Hear voice”.

## 12. Mapas, iconos, tarjetas y animación

### Mapas

**PROPUESTA PREVIA:** macro con Azgaar; plano urbano con Watabou; mazmorra con Tiled/Krita. El plano publicable debe corresponder al grafo real de `content/world/`.

El `/map` actual es textual y de viaje directo (0.8.0): un futuro mapa gráfico no debe obligar a atravesar diez pantallas para el mismo viaje. Capas: posición, lugares conocidos, objetivos autorizados, peligro y rutas bloqueadas, renderizadas por personaje. No enviar al grupo un mapa con información privada. Nombres y líneas con SVG/Pillow.

### Iconos y tarjetas

Un conjunto consistente por categorías vale más que un icono único por espada (Kenney CC0, Game-icons CC BY). Rareza con forma/símbolo además de color.

Tarjeta de héroe de 900 × 1200: nombre, retrato, clase, nivel, especialización, facción, PV, seis atributos, dos habilidades y equipo destacado, generada desde datos del motor, sin notas privadas ni identificadores.

### Stickers y animaciones

Pack inicial: Bram saluda, Mira sospecha, Tessa aprueba, Vale celebra, dado de fortuna y fogata. Partir de retratos aprobados.

Animaciones candidatas: brasas, niebla de la cripta, brillo de reliquia y bandera de ciudad. No confirman botín ni daño; son extras que no bloquean la escena. Requisitos de packs y codecs, a comprobar al implementar.

## 13. Experiencia en Telegram

**PROPUESTA NUEVA:** imagen a petición como modo inicial y audio siempre voluntario. Una preferencia futura podría mostrar la ilustración en la primera visita, guardada desde `services/`.

1. Llegas a La Corona Rota: escena compacta con lugar, descripción y acciones.
2. «🖼️ Ver lugar / View place» abre la imagen.
3. «🎵 Escuchar ambiente / Listen to ambience» entrega la pista.
4. Hablas con Bram; voz opcional solo si existe una grabación válida.
5. Una segunda visita no vuelve a enviar foto y canción.

| Uso | Método | Entrega |
|---|---|---|
| Ciudad, criatura, retrato | `sendPhoto` (actual) | JPEG optimizado |
| Álbum | `sendMediaGroup` (actual) | 2–10 imágenes |
| Mapa de detalle | `sendDocument` | PNG con texto legible |
| Música | `sendAudio` | MP3/M4A |
| Voz | `sendVoice` | OGG/Opus |
| Animación breve | `sendAnimation` | MP4/GIF |
| Reenvío | `file_id` guardado | Sin volver a subir |

La API admite fotos de hasta 10 MB, con suma de ancho y alto ≤ 10.000 y relación de aspecto ≤ 20. 1280 × 720 es nuestro objetivo de entrega, no un límite de la API.

## 14. Producción, formatos y metadatos

### Estructura vigente y extensiones propuestas

```text
content/world/world.yaml                       # start y orden de continentes
content/world/<continente>/continent.yaml      # images/map.jpg (futuro)
content/world/<continente>/<zona>/zone.yaml
content/world/<continente>/<zona>/images/panorama.jpg         # «Ver ciudad»
content/world/<continente>/<zona>/images/panorama.night.jpg   # variante nocturna
content/world/<continente>/<zona>/<lugar>/place.yaml          # hub: true → «Ver ciudad»
content/world/<continente>/<zona>/<lugar>/images/cover.jpg    # (futuro) «Ver lugar»
content/classes/<clase>/images/portrait.male.jpg | portrait.female.jpg
content/monsters/<criatura>/images/portrait.jpg
content/npcs/<npc>/images/portrait.jpg         # (propuesta) retratos de NPC
content/officina/<prueba>/<nombre>.jpg + <nombre>.prompt.md   # laboratorio, fuera de git
```

Junto a cada imagen integrada: `media.yaml` (en su carpeta `images/`) y `<stem>.prompt.md`, por ejemplo `portrait.female.prompt.md`. `audio/` junto a zona, lugar o NPC queda pendiente de aprobación. Los originales editables siguen fuera de git. No crear un segundo árbol `assets/`.

### Flujo de un activo

borrador en `content/officina/<prueba>/` → revisión visual → revisión de procedencia → aprobado → copiar la versión de entrega a su carpeta `images/` con `media.yaml` y `.prompt.md` → integrado → retirado. El código avisa de créditos o prompts ausentes y el test lo exige, pero no verifica el contenido de una licencia.

### Entregas

| Tipo | Proporción/tamaño | Exportación |
|---|---|---|
| Ciudad, lugar, evento | 16:9, 1280 × 720 | JPEG calidad 85 progresivo, sin EXIF; objetivo ≤ 350 KB |
| Clase, NPC, criatura | 3:4, 768 × 1024 | JPEG calidad 85 |
| Tarjeta | 3:4, 900 × 1200 | JPEG/PNG generado desde datos |
| Mapa | ~2048 px lado largo | PNG como documento; fuente SVG/PNG aparte |
| Icono | 1:1, 128 × 128 | PNG con transparencia |
| Sticker | Lienzo 512 × 512 | PNG/WebP conforme al pack |
| Música | 60–90 s | MP3 |
| Voz | Frases breves | OGG/Opus |

Originales orientativos: entornos 2560 × 1440 o nativo del modelo (1344 × 768); retratos 1536 × 2048. No ampliar una imagen pobre para cumplir una cifra.

`prepare_image.py` recorta al centro: comprobar que no corta orejas, manos, armas ni torres. Un PNG con alfa pierde la transparencia por el camino JPEG. Para mapas, pixel art y tarjetas, no aplicar recorte fotográfico; el pixel art necesita escalado entero con vecino más cercano (la utilidad usa LANCZOS).

### media.yaml

Mapa por nombre de archivo:

```yaml
cover.jpg:
  author: Josue
  source: Leonardo AI
  license: "PENDIENTE: términos y plan aplicables"
  notes: "Entrega aprobada visualmente; registrar derechos antes de publicación"
```

Completar en el prompt o en el registro: herramienta, modelo/versión, fecha, prompt positivo, negativo, semilla, ajustes, referencia, dimensiones originales, retoques, responsable de revisión y estado. No inventar valores desconocidos; para fotos o audios no generados, registrar la procedencia real.

## 15. Herramientas, procedencia y licencias

- **Imágenes:** Leonardo AI con producción manual; Krita/GIMP para correcciones. FLUX.1 schnell / FLUX.2 klein 4B (Apache 2.0, local) como alternativa; no confundir klein 4B con 9B, no comercial.
- **Audio:** Stable Audio para una pista; edición con Audacity o BandLab. ACE-Step local como alternativa. Revisar la procedencia de los samples.
- **Voz:** evaluar TTSMaker u otra voz con términos claros; Kokoro, Chatterbox, Piper y edge-tts son alternativas mencionadas, no dependencias aprobadas.
- **Mapas:** Azgaar/Watabou como boceto; Tiled/Krita/SVG para ajustar al mundo real.
- **Iconos y SFX:** Kenney, Game-icons y Freesound; licencia por paquete o archivo.

Comprobaciones y límites:

- Leonardo comunica permiso comercial para outputs gratuitos bajo sus términos, con generaciones públicas en el plan gratis. No prometer exclusividad ni privacidad.
- Stable Audio permite uso comercial y distribución bajo sus términos; conservar los términos aplicables a cada activo.
- No se han revalidado Suno, AIVA, ElevenLabs, MusicGen, TTSMaker, FLUX, Kokoro, Chatterbox, Piper, Inkarnate ni Dungeon Scrawl. Las restricciones de la guía (no comercial en planes gratuitos de Suno/AIVA/ElevenLabs/Inkarnate/Dungeon Scrawl y pesos de MusicGen) son referencias históricas.
- Diferenciar licencia de código, pesos, voces, muestras y servicio.
- Enviar un MP3 por el bot es distribuir el archivo: comprobar que la licencia lo permite, no solo «usar en un vídeo».
- CC BY exige atribución y créditos accesibles (`/credits`, propuesta). CC0: comprobar cada archivo.

No usar recursos de juegos comerciales. Voces humanas: consentimiento y alcance de uso; nunca clonar a alguien por tener una grabación.

## 16. Costes, prioridades y primera versión

Los archivos precocinados no consumen Gemini por visualización. Sí hay coste de producción, espacio, envío y, si se elige, TTS. La caché `file_id` evita re-subidas, no el consumo de datos del jugador.

Presupuesto orientativo heredado: 12 pistas (~24 MB), 30 voces (~3,6 MB), 50 imágenes (~25 MB) y 10 mapas (~10 MB): unos **63 MB**. Al pasar de ~100 MB, valorar Git LFS u otra entrega.

### Primera versión implementable — PROPUESTA NUEVA

1. Completar prompts/procedencia de las 27 imágenes y elegir estilo con las pruebas en officina.
2. Producir **tres portadas**: taberna, bosque y entrada de cripta. Integrar «Ver lugar» con el catálogo de lugares existente (`location_images`).
3. Producir **un retrato**, Vale o Bram, y añadir la categoría de NPC al catálogo de forma consistente.
4. Producir **una pista**, La Corona Rota, con botón voluntario y caché de audio adaptada.
5. Un saludo de Bram en ES y EN solo después de validar interés por audio.
6. Evaluar con amigos: reconocimiento del lugar, uso de botones, peso de descarga, exceso de mensajes y coherencia.

La producción puede avanzar sin bloquear cooperativo, balance ni tutorial.

| Mejora | Depende de | Áreas que actualizar |
|---|---|---|
| Portadas de lugares | Arte aprobado y botón | `content/world/`, handlers, render, locales es/en |
| Retratos NPC | Ruta y catálogo acordados | `content/npcs/`, `content/media.py`, loader y handlers |
| Audio ambiente | Archivo autorizado y envío/caché de audio | `services/media.py`, catálogo, handlers, ajustes |
| Voz | Texto válido, idioma y permisos | Diálogo, catálogo, servicios y locales |
| Mapas personales | Grafo y descubrimiento | Mundo, render de mapa y capa gráfica |
| Tarjeta compartible | Composición y datos autorizados | Render de ficha, botón y privacidad |

Los handlers seleccionan y envían; el motor mantiene las reglas y `services/` las escrituras.

## 17. Organización documental

Hecho en la v0.8.3:

- `planning/audiovisual.md` se sustituyó por este archivo y se actualizaron los enlaces (`media.yaml`, `world.yaml`, `tools/prepare_image.py`, TODO).
- La guía audiovisual en PDF se retiró; su texto íntegro está en el anexo de Possibilium.
- `content/**/images/*.prompt.md` y `media.yaml` se conservan: ars no sustituye los prompts históricos de cada activo.
- Se creó `content/officina/` para pruebas.

## 18. Preguntas abiertas

- ~~¿A, B, C, D o E como estilo principal?~~ Resuelto en 0.10.4: gouache de libro de rol (§5).
- ¿Imagen siempre a petición o primera visita automática? Recomendación: a petición durante la beta.
- ¿Quién aprueba calidad y procedencia? Propuesta: Josue o una persona delegada.
- ¿Voz ES/EN desde el primer piloto? Recomendación: sí, para las pocas frases del piloto.
- ¿La catedral tendrá dos torres y rosetón? Revisar primero la panorámica aprobada.
- ¿Audio apagado por defecto (modo silencioso) y que el jugador lo active?

## 19. Fuentes y trazabilidad

Repositorio auditado: `main` en `a1a7687` (0.8.0), comprobado de nuevo en 0.8.2. Lecturas: `oathforge/content/media.py`, `oathforge/services/media.py`, handlers, render, `tools/prepare_image.py`, YAML de ciudad/NPC/monstruos e imágenes/prompts/créditos. Guía audiovisual: texto íntegro en el [anexo](Possibilium.md#anexo-audio).

Documentación externa consultada el 17-10-2026:

- Telegram Bot API: https://core.telegram.org/bots/api#sendphoto
- Leonardo: https://www.leonardo.ai/news/can-you-use-ai-generated-images-commercially
- Leonardo, uso comercial: https://intercom.help/leonardo-ai/en/articles/8044018-commercial-usage
- Stable Audio: https://kb.stability.ai/knowledge-base/stable-audio-commerical-and-usage-licensing

Las condiciones externas son temporales: este documento fija una revisión, no garantías permanentes.
