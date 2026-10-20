# R5.4 — Marco y controles de vista dividida

Fecha: 20-oct-2026. Rama aislada: `assistant/archium-r5-split-polish-batch`.
Base: `73a07080857bff4ac7d30a24aad6aa457d343f2e`.
Destino: PR borrador hacia `assistant/archium-r5-arc-experience`, para agrupar mejoras antes de otra APK.

## Comportamiento implementado

- Marco de 4 dp, del color de la ventana, separación central de 8 dp y esquinas de 10 dp.
- Contorno discreto del panel activo; marco no interactivo debajo del contenedor modal nativo.
- Geometría compartida: el espacio del marco se reserva en ContentView y en las capas nativas; no se pinta un borde sobre texto visible.
- Cápsula blanca: arrastrar redimensiona; pulsar muestra intercambio, agarre y X. El agarre expandido también redimensiona.
- X sale de la división, conserva las dos pestañas y mantiene la identidad activa. Intercambio conserva la transición nativa de 180 ms sin recargar.
- Expansión de 150 ms con movimiento reducido respetado; cierre por toque exterior, Escape, ocultación y destrucción.
- El ancho mínimo de 240 dp por página incluye ahora marco y separación; la adaptación móvil usa el ancho interior real.
- Los toques fuera del agarre y de la cuña central siguen llegando a las páginas.

## Verificación

SHA de implementación: `3a41bf1d95d040f7f20350e83d77e9c66870152a`.

- PASS: 106/106 casos JVM de controles, geometría, ContentView, estado, viewport, controlador y puente Java/JNI en SDK 30 y 36 (`component-final.log`).
- PASS: preparación del parche y compilación aislada de adaptadores con SDK API 37 (`preparation-final.log` y `preparation-verified.log`).
- PASS: 24/24 pruebas de aplicación/transición del parche (`patch-verified.log`).
- PASS: 17/17 regresiones host de Arc y 1/1 de descubrimiento de suites; política de paleta también comprobada individualmente.
- PASS: escena C++ entregada con adaptadores host de capas (`native.log`), sin ejecución GPU.
- PASS: Python syntax, `git diff --check` y reproducción idéntica del parche/manifiesto.
- Revisión de código: corregido el resize ausente en la cápsula expandida; fallback Escape probado en el contenido con foco hijo. Sin hallazgos importantes abiertos en el reexamen acotado.

RED inicial: las pruebas nuevas no compilan sobre la API anterior, que carece de marco y acciones desplegables.
La revisión adicional reprodujo la ausencia de resize en el agarre expandido en SDK 30 y 36.
Escape se prueba en el límite del contenido del popup con un botón enfocado. Se conserva el manejo nativo de PopupWindow y se añade un fallback antes de despachar a hijos. La entrega real de teclas por WindowManager queda pendiente: el decorador de Robolectric no proporciona siempre el estado de seguimiento de teclas de una ventana adjunta.

Comandos reproducibles:

```sh
python3 scripts/test-robolectric-split.py --controller --classpath-file "$SPLIT_CLASSPATH" --java-home "$JAVA_HOME" --work "$EVIDENCE/split"
python3 scripts/check-arc-preparation.py --android-jar "$ANDROID_JAR"
python3 -m unittest discover -s tests -p 'test_patch*.py'
python3 -m unittest discover -s tests -p 'test_arc_*.py'
python3 -m unittest discover -s tests -p 'test_r53_test_discovery.py'
python3 scripts/test-native-split-scene.py --work "$EVIDENCE/native"
git diff --check
```

Las pruebas JVM usan Android Views reales con Robolectric y adaptadores explícitos para Tab/compositor/JNI. La prueba C++ usa adaptadores host de capas. Ninguna ejecuta una APK o comprueba píxeles GPU.
Evidencia local privada: `/workspace/macdesk-maintenance/archium-r54-split-polish/`.

## Pendientes y límites

- `PENDING_DEVICE_VALIDATION`: aspecto final del marco/cápsula, redimensionado continuo, hover, Escape con teclado real y salida manteniendo foco.
- Comprobar teclado/IME, insets inferiores, ventanas estrechas, cambio de tema/incógnito, diálogos nativos y restauración de superficie en una APK futura.
- La confirmación del usuario de que el split instalado funciona corresponde a la APK anterior; este acabado todavía no está instalado.
- QEMU deshabilitado por instrucción del usuario; no se presenta como PASS.
- Amazon permanece `UNRESOLVED_GRAPHICS_BLOCKER`; este PR no modifica su ruta gráfica.
- No se despacha build, no se modifica el supervisor ni sus procesos, y no se tocan checkpoints, GN args, toolchain, pin o package name.
- Una APK futura deberá usar el último checkpoint compatible verificado y compilar sólo dependencias invalidadas por estos cambios.
