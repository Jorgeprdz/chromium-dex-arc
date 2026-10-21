# R5.3 — reparación de compilación y monitor persistente

## Fallo confirmado

Run `39362104801`, SHA `1a6ddb45815740040a4a3a33e7b71c4b309043e6`: preflight y restauración PASS; compilación Java FAIL. Cuatro declaraciones situaron `@Nullable` TYPE_USE delante del paquete `java.util.function` en lugar del nombre de tipo. Afectó campo/setter de IntConsumer en CompositorViewHolder y campo/setter de Consumer<Tab> en VerticalTabListCoordinator.

Corrección mínima: importar IntConsumer/Consumer y anotar el tipo simple. Se conservan firmas, callbacks, split, foco, modo móvil y navegación. La regresión compila declaraciones y setters entregados con la anotación TYPE_USE realista: RED cuatro errores, GREEN tras imports. No es una compilación completa de Chromium.

## Checkpoint de recuperación

Último checkpoint: `archium-checkpoint-39362104801-1`, fuente SHA `1a6ddb45815740040a4a3a33e7b71c4b309043e6`, run `39362104801`.
Receipt: BUILD_FAILED por compilador, exit 1; pack_verified y checkpoint_verified true. No se confunde con BUILD_INCOMPLETE recuperable automático. Se permite el nuevo intento tras reparar el código.
Inventario remoto verificado: 4 grupos/25 partes, 26,509,074,218 bytes; manifiesto SHA256 `5e8e31299e2f56d496513bdb1185f0a924552be40607c43f70653c8d2d738672`. Progreso conservado: 733 outputs, 2 gates. Espacio/inodos, hashes completos y configuración se validan otra vez en el runner antes de restaurar/compilar.
No cambian pin Chromium, GN args, toolchain, firma ni package. No limpieza de outputs ni build desde cero.

## Cambio solicitado: sin QEMU y sólo observación

El caller recibe `run_qemu=false` en este despacho. QEMU queda desactivado por defecto y en los inputs de este despacho; su job no se ejecuta. La infraestructura opcional se conserva para una futura activación explícita. No se convierte QEMU_ABI_BLOCKED anterior en PASS: esta ejecución se registra DISABLED_BY_USER.
Se conservan preflight, tests host/Robolectric, compilación nativa/JNI y verificación de APK. La aceptación visual de las funcionalidades nuevas permanece pendiente de APK y dispositivo.

El nuevo `scripts/archium-r5-watch.py` observa un solo RUN_ID/SHA y sus jobs/artefactos. No despacha, repara, reanuda Codex ni instala. El bloqueo anterior de resume por escritor activo no se presenta como resuelto: el modo solicitado no utiliza ese mecanismo.

## Terminal

- Sesión nativa independiente de Termux, con locks contra duplicados y estado persistente.
- Primera consulta inmediata; consultas activas en slots de 600 segundos, sin añadir el tiempo de petición al intervalo.
- Marco ASCII, fondo oscuro, encabezado cian, estados verde/ámbar/rojo y limpieza ANSI de pantalla/cursor antes de cada redibujado.
- RUN_ID, SHA, workflow, etapa, checkpoint, restauración, job/step, tiempo, consultas y estado APK.
- Al finalizar conserva el resultado y mantiene la ventana abierta; deja de consultar GitHub. Ctrl+C cierra de forma explícita.
- Los logs persistentes son JSONL, separados de la salida ANSI. Si se vuelve a abrir un resultado terminado, conserva su pantalla sin relanzar nada.
- La existencia de un artefacto APK se distingue de su descarga/verificación. No se declara APK_VERIFIED con sólo metadatos.
- BUILD_INCOMPLETE se comprueba con el receipt exacto y se muestra con checkpoint guardado; no inicia otra etapa.

## Verificación

Regresiones dirigidas: 13 PASS (Java TYPE_USE, opt-out vinculado al despacho, identidad de run/receipt, colores y clear, finalización sin cierre, intervalos, errores de red y ausencia de acciones automáticas).
Preparación del parche/API37 PASS; actionlint y sintaxis shell/Python PASS. Suite host completa: 352/352 PASS (618.900 s); tras los últimos ajustes del monitor/default QEMU se ejecutaron de nuevo las 13 regresiones dirigidas, PASS. Compilación Chromium real y nueva APK pendientes del nuevo run.

TODO y estado privado registran el nuevo SHA/RUN_ID durante el handoff. Se conserva la ventana de diez horas ya autorizada y los contadores existentes, sin reiniciarlos.
