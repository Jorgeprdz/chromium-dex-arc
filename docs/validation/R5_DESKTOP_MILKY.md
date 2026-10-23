# R5 — Desktop lechoso y corrección de paneles móviles

Fecha: 23-oct-2026 CDMX. Rama: `assistant/archium-r5-desktop-native-mobile`.

## Alcance autorizado

El usuario aprobó extender el material liquid a Desktop, con más opacidad. Se reutiliza el sampler acotado existente: no se captura el escritorio, otras ventanas ni una página completa. La barra de título y los botones exteriores de DeX pertenecen al sistema.

- Marco interior, rail, columna y fondo de pestañas: material estable con la paleta del Space y un degradado de iluminación discreto. No se simula blur de contenido inexistente detrás de estas zonas.
- Omnibox: mismo editor, geometría, insets y radio nativos. Un LayerDrawable añade sólo el relleno; Chromium conserva foco/hover y su borde. La API pública está en LocationBarLayout: LocationBarTablet es package-private y no se importa desde Arc.
- Command Bar y contenedor de sugerencias nativas: mismo editor y sesiones; fondo lechoso y muestreo regional. Cerrar/Escape restaura la presentación nativa y no crea pestañas.
- AppMenu, PageInfo y ContextMenu existentes: decorador opt-in compartido por Activity. Conserva padding, restaura fondos al desactivar/detach y sólo despeja capas declaradas por sus owners. PopupMenu del framework y diálogos de Ajustes no se han convertido en cristal.
- Salida de Desktop/destroy: se desactiva el sampler, se retiran fondos/sugerencias y el registro del decorador sólo si pertenece a este coordinator. No se cambian tamaños, proporciones, Spaces, datos, Split View ni controles de ventana del sistema.

## Defectos móviles demostrados y correcciones locales

Evidencia: `/workspace/archium-evidence/phone-review-after-052c55a/`. El run39982605276 terminó correctamente y la APK052c55a se instaló verificada; esa instalación no aceptó todos los requisitos visuales.

`bottom-menu.png` muestra el panel opaco; `more-options.png` muestra texto web nítido a través del menú. La jerarquía de ChromeTabbedActivity reanudada tiene ScrollView904×1880, trasladado aproximadamente a y640 sobre contenido904×1966. La solicitud rebasa el contenido; el sampler exigía contención completa y registraba `copy success=false sample=62x128`.

Ahora se intersectan el área visible y los bounds reales de ContentView. El bitmap se dibuja únicamente en su fracción original, sin estirar el recorte al resto del panel. La captura continúa siendo regional, pequeña y de una sola solicitud en vuelo. Menú móvil y menús nativos usan un tinte más denso y fallback opaco cuando no hay captura; no quedan textos web nítidos como fallback deliberado. Se rechazan resultados de una fuente retirada.

La pill conserva fondo exterior transparente en páginas nativas/NTP aunque el muestreo web esté desactivado. No se rediseña la NTP. La flecha y el título anterior en status bar **no se reprodujeron**: causa/corrección pendientes de evidencia. `site-info.png` capturó otra vez el menú inferior, no prueba física de PageInfo.

## Pruebas y límites

