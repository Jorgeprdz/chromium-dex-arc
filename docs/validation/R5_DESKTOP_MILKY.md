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
