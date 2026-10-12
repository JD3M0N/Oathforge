# Audiovisual

Imágenes, música, voces, mapas y efectos. Fuente principal: [Guía de recursos audiovisuales](referencias/guia-recursos-audiovisuales.pdf) (citada como *Guía §N*).

**Principio:** los activos representan el mundo, pero la verdad está en la base de datos. La geografía, los NPC presentes y los hechos los decide el motor. Nunca se genera arte ni audio en cada turno: se produce una vez, se revisa, se cataloga y se reutiliza.

## Estado actual

- **v0.3.0**: el mundo vive en carpetas (`content/world/<continente>/<zona>/<lugar>/`) y cada carpeta puede tener `images/` y `audio/`. Catálogo por convención (`oathforge/content/media.py`), caché de `file_id` por bot en la tabla `media_files` y botón «🏙️ Ver ciudad» en la plaza de Crownreach con su panorámica.
- **v0.4.1**: retratos de clase en `content/classes/<clase>/images/portrait.jpg` (768 × 1024) para Paladín, Guerrero, Pícaro y Sacerdote; `/sheet` y «📜 Ficha completa» los envían antes de la ficha completa. Faltan Mago, Druida y Bardo (su ficha va sin foto).
- **v0.4.4**: el jugador elige hombre o mujer al crear el personaje; los retratos pueden ir por sexo (`portrait.male.jpg` / `portrait.female.jpg`) y `/sheet` envía el suyo, o el neutro `portrait.jpg`. El Brujo tiene los dos; el resto, uno neutro.
- **v0.5.1**: retrato de hombre y de mujer para las 8 clases (`portrait.male.jpg` / `portrait.female.jpg`), salvo la barda, que de momento usa el del bardo. Los neutros antiguos eran de hombre y se renombraron.
- Aún no hay imagen por lugar, retratos de NPC ni audio.
- Todo texto visible existe en es/en; cualquier audio necesitará también su equivalente en texto.

## Decidido

### Dónde se guarda cada cosa

```
content/world/
  world.yaml                      # start y orden de continentes
  terra_coronata/                 # continente
    continent.yaml
    images/map.jpg                # (futuro) mapa del continente
    crownreach/                   # zona: city | wilds | dungeon
      zone.yaml
      images/panorama.jpg         # «Ver ciudad»; panorama.night.jpg = variante nocturna
      images/media.yaml           # créditos y licencia por archivo
      audio/                      # (futuro) tema de la ciudad
      crownreach_plaza/           # lugar (hub: true → muestra «Ver ciudad»)
        place.yaml
        images/cover.jpg          # (futuro) «Ver lugar»
content/classes/<clase>/images/portrait.jpg  # retrato de clase en /sheet (+ media.yaml)
content/classes/<clase>/images/portrait.male.jpg / portrait.female.jpg  # variante por sexo (opcional)
content/npcs/<npc>/portrait.jpg   # (futuro) retratos
```

- Texto y medios de cada nodo van juntos en su carpeta. Los ids de lugar son globales y no cambian al mover carpetas.
- Imágenes por convención de nombre, ordenadas alfabéticamente (2–10 forman álbum). Sufijo `.night` para la noche; si no existe, se usa la de día.
- En git solo va la **versión de entrega** optimizada; los originales grandes y los PSD/Krita se guardan fuera (Drive).
- `file_id` en la base de datos por `(bot_id, asset_key)` con checksum: cada bot (Josue, Rayko, Edian) sube la imagen una vez, y si el archivo cambia se vuelve a subir sola.

### Escala de las imágenes

Telegram recomprime `sendPhoto` a **1280 px en el lado largo**; subir más grande solo gasta disco. Límite de la API: 10 MB por foto. `tools/prepare_image.py` recorta, escala y optimiza.

| Tipo | Proporción | Entrega (git) | Original (fuera de git) | Formato |
|---|---|---|---|---|
| Ciudad, zona, lugar, evento | 16:9 horizontal | **1280 × 720** | 2560 × 1440 o nativo del modelo (1344 × 768) | JPEG 85 progresivo, sin EXIF, ≤ 350 KB |
| Retrato de NPC | 3:4 vertical | **768 × 1024** | 1536 × 2048 | JPEG 85 |
| Ficha de personaje | 3:4 | 900 × 1200 | — (Pillow) | JPEG/PNG |
| Mapa de continente/ciudad | libre | 2048 px lado largo, por `sendDocument` | SVG/PNG | PNG |
| Iconos de objeto | 1:1 | 128 × 128 | 512 | PNG transparente |
| Stickers | 1:1 | 512 × 512 | — | WEBP/PNG |