- RED/GREEN del recorte: solicitud parcialmente fuera del contenido y destino sin estiramiento. Ver logs de Robolectric en evidencia; errores iniciales de fixtures corregidos sin relajar política Chromium.
- RED/GREEN de contraste Desktop: la primera prueba detectó fallo AA en una paleta azul; otra paleta próxima al umbral blanco/negro detectó la aproximación del umbral. La iluminación ahora sigue la elección real de contraste; los tonos intermedios usan relleno opaco.
- `final-policy-and-ui.log`: 122 pruebas Android PASS en SDK30/36 (vistas entregadas, sampler, menú y Command Bar; controller/JNI explícitamente adaptados). Incluye 4.096 colores por tema/fondo y conservación de editor, padding y elevación.
- `desktop-native-final.log`: 8 pruebas PASS de métodos de producción extraídos, drawables/layout Android; relleno con insets nativos, foco y restauración.
- `tablet-focus-final.log`: 18 pruebas de foco/layout PASS con ventanas Robolectric reales y fronteras Chromium declaradas.
- `desktop-transitions.log`: 12 pruebas de transición PASS; no son una prueba gráfica Desktop↔Phone.
- Preparación aislada SDK37.2/JDK21 PASS (`preparation-delivery.log`); fronteras Chromium sintéticas, no compilación completa nativa. Revisión de LocationBarBackgroundDrawable fijado confirma relleno y borde dibujados por separado.
- Suite host general424 PASS (`host-final.log`), completada antes del checkpoint; las rutas modificadas se comprobaron además con los runners específicos posteriores. Política original Chromium61 métodos PASS, sin shadows de aplicación nuevos.
- Parche/manifest187 archivos: regeneración idéntica PASS y transición sparse desde fuente198fe8a/checkpoint39829306775-1 PASS,153 timestamps sin cambios conservados. El fixture sustituye únicamente su HEAD sintético; no restaura aquí los bytes del checkpoint. Recibos `patch-reproduction.json`, `source-transition-result.json` y `candidate-local-verification.json`.
- No hay publicación/instalación nueva ni limpieza adicional de checkpoints. Candidato de código local comprobado, aceptación gráfica PENDIENTE.

La matriz gráfica **Claro/Oscuro de todas las superficies es PENDIENTE**. Falta APK del candidato, comparación instalada, menús, teclado, NTP/pill, fullscreen, rotación y transición DeX↔Phone. Se liberó el teléfono para uso del usuario; no se enviaron nuevas acciones después de avisarle. No se lanzó Actions ni se instaló un candidato nuevo en esta revisión.


## Revisión física posterior — 23-oct-2026 CDMX

Run40004797899 terminó con éxito y se instaló la APK1298b31. Hash instalado comprobado nuevamente por ADB: `705b11028f55969af5a486427582145ea57cdf964d4d5cedeea66cd8854de363`. No era una APK anterior.

Evidencia propia: `/workspace/archium-evidence/installed-1298b31-review/`. Se capturaron la pantalla integrada y la ventana Desktop real. Una página diagnóstica local de tres colores confirmó que las barras y el menú móvil sí dibujan contenido desenfocado. La transición rojo/azul, abrupta en la página entre x300 y302, se distribuye gradualmente bajo la pill; `probe-edge-pixels.json` conserva la medición. El usuario reconoció el efecto y pidió **dejar el móvil como está**. Esta decisión congela su material; no equivale a validar temas, NTP e interacciones que no se probaron.

Desktop: `desktop-command.png` y log muestran copias exitosas y dibujo en Command Bar/sugerencias (760×360 y760×299). En cambio, marco/rail/columna/pestañas proceden de `desktopMaterial()` sin targets de captura: `Backdrop.draw()` usa relleno opaco cuando no hay frame. El brillo máximo es0x12 y la sidebar medida cambia apenas de RGB(231,233,236) a(230,232,235) entre zonas vacías. La apariencia prácticamente plana coincide con el reporte. **El material visible del marco/sidebar Desktop NO cumple la expectativa liquid; pendiente de corregir.** No se presenta el fallback opaco como blur del escritorio ni se propone muestrear otras aplicaciones.

Se cerraron únicamente las dos pestañas temporales creadas para diagnóstico y se restauraron las dos pestañas originales del teléfono. Se retiró la redirección ADB tcp18767 y se detuvo el servidor local. Command Bar Desktop cerrada sin navegar ni cambiar proporciones. El usuario fue avisado de que puede desconectar DeX y usar el teléfono. No hubo cambios de producción ni nuevo dispatch durante esta revisión.


## Fix y control de intensidad autorizados — 23-oct-2026 CDMX

