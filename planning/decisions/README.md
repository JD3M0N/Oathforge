# Decisiones de arquitectura (ADR)

Una decisión por archivo, corta: contexto, decisión y consecuencias. Para cambiar una, se escribe otra que la sustituya y se marca la antigua como *sustituida*. Numeración `NNN-title.md`.

| # | Decisión |
|---|---|
| [001](001-engine-decides-ai-narrates.md) | El motor decide, la IA narra |
| [002](002-only-services-write-state.md) | Solo los servicios escriben estado |
| [003](003-no-slow-io-under-lock.md) | Ninguna E/S lenta con un lock abierto |
| [004](004-gemini-only-provider.md) | Gemini es el único proveedor de IA |
| [005](005-english-codebase-two-languages.md) | Base en inglés, texto visible en es y en |
| [006](006-one-folder-per-thing.md) | Una carpeta por cosa en `content/` |
| [007](007-solo-project.md) | Proyecto de una sola persona |