Sin texto dentro de la imagen: los nombres van en el caption o se añaden con Pillow.

## Ideas

### Capas de inmersión (Guía §1)

| Capa | Recurso | Entrega en Telegram |
|---|---|---|
| Región | Ilustración panorámica + tema musical | Foto al llegar por primera vez, audio opcional |
| Lugar | Taberna, herrería, bosque, mazmorra | `sendPhoto` + botones inline |
| Personaje | Retrato fijo + expresiones | Foto, ficha y voz breve |
| Evento | Ilustración especial + efecto | Foto o álbum, pista de ambiente |
| Exploración | Mapa base + niebla de lo descubierto | Mapa renderizado bajo demanda |
| Combate | Retratos, iconos, barra de PV | Imagen al inicio y mensaje editado |

### Música en las tabernas y regiones (Guía §2)

- Bases instrumentales de 60–90 s, sin voces, en bucle. Dos versiones: `music_only` y `ambience_mix` (con fuego, vasos, murmullos CC0).
- Botón **«Escuchar ambiente»**: Telegram no permite reproducir música de fondo automáticamente, y enviar audio en cada acción cansa.
- Banco inicial propuesto (12 pistas): 3 tabernas (La Corona Rota, una clandestina, una marinera), 4 regiones, 2 mazmorras (empezar por la Cripta Hundida), 2 combates (emboscada, jefe) y el tema principal.
- Herramientas aptas para uso comercial: **Stable Audio** (cuota gratuita), **ACE-Step** (local, Apache 2.0), **BandLab** y **Audacity** para montar. Suno, AIVA y MusicGen solo sirven para prototipos (no comercial).
- Hay prompts listos en la Guía §9 (taberna acogedora, clandestina, bosque antiguo, jefe).

### Voces para personajes importantes (Guía §3)

- Solo para diálogos importantes, introducciones, juramentos y escenas emocionales; lo trivial queda en texto con un botón opcional de audio.
- Tres vías: **pregrabación** (30–50 frases recurrentes por NPC, cacheadas), **bajo demanda** (solo escenas únicas, con cola y cuota) o **voces humanas** de amigos con consentimiento.
- Ficha de voz por NPC: proveedor, modelo, voz, velocidad, tono y 2–3 estados (neutral, preocupado, enfadado). Ejemplo: Bram, voz grave y pausada, velocidad 0.93.
- Proveedores: **TTSMaker** (licencia comercial del audio) y **Kokoro-82M** (local, Apache 2.0) para producción; ElevenLabs Free y edge-tts solo para pruebas.
- Notas de voz con `sendVoice` en OGG/Opus (`ffmpeg -i in.mp3 -c:a libopus -b:a 32k out.ogg`); música con `sendAudio` en MP3.
- La voz se genera o se recupera **después** de validar el texto narrado.

### Sistema de imágenes (Guía §4)

- **Biblia visual** antes de generar nada: paleta, arquitectura, iluminación, estilo de pintura, ropa por facción y versiones de día y de noche. Un prompt maestro por familia de imágenes.
- Retratos de NPC: un rostro canónico y después variantes (hablando, enfadado, herido).
- Ciudad: exterior, plaza, taberna, mercado y mazmorra cercana; variante nocturna enlazada al reloj del mundo.
- Personajes jugadores: retrato base + marco por clase; no se regenera al cambiar de equipo.
- Objetos: iconos uniformes (Kenney CC0, Game-icons CC BY), no una ilustración por espada.
- Herramientas: **Leonardo AI** (gratis con uso comercial; las generaciones son públicas), **FLUX.1 schnell** o **FLUX.2 klein 4B** (local, Apache 2.0), Krita y GIMP para retocar.
- Los textos y nombres se añaden con Pillow o SVG, nunca dentro del generador.

### Ficha de personaje compartible (Guía §4)

Tarjeta de 900 × 1200 px compuesta con Pillow: retrato, nombre, clase, especialización, facción, nivel, PV, seis atributos, dos habilidades y equipo destacado. Marcos según rareza o facción. Se podría enviar con `/sheet` o con un botón «Compartir».

### Stickers por personaje

