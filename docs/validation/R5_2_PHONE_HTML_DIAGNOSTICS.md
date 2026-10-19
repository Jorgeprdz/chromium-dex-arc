# R5.2 — HTML original y reproducción real en Galaxy

Fecha: 2026-10-19. **DEVICE_RUNTIME=EXECUTED, P0-02=FAIL reproducido en DeX.**
No hay corrección del APK ni GREEN posterior. Los PASS de esta matriz cubren
solamente la visibilidad del caso capturado. QEMU sigue QEMU_ABI_BLOCKED.

## Original, acceso y permisos

Ruta aportada por el usuario:
`/storage/emulated/0/Download/Archium_R5_Popup_Diagnostics/archium_popup_diagnostics.html`.
Tamaño: **19475 bytes**. SHA-256:
`ea568bda931099858fc8d24336507d194bb60a6a0ef0e07ef7843fec87427dac`.
Se comprobaron hashes en Android y tras recuperación. Original intacto; copia
idéntica archivada en `tests/fixtures/rendering/r52/original/`.

La ejecución ocurre en Debian/PRoot aarch64 sobre Termux. El directorio `/storage`
visible desde PRoot no expone esos archivos. No se montó almacenamiento ni se
cambiaron permisos. Se utilizó la conexión ADB ya autorizada `emulator-5554`:
Android identifica **Galaxy S25 SM-S931B**, no un emulador QEMU. MediaStore confirma
el archivo y permite abrirlo como **`content://media/external/file/113091`**.
No se trató este URI como equivalente a `file://`; se abrió mediante ACTION_VIEW,
MIME text/html y permiso de lectura del Intent. Sin root, SELinux, desinstalación,
reinicio de PRoot ni acceso a cuentas personales.

Se conservó también `archium-popup-log.txt`, 3759 bytes, SHA-256
`bb067ee97def1f5db06dd2c26c12a7942497e123c8fb0833ff74ea59ff8ae70f`.
Es un registro JavaScript; no es Logcat ni prueba que un cuadro fuera visible.
La copia alternativa `(1)` tiene el mismo hash HTML, pero distinto URI/origen;
los ensayos de esta matriz usaron el original 113091.

## Método realmente ejecutado

Se pusieron al frente exclusivamente el HTML y su pestaña de diagnóstico.
Cada mosaico recibió un clic de mouse mediante CDP Input.dispatchMouseEvent.
Se capturó la pantalla física externa `4620743956780835349`, display lógico 35,
y dumps reales de Activity, WindowManager, SurfaceFlinger y Logcat durante la
apertura, antes de resolver el cuadro. CDP notificó los tipos de diálogos nativos.
Tras capturar, se resolvieron por CDP para continuar; esto **no demuestra** que sus
botones fueran visibles o utilizables. Prompt recibió únicamente `PRUEBA`.
Las capas HTML se cerraron con su botón original; el selector Android se canceló
sin seleccionar archivos. Se cerró sólo la pestaña nueva identificada como
`about:blank` / `Archium popup test`. No se cerraron pestañas personales.

Las primeras capturas de teléfono no correspondían a la superficie externa y
quedaron excluidas. No se interpretan como corrupción. Un ensayo válido anterior
sí capturó alert visible en la pantalla del teléfono, con ModalDialogView presente;
la diferencia teléfono/DeX se observó, pero no es una comparación controlada de
todas las variables. En DeX se probaron sidebar compacta y expandida en distintos
ensayos, sin concluir una comparación exhaustiva entre configuraciones.

## Matriz de los doce mosaicos

