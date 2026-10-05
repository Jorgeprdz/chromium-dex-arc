# Archium for Android — preparación

Diseño aprobado: [docs/design.md](docs/design.md).

Este directorio contiene la preparación del proyecto, no un navegador terminado.
Incluye código nativo y parches contra la revisión fijada de Chromium, descritos
en [docs/arc-preparation.md](docs/arc-preparation.md). No contiene un checkout
completo de Chromium ni una APK propia compilada.
El workflow de baseline intenta compilar la base sin modificaciones en GitHub;
sus archivos temporales nunca se descargan al teléfono.

## Base identificada

- Snapshot AndroidDesktop_arm64: `1710899`.
- Chromium Git: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
- La revisión está identificada por el archivo REVISIONS oficial de ese snapshot.

## Primera comprobación

El workflow manual `runner-probe.yml` mide arquitectura, memoria, discos y tamaño
de herramientas preinstaladas. No descarga Chromium, borra archivos, crea montajes,
publica artifacts ni utiliza servicios externos de compilación.

El inventario terminó correctamente; resultados en [docs/builder-inventory.md](docs/builder-inventory.md). El runner estándar publicado tiene 16 GB de
RAM y 14 GB de almacenamiento para proyectos públicos; Chromium documenta al menos
100 GB libres. Medir el runner no garantiza que una compilación completa quepa o
termine dentro de sus límites.

Fuentes:
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md
- https://commondatastorage.googleapis.com/chromium-browser-snapshots/AndroidDesktop_arm64/1710899/REVISIONS

No se publicarán datos del teléfono ni claves de firma en este proyecto.
