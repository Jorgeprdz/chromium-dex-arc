# R5 — Desktop fixes y Mobile nativo

Base verificada: `33e79a5` (documentación posterior al código `b51d9b0494a379a58b808d3b4fbf5b3566890fb0`, run39634608887 successful). Rama nueva: `assistant/archium-r5-desktop-native-mobile`; worktree `/workspace/Archium-R5-desktop-native-mobile`. No cambios en main/feat ni eliminación de checkpoints/outputs. Sin Actions en esta tarea.

## P0: defecto localizado y alcance de la corrección

`ArcSplitGeometry` y `ArcSplitContentHost` calculaban y asignaban bounds individuales. `updateWebContentsSize` ya elegía el ancho del panel y llamaba `WebContents.setSize`; la política de compatibilidad no cambia UA ni escala. El hueco está al completar el layout: `CompositorViewHolder.onLayout` no sincronizaba las dos superficies después de `super.onLayout`. Las llamadas previas de inicialización/onSizeChanged pueden usar geometría anterior; el resize de hijos no cambia necesariamente los bounds del holder ni dispara su onSizeChanged.

Se vuelve a ejecutar `updateArcSplitPresentation()` después del layout mientras existe la pareja. Se recalculan bounds con el viewport definitivo y se publican ambos tamaños por el camino existente `updateWebContentsSize` → `WebContents.setSize` → `WebContentsAndroid::SetSize` → `ViewAndroid::OnSizeChanged` → `WebContentsViewAndroid::OnSizeChanged`/sincronización de propiedades visuales. No se cambian ratios, selección, UA/Client Hints, page scale, DPR, WebContents, navegación ni GPU. Las asignaciones de LayoutParams siguen siendo condicionales; el guard de reentrada se conserva.

RED: la prueba del onLayout entregado no publicaba ningún ancho después de la travesía. GREEN: ambos anchos y las vistas Android quedan coherentes para 50→25→50 y 25→75→25. **Esto acredita el hueco de sincronización y su corrección local, no demuestra todavía que explique por sí solo el zoom de todos los sitios. CSS/visual viewport de la APK corregida: NOT RUN.**

Referencias del pin cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 y logs en `/workspace/archium-evidence/r5-desktop-native-mobile/`. El acceso CDP al paquete instalado se identificó como app.archium.android/Chrome157; las consultas posteriores agotaron el timeout. Se retiraron los dos forwards creados; no se alteraron las pestañas del usuario.

## P1: un editor, una Command Bar

Se elimina únicamente el veto ADDRESS_SIDEBAR de `openAddressCommandBar()`. La omnibox superior y la lateral usan el mismo hook LocationBarLayout, editor nativo, selección completa de URL y ArcCommandBar.openAddress. Se mantienen los guards de Desktop, destrucción y popup abierto, el cierre del popover nativo y la restauración compacta.

No se modifica el dispatcher de gestos aprobado ni se crean overlays, editores o pestañas nuevos. Ctrl+T/Meta+T mantiene el modo de nueva búsqueda; Ctrl+L/Meta+L usa el mismo modo de edición de dirección también arriba. Escape/Enter/resultados y animaciones conservan su implementación existente. RED del primer clic superior y GREEN del probe con código de entrada real; foco/autocomplete/GPU en APK nueva pendientes.

## P2: quitar y cerrar son operaciones diferentes

Las filas fijadas añaden clic derecho explícito y mantienen long press. Tooltip descubre ambas acciones. El menú muestra «Quitar de <Space>», mover a carpeta y «Cerrar pestaña» cuando hay identidad nativa disponible. La apertura valida de nuevo la entrada; una fila reciclada o borrada no provoca una excepción.

Quitar usa el comando existente: guardar metadata sin esa entrada y desfijar el tab local sin cerrarlo. Cerrar delega a ArcTabActions.closeTab y ArcNativeTabSession.close, que conserva TabClosureParams.allowUndo(true). No se borra la entrada por solicitar cierre: el callback nativo de confirmación determina la asociación; URL/favoritos se conservan.

Auditoría: rememberTab sólo nace de las acciones explícitas de colecciones; selectOrOpen puede fijar nativamente una entrada ya guardada al seleccionarla. Constructor/restauración/cambio de Space adoptan asociaciones de tabs, sin inventar entradas. Una regresión del adapter cubre restore, didAddTab y selección de Space sin entradas ni pin nativo espontáneo. **El origen histórico de Indeed sigue sin atribuirse: no hay un registro de esa acción y no se modificaron datos del usuario para investigarlo.**

## P3: rollback selectivo

Eliminados:
- ArcMobileControls.java y ArcMobileHomeView.java.
- ArcMobileControlsTest.java y test-robolectric-mobile.py.
- Hook de inicialización, Host, barra inferior/insets, alineación móvil de URL, menú/sheet, NTP superpuesta, selector móvil de Spaces, sesiones y limpieza exclusivos en ChromeTabbedActivity (158 líneas).
- Sus entradas en chrome_java_sources.gni, junit/BUILD.gn, filtros de gates, cobertura y 12 strings arc_mobile_*.
- Hook obsoleto prepareArcMobileNavigation del Root UI; no se restauró el antiguo override de UA.
- Sobrecarga/flags de restauración de ArcNativeTabSession exclusivos de Mobile y sus casos sintéticos huérfanos. Se conserva la clase compartida y su contrato Desktop previo.

El observador de ventanas y la recreación nativa siguen gestionando Desktop↔Phone. Su aplicación de fuente ahora se limita a ventanas Desktop; los controles del teléfono mantienen su tipo nativo. ChromeTabbedActivity queda idéntico a su fuente anterior a la integración Mobile (239750c). Ningún acceso a los datos persistidos cambia de esquema.

