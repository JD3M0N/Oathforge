# Multijugador

## Estado actual

- Solo en solitario. Las tablas para grupos ya existen (`parties`, `party_members`, `encounter_participants`).
- Los jugadores se afectan de forma indirecta mediante rumores.

## Ideas

- **Grupos** de 2–4 en un chat de grupo de Telegram, con un panel de combate compartido.
- Turnos con temporizador (JobQueue); si alguien no actúa, defiende automáticamente.
- Habilidades que apuntan a aliados (curas del Sacerdote, Bendición en área, protección del Guerrero).
- Botín por turnos o tirada de necesidad/codicia.
- **PvP** solo con consentimiento (duelos) y en zonas marcadas.
- Gremios ligados a facciones.

### Espacios de Telegram (GDD §2.2)

| Espacio | Para qué | Precaución |
|---|---|---|
| Chat privado con el bot | Personaje, exploración, secretos | Notificaciones y privacidad |
| Grupo de expedición | Combate y escenas en grupo | Turnos, ausencias, ruido |
| Grupo de gremio | Organización, reclutamiento | Permisos, suplantación |
| Comunidad con temas | Mercado, taberna global, anuncios | Separar temas, spam |
| **Canal de noticias** | Periódico del reino (*Herald*) y grandes eventos | Publicar solo hechos confirmados |
| Mini App (futuro) | Mapa, talentos, mercado | Validar `initData` en el servidor |

### Expediciones y campañas (GDD §12.5, §13.2)

- El líder invita, elige destino y el ritmo: **sincronía rápida** o **campaña lenta** (decisiones en horas o días).
- Se guarda `party_id`, miembros, permisos y progreso. Solo los mensajes dirigidos al bot con una acción válida afectan al motor; el resto es charla.
- Hay que responder antes de abrir grupos: ¿qué pasa si alguien se desconecta?, ¿quién negocia por el grupo?, ¿cómo se vota?, ¿se sigue con 2 de 4?
- Si alguien abandona: reemplazo o personaje asistido con reglas limitadas, nunca usar su personaje sin consentimiento.
- Resumen «anteriormente en la aventura» para quien vuelve tras varios días.

### Información asimétrica (GDD §13.3)

El experto en Percepción ve las marcas detrás del cuadro; la pista le llega por privado y decide si la comparte. Para secretos importantes, mensaje privado normal (no efímero) y registro de pista.

### Invitaciones (GDD §13.4)

Enlaces profundos con token firmado y caducidad. Un enlace nunca da botín ni permisos por sí solo: se valida cuenta, grupo, plazas y estado.

### PvP: cuatro modalidades (GDD §5.7)

| Modalidad | Reglas | Salvaguarda |
|---|---|---|
| Duelo amistoso | 1v1 sin pérdidas | Consentimiento de los dos |
| Arena clasificatoria | 1v1 o 2v2 por temporadas | Emparejamiento por nivel |
| Guerra de facciones | Objetivos coordinados | Ventanas anunciadas y límites |
| PvP de frontera | Zonas señalizadas | Protección a novatos y contra acoso |

El PvP premia planificar, no abusar: sin robo libre de equipo ni pérdidas irrecuperables.

### Gremios (GDD §8.6)

Roles (líder, oficial, tesorero, reclutador, miembro, visitante), permisos, tablón, banco con auditoría, misiones comunitarias y sede mejorable. Guerras de gremio en ventanas programadas.

### Convivencia (GDD §13.1, §13.5)

- Mostrar nombres de personaje, nunca datos de Telegram que el jugador no haya hecho públicos.
- Las interacciones privadas (intercambio, desafío, invitación) necesitan consentimiento.
- Código de conducta, bloqueo y reporte. Un personaje villano está permitido; acosar a una persona, no. Las sanciones permanentes requieren revisión humana, no de la IA.

## Preguntas abiertas

- ¿Un mensaje por combate en el chat del grupo o un panel privado por jugador?
- ¿Cómo evitamos que el grupo espere a un jugador lento?
- ¿Abrimos un canal de noticias antes de tener grupos? (solo necesita eventos y rumores, que ya existen)
- ¿Tamaño de grupo: 2–4 (lo nuestro) o 2–5 (GDD)?
