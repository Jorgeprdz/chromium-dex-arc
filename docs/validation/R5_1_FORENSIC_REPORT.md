# Archium R5.1 — auditoría post-build

Estado: **REPARACIÓN PARCIAL PREPARADA PARA BUILD INCREMENTAL**. Ningún defecto visual está cerrado.

## Identidad y ejecución anterior

Run evaluado: [39259086848](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39259086848),
SHA `fca5d00619a531a7ec8f702ab8272a926bc170fb`, Chromium
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` / 157.0.8086.0.
GitHub terminó SUCCESS con preflight/build aprobados y APK ARM64 publicada.
El hash medido mediante Android del APK instalado coincide con el recibo del run:
`6807d5a200f0e98b5f329510af3c3b2807e1c2e12742affd7b6c17da0677d70f`.
Package `app.archium.android`, versionCode 808600074.

El job QEMU terminó con éxito administrativo, pero su resultado fue
**QEMU_ABI_BLOCKED**: host x86_64, sin KVM, emulador ni AVD ARM64 disponible.
Sus 32 casos Android quedaron BLOCKED. No hubo screenshots ni ejecución Android
QEMU. El supervisor original se detuvo tras tres fallos de conexión a GitHub;
no acredita instalación automática ni auditoría final.

## Evidencia recuperada

Directorio privado: `/workspace/macdesk-maintenance/archium-r51/`.
Se conservaron originales, hashes y tamaños en `evidence-manifest.json`.
No se publican capturas ni dumps completos porque contienen información del usuario.

- `amazon.jpg`: captura de teléfono con regiones negras, repetición de texto e imágenes.
- `dialog.jpg`: captura DeX de las 11:09:22 con títulos superpuestos en una fila.
- `drag.jpg`: captura DeX de las 11:11:54 con página oscurecida sin cuadro visible y
  superposición persistente de títulos. Estos nombres locales son descriptivos;
  no establecen qué acción exacta precedió cada captura.
- `archium-popup-log.txt`: registro **JavaScript**, exportado a las 17:02:58 UTC;
  no es Logcat. Registra alert, confirm, prompt, showModal, show y overlay CSS.
  Sus retornos/etiquetas OK no demuestran visibilidad. La captura posterior no
  puede alinearse por sí sola con una acción de este registro anterior.
- `logcat.txt`, `activity.txt`, `windows.txt`, `surfaces.txt`, `gfxinfo.txt`:
  evidencia Android auténtica recogida sin lanzar acciones de prueba en el teléfono.
- `gpu-system-info.json`: consulta DevTools de solo lectura del navegador instalado.
- `graphics-trace.atrace`: captura auténtica y acotada de cinco segundos, categorías
  gfx/view/wm; no se sincronizó con una reproducción del defecto.

## FAIL 1 — corrupción de renderizado

**FAIL reportado por usuario y visible en captura. Causa raíz: NOT_PROVEN.**
La captura en teléfono impide atribuir el conjunto del fallo exclusivamente al
recorte del frame Arc de escritorio. La consulta de GPU informa Adreno 830,
ANGLE Vulkan 1.3.284, driver 512.800.64, backend Skia GraphiteDawnVulkan,
rasterización y composición GPU habilitadas; crashCount=0 en esa consulta.
Esto identifica la ruta activa, no demuestra un defecto de driver, Blink, Viz,
Skia o sincronización. No se modifican GPU, GN args, cachés ni flags del usuario.

Hipótesis pendientes: raster/tiles bajo Graphite, recursos/buffers reutilizados,
invalidación y sincronización de Surface. Falta una reproducción Android con
traza correlacionada y comparación controlada. Los incidentes upstream de otros
GPUs/versiones no constituyen prueba para este equipo.

RED visual: captura del usuario. GREEN visual: **NOT_TESTED**.

## FAIL 2 — cuadros invisibles

**FAIL reportado por usuario. Causa raíz: NOT_PROVEN.**

| Ruta | Evidencia disponible | Resultado visual |
| --- | --- | --- |
| JS alert/confirm/prompt | inicio/retorno registrados en JavaScript | FAIL reportado; sin GREEN |
| HTML dialog modal | showModal/open y cierre registrados | FAIL de categoría reportado; caso individual no aislado |
| HTML dialog no modal | show y cierre registrados | NOT_TESTED individualmente con evidencia visual correlacionada |
| Overlay CSS | apertura/cierre registrados | NOT_TESTED individualmente con evidencia visual correlacionada |
| Chromium/Android nativo | selector solicitado; ruta de descarga reportada operable | no equivale a PASS de todos los diálogos |

La jerarquía capturada fuera del incidente muestra el contenedor modal GONE y
0×0; ese estado normal cerrado no demuestra que estuviera vacío durante alert.
No se altera z-order, tokens, foco o reparenting sin identificar un cuadro activo.
Una causa compartida con FAIL 1 permanece hipótesis, no conclusión.

RED visual: reporte/captura del usuario. GREEN visual: **NOT_TESTED**.

## FAIL 3 — superposición al reordenar

**Defecto de preservación de modelos demostrado; aceptación visual pendiente.**
El dump auténtico conserva una fila antigua de ancho 208 en y=72..108 junto a
otra de ancho 44 en el mismo y=72..108, dentro de RecyclerView compacto. Dos filas
conservan estado seleccionado. Esto demuestra coexistencia de vistas con geometría
obsoleta; no prueba por sí solo la cadena exacta que las dejó retenidas.

La implementación añadida por Arc llama refreshTabPresentation después de mover
pestañas y en notificaciones de selección. El reset del mediador borra/recrea
modelos cuando cambia su orden. Una prueba JVM de los métodos entregados, con
TabModel/reset explícitamente simulados, reproduce pérdida de identidad de filas
al reordenar: **RED**. La corrección reconcilia únicamente la misma población de
pestañas simples usando movimientos del ModelList y conserva sus PropertyModel:
**GREEN** en cinco casos JVM. No oculta filas ni recrea Activities/WebContents.
Altas/bajas, grupos, fijadas y presentación sin filtro mantienen el reset anterior.

Se añade también un test de Chromium/Robolectric para ciclos repetidos A/B/C
con sidebar expandida y compacta; su ejecución queda pendiente del gate CI.
La prueba JVM verifica orden, identidad y selección de modelo durante 30 ciclos;
no ejecuta drag Android, no mide píxeles ni demuestra selección de WebContents.
La relación causal con el solapamiento físico sigue **PENDING_DEVICE_VALIDATION**.

Archivos de implementación:
`.source-modified/.../vertical_tabs/VerticalTabListCoordinator.java` y su
`VerticalTabListCoordinatorUnitTest.java`; patch y manifest regenerados.
Regresión host: `tests/test_r51_reorder_projection.py`. La mutación negativa que
elimina el guard de reconciliación vuelve a fallar por pérdida de identidad; el
código restaurado pasa de nuevo.

## Regresiones y alcance

Regresión Surface: **4 tests Robolectric PASS** (SDK30/36), limitada a crops y
listeners. Preparación API Android, compilación Python, workflow lint e idempotencia
del parche: PASS. Suite host completa: **325 tests PASS**, 626.432 segundos.

Se preservan los PASS informados por el usuario para restauración entre apps y
pestañas, omnibox/navegación y ventanas/formularios como **USER_REPORTED_PASS**.
No se convierten en ejecución propia. Las suites existentes de sesión, navegación,
omnibox y Surface forman parte de la verificación local/CI. Marcadores, descargas
y persistencia completa permanecen PENDING. GPU Samsung y DeX:
**PENDING_DEVICE_VALIDATION**.

## Build y supervisor

Checkpoint candidato más reciente: `archium-checkpoint-38511423805-1`,
run 38511423805, SHA `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`.
El run evaluado no publicó un checkpoint nuevo. Se reverifican cuatro grupos y
manifiesto SHA256 `50d9ad33ed84646d15368c696ff74fd103a7a9ef5e5829c152c399b95ccea56f`.
GN args/toolchain/pin se conservan; capacidad y validación de todos los bytes son
gates obligatorios del runner antes de compilar. No existe fallback limpio.

Nueva ventana de diez horas autorizada explícitamente por el usuario; se conservan
historial y contadores de reparación. Al despachar se generará el informe de entrega privado
`/workspace/macdesk-maintenance/archium-r51/R5_1_HANDOFF_REPORT.md`, con SHA de
implementación, RUN_ID real, checkpoint y prueba del proceso independiente. El
registro del supervisor es `/workspace/.local/state/archium-r5-progressive/state.json`.
La APK de la reparación sigue PENDING_BUILD hasta que CI la verifique.
Estas identidades son distintas de las del build evaluado. No se presenta esta reparación parcial como resolución de los
fallos de GPU o diálogos.