| Mosaico | Resultado visual DeX | Evidencia observada |
| --- | --- | --- |
| Alert | FAIL | Scrim visible, sin cuadro; evento alert activo |
| Confirmar acción | FAIL | Scrim visible, sin cuadro; evento confirm activo |
| Prompt | FAIL | Scrim visible, sin campo; evento prompt activo |
| Confirmar descarga | FAIL | confirm invisible; después, snackbar de TXT descargado visible |
| Agregar a favoritos | FAIL | confirm invisible; sólo localStorage de prueba, no bookmarks |
| Secuencia nativa | FAIL | alert → confirm → prompt; capturas sin cuadro en los tres |
| HTML dialog modal | PASS | Cuadro y botones visibles, backdrop visible |
| HTML dialog no modal | PASS | Cuadro visible al pie de la página, sin scrim |
| Overlay personalizado | PASS | Tarjeta CSS y botones visibles sobre scrim |
| window.open | PASS | Nueva pestaña con el texto original de prueba visible |
| Selector de archivo | PASS | Selector Android de acción visible; cancelado sin elegir archivo |
| Comprobar capa HTML | PASS | Mismo showModal original: cuadro y backdrop visibles |

El no modal tiene bounds CSS aproximados x916,y1176,w425,h155 en viewport
2256×1330; su borde inferior excede unos 0.34px el viewport. No estaba ausente ni
centrado: el HTML original usa la colocación no modal del documento.
Modal: x913,y575,w430,h179. Overlay: 2256.7×1330.3, display:flex,z-index:5000.
Son coordenadas CSS, no coordenadas físicas Android.

## Diagnóstico demostrado y límite causal

Durante los eventos JS activos en DeX, `tab_modal_dialog_container` está GONE,
con bounds `0,0–0,0`, y **ModalDialogView no aparece en la jerarquía capturada**.
Esto demuestra un problema de presentación/adjunción (categoría D) durante esos
incidentes. No demuestra que un cuadro correctamente adjunto estuviera detrás de
SurfaceView. Los tokens y el orden SurfaceControl no se deducen de la captura.
No se observó creación y cierre prematuro: los eventos seguían abiertos al capturar
y se cerraron después mediante el protocolo. No se descartan todas las carreras.

El source fijado contiene una ruta compatible: ChromeTabModalPresenter crea el
scrim aunque difiera runEnterAnimation hasta que los browser controls estén
completamente visibles; TabModalPresenter agrega ModalDialogView únicamente en
runEnterAnimation. Archium oculta la toolbar y modifica TopControlsStacker.
**Falta observar hiddenRatio y el callback pendiente dentro del proceso para
probar que ésta es la causa concreta.** No se cambian z-order ni flags GPU por
esta hipótesis. HTML y selector Android visibles separan rutas de implementación;
no prueban una causa compartida con la corrupción de Amazon.

## Evidencias y correlación

Índice depurado por caso: [r52/phone-cases.json](r52/phone-cases.json), con timestamps
UTC, acción, bounds, tipos JS, hashes de captura y logs. Ejemplo alert:
18:11:55.294Z inicio; 18:11:57.152Z captura. Logcat usa hora local UTC−6 del teléfono.
Los dumps/capturas se tomaron secuencialmente, no de forma atómica; Logcat incluye
una ventana retrospectiva de 400 líneas con filtros. No se atribuye cada línea
al clic sin cotejar timestamp/PID. Originales privados:
`/workspace/macdesk-maintenance/archium-r52/device-original/`.
Capturas: `dex-*-during.PRIVATE.png`; secuencia adicional `dex-chain-native-1/2`.
Logs reales: `*-activity.PRIVATE.txt`, `*-window.PRIVATE.txt`,
`*-surface.PRIVATE.txt`, `*-logcat.PRIVATE.txt`. No se publican capturas completas,
URLs privadas ni dumps sin depurar. Manifiesto de originales:
`/workspace/macdesk-maintenance/archium-r52/phone-originals-manifest.json`.

Chrome Android comparativo: **NOT_TESTED**; no se activaron perfiles personales.
Botones auxiliares de exportar/copiar/importar log: NOT_TESTED en esta sesión;
no son los doce mosaicos. Marcadores reales, descargas generales y persistencia
completa: PENDING. GPU Amazon: causa NOT_PROVEN; no ensayo sobre sesión comercial.
APK probada: versión instalada 808600074, hash
`6807d5a200f0e98b5f329510af3c3b2807e1c2e12742affd7b6c17da0677d70f`,
correspondiente al run 39259086848 / fca5d00619a531a7ec8f702ab8272a926bc170fb.
No se instaló la APK del run actualmente activo.
