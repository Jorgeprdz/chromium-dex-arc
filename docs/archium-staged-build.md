# Compilación por etapas de Archium

Workflow: `baseline-build.yml`, rama `feat/arc-desktop`.

Hasta doce jobs secuenciales compilan dos horas cada uno (24 horas de compilación
acumulada). Cada job dispone de seis horas totales; el resto se reserva para
preparación, compresión, subida y descarga. La cadena termina en cuanto Ninja
completa `chrome_public_apk`; un error real detiene la cadena.

El checkpoint conserva **todo** el directorio dedicado del constructor:
checkout fijado y dependencias, depot_tools, objetos, ejecutables generados,
`.ninja_log` y `.ninja_deps`. Se transmite como tar PAX + gzip rápido, preservando
permisos, symlinks y fechas con nanosegundos. Se divide en partes de 1 GiB y se
sube por streaming a un draft de GitHub Releases, sin duplicar todo el archivo
en el disco del runner. Solo ocupa temporalmente una parte adicional.

La siguiente etapa comprueba commit, revisión y ruta absoluta antes de extraer.
Cada parte se verifica por tamaño y SHA-256. El manifiesto se publica únicamente
cuando todas las partes se han subido. No se ejecutan nuevamente sync, runhooks,
parches ni GN al continuar: se conserva el estado de la compilación. Se instalan
las dependencias del sistema en cada VM y se inicializa el intérprete de depot_tools.

El nombre del checkpoint es `archium-checkpoint-RUN_ID-ETAPA`. Los drafts son
archivos temporales del constructor, no releases de navegador. La APK final queda
en el artifact `Archium-for-Android-arm64`; sigue siendo una compilación de prueba.
Los checkpoints permanecen disponibles para inspección/recuperación y su limpieza
posterior. No se sobrescriben checkpoints existentes en una repetición accidental.

## Verificación y límites

La prueba local hace un ciclo completo de empaquetado/restauración con transporte
GitHub simulado y comprueba fechas exactas, modo ejecutable, symlinks y el archivo
oculto de Ninja. Rechaza manifiestos de otra revisión, commit, ruta o partes fuera
de orden. Actionlint valida ambos workflows. La transferencia real de un checkout
grande y la continuidad de Chromium se comprobarán con las primeras dos etapas.

Si se consumen las doce etapas sin APK, el workflow informa que sigue incompleto;
la etapa doce conserva su checkpoint. El tamaño y velocidad reales de transferencia
pueden impedir terminar un job antes de seis horas. No se garantiza la APK en
20–24 horas; el tiempo total incluye también transferencias y preparación.

El run anterior, sin checkpoints, no puede convertirse retroactivamente en etapas.
El primer run por etapas parte de cero y los jobs siguientes restauran el avance.

Fuentes: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
(límite de 2 GiB por asset, sin límite total de release) y
https://docs.github.com/en/actions/reference/limits (seis horas por job hospedado).
