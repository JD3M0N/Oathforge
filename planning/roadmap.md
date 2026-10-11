# Roadmap

Versionado `0.x.y`: sube **y** (parche) en arreglos y cambios pequeños; sube **x** (menor) en features grandes. `1.0.0` queda reservado para la primera versión pública estable. El detalle de cada versión está en `../CHANGELOG.md`.

## Hecho

- **0.1.0**: vertical slice en solitario. Creación de personaje (4 linajes, 4 trasfondos, Paladín y Pícaro), Crownreach, el Camino, el Bosque y la Cripta Hundida, combate por turnos, misión ramificada, NPC con memoria, tiendas con reputación, rumores del mundo, es/en.
- **0.1.1**: versionado, CHANGELOG, `planning/` y registro de partidas en `artifacts/`.
- **0.2.0**: Guerrero y Sacerdote; tipos de daño, resistencias y tipos de criatura.
- **0.2.1**: documentos de referencia (GDD y guía audiovisual) en `planning/referencias/`; planning ampliado con ellos; `audiovisual.md` e `interfaz-telegram.md`.
- **0.2.2**: hoja de héroe y límite de 150 llamadas de IA al día.
- **0.3.0**: mundo en carpetas (continente → zona → lugar), catálogo de imágenes, caché de `file_id` y «Ver ciudad» en Crownreach.
- **0.4.0**: Mago, Druida y Bardo; tiradas de salvación (DES/SAB), conjuros de área por fila, PV temporales.
- **0.4.4**: Brujo (Maleficio y maldiciones sin salvación), elección de hombre o mujer con retrato por sexo y `/sheet` en el menú de comandos.

## Próximo (candidatos)

- **0.2.x**: balance con datos de `artifacts/battles/` y ajustes de los testers.
- **0.3.x**: imagen por lugar («Ver lugar») y retratos de NPC sobre el catálogo de 0.3.0.
- **0.4.x**: balance de las 8 clases con datos de `artifacts/battles/`.
- **0.5.0**: especializaciones a nivel 5 (los datos ya existen).
- **0.6.0**: economía: profesiones/crafteo y sumideros de oro (ver `comercio.md`).
- **0.7.0**: grupos cooperativos y combate en grupo (fase 3, ver `multijugador.md`).
- **0.8.0** (propuesta): audio: música de la taberna y voces de NPC (ver `audiovisual.md`).
- Más adelante: salvaciones de FUE/CON/INT/CAR para monstruos, IA enemiga con habilidades, simulador de batallas, mercado entre jugadores, PvP, Mini App, TTS.

## Visión a largo plazo (GDD)

Fuente: [GDD](referencias/gdd-aetherfall-chronicles.pdf) §17 y §20.

**El núcleo que hay que proteger:** un jugador actúa con libertad, el motor resuelve con rigor, el DM cuenta lo sucedido y el mundo lo recuerda. Todo lo demás alimenta ese ciclo.

Secuencia recomendada (§20) y dónde estamos:

1. Un buen turno y una buena escena: ✅ 0.1.0–0.2.0.
2. Una misión que se puede resolver de dos formas: ✅ «El relicario sellado».
3. Un NPC que recuerda: ✅ básico; falta la memoria en tres capas (`ia-y-narracion.md`).
4. Una aventura compartida: 0.6.0.
5. Un hecho que cambia la ciudad: `world_facts` y eventos encadenados (`mundo-y-misiones.md`).
6. Economía y facciones que reaccionan: 0.5.0 y más facciones.

Fases del GDD (§17.2) frente a nuestras versiones:

| Fase GDD | Contenido | Oathforge |
|---|---|---|
| 0 · Diseño en papel | Contrato de acciones, ficha, situaciones de abuso | Hecho antes de 0.1.0 |
| 1 · Vertical slice | `/start`, 3 nodos, NPC, tiradas, combate, inventario, PostgreSQL | 0.1.0 |
| 2 · Narrador y misión | Texto libre con JSON validado, misión ramificada, memoria | 0.1.0 |
| 3 · Multijugador | Grupos, turnos, intercambio, duelos | 0.6.0 |
| 4 · Mundo pequeño vivo | 3 profesiones, 2 facciones, mercado, rumores, evento semanal, periódico, audio | 0.5.0 + 0.7.0 |
| 5 · Expansión por métricas | Clases, especializaciones, regiones, gremios, Mini App | 0.4.0 y después |

**Antes de invitar a amigos** (§17.6):

- Cero duplicados en 1.000 repeticiones automatizadas de acciones económicas críticas.
- El 100 % de los cambios de turno respeta iniciativa y permisos.
- El bot recupera personajes y aventuras tras un reinicio sin intervención manual.
- El DM nunca aumenta oro ni inventario por texto libre.
- Los jugadores de prueba saben salir de una escena y volver al menú.
- Hay modo de recuperación cuando la API de IA no responde.
- Los registros permiten investigar un combate o un intercambio dudoso.

**Indicadores de la beta** (§17.7): retención D1/D7, tutorial completado, duración de sesión, acciones libres por sesión, acciones rechazadas, latencia p95, abandono en combate, coste de IA por usuario y divergencias de estado. Sin trucos de retención: un buen juego entre amigos respeta las pausas.

**Riesgos principales** (§19.1): sobrealcance (meses de clases sin bucle jugable), narrador incoherente, desequilibrio entre clases, spam en Telegram, coste de IA, inflación, duplicados y dependencia de un hosting gratuito.
