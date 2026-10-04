# Inventario medido — 2026-10-04

Resultado: SUCCESS en [run 37229418264](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/37229418264).

- Ubuntu 24.04.5, x86_64; runner image 20260927.320.1.
- RAM total: 15,988 MiB; disponible durante la prueba: 15,057 MiB.
- Swap: 3,071 MiB.
- Filesystem raíz: 154,894,188,544 bytes; libres: 92,421,394,432 bytes.
- `/`, workspace y `/mnt` pertenecen al mismo filesystem: no sumar sus cifras.
- Herramientas preinstaladas: dotnet 6,166,843,392 bytes; Android SDK
  11,781,832,704 bytes; hostedtoolcache 5,347,201,024 bytes.

La máquina física ofrece más espacio que los 14 GB anunciados como especificación
estándar. Los tamaños de herramientas sugieren que una limpieza del runner
temporal permite superar los 100 GB; el script de baseline comprueba el espacio
real tras limpiarlas y aborta si no alcanza. No toca archivos del teléfono.

Esto justifica intentar un build; no demuestra todavía que alcance el espacio
durante la compilación ni que termine en las seis horas máximas del runner.

Primera revisión de preparación: sin hallazgos bloqueantes. Se corrigieron los
estados obsoletos de README y plan tras terminar el inventario.
