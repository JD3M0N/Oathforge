# TODO-images — imágenes pendientes

Lista de lo que falta por ilustrar, con su prompt sugerido. Dirección artística en [planning/ars.md](planning/ars.md); fase F02 de [planning/roadmap.md](planning/roadmap.md#F02).

## Cómo se escribe un prompt

**Estilo** (va siempre al final; donde pone `[ESTILO]`, pega esto):

```text
Tabletop RPG book illustration in opaque gouache, fine details, earthy colors with jewel-toned accents, subtle painted texture. Full-bleed, no border, no text, no watermark.
```

**Orden:** qué es y desde dónde se ve → 3–6 detalles concretos → la luz en una frase → `[ESTILO]`. La proporción se elige en el generador.

| Tipo | Proporción | Entrega | Preparar |
|---|---|---|---|
| Zona, lugar, evento, mapa | 16:9 | 1280 × 720 | `tools/prepare_image.py src dst --kind panorama` |
| PNJ, linaje, clase, criatura | 3:4 | 768 × 1024 | `--kind portrait` |
| Avatar, emblema | 1:1 | 512 × 512 | `--kind sticker` |

Para retratos, la escena es: `<quién>, <rasgos>, <ropa>, <pose>, waist-up portrait, simple softly painted background.`

**Ejemplo, Crownreach de día** (ya hecha, `panorama.jpg`):

```text
Crownreach, a medieval fantasy capital beside a river, seen from a nearby hillside. Stone bridges, red tiled roofs, a pale stone cathedral by the central square, a fortified castle on the hill behind. Teal and gold banners, market stalls, small distant townspeople. Warm afternoon sunlight. [ESTILO]
```

### Versión de noche (`<nombre>.night.jpg`)

No se regenera desde texto: la ciudad cambiaría. Se parte de la imagen de día **aprobada**:

1. Leonardo → Image Guidance → **Image to Image** con la imagen de día (fuerza 0,6–0,7: más alto, más fiel), misma semilla y proporción. O un modelo de edición si lo hay.
2. El mismo prompt cambiando **solo** la frase de luz por:
   `Night under a clear starry blue sky, warm lamplit windows, lanterns in the square, small braziers on the battlements, lights reflected in the river. Keep the same composition.`
3. Con un modelo de edición basta: `Turn this scene into night; keep the exact composition and buildings. Starry blue sky, lamplit windows, lanterns, lights reflected in the water. No fire on buildings.`
4. Comprobar que no cambian puentes, catedral ni castillo; si cambian, se descarta.

En interiores y bosques la frase de noche se adapta (velas, luna, niebla), pero siempre desde la imagen de día.

### Flujo

Prueba en `content/officina/` → Josue aprueba → `prepare_image.py` a la carpeta `images/` del nodo → entrada en `media.yaml` y `<nombre>.prompt.md` al lado (lo exige `tests/test_content.py`) → tachar aquí.

---

## Zonas · `content/world/terra_coronata/<zona>/images/panorama.jpg`

Se ven con «🖼️ Ver lugar» en la plaza de la ciudad (lugar `hub`) mientras la plaza no tenga imagen propia.

- [x] **Crownreach** de día y de noche (`panorama.jpg`, `panorama.night.jpg`, 0.10.4).
- [ ] **Thornwood** (`thornwood/`)
  ```text
  Thornwood, an ancient oak forest seen from a hill at its edge. A cracked old stone causeway winds into the trees, mossy standing stones from old druidic oaths, a cold stream glinting between the trunks, the towers of a distant city on the horizon. Soft overcast afternoon light with drifting mist. [ESTILO]
  ```
- [ ] **Cripta Hundida** (`sunken_crypt/`)
  ```text
  The Sunken Crypt, a forgotten tomb half-swallowed by the roots of a great oak forest. Moss-covered stone arch, worn steps descending into darkness, a bronze door glimpsed below, faceless knight statues tilted in the earth. Cold blue-green shadows with a single warm shaft of light. [ESTILO]
  ```

## Mapa · `content/world/terra_coronata/images/map.jpg`

- [ ] **Terra Coronata ilustrado** (no hay botón todavía). Debe coincidir con el grafo de `content/world/`: Crownreach junto al río, Camino del Viejo Rey hacia Thornwood, el prado al sur, la mina en el paso, la cripta bajo el bosque. Nombres con Pillow, nunca en el generador.
  ```text
  Illustrated fantasy regional map seen from above, painted on aged parchment. A walled river capital in the center, an old road leading into a vast oak forest, a grassy meadow to the south, a mine in a rocky pass, a stream running from the hills, a small tomb hidden in the woods. Compass rose drawn without letters. [ESTILO]
  ```

## Lugares · `<lugar>/images/cover.jpg`

Se ven con «🖼️ Ver lugar» (0.10.5); mientras falten, el botón responde con una ventanita. Por prioridad. 🌙 = el lugar tiene texto de noche: hacer también `cover.night.jpg`.

### Primer lote

- [ ] **Taberna La Corona Rota** 🌙 (`crownreach/broken_crown_tavern/`)
  ```text
  Interior of the Broken Crown tavern, a lived-in medieval inn. Broad oak counter, heavy dark beams, a stone fireplace with roasting meat, round tables, two mercenaries arguing by the fire, a simple broken-crown emblem carved above the counter. Warm amber firelight and lanterns. [ESTILO]
  ```
- [ ] **Bosque de los Susurros** (`thornwood/whispering_woods/`)
  ```text
  The Whispering Woods, a dense old oak forest in the rain. Huge dark trunks, ferns and wet leaves, a narrow trail vanishing between the trees, mist hanging low, a faint sense of being watched. Grey rainy light filtering through the canopy. [ESTILO]
  ```
- [ ] **Cripta Hundida: entrada** (`sunken_crypt/crypt_entrance/`)
  ```text
  Entrance of the Sunken Crypt, slippery moss-covered stone steps leading down to a heavy bronze door with a worn knightly relief. Roots breaking through the walls, damp earth, puddles on the stairs. Cold blue-green gloom with warm torchlight at the top of the steps. [ESTILO]
  ```

### Crownreach

- [ ] **Plaza de Crownreach** 🌙 (`crownreach/crownreach_plaza/`)
  ```text
  Crownreach Plaza, a great paved medieval square bustling with carts, town criers and Silver Guard soldiers in silver-grey tabards. A white stone chapel on the north side, a recruitment table with a veteran sergeant, teal and gold banners. Warm afternoon sunlight. [ESTILO]
  ```
- [ ] **Mercado de Crownreach** 🌙 (`crownreach/crownreach_market/`)
  ```text
  Crownreach Market, narrow lanes of colorful awnings and wooden stalls with cloth, fruit, rope and potions. A smithy with an anvil at the end of the lane, haggling merchants and customers. Bright warm daylight. [ESTILO]
  ```
- [ ] **Capilla del Alba** 🌙 (`crownreach/crownreach_chapel/`)
  ```text
  Interior of the Chapel of the Dawn, a small white stone chapel smelling of wax and herbs. A plain altar with candles, wounded adventurers resting on the pews, a calm priestess bandaging an arm, a copper offering bowl. Soft golden morning light through tall windows. [ESTILO]
  ```
- [ ] **Barrio de Oficios** 🌙 (`crownreach/crownreach_workshops/`)
  ```text
  Craftsmen's Row, a narrow medieval street of workshops behind the market, one stall per trade down both sides. Smiths at their anvils, an alchemist's bubbling stills, carpenters sawing planks, a tannery at the far end, each door with a slate board for apprentices. Smoke and sparks, warm afternoon light. [ESTILO]
  ```
- [ ] **Gremio de Aventureros** 🌙 (`crownreach/adventurers_guild/`)
  ```text
  Interior of an adventurers' guild hall of grey stone, the crest above the door and a notice board thick with pinned parchments. A smelting furnace glowing at the back, a sawing station by the window, hides on a curing rack, a long table of herbs being cleaned, recruits coming and going with sacks. Warm firelight and dusty sunbeams. [ESTILO]
  ```
- [ ] **Forja de Tessa** (`crownreach/forge_stall/`)
  ```text
  A smith's stall at the mouth of a medieval craft street, under a tin awning. A cheerful soot-covered woman smith at her anvil, tools hanging from a crossbeam, a half-finished sword clamped to the bench, glowing coals. Sparks and heat haze, warm afternoon light. [ESTILO]
  ```
- [ ] **Botica del Alquimista** (`crownreach/alchemist_stall/`)
  ```text
  A narrow alchemist's shopfront on a medieval craft street, flasks of every colour in the window, three copper stills bubbling inside, walls lined with hand-labelled drawers. Green and amber light, faint vapour. [ESTILO]
  ```
- [ ] **Taller del Carpintero** (`crownreach/carpenter_stall/`)
  ```text
  A carpenter's workshop on a medieval craft street, sawdust ankle-deep, staves and fishing rods leaning against the wall, a workbench crowded with clamps, fresh oak boards. Warm dusty light through the open door. [ESTILO]
  ```
- [ ] **Curtiduría** (`crownreach/tannery_stall/`)
  ```text
  A tannery at the end of a medieval craft street, hides stretched on wooden frames, tanning vats, leather straps hung up to dry, a wiry stained-armed tanner at work. Grey-green light, steam off the vats. [ESTILO]
  ```
- [ ] **Banco del Joyero** (`crownreach/jeweler_stall/`)
  ```text
  A tiny jeweler's stall behind an iron grille on a medieval craft street, fine tweezers, a magnifier on a jointed arm, half-set rings on a felt tray, an elderly immaculate jeweler bent over his work. Focused lamplight in a dim interior. [ESTILO]
  ```
- [ ] **Escritorio del Escriba** (`crownreach/scribe_stall/`)
  ```text
  A scribe's arcade on a medieval craft street, two slanted desks, inkwells in a row, parchments drying on a line, a stooped scribe with ink-stained cuffs copying a map. Cool even daylight. [ESTILO]
  ```
- [ ] **Telar de Hedda** (`crownreach/tailor_stall/`)
  ```text
  A tailor's stall on a medieval craft street, a wooden loom and a spinning wheel, skeins of yarn hanging from the ceiling by colour, folded cloth stacked on a shelf, a half-dressed dummy by the door, a calm tailor at work. Soft diffuse daylight, quiet. [ESTILO]
  ```
- [ ] **Taller del Ingeniero** (`crownreach/engineer_stall/`)
  ```text
  An engineer's shed on a medieval craft street, reinforced door with soot marks on the lintel, coiled fuses, powder crates stacked away from the fire, half-assembled clockwork mechanisms on the bench. Cluttered, smoky, bright work light. [ESTILO]
  ```

### Thornwood

- [ ] **Camino del Viejo Rey** (`thornwood/old_kings_road/`)
  ```text
  The Old King's Road, an ancient cracked stone causeway leading from a distant walled city toward a dark oak forest. Abandoned broken carts at the roadside, weeds between the paving stones, crows on a fallen milestone. Pale late-afternoon light. [ESTILO]
  ```
- [ ] **Arboleda Antigua** 🌙 (`thornwood/elderwood_grove/`)
  ```text
  Elderwood Grove, enormous ancient oaks too wide for three men to circle, young straight ash trees growing between them. Wood chips on the ground and a forgotten woodcutter's axe stuck in a stump. Soft green light through the canopy. [ESTILO]
  ```
- [ ] **Claro de la Raíz Roja** 🌙 (`thornwood/redroot_clearing/`)
  ```text
  Redroot Clearing, a damp forest clearing with almost red soil. Crimson bloodroot plants everywhere and silvery leaves in the shade of mossy rocks, a herb basket left on a stone. Misty diffuse daylight. [ESTILO]
  ```
  Noche: las hojas de plata brillan tenuemente bajo la luna.
- [ ] **Mina del Paso Viejo** (`thornwood/ironvein_mine/`)
  ```text
  Old Pass Mine, a stone mine mouth at the foot of a rocky hill, shored up with blackened timber beams. Reddish iron veins in the rock, a rusty ore cart on rails, a pickaxe leaning by the entrance, something glinting deep inside. Low afternoon light and torch glow. [ESTILO]
  ```
- [ ] **Ribera de Silverbrook** (`thornwood/silverbrook_bank/`)
  ```text
  Silverbrook Bank, a wide cold stream running down from the hills over polished stones. An old wooden jetty, silver fish swimming upstream, reeds and a fishing rod resting on the planks. Clear fresh morning light. [ESTILO]
  ```
- [ ] **Prado de los Colmillos** 🌙 (`thornwood/tusk_meadow/`)
  ```text
  Tusk Meadow, tall-grass fields south of a city, the ground churned up by boar snouts. Dark rock cracks opening between boulders, a distant boar grazing, the city walls far behind. Bright warm daylight. [ESTILO]
  ```
  Noche: luna, hierba plateada y murciélagos saliendo de las grietas.

### Cripta Hundida

- [ ] **Sala de los juramentos** (`sunken_crypt/crypt_hall/`)
  ```text
  Hall of oaths inside an ancient crypt, rows of faceless stone knight statues lining both sides, all their swords pointing toward the same dark corridor. Dust, cracked flagstones, a fallen banner. Cold blue-green gloom with one warm torch. [ESTILO]
  ```
- [ ] **Galería inundada** (`sunken_crypt/crypt_gallery/`)
  ```text
  A flooded crypt gallery, knee-deep black water between stone arches, ripples suggesting something beneath the surface, drowned tomb niches along the walls. Cold spectral blue-green light reflected on the water. [ESTILO]
  ```
- [ ] **Osario** (`sunken_crypt/crypt_ossuary/`)
  ```text
  A crypt ossuary whose walls are covered with thousands of skulls and bones arranged in careful patterns, a narrow passage between them, a single candle on a stone shelf. Cold gloom with a small warm light, eerie but not gory. [ESTILO]
  ```
- [ ] **Santuario** (`sunken_crypt/crypt_sanctum/`) — mismo Ser Aldren que el bestiario (`content/monsters/crypt_warden/`): usar su retrato como referencia.
  ```text
  The crypt sanctum, an iron chandelier hanging above an open stone sarcophagus. Beside it an undead knight in ancient battered plate armor slowly rises, faint turquoise light in his helmet, greatsword in hand. Solemn cold blue-green light with warm candle glints. [ESTILO]
  ```

## PNJ · `content/npcs/<id>/images/portrait.jpg`

Ruta propuesta (ars §3): aún no hay cargador ni botón. Rasgos de `content/npcs.yaml`; nada de marcas faciales que el canon no tenga. Más adelante, tres expresiones (neutral, preocupado, satisfecho).

- [ ] **Sargenta Vale** (`vale`) — primera: es la del tutorial.
  ```text
  Sergeant Vale, a stocky sunburnt woman in her forties, veteran of border wars, short practical hair, worn silver-grey Silver Guard tabard over mail, hands on her belt, loud confident grin. Waist-up portrait, simple softly painted city plaza background. [ESTILO]
  ```
- [ ] **Bram** (`bram`)
  ```text
  Bram, a broad bald middle-aged tavern keeper, clean-shaven, rolled-up sleeves and a stained apron, drying a tankard with a rag, warm but shrewd smile. Waist-up portrait, simple softly painted tavern background with firelight. [ESTILO]
  ```
- [ ] **Tessa** (`tessa`)
  ```text
  Tessa, a cheerful young woman smith covered in soot, burn-scarred forearms, leather apron, hammer resting on her shoulder, loud laughing expression. Waist-up portrait, simple softly painted forge background with warm glow. [ESTILO]
  ```
- [ ] **Mira** (`mira`)
  ```text
  Mira, a sharp soft-spoken hooded woman informant, dark crimson hood shadowing half her face, plain dark clothes, a dagger hilt at her belt, cool appraising gaze. Waist-up portrait, simple softly painted shadowy tavern corner background. [ESTILO]
  ```
- [ ] **Sargento Holt** (`holt`)
  ```text
  Sergeant Holt, a weathered rigid officer of the Silver Guard, greying close-cropped hair, polished breastplate with a silver-grey Silver Guard tabard, standing at attention, stern but honest expression. Waist-up portrait, simple softly painted city plaza background. [ESTILO]
  ```
- [ ] **Hermana Ysolde** (`ysolde`)
  ```text
  Sister Ysolde, a calm tired priestess in her fifties, simple white and pale gold robes, a dawn-sun pendant, rolling a linen bandage, gentle wry expression. Waist-up portrait, simple softly painted chapel background with candles. [ESTILO]
  ```

## Linajes · `content/lineages/<id>/images/portrait.{male,female}.jpg`

Para `/lineage` (ruta propuesta; sin cargador). Ropa de viajero común, sin clase: el linaje no implica oficio. Hacer hombre y mujer cambiando el sujeto.

- [ ] **Humano** (`human`)
  ```text
  A human traveler of Aetherfall, ordinary adaptable look, plain linen shirt and travel cloak, leather satchel, determined expression. Waist-up portrait, simple softly painted countryside background. [ESTILO]
  ```
- [ ] **Elfo** (`elf`)
  ```text
  An elf traveler of Aetherfall, long-lived and watchful, slender build, pointed ears, green and grey travel clothes, calm attentive eyes. Waist-up portrait, simple softly painted ancient oak forest background. [ESTILO]
  ```
- [ ] **Enano** (`dwarf`)
  ```text
  A dwarf traveler of Aetherfall, short sturdy build, braided beard, thick wool and leather clothes, stubborn steady gaze. Waist-up portrait, simple softly painted snowy mountain stone background. [ESTILO]
  ```
  Mujer: braided hair, without beard (o decidir canon antes).
- [ ] **Orco** (`orc`)
  ```text
  An orc traveler of Aetherfall, tall strong build, grey-green skin, small tusks, dignified travel clothes, intelligent composed expression, neither monstrous nor savage. Waist-up portrait, simple softly painted road background. [ESTILO]
  ```

## Eventos · ruta por decidir

Hitos, no cada ataque (ars §9).

- [ ] **Victoria sobre el Viejo Colmillo** (fin del tutorial) — mismo jabalí que `content/monsters/old_tusk/`.
  ```text
  A lone adventurer standing over a defeated giant old boar with broken tusks in a tall-grass meadow, sword lowered, breathing hard, the city walls far behind. Golden sunset light. [ESTILO]
  ```
- [ ] **Juramento**
  ```text
  An adventurer kneeling before a stone altar, hand on a sword laid across it, swearing an oath, a single beam of light falling on them in a quiet chapel. [ESTILO]
  ```
- [ ] **Descubrimiento**
  ```text
  An adventurer pushing aside ferns to discover a hidden moss-covered ruin in an ancient forest, lantern raised, carved stones half-buried in roots. Soft green light with a warm lantern glow. [ESTILO]
  ```

## Comunidad · fuera del contenido

Recorte circular: el motivo centrado y legible en pequeño.

- [ ] **Avatar del bot**
  ```text
  A simple emblem of a sword crossed with a crown, forged steel and gold, centered on a deep teal background, bold readable silhouette, icon composition. [ESTILO]
  ```
- [ ] **Emblema de los canales** (ES y EN, el mismo)
  ```text
  An open old book with a glowing quill and a small crown above it, centered on a deep teal background, bold readable silhouette, icon composition. [ESTILO]
  ```

## Clases nuevas (B06) · `content/classes/<clase>/images/portrait.{male,female}.jpg`

Las seis clases que llegaron con 0.10.29 y 0.10.31 **ya se juegan sin retrato**: la ficha sale sin foto hasta que haya arte. Al integrar cada imagen: `tools/prepare_image.py … --kind portrait`, su `media.yaml` y su `portrait.<género>.prompt.md` al lado (lo exige `tests/test_content.py`), y quitar la clase de `pending_art` en `test_class_portraits_and_unknown_class_folder`.

- [ ] **Bárbaro** ♂ / ♀
  ```text
  A male barbarian of Aetherfall, broad and scarred, braided dark beard, bare shoulders painted with ochre war marks, a fur mantle, a warhammer resting on his shoulder, fierce grin. Waist-up portrait, simple softly painted windswept highlands background. [ESTILO]
  A female barbarian of Aetherfall, tall and powerful, wild braided hair, ochre war marks across her cheekbones, fur mantle over bare arms, a handaxe in each hand, defiant stare. Waist-up portrait, simple softly painted windswept highlands background. [ESTILO]
  ```
- [ ] **Monje** ♂ / ♀
  ```text
  A male monk of Aetherfall, lean and calm, shaved head, simple undyed linen robes, hands wrapped in leather strips, balanced fighting stance, serene focused gaze. Waist-up portrait, simple softly painted mountain monastery courtyard background. [ESTILO]
  A female monk of Aetherfall, wiry and composed, hair tied in a short topknot, plain grey linen robes, wrapped hands raised in guard, quiet intense gaze. Waist-up portrait, simple softly painted mountain monastery courtyard background. [ESTILO]
  ```
- [ ] **Explorador** ♂ / ♀
  ```text
  A male ranger of Aetherfall, weathered and watchful, short beard, green-grey hooded cloak over leather armor, a shortbow in hand and a quiver at his shoulder, reading tracks on the ground. Waist-up portrait, simple softly painted autumn forest background. [ESTILO]
  A female ranger of Aetherfall, sharp-eyed and lithe, dark braid over one shoulder, green-grey hooded cloak over leather armor, drawing a shortbow, calm focused expression. Waist-up portrait, simple softly painted autumn forest background. [ESTILO]
  ```
- [ ] **Artífice** ♂ / ♀
  ```text
  A male artificer of Aetherfall, inventive and ink-stained, round brass goggles pushed up on his forehead, scale armor with copper fittings, a humming brass-and-crystal device strapped to his forearm. Waist-up portrait, simple softly painted cluttered workshop background with warm lamplight. [ESTILO]
  A female artificer of Aetherfall, quick and curious, short hair, brass goggles around her neck, scale armor with copper fittings, a humming brass-and-crystal device on her forearm, amused smile. Waist-up portrait, simple softly painted cluttered workshop background with warm lamplight. [ESTILO]
  ```
- [ ] **Chamán** ♂ / ♀
  ```text
  A male shaman of Aetherfall, middle-aged and weathered, bone and feather charms woven into long hair, leather vest with painted spirals, a gnarled quarterstaff topped with a small glowing stone. Waist-up portrait, simple softly painted river-bank at dusk background. [ESTILO]
  A female shaman of Aetherfall, ageless and watchful, feather and shell charms in her braided hair, leather vest with painted spirals, a gnarled quarterstaff with a small glowing stone, a faint smile. Waist-up portrait, simple softly painted river-bank at dusk background. [ESTILO]
  ```
- [ ] **Caballero de la Muerte** ♂ / ♀
  ```text
  A male death knight of Aetherfall, grim and pale, black plate-and-chain armor etched with glowing pale-blue runes, a longsword with frost-lit runes held point-down, hollow resolute eyes. Waist-up portrait, simple softly painted cold ruined chapel background. [ESTILO]
  A female death knight of Aetherfall, severe and pale, black plate-and-chain armor etched with glowing pale-blue runes, a longsword with frost-lit runes held point-down, hollow resolute eyes. Waist-up portrait, simple softly painted cold ruined chapel background. [ESTILO]
  ```

## Rehacer al nuevo estilo (baja prioridad)

Las 26 imágenes actuales son de un estilo anterior. Se rehacen con el prompt de su `.prompt.md` + `[ESTILO]` cuando toque; mientras, valen.

- [ ] **Clases** (16, `content/classes/<clase>/images/portrait.{male,female}.jpg`): paladín, guerrero, pícaro, sacerdote, mago, druida, brujo, bardo. Prompts incompletos (PENDIENTE) en mago ♂♀, druida ♂♀, brujo ♂♀ y bardo ♂.
- [ ] **Criaturas** (10, `content/monsters/<criatura>/images/portrait.jpg`): bandido, capitán bandido, goblin explorador, lobo gris, esqueleto de la cripta, Guardián de la Cripta (Ser Aldren), jabalí, murciélago de cueva, Viejo Colmillo, rata gigante.

- [ ] **Criatura nueva (0.10.37)**: El Recaudador de Ceniza (`content/monsters/ash_collector/images/portrait.jpg` es un marcador de posición; el prompt real está en `portrait.prompt.md`). Falta también un retrato de Tamsin Harrow y una imagen del Puesto de Peaje Abandonado.

- [ ] **Criatura nueva (0.10.38)**: El Ciervo de Hierro (`content/monsters/iron_stag/images/portrait.jpg` es un marcador de posición; prompt en `portrait.prompt.md`) y una imagen de la Hondonada del Ciervo.

- [ ] **Región nueva (0.10.39)**: doce criaturas con retrato de marcador de posición en `content/monsters/<criatura>/images/` (contrabandista y ballestero de ceniza, reptante de cantera, lobo astado, cervato de hierro, leñador desbocado, autómata de sierra, anguila de vidrio, acechador de esquirlas, centinela del regulador, guardián de baliza y Custodio de las Balizas), imágenes de los ocho lugares del Valle de la Fragua Gris y retratos de Orsa, Kellan e Iwen.

- [ ] **Criaturas 6–9 (0.10.40)**: sabueso de ceniza, cobrador del peaje y sargento del peaje (marcadores de posición en `content/monsters/<criatura>/images/`).