El usuario autorizó corregir Desktop, añadir intensidad con vista previa/guardado y realizar un único build incremental. El móvil conserva exactamente su código de producción aprobado.

Diagnóstico adicional de sólo lectura: `adb shell wm disable-blur` informó `Blur supported on device: false` y `Blur enabled: false`. No se cambió ningún flag de blur, GPU o ventana. El marco no puede prometer blur entre ventanas en este dispositivo. Los paneles sobre contenido web mantienen el sampler existente.

Corrección localizada: `ArcDesktopMaterial` sustituye el fallback casi plano únicamente en los cuatro fondos Desktop. Genera una rampa lechosa de tres tonos basada en el color actual del Space, con iluminación y sombra visibles sin bitmap; adapta los extremos para mantener AA frente al foreground nativo, incluidos4.096 colores de prueba y tres intensidades. Las superficies comparten coordenadas verticales de ventana para evitar saltos entre rail, columna y pestañas. Se conservan el clip rectangular y alpha de sombra original. No cambia layout, tamaños, anchos, proporciones ni WebContents.

Apariencia (rueda de color) conserva acceso al selector de color y añade «Intensidad del acabado Desktop». `ArcDesktopMaterialDialog` usa SeekBar nativo de0–100 y muestra el porcentaje, muestra del material y vista previa de la ventana. Predeterminado60; Aceptar guarda en preferencias existentes; Cancelar/Back/dismiss restaura el guardado; Restablecer modifica sólo el borrador hasta aceptar. Borrador por coordinator/ventana y limpieza al destruir. Pulsación prolongada de la rueda mantiene su acceso anterior a posición de dirección.

Pruebas locales reales:
- `candidate-ui.log`:134 ejecuciones Android/Robolectric PASS (SDK30/36), política Chromium67 métodos PASS. Nuevas pruebas: relieve perceptible por los tonos, intensidad, AA, clip/sombra y borrador/cancelación/aplicación/restablecimiento. No son aceptación gráfica de APK.
- `flat-regression/red.log`: mutación del material a relleno plano rechazada por cuatro ejecuciones de los tests de relieve/intensidad. El defecto visual original está capturado en el checkpoint anterior. La primera ejecución del nuevo diálogo falló por callbacks pendientes del looper del fixture; corregido ejecutando el looper real, sin shadows nuevos ni relajar gates.
- `desktop-native.log`:8 PASS; `desktop-transitions.log`:12 PASS. Foco nativo, restauración y métodos de transición preservados en sus fronteras declaradas.
- `patch-tests.log`:25 PASS; `resource-tests.log`:8 PASS; `host-coverage-verified.log`:2 PASS. La expectativa de cobertura host se amplió para incluir la nueva suite, conservando todas las anteriores.
- `preparation-candidate.log`: preparación aislada SDK37.2/JDK21 PASS con fronteras Chromium sintéticas. Nuevas clases y test registrados en GN y gates JVM reales.
- Parche/manifest190 archivos reproducibles; transición sparse desde198fe8a/checkpoint39829306775-1 comprobada en los recibos finales. No se restauró el checkpoint completo localmente.

Evidencia: `/workspace/archium-evidence/desktop-material-control/`. La comparación de hashes confirma que no se modificaron ArcPhoneGlass, navegación móvil, ToolbarManager ni los owners móviles nativos. Sólo hay código Desktop nuevo/coordinator, registros GN y recursos nuevos. No hay nuevas dependencias ni actualización de Chromium.

Aceptación instalada del nuevo acabado y del control en Claro/Oscuro/DeX: PENDIENTE hasta APK de este candidato. La suite host completa se ejecutará en el preflight remoto; no se declara repetida localmente. Fuente incremental conservada y único dispatch con SHA final exacto, sin reintentos automáticos. Estado del run en el directorio nuevo `/workspace/.local/state/archium-r5-material-control/`.
