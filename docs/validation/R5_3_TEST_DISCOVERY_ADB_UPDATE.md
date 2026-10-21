# R5.3 — descubrimiento de tests y actualización ADB

## Fallo y corrección

Run fallido: [39370769321](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39370769321), SHA `8d26b0cf7a5a55701a58ff7d14b59fdd479aa4ca`.
El gate ejecutó suites anteriores y se detuvo al descubrir cero tests de `ArcSplitStateTest`.
`testing/android/junit/java/src/org/chromium/testing/local/JunitTestMain.java`, en el pin
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, descubre únicamente clases anotadas `@RunWith`.
Faltaba en `ArcSplitStateTest` y `ArcSplitViewportPolicyTest`. Ambas conservan todos sus asserts y filtros.
Se añade el runner Robolectric y la configuración API30/36 con gráficos/SQLite LEGACY usada por las otras suites.
No cambia el comportamiento de producción ni se salta el gate que falló.

RED: regresión de descubrimiento falla en las dos clases originales.
GREEN: regresión pasa; 86 tests JVM del harness split pasan, incluidos estado y política de viewport.
El harness utiliza adaptadores explícitos para límites nativos; no demuestra renderizado GPU ni ejecución en el Galaxy.
51 regresiones de monitor/gates PASS, preparación API37 PASS, actionlint y sintaxis Python/shell PASS.
La suite host completa se exige de nuevo en preflight de CI; no se atribuye a este SHA la ejecución local completa del SHA anterior.
La confirmación con el runner íntegro de Chromium queda pendiente de CI.

## Checkpoint

Reutilizar exclusivamente `archium-checkpoint-39370769321-1`, commit origen `8d26b0c`, run origen `39370769321`.
El recibo indica `checkpoint_verified=true`, `pack_verified=true`, aunque el gate terminó en fallo técnico.
Inventario autenticado: cuatro grupos, 25 partes, 26.518.090.449 bytes de artefactos.
SHA256 del manifiesto: `e9d0c6d6060e234b836ce90b3684473c4946b352fe0744cb9bcef6ea44b05da7`.
Pin y GN args permanecen iguales. CI deberá comprobar capacidad, toolchain y todos los hashes antes de restaurar.
No se descargaron 26 GB al teléfono ni se afirma restauración local completa. No hay limpieza de outputs.

## Monitor y actualización autorizada

El usuario solicita «aplica fix lanza workflow y haz autoinstall con ADb».
Se mantiene un único monitor, consulta inmediata y cada 600s, pantalla ASCII con colores y limpieza previa;
la ventana permanece abierta tras terminar. QEMU sigue desactivado por decisión expresa, sin PASS ficticio.
No se habilitan reparaciones ni relanzamientos automáticos.
La nueva solicitud autoriza un reintento manual adicional; se conserva el historial de etapas y reparaciones,
sin reiniciar la ventana nocturna previamente autorizada.

Tras SUCCESS, exige authorize/preflight/build PASS y recibo exacto; descarga sólo el artefacto del run esperado.
Comprueba BUILD_REPORT, SHA256SUMS, package, ARM64 y firma. ADB identifica el mismo teléfono autorizado.
Compara certificado y versionCode con el APK instalado antes de usar únicamente `adb install -r`.
Conserva datos, rechaza certificado incompatible/downgrade y persiste intención antes de instalar.
No repite un intento ambiguo tras reinicio. INSTALL_SUCCESS exige APK leído otra vez de Android con hash,
certificado, package y versionCode esperados y dumpsys coincidente. Confirmación exigida por Android queda pendiente.
Si ADB no está autorizado al finalizar: INSTALL_PENDING_DEVICE, APK conservada.

Pruebas del instalador: éxito con evidencia del sistema, certificado incompatible, downgrade, dispositivo ausente,
bytes incorrectos tras Success, instalación ya coincidente, intento previo ambiguo y confirmación Android.
Estas pruebas son simulaciones del límite ADB; la nueva APK aún no está instalada.
Prueba ADB real previa: APK instalada ARM64, app.archium.android, versionCode 808600074,
SHA256 `9db795ddf861a008e0181a60c52bbdf96e91c070c3464ae2b85913f545e6dc37` (APK anterior).

## Pendientes

Run/SHA nuevos, configuración ADB y evidencia de handoff se registran en el estado persistente privado.
Build, instalación y aceptación visual R5.3 continúan pendientes hasta ejecución real.
Amazon permanece UNRESOLVED_GRAPHICS_BLOCKER; no se ha tocado GPU, flags, diálogos ni identidad de pestañas.
