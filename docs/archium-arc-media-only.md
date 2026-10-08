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

Checkpoint fuente validado: `archium-checkpoint-37788278858-1`, producido por
`a16e3f76b0c461de7b0a0a3dbc6d3ed30c7bb6e2`. La transición verifica inputs y
regenera GN con el flag apagado; Ninja puede reutilizar outputs válidos y debe
recompilar aquellos afectados por el cambio de configuración.

Política del intento: un único `workflow_dispatch` para esta variante. Los
slices normales pueden continuar dentro de ese mismo run. Ante failure final,
se conserva la evidencia y no se corrige, reintenta ni despacha otro run
automáticamente. El monitor existente continúa siguiendo el run original.

Validación local:

```bash
ARCHIUM_BUILD_SCOPE=arc-media ARCHIUM_TEST_GN=/path/to/gn \
  python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check-arc-preparation.py \
  --android-jar /opt/android-sdk/platforms/android-37.0/android.jar
bash -n scripts/build-archium.sh
python3 -m py_compile scripts/archium-java-preflight.py scripts/archium-test-gates.py
git diff --check
```
