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
parches al continuar: se conserva el estado de la compilación. GN se regenera si los args difieren de los esperados. Se instalan
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

## Reutilizar la compilación anterior

El checkpoint conservado `archium-checkpoint-37255997027-7` corresponde al commit
`c8ffd13ee7fe1c6baab4913da6a01e8009febe18`. El workflow acepta `source_checkpoint`
y `source_commit` explícitos para la primera etapa. La restauración verifica esa
identidad exacta y mantiene las verificaciones de revisión, ruta y partes.

La transición carga patch/manifiesto del commit antiguo, comprueba ambos bundles
y cada input, reconstruye el nuevo estado en un staging independiente y solo
reemplaza archivos cuyos bytes cambiaron. Restaura originales de cambios
eliminados y borra únicamente overlays antiguos que todavía coinciden con su hash.
Cualquier divergencia o symlink aborta antes de cambiar los inputs. Errores
manejables durante la escritura restauran bytes, modos y marcas de tiempo; una
interrupción fatal del proceso invalida esa VM y no publica un checkpoint.

Después se copian los args nuevos y se ejecuta `gn gen out/Archium`. Ninja conserva
los objetos y estado anteriores y determina qué dependencias recompilar. Las
etapas posteriores restauran el commit nuevo estrictamente y no repiten la
transición. La reducción de tiempo se debe medir, no se garantiza.

Con `validate_native=true`, se compilan primero `archium_key_provider_tests` y
`archium_key_java`, registrados en el BUILD.gn de password_manager/android. El
primero es un ejecutable nativo Android con pruebas de Encryptor real; el segundo
compila las clases de Keystore y el JNI. Comparten con el APK un único presupuesto
de 120 minutos de Ninja por etapa. Un error detiene la cadena; un timeout guarda
el checkpoint actual. Cuando termina el APK, se conserva también el ejecutable de
pruebas en el artifact si está disponible. Compilación de esos targets y ejecución
en Android son comprobaciones distintas: no presentar una como la otra.

La orden del usuario es actualizar los monitores con el nuevo ID y pausar tras
lanzar el run final. El estado de build/runtime se mantiene pendiente durante esa
pausa; la instalación y E2E requieren reanudar.


Fuentes: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
(límite de 2 GiB por asset, sin límite total de release) y
https://docs.github.com/en/actions/reference/limits (seis horas por job hospedado).