Preservados byte a byte respecto al HEAD verificado: ArcCommandBar, ArcCompactOmnibox, ArcOmniboxPlacement, ArcSplitGeometry, ArcSplitContentHost, ArcSidebarState, ArcSidebarStore, ArcSidebarProfiles y ArcTabActions. No se modifican colores, radios, anchos elegidos, favicon, orden/ratio/parejas, branding/package, motor, GN args, toolchain ni dependencias. Los guards de build se restringen a esta rama nueva conservando SHA exacto y checkpoint obligatorio.

## Pruebas y límites

- Split: RED del callback posterior al layout; GREEN144 casos Robolectric SDK30/36, con contratos Tab/WebContents/JNI explícitos. Prueba de reversibilidad registrada también en ArcSplitContentHostTest para el runner nativo.
- Omnibox: RED del clic superior; GREEN26 casos del probe de vistas Android y ArcCommandBar entregada, adaptando el callback nativo de foco. Además, 18 casos del ArcCommandBarTest existente PASS (Escape/Enter/flechas/Tab, resize, RTL, editor único y confirmación nativa).
- Colecciones: RED clic derecho/cierre y fila borrada; GREEN28 casos, quitar/persistencia, cierre separado y favoritos conservados.
- Transiciones: RED fuente personalizada en Phone; GREEN12 casos, recreación/cancelación y geometría del rail.
- Adapter compartido: 12 escenarios PASS; incluyendo aislamiento/perfiles/undo/restore y ausencia de pins implícitos.
- Rollback: 5 invariantes PASS; sin clases, hooks, recursos ni registros Mobile huérfanos.
- Preparación SDK37.2: PASS, 159 archivos. Parche y manifest reproducidos dos veces con hashes idénticos.
- Suite host completa: **389 PASS** (856.117s), con JDK21 instalado, GN real y AAPT2/SDK existentes. Discovery Robolectric específico: PASS.
- Fixture JavaScript: sintaxis comprobada con Node ya disponible en Termux; sin dependencias nuevas.
- Compilación Chromium nativa/APK nueva, aceptación física, CSS/visual viewport, zoom, rendimiento y memoria: NOT RUN. No atribuir estos PASS host a Blink/Viz ni al dispositivo.

## Fixture determinista de aceptación tras el build autorizado

Servir únicamente tests/fixtures: `python3 -m http.server 18765 --bind 127.0.0.1 --directory tests/fixtures`. Si el servidor no reside en el mismo dispositivo, usar el forward/reverse ADB adecuado. Abrir dos pestañas de prueba, con `split-responsive.html?side=left` y `split-responsive.html?side=right`. No inyectar el script en sitios externos.

Usar una ventana amplia que permita 25% sin alcanzar el mínimo de panel existente. Escribir un valor y enviar el formulario una vez antes del primer checkpoint. Mantener fija la ventana; variar la división izquierda 50,25,50,25,75,25 y registrar cada etapa en ambos paneles. Las derechas son las proporciones complementarias. Repetir estrechando el otro panel. Comprobar scroll vertical/horizontal, foco y teclado del formulario sin cambiar el valor ni recargar.

La fixture tiene breakpoints380/700 CSS px, grid1/2/3 columnas y registra innerWidth, clientWidth, visualViewport(width,height,scale), DPR, matchMedia, scroll, estado del formulario, documentId y eventos resize. Exportar ambos JSON. La sexta marca comprueba reversibilidad por las proporciones conocidas y conservación del formulario; cada fila comprueba CSS, overflow, DPR y escala. Un ID/etapas nuevos evidencian recreación/recarga. Contrastar los anchos con los bounds de panel en el diagnóstico nativo: se requiere esa evidencia para cerrar P0.

Sitios sin responsive real, con meta viewport fija o selección de plantilla por servidor/UA pueden conservar su diseño. Se documentará por sitio; no se cambia identidad global ni preferencia de sitio para disimularlo.

## Revisión final

Autorrevisión de la diferencia completa, sin subagentes: nueve componentes compartidos/visuales idénticos; Activity igual a la fuente pre-Mobile; comandos de metadata y cierre separados; callbacks de foco/gestos/seguridad sin modificar; layout condicionado a pareja y con guard de reentrada; ausencia de registros huérfanos y fuente propia fuera de Phone. Las pruebas host no resuelven la aceptación física pendiente. Los stubs exclusivos del antiguo hook móvil también se retiran del probe de transiciones.

## Build

**Estado del candidato: READY FOR BUILD.** La aceptación física y el cierre de P0 en Blink permanecen pendientes; este estado sólo acredita preparación y gates locales.

Checkpoint disponible: archium-checkpoint-39551668868-1, SHA35747e28fec81d80c6b97f82f366fc97809aa339, cuatro grupos no expirados y metadata compatible con el mismo pin. Fue consumido por el run exitoso39634608887. Inventario y comprobación en checkpoint-artifacts.json/checkpoint-compatibility.json. No se descargaron/restauraron los26GB ni se acreditan hashes de bytes o capacidad de runner locales: CI debe verificarlos antes de compilar. Última APK válida conservada.

No se lanzó ningún workflow ni se instaló APK en esta tarea. Siguiente paso: autorización del usuario para un único build incremental del SHA final de esta rama, sin clean fallback, sin QEMU y sin reintentos automáticos. Después, ejecutar la aceptación física anterior y las regresiones de primer clic/atajos, pin/remove/close/reinicio, Mobile nativo e insets, Desktop→Mobile→Desktop.
