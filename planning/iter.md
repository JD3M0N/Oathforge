# Iter — hoja de ruta

Qué entra en cada versión. El detalle de cada versión publicada está en [`../CHANGELOG.md`](../CHANGELOG.md); las ideas y su justificación, en [Possibilium](Possibilium.md) (paquetes en §28).

Versionado `0.x.y`: **y** (parche) en arreglos y cambios pequeños; **x** (menor) en features grandes. `1.0.0` queda reservado para la primera versión pública estable.

## Hecho (resumen)

| Versión | Qué trajo |
|---|---|
| 0.1.x | Vertical slice en solitario: creación, Crownreach, camino, bosque y cripta, combate por turnos, relicario, NPC con memoria, tiendas, rumores, es/en; `artifacts/` |
| 0.2.x | Guerrero y Sacerdote, tipos de daño y criatura; hoja de héroe; límite de 150 llamadas de IA |
| 0.3.0 | Mundo en carpetas, catálogo de imágenes, caché `file_id`, «Ver ciudad» |
| 0.4.x | Mago, Druida, Bardo y Brujo; salvaciones, área por fila, PV temporales, maldiciones; elección de sexo; comandos `oathforge` |
| 0.5.x | Misiones en cadena y diario, Prado de los Colmillos, bestiario, compra por puntos, `/roll`, retratos de las 8 clases, simulador, `tgtest`, subida de nivel, `/classes`, informe de batalla |
| 0.6.x | Actividades de campo con espera, maestrías, oficios, recetas, `/professions`, crónicas con presupuesto, pociones con efectos tipados |
| 0.7.0–0.7.13 | Aficiones, Escribanía e Ingeniería (pergaminos y bombas), capilla, descanso largo, `/settings`, textos de respaldo, bestiario ilustrado, `/map`, `oath`, trasfondos (12 + propio), `/rulebook`, `/skill_`, tutorial de Vale |
| 0.7.14–0.7.31 | Pulido antes del multijugador: tutorial sin horas y acelerado, teclado fijo, fichas `/item_` y `/monster_`, actividades que terminan solas, `/skin`, ronda 0 y botones por clase, estadísticas, `tutorial-stats`, resiliencia de Gemini, viaje sin tiempos, balance para mago y druida |
| 0.8.0 | Viaje directo a lugares conocidos, una emboscada por viaje, «▶️ Seguir», 📜 al objetivo |
| 0.8.1 | `tests/features.md`: checklist de pruebas tras una feature grande |
| 0.8.2 | Tutorial de 10 misiones sin mazmorras (Viejo Colmillo como jefe final), objetivo `hunt`, beta instantánea y pociones a 1 de oro |
| 0.8.3 | Planning reorganizado: Possibilium, resúmenes en latín, `ars.md`, PDF retirados, `AGENTS.md`, `content/officina/` |
| 0.9.0 | Logros e identidad: 30 logros, dos metalogros, títulos, destacados, objetivos seguidos y reconocimiento retroactivo verificable |
| 0.9.1 | Hoja de ruta de 0.10 (consolidación) y 0.11 (multijugador): `planning/roadmap.md` |
| 0.10.25 | 0.10-I (B03): la barra de clase en el motor (coste, generación, enfriamientos por turno), Guerrero con Foco y Hechicero con Maná, y los jefes que no se encadenan |
| 0.10.24 | 0.10-I (B02): el nivel necesita XP y un hito narrativo, y las misiones se entregan y se cobran en persona |
| 0.10.23 | 0.10-I: Sacerdote pasa a Clérigo (`cleric`) y Mago a Hechicero (`sorcerer`), id incluido |
| 0.10.22 | 0.10-I (B01): los contratos de las 41 ramas de clase, la tabla de XP de 20 niveles con sus dos puertas y las nueve barras de clase; `engine/class_build.py` y la migración 0013 |
| 0.10.21 | 0.10-I (B00): el contrato de la revisión de clases, progresión 1–20 y campaña en `planning/roadmap_balance.md`, y la auditoría de la base (solo documentación) |
| 0.10.20 | Marcado en `TODO.md` y `planning/roadmap.md` lo que F15 deja hecho (solo documentación) |
| 0.10.19 | Profesiones (F15, cierre): `tests/features.md` con el recorrido completo y los resúmenes de planning al día; queda la partida de prueba en ES y EN |
| 0.10.18 | Profesiones (F15, 10.ª parte): el catálogo T1 (materiales de rango 4, acero y ocho recetas con nivel 10 para equiparse) y los maestros que venden los componentes de su oficio |
| 0.10.17 | Profesiones (F15, 9.ª parte): quince herramientas especializadas (rápida, selectiva y productiva por disciplina), una elegida por disciplina y fijada al empezar cada trabajo |
| 0.10.16 | Profesiones (F15, 8.ª parte): doce ramas de maestría, elegidas a rango 2 en el Gremio, con la anterior pausada y no perdida, y el piloto de Rastreo |
| 0.10.15 | Profesiones (F15, 7.ª parte): la instantánea de reglas al empezar una actividad y el hallazgo raro de una sola tirada por actividad |
| 0.10.14 | Profesiones (F15, 6.ª parte): tu cuarto en el Gremio de Aventureros, con la misión del tutorial que lo amuebla, el descanso gratis en tu cama y el cofre personal con `/room` y `/stash` |
| 0.10.13 | Profesiones (F15, 5.ª parte): Sastrería como octavo oficio con su telar, las técnicas que se aprenden enteras al subir de rango y los planos de las recetas especiales |
| 0.10.12 | Profesiones (F15, 4.ª parte): el refinado como maestría (horno, aserradero, secadero y mesa), y las recetas con panel y comandos (`/recipes`, `/r_<receta>`, `/craft_<receta> n`) |
| 0.10.11 | Profesiones (F15, 3.ª parte): el Gremio de Aventureros (refinado, Vale y el alistamiento) y el Barrio de Oficios convertido en una calle con un puesto y un maestro por oficio |
| 0.10.10 | Profesiones (F15, 2.ª parte): el contrato de las recetas (estación por receta, disciplina de la XP, tiers por rango, lotes y requisito de nivel para equipar) |
| 0.10.9 | Profesiones (F15, 1.ª parte): el contrato de oficios, maestrías y aficiones en `planning/roadmap-profesiones.md` (solo documentación) |
| 0.10.8 | Logros (F04): auditoría, un solo nombre «Logros», título visible en la ficha y para la IA, y cuatro logros nuevos con un título |
| 0.10.7 | Diario y reglamento (F03): diario por pestañas con portada «Ahora», Crónica del héroe desde los hechos del motor, estadísticas verificables y reglamento con las cifras del motor |
| 0.10.2 | Interfaz (F01, 3.ª parte): inventario por pestañas e icono para cada objeto |
| 0.10.1 | Interfaz (F01, 2.ª parte): tiradas con bono y veredicto, leyenda de `/sheet`, artículos por lugar («al Mercado») y singular automático |
| 0.10.0 | Interfaz (F01, 1.ª parte): teclado con ⚒ Actividades, escena social, un mensaje por acción, rechazos y menús viejos en ventanita, 🛠️ Oficios desde Héroe |

