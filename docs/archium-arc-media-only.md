# Variante Arc y multimedia sin gestor local Archium

Rama: `feat/arc-media-only`, basada en
`33db26aa6fad2e8a9ac9ccf26774605edb9db771`.
Chromium: `157.0.8086.0`, revisión
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

Esta variante conserva el diseño Arc, Spaces, restore, pestañas verticales y la
configuración multimedia integrada. Establece
`enable_archium_local_passwords = false` y `ARCHIUM_BUILD_SCOPE=arc-media`.
El gestor local cifrado Archium, su proveedor Keystore y sus cuatro targets de
tests nativos quedan fuera del build. Las condiciones GN existentes controlan
esta selección; no se borran claves, bases de datos ni código de la rama completa.

La infraestructura genérica de contraseñas de Chromium permanece. Los bridges
Java/JNI que soportan el modo desactivado siguen compilándose, así como CSV y
settings. El control Arc usa su alternativa existente de Autorrelleno cuando
`isLocalEnabled()` devuelve false. Esta variante no ofrece el vault local Archium.

El preflight consulta el valor **efectivo** del flag en GN y rechaza la variante
si sigue habilitado. Únicamente deja de exigir los propietarios javac de
`ArchiumPasswordKey.java` y `ArchiumPasswordKeyBridge.java`, que pertenecen al
target condicionado `archium_key_java`. Todos los demás sources Java entregados
siguen necesitando acciones reales de compilación.

Gates obligatorios:

- Antes de descargar cualquier checkpoint: sintaxis Bash/Python y suite completa
  del repositorio con Python 3.12, JDK 17 y GN standalone de la revisión fijada.
- Verificación de argumentos multimedia efectivos.
- Compilación Java/JNI de cada propietario activo.
- `gn check //chrome/android:chrome_public_apk`.
- Compilación de `chrome_junit_tests` y presencia de su runner generado.
- Preparation gate, suite Python y seis suites Robolectric de Arc, proyección
  de tabs, layout y toolbar, ejecutadas antes de permitir el target APK.
- Instrumentación de window policy y smoke del APK en dispositivo cuando se
  invoquen explícitamente los gates device/post-build. No se declara runtime PASS.

Los tests de passwords permanecen escritos; la suite de repositorio y los tests
host de sources retenidos siguen ejecutándose. Los targets nativos de una función
desactivada no se solicitan ni se etiquetan como ejecutados o aprobados.

El workflow mantiene los 12 slices y sus checkpoints verificados. Usa un grupo
de concurrencia por ref con `cancel-in-progress: false`, para permitir este build
alternativo sin cancelar el run completo `37807259506`. Los tags contienen el
RUN_ID, por lo que los checkpoints de ambos builds no se mezclan.

Checkpoint fuente validado: `archium-checkpoint-37807259506-1`, producido por
`33db26aa6fad2e8a9ac9ccf26774605edb9db771`. La transición verifica inputs y
regenera GN con el flag apagado; Ninja puede reutilizar outputs válidos y debe
recompilar aquellos afectados por el cambio de configuración.

El primer intento de esta variante, `37810745991`, compiló los 31 propietarios
Java activos, pasó `gn check` y compiló `chrome_junit_tests`. Falló en las tres
pruebas de configuración GN del gate host: el launcher de depot_tools busca el
binario relativo al checkout del directorio actual, mientras esas pruebas se
ejecutan en directorios temporales. El gate ahora resuelve el binario nativo
del checkout antes de cambiar de directorio y transmite su ruta absoluta en
`ARCHIUM_TEST_GN`. Conserva las tres pruebas, los criterios de configuración y
las seis suites Robolectric. Los sources del diseño Arc no cambian por esta
corrección. Ese intento no publicó un checkpoint real nuevo: los mensajes de
checkpoint con ocho partes provenían de fixtures de la suite Python. Se utiliza
el checkpoint verificado de 23 partes del run completo, con passwords apagadas
al regenerar GN para esta variante. El fallo de passwords de ese run se conserva
sin corregir y sus targets nativos continúan excluidos de esta variante.

El intento `37819474930` compiló `chrome_junit_tests`, pasó las 116 pruebas del
repositorio y las primeras cuatro suites Robolectric. Se detuvo en dos variantes
de `testSetThumbnailSpinnerVisibility_NotFlatLayout_Asserts` (Android 29 y 37):
el build oficial deja `enable_java_asserts=false`, por lo que su wrapper JVM no
activa las aserciones que esa prueba requiere. El método conserva la aserción
original de Chromium.

El gate añade `-ea` a `JAVA_TOOL_OPTIONS` únicamente en los procesos de las seis
suites Robolectric, conservando las opciones existentes. Los argumentos GN del
APK oficial no cambian. Una regresión ejecuta un JVM real a través del gate para
verificar que las seis suites reciben aserciones activas y conservan otras
opciones Java, incluso con un `-da` heredado. Esa regresión valida el contrato del
lanzador; la ejecución completa de las suites Chromium sigue siendo obligatoria
en Actions.

El intento `37827632401` volvió a compilar `chrome_junit_tests`, pero la nueva
regresión del lanzador se detuvo antes de las suites Robolectric: ejecutaba
`unittest discover` sobre un directorio temporal vacío. Python 3.11 devolvía 0;
Python 3.12 en Ubuntu 24.04 devuelve 5 (`NO TESTS RAN`). La fixture ahora contiene
una prueba real y comprueba que se ejecutó antes de verificar las seis llamadas
al JVM. No se ignora el código de salida ni se cambia la versión de Python en CI.

Cada stage ejecuta `scripts/check-archium-repository.sh` justo después del
checkout, con un límite de 10 minutos y antes de restaurar Chromium. Usa el
Python 3.12 del sistema y JDK 17 del runner. El GN standalone corresponde a
`gn_version` del DEPS de Chromium fijado; se comprueba el SHA-256 del binario
tanto al descargarlo como al reutilizarlo. La suite incluye las tres pruebas
GN de multimedia y la regresión JVM con aserciones, sin necesitar el checkpoint.
Una prueba fallida detiene el job antes de la descarga y la compilación. Los
gates posteriores con el checkout real de Chromium siguen siendo obligatorios.

Política por autorización: un único `workflow_dispatch` para cada intento. Los
slices normales pueden continuar dentro de ese mismo run. Ante failure final,
se conserva la evidencia y no se corrige, reintenta ni despacha otro run
automáticamente. El monitor existente sigue el último run de esta variante.

Validación local:

```bash
# python3 debe ser 3.12; java/javac deben ser JDK 17.
ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh
python3 scripts/check-arc-preparation.py \
  --android-jar /opt/android-sdk/platforms/android-37.0/android.jar
bash -n scripts/build-archium.sh
python3 -m py_compile scripts/archium-java-preflight.py scripts/archium-test-gates.py
git diff --check
```