Pack de stickers de Telegram con los retratos y expresiones de los NPC principales (Bram, Tessa, el Guardián de la Cripta…) y quizá de las clases. Sale del mismo arte de los retratos; hay que revisar los requisitos de formato de los packs (PNG/WebP 512 px).

### Mapas (Guía §5)

- **Macro**: continente con Azgaar (exporta SVG/PNG/GeoJSON, uso comercial).
- **Meso**: plano de Crownreach con Watabou (taberna, mercado, puerto, castillo).
- **Micro**: taberna o mazmorra en un editor táctico (Tiled + Krita).
- El mapa es solo una **vista del grafo** de `content/world/`; los desplazamientos los valida el código, no la imagen.
- Capas automáticas con Pillow/SVG sobre el mismo mapa base: posición actual, niebla de guerra por personaje, rutas bloqueadas, misiones y peligro.

### Efectos de sonido (Guía §6)

Solo en eventos relevantes: puerta de la taberna, monedas al vender, acero al atacar, viento al explorar, magia y fanfarria al subir de nivel. No enviar audios de 0,3 s por cada botón. Fuentes: Freesound (solo archivos CC0) y Kenney.

### Envío por Telegram (Guía §7)

| Necesidad | Método | Formato |
|---|---|---|
| Retrato o ciudad | `sendPhoto` / `editMessageMedia` | JPEG/PNG |
| Mapa legible | `sendDocument` o `sendPhoto` | PNG |
| Música | `sendAudio` | MP3/M4A |
| Diálogo con voz | `sendVoice` | OGG/Opus |
| Animación | `sendAnimation` | GIF/MP4 |
| Álbum de escenas | `sendMediaGroup` | 2–10 medios |
| Reenvío | `file_id` ya guardado | sin volver a subir |

Una sola imagen por lugar en el flujo normal; los álbumes, para «Ver ciudad».

### Catálogo de activos (Guía §8)

```
assets(id, kind, slug, version, source_url, license_id, attribution,
       status, checksum, path, telegram_file_id)
character_media(character_id, portrait_asset_id, voice_profile_id)
location_media(location_id, cover_asset_id, music_asset_id, ambient_asset_id, map_asset_id)
voice_profiles(id, provider, model, voice_name, speed, pitch)
media_generation_jobs(id, kind, prompt_hash, status, cost_estimate)
```

Flujo: ¿hay un activo aprobado? → reutilizar `file_id`. Si no → trabajo en cola fuera del turno, revisión manual de calidad y licencia, subida a Telegram, guardar `file_id`. Alternativa más simple para empezar: `assets/manifests/assets.yaml` + carpetas `assets/{music,voices,sfx,images,maps,icons,licenses,prompts}/`, siguiendo el mismo patrón que `content/*.yaml`.

Presupuesto de espacio orientativo: unos 63 MB para 12 pistas, 30 voces, 50 imágenes y 10 mapas.

### Licencias (Guía §11)

- Para cada activo guardar: autor/proveedor, URL, fecha, licencia, atribución, prompt y modelo, hash y estado de aprobación.
- **No usar en una versión monetizada:** Suno, AIVA y ElevenLabs Free, Inkarnate Hobby, Dungeon Scrawl Free, pesos de MusicGen.
- Ojo: enviar un MP3 por un bot es distribuir el archivo; comprobar que la licencia lo permite, no solo «usar en un vídeo».
- Game-icons (CC BY) necesita una página de créditos (`/credits`).

### Plan de producción (Guía §10)

1. Identidad: biblia visual, Crownreach, 4 NPC (Bram, Tessa…).
2. Audio: 6 músicas, 12 efectos, 20 frases de NPC.
3. Mapas: continente, Crownreach, la Cripta.
4. Integración: catálogo, `file_id`, pruebas con amigos.

## Preguntas abiertas

- ~~¿Los activos van en git?~~ Sí, solo la versión de entrega optimizada (v0.3.0). Revisar con el audio (si pasa de ~100 MB, Git LFS).
- ~~¿Catálogo en tablas o en YAML?~~ Por convención de carpetas + `media.yaml` de créditos; en la base de datos solo la caché de `file_id`.
- ¿Audio por defecto apagado (modo silencioso) y que el jugador lo active?
- ¿Las voces existen en es y en en, o solo en un idioma con subtítulos?
- ¿Quién revisa y aprueba los activos generados?
