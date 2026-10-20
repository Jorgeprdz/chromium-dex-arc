# R5.4 — Enlaces, gestos y ampliación temporal

Implementación: `b26ef0cd6419649b47e101768cebaa6f2bc60990`. Se añade al PR2 sobre el marco/cápsula anteriores; integración y compilación incremental autorizadas por el usuario al terminar los gates.

## Entregado

- Doble clic en el agarre devuelve la proporción a 50/50 con transición de 180 ms.
- Magnetismo al centro: captura dentro de 2,5 puntos porcentuales, libera fuera de 4,5; 75/25 y 25/75 siguen siendo ajustes libres sujetos al mínimo real de 240 dp por página.
- Iluminación breve al encajar y hover/foco discreto en botones; se respetan las animaciones desactivadas.
- Ampliación temporal del panel activo desde la cápsula; un agarre de restauración visible permite recuperar la pareja y proporción originales sin crear WebContents ni recargar.
- Menú nativo de enlaces: «Abrir en pestaña dividida», junto a las opciones existentes, tanto con clic derecho como con pulsación larga.
- Ctrl+Alt+clic utiliza el `NEW_SPLIT_VIEW` que ya genera Chromium; Ctrl+clic y Alt+clic conservan sus disposiciones nativas.
- Enlaces HTTP(S) desde ventanas Arc elegibles: con pareja navegan el vecino usando Tab.loadUrl; sin pareja crean una pestaña nativa y la muestran al lado.
- Las creaciones de WebContents hechas por el renderer conservan su propiedad/opener/metadatos nativos: se adopta la pestaña creada en el panel vecino y la anterior se conserva en la sidebar. No se destruyen ni trasplantan contenidos para forzar la ruta.
- Se rechazan fuentes cerradas, otro modelo/ventana/perfil, páginas nativas o acciones bloqueadas por un modal. Esquemas externos conservan su tratamiento nativo.

## Ruta nativa y causa del atajo ausente

`ui::DispositionFromClick` en el pin ya devuelve `NEW_SPLIT_VIEW` para Ctrl+Alt sin Shift. `WebContentsDelegateAndroid::OpenURLFromTab` lo rechazaba antes de Java. Dos condiciones ahora admiten y remiten esa disposición; `TabWebContentsDelegateAndroidImpl` la conecta al router de la ventana Arc. Fuera de una ventana elegible, se normaliza a pestaña de primer plano.

El menú usa `ContextMenuParams`: conserva referrer y AdditionalNavigationParams. La ruta de atajo conserva headers, cuerpo POST y bandera del renderer disponibles en el puente existente. La navegación estándar conserva autoridad sobre beforeunload, descargas y redirecciones; su aceptación real queda pendiente de APK.

## RED/GREEN y revisión

- RED: APIs nuevas de gestos/controlador ausentes en la base.
- RED nativo: el puente rechazaba `NEW_SPLIT_VIEW`; GREEN con la política de clic fijada y las condiciones reales del puente.
- RED/GREEN de los cuerpos Java entregados del menú/atajo; comprobación de identidad de metadata y fallback sin interceptar Ctrl/Alt ordinarios.
- RED: el botón extra desplazaba el agarre expandido 22 dp; GREEN: menú y pivot se anclan al agarre, también después del layout.
- RED: terminar el equilibrado tras cambiar de modelo sobrescribía ratio 0,3 con 0,5; GREEN: ambas animaciones terminan bajo mUpdating antes de desvincular el modelo anterior y al ocultarse la Activity.
- Revisión independiente de código y reexamen de la corrección: sin hallazgos Important/Critical abiertos.

Resultados locales:

- 124/124 casos JVM split/controles/controlador/puente PASS en SDK 30 y 36.
- Preparación de parche y compilación aislada de adaptadores SDK37 PASS.
- Suite host completa de 371 casos: 369 PASS inicialmente; dos fixtures AAPT2 requerían configurar las variables del SDK y pasaron al reejecutarse con AAPT2 genuino/SDK37. No se omitieron ni modificaron sus exigencias.
- Dos casos host nuevos de hooks Java/política nativa PASS por separado; descubrimiento de suites PASS.
- actionlint, sintaxis Python/shell, diff check y reproducción idéntica de patch/manifiesto PASS.

Evidencia privada: `/workspace/macdesk-maintenance/archium-r54-links/`. Robolectric usa adaptadores explícitos para Tab/compositor; los probes nativos ejecutan política/condiciones con adaptadores. No son ejecución GPU, JNI completo ni pruebas de APK. No se han publicado capturas del teléfono ni información de navegación.

## Compilación progresiva

Checkpoint aprobado: `archium-checkpoint-39370769321-1`, run origen `39370769321`, commit origen `8d26b0cf7a5a55701a58ff7d14b59fdd479aa4ca`.
Cuatro grupos, 25 partes; manifiesto SHA256 `e9d0c6d6060e234b836ce90b3684473c4946b352fe0744cb9bcef6ea44b05da7`. Inventario, expiración, digest de artefactos, SHA y pin verificados mediante lectura acotada. El último APK correcto (run39454543084) restauró este mismo checkpoint.
Pin, GN args, toolchain y scripts/workflow de build permanecen iguales al commit origen. La integridad completa, capacidad del runner y productos intermedios se comprueban de nuevo antes de restaurar en CI. No se permite fallback limpio.
La nueva compilación invalida las dependencias reales de Java y del puente C++ modificado; no cambia flags GPU ni borra outputs.
El RUN_ID/SHA despachados y la prueba de sesión independiente se guardarán en el estado persistente del monitor y en el handoff privado; no se anticipa un resultado de CI.

## Pendientes reales

- Validación visual del nuevo APK: doble clic, magnetismo, hover, focus/restore, menú de enlaces y Ctrl+Alt+clic en páginas diversas, incluyendo target=_blank, formularios con cambios, descargas y ventanas estrechas.
- Verificar funcionamiento y foco con IME/insets, diálogos nativos, cambios de perfil, background y pérdida de superficie.
- Adaptación móvil depende del ancho interior; no es sinónimo de 75/25 ni obliga a cada web a tener un diseño móvil correcto.
- Android QEMU deshabilitado por el usuario. Samsung GPU/DeX y Amazon conservan sus pendientes; Amazon sigue UNRESOLVED_GRAPHICS_BLOCKER.
- El monitor conserva seguimiento cada 600 s, ventana abierta al terminar y actualización ADB verificada previamente autorizada; no se reactivan continuaciones ni reparaciones automáticas deshabilitadas por el usuario.