## Próximo

El detalle de 0.10 y 0.11 (fichas por sistema, hitos, puerta de salida y trazabilidad del TODO) está en [roadmap.md](roadmap.md). Aquí solo el resumen.

- **0.10.x, consolidación**: revisión integral de los sistemas individuales antes del multijugador, en hitos A–H que se publican como parches 0.10.x (la serie 0.9 terminó en 0.9.1). Empieza por la interfaz (F01: 0.10.0–0.10.2); la puerta de salida la supera el último 0.10.x. Incluye:
  - seguridad y operación primero: idempotencia del texto libre, contexto versionado y reserva de IA (CORE-01..03, AI-01..02);
  - confianza de los PNJ determinista, servicios de Bram, botones «Oficios» y «Actividades» ([narratio](narratio.md), [facies](facies.md));
  - descanso corto, cofre personal, «Algo brilla», entrega de misiones al dador ([pugna](pugna.md), [mercatura](mercatura.md), [mundus](mundus.md));
  - juramento verificable y auditoría de los logros de 0.9.0 ([progressio](progressio.md));
  - contrato de combate, jefe de dos fases y matriz de ocho clases ([pugna](pugna.md), [ordines](ordines.md));
  - **oficios, maestrías y aficiones por fases** (F15, su [contrato](roadmap-profesiones.md)): refinado de maestrías, Sastrería como octavo oficio, Gremio de Aventureros, una calle con un puesto y un maestro por oficio, habitación con cama y cofre, ramas a rango 2, herramientas especializadas y catálogo T0/T1 ([opificia](opificia.md));
  - economía auditada ([mercatura](mercatura.md));
  - **la revisión de clases, progresión y campaña** (hito 0.10-I, su [contrato](roadmap_balance.md), desde 0.10.21): catorce clases con recurso propio, 41 ramas elegidas al nivel 10, XP más hitos hasta el 20, entrega de misiones al dador, campaña nueva con el Recaudador y el Ciervo, región cercana para 11–20, tiempos sin atajos de beta y reinicio limpio antes de abrir ([ordines](ordines.md), [progressio](progressio.md), [mundus](mundus.md)). *Sustituye a las especializaciones al nivel 5 y al arco de nivel 5 que figuraban aquí.*
- **0.11, multijugador por incrementos** ([societas](societas.md)): grupo de 2 en la cripta (PKG-01 + PKG-02), grupos de 2–4 con ausencias (PKG-03), misiones y encargos con custodia (PKG-05), gremio mínimo y duelo consentido; después, eventos como la crisis del hierro (PKG-08).
- **Producción audiovisual en paralelo** (no bloquea lo anterior): estilo, tres portadas de lugar, un retrato de NPC y una pista ([ars](ars.md) §16).
- **Expediciones** (fase 2 del viaje: escenas, estilos, atajos, favoritos) cuando haya contenido que las merezca.
- **Más adelante**: más regiones (Frosthold o Stormport) después de la del hito 0.10-I, Mini App, TTS.

## Antes de invitar a amigos (GDD §17.6)

- Cero duplicados en 1.000 repeticiones automatizadas de acciones económicas críticas.
- El 100 % de los cambios de turno respeta iniciativa y permisos.
- El bot recupera personajes y aventuras tras un reinicio.
- El DM nunca aumenta oro ni inventario por texto libre.
- Los jugadores saben salir de una escena y volver al menú.
- Hay modo de recuperación cuando la API de IA no responde.
- Los registros permiten investigar un combate o intercambio.

## Riesgos principales

Sobrealcance, narrador incoherente, desequilibrio entre clases, spam en Telegram, coste de IA, inflación, duplicados y dependencia de un hosting gratuito.
