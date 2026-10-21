# R4 — Viabilidad técnica: refinamiento visual y Link Hover Preview

Fecha: 2026-10-21. Alcance: auditoría de fuentes; **sin autorización de implementación**.
Base Archium examinada: `cb9822aa0a4a0e4a5d5609bd80da470b0d4db325`.
Chromium fijado: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, `chrome/VERSION` = **157.0.8086.0**.
No se cambió producción, configuración gráfica, TODO, supervisor ni checkpoints; no se ejecutaron builds, pruebas Android, benchmarks ni PRs. Los cambios documentales previos del workspace se conservaron.

## Dictamen

**La preview real es técnicamente viable como experimento Android nativo: SPIKE.** El pin contiene eventos de URL bajo el cursor, observación no consumidora de hover, creación de WebContents auxiliares y una infraestructura de preview efímera con compositor propio. No hace falta sustituir Chromium por WebView ni inyectar JavaScript en todas las páginas. La dependencia de pestañas efímeras ya aparece en el BUILD Android de la base.

No existe, en los componentes inspeccionados de Archium, una función completa que conecte esos mecanismos para una ventana de hover. La preview efímera existente se abre explícitamente en un bottom sheet; convertirla en superficie flotante pasiva requiere trabajo nuevo de coordinación y políticas. Aislamiento gráfico, foco, historial global, privacidad y presupuesto de recursos siguen sin validación experimental. El fallo gráfico de Amazon no se considera resuelto ni atribuido a esta infraestructura.

Los siete refinamientos visuales son viables sobre componentes existentes. Los GO siguientes significan recomendación técnica, **no autorización para implementarlos**. Se conserva el retardo solicitado de **3000 ms**.

## A. Inventario verificable y procedencia

Las rutas de esta tabla son relativas a la raíz de Chromium, salvo las que empiezan por `chromium/`, `patches/` o `scripts/`, que pertenecen al repositorio Archium. Las modificaciones upstream de Archium se distribuyen mediante `patches/archium-desktop.patch`; sus versiones de referencia y modificada están declaradas por hash en `patches/upstream-files.json`. Se examinaron las copias locales `.source-reference/` y `.source-modified/` correspondientes. No se confunden con un checkout completo de Chromium compilado.

| Área | Archivo, clase o método comprobado | Hallazgo |
|---|---|---|
| Pin | `scripts/check-recovery-checkpoint.py`, `patches/upstream-files.json`; [chrome/VERSION][version] | Revisión fijada y versión 157.0.8086.0. |
| Estado de filas | `chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java:470`, `updateSelectionAndBackground`, `applyHoverBackgroundState:906`, `setupTabHoverListener:955` | Usa PropertyModel/IS_SELECTED, multiselección, estado fijado, título, favicon y alertas; no necesita otro store de selección. |
| Modelo y regiones | Misma raíz `tab_management/TabListMediator.java`, `vertical_tabs/VerticalTabListCoordinator.java`, `updatePinnedTabsSeparatorVisibility` | Listas fijadas y ordinarias existentes, predicado de visibilidad por Espacio; separador condicionado por listas visibles y posición colapsada. |
| Hover de pestañas | Misma raíz `vertical_tabs/VerticalTabItemHoverController.java:163,321,478,608`, `TabHoverCardView` | Hover cards nativas, foco, temporizador, cancelación, posicionamiento y destrucción. Omite hover card para pestaña seleccionada; disponibilidad efectiva depende de configuración/stubs. |
| Apariencia Arc | `chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java:139–164` | Preferencias, superficie, superficie activa, foreground y selección existentes. |
| Contenedores Arc | `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java`, `styleInteraction`, `refreshNativeRows` | Cabecera, contenido y footer existentes. Algunos controles comparten tratamiento de hover/foco; evitar notifyDataSetChanged por cada evento. |
| Spaces reales | Misma raíz `arc/ArcSidebarState.java:66,319,350`, `ArcSidebarStore`, `ArcSidebarProfiles.java:14–29`, `ArcNativeTabSession` | Modelo propio de Espacios, pertenencia de tabs, serialización y preferencia por perfil `archium.sidebar.state`. OTR usa store en memoria. No son simplemente TabGroups. |
| Selector de Espacio | Misma raíz `arc/ArcCollectionsView.java:97,242,311` | Ya muestra Espacio actual y menú para elegir/crear/eliminar. Las colecciones tienen tooltips en favoritos. |
| Animaciones | Misma raíz `arc/ArcSplitSwapAnimator.java:14`, `ArcSplitViewCoordinator` | Hay animador localizado de 180 ms para split; su existencia no justifica aplicarlo a todas las filas ni demuestra su costo. |
| Favicons | [TabListFaviconProvider][favprovider], `getFaviconForTabFetcher`, `getFaviconForTabAsync`, `destroy`; `TabListViewBinderUtils.updateFaviconImage` | Reutiliza icono del WebContents y servicios de favicon, fallback y callbacks. La identidad de fila/resultado debe preservarse al reciclar. |
| Iconos de colecciones | `ArcDesktopCoordinator.java:874`; [LargeIconBridge][largeicon] | Solicitud local mediante getLargeIconForUrl y protección de callbacks. Existe otra API explícita de Google Server: no usarla como si fuera cache local. |
| URL bajo puntero | [WebViewImpl.UpdateTargetURL][blink], [WebContentsImpl.UpdateTargetURL][wcimpl], [WebContentsDelegateAndroid.UpdateTargetURL][delegate] | Ruta nativa Blink → navegador → Java; el callback comunica URL, no rectángulo del enlace ni título. |
| Entrega al tab | `chrome/android/java/src/org/chromium/chrome/browser/tab/TabWebContentsDelegateAndroidImpl.java:227`; [TabObserver.onUpdateTargetUrl][tabobserver] | El delegate notifica observadores del Tab. El observador existe en Android 157. |
| Puntero sin interceptar | [ContentView.addOnHoverListener/removeOnHoverListener/onHoverEvent][contentview] | Lista de observadores; después reenvía el evento a EventForwarder. No sustituir su listener ni consumir entrada del motor. |
| Gestos y coordenadas | [EventForwarder][events], [RenderCoordinates][coordinates], `content_public.browser.GestureListenerManager`, `GestureStateListener` | Diferencia mouse/trackpad y rutas relativas; escala y offsets del contenido; eventos de scroll/fling para cancelar. |
| Preview existente | [EphemeralTabCoordinator][ephemeral], [EphemeralTabMediator][mediator], [EphemeralTabSheetContent][sheet] | WebContents real auxiliar, carga, navegación, presentación en bottom sheet y liberación. `chrome/android/BUILD.gn` ya depende de `//chrome/browser/ui/android/ephemeraltab:java`. |
| Creación y perfil | [WebContentsFactory][factory] | createWebContents(Profile, initiallyHidden, initializeRenderer); además existe una fábrica con StoragePartition separada **marcada experimental y específica de otro experimento**, no un contrato listo para este producto. |
| Compositor auxiliar | [ThinWebViewFactory][thin], [ThinWebViewImpl][thinimpl], [CompositorViewImpl][compositor] | ThinWebView muestra WebContents de Chromium con superficie propia; no es android.webkit.WebView. El overload con IntentRequestTracker crea WindowAndroid propio. |
| Miniaturas | [TabContentManager][thumbnails], getTabThumbnailWithCallback:355, cacheTabThumbnailWithCallback:578 | Cache ligada a tabId y captura de un Tab existente; no API universal URL→captura. |

Las fuentes adicionales se recuperaron de la revisión exacta, con tamaños y SHA-256 registrados en `/workspace/macdesk-maintenance/archium-r4-feasibility/inventory.json`; copias en su subdirectorio `source/`. Ese inventario privado conserva también búsquedas fallidas de rutas: un 404 no se utilizó para demostrar ausencia de una API.

## B. Matriz de las nueve propuestas

Complejidad y riesgo son estimaciones de arquitectura, no mediciones.

| Propuesta | Viable | Complejidad | Riesgo | Veredicto y recomendación |
|---|---|---|---|---|
| Selección activa refinada | Sí | Baja-media | Bajo; medio al integrar parejas | **GO**. Derivar actividad de TabModel/IS_SELECTED, distinguir multiselección y conservar activo+hover+foco. Usar colores existentes y trazos dentro de bounds. |
| Separadores sutiles | Sí | Baja | Bajo | **GO**. Aprovechar regiones y listas existentes; priorizar espaciado disponible o trazo sin consumir alto adicional. No alterar ancho, botones ni orden. |
| Tooltips flotantes premium | Sí, condicionada | Media | Medio por entrada/accesibilidad | **GO para reutilizar hover card/tooltip nativo**. Corregir reciclado y cobertura de seleccionada si procede. Un overlay completamente nuevo requiere SPIKE y no aporta ventaja demostrada. |
| Normalización óptica de favicons | Sí, limitada | Baja-media | Bajo | **GO**. Centrado, FIT_CENTER y fallback uniforme dentro del tamaño actual. No teñir, redibujar, recortar marcas ni decodificar bitmaps en cada hover. |
| Profundidad de sidebar | Sí | Baja | Bajo con trazo; mayor con efectos | **GO para borde interior de 1 píxel físico** usando paleta actual. Sombra añade composición/overdraw; blur continuo no se recomienda para este alcance. |
| Indicadores de Spaces | Sí: modelo ya existe | Baja-media | Medio si duplica estado | **GO**. Proyectar Espacio actual desde ArcSidebarState y su selector; sin otra persistencia, badge de color nuevo ni confundirlo con grupos. |
| Microanimaciones | Sí, condicionada | Media | Medio por reciclado/frames | **GO limitado** a propiedades de UI, cancelables y respetando animaciones desactivadas. No animar tamaño de WebContents ni superficies durante selección. Medir antes de aprobar efectos adicionales. |
| Hover Preview estático | Sí para cache; incompleto para destino nuevo | Media en cache; alta si requiere carga | Bajo-medio en cache; alto con red | **GO para snapshot existente del mismo perfil y URL vigente; SPIKE para cobertura general**. Un cache miss no debe navegar silenciosamente. |
| Hover Preview real | Sí, infraestructura Android comprobada | Alta, integración localizada más políticas | Alto: red, perfil, superficie, lifecycle | **SPIKE**. WebContents y compositor auxiliares, una sola preview, privacidad explícita y gates medidos. No necesita parchear Blink/Viz para demostrar el concepto. |

Normalización óptica no significa que todos los logos ocupen igual área de tinta: corregir automáticamente transparencia interna exige análisis/crop que puede alterar la marca; queda fuera del GO.

## C. Comparación de las tres alternativas de preview

| Alternativa | Información disponible y dependencias | Red, estado y costo | Qué gana / qué pierde |
|---|---|---|---|
| A. Tarjeta enriquecida | URL del callback; favicon local; título de tab/historial/bookmark si existe coincidencia y autorización. Descripción solo si ya almacenada legítimamente. El callback no entrega texto ni atributo title del enlace. | No necesita renderer nuevo. Cache/historial requieren lookup acotado y aislamiento por perfil. No hacer GET/HEAD, favicon remoto ni scrape de metadatos implícitos. | Menor costo, información limitada y a veces solo dominio/URL. **No equivale a la vista real solicitada**. |
| B. Snapshot | Miniatura existente de un Tab mediante TabContentManager, validando URL, generación y perfil. Capturar una nueva página precisa cargarla primero. | Bitmap cacheado: sin navegación ni renderer nuevo; memoria proporcional a resolución. Una captura nueva mediante WebContents tiene casi los mismos riesgos de red/JS que C. | Vista visual barata si ya existe, puede estar obsoleta o no existir. Nunca presentar cache viejo como contenido actual. |
| C. Vista real | WebContentsFactory + ContentView + ThinWebViewFactory, adaptación de patrones EphemeralTab. Viewport propio, delegate de políticas y superficie flotante Android. | Puede requerir proceso renderer, JS, red, buffers y texturas; usar Profile normal comparte contexto de sesión. Mantenerse aislada visualmente no aísla cookies. | Contenido real sin pestaña visible; mayor complejidad y riesgo. Es el objetivo a validar, no una capacidad ya implementada. |

`WebContents.captureContentAsBitmapForTesting` no es una justificación para una API de captura de producción. Copias nativas de superficies tampoco resuelven la ausencia de contenido previamente renderizado.

## D. Respuestas a las diez preguntas arquitectónicas

1. **Recepción actual.** Archium hereda ContentView/EventForwarder para mouse y TabWebContentsDelegateAndroidImpl → TabObserver para URL objetivo. No se encontró un coordinador Archium que una ambos para Link Hover Preview. La sidebar tiene una ruta de hover distinta que no observa enlaces web.
2. **URL nativa sin JavaScript.** Sí: WebViewImpl actualiza target URL, WebContentsImpl valida la procedencia del frame al limpiar el valor, WebContentsDelegateAndroid llama a Java y el Tab distribuye onUpdateTargetUrl. No exige hit-test DOM inyectado. El callback puede no cambiar al pasar entre enlaces con igual URL y no certifica por sí solo una interacción mouse.
3. **APIs aprovechables.** TabObserver.onUpdateTargetUrl; ContentView.add/removeOnHoverListener; GestureListenerManager; WebContentsObserver; RenderCoordinates; WebContentsFactory; ThinWebViewFactory; referencias EphemeralTab; TabContentManager para miniaturas existentes. La URL y el puntero llegan por vías distintas: correlacionar tab/WebContents, generación y momento, rechazando callbacks tardíos.
4. **Ventana flotante en DeX.** Viable mediante overlay dentro del root de la Activity, sin otra Activity ni permisos SYSTEM_ALERT_WINDOW. Las hover cards nativas ya se posicionan en un contenedor Android. PopupWindow no enfocable es alternativa a probar, no requisito; los tokens y el orden con superficies deben validarse. No requiere API Samsung.
5. **Coordenadas.** El MotionEvent de ContentView ya entrega coordenadas de vista en píxeles: convertir a root/ventana mediante ubicaciones y transformaciones reales de las vistas. Usar densidad del display actual para 12–16 dp; descontar insets y limitar al pane/área visible. No multiplicar de nuevo por zoom/DSF. Si se necesitan coordenadas CSS, RenderCoordinates aporta conversión local CSS→px, scroll y offset, pero frames remotos y transforms requieren tratamiento específico. La API URL no entrega bounds del enlace; evitar taparlo perfectamente no puede garantizarse con solo ese callback.
6. **Vista auxiliar, pestañas e historial.** EphemeralTab demuestra un WebContents sin añadir una pestaña visible y con NavigationController separado; la promoción a Tab ocurre únicamente por acción explícita. Eso conserva el back stack principal. **No se ha demostrado ausencia de escrituras al HistoryService, engagement, cache o métricas de perfil**: fábrica y coordinador examinados no constituyen garantía. Es un gate obligatorio antes de aprobar hover con carga. Nunca reutilizar/mover el WebContents de la página principal para hacer la preview.
7. **iframe, CSP, X-Frame-Options y autenticación.** La URL objetivo usa la ruta nativa de WebContents; hay tratamiento de frames al limpiar el target. Validar OOPIF y link transit entre frames en el SPIKE. Una preview top-level auxiliar no es un iframe: no necesita eludir restricciones de embedding XFO/frame-ancestors. Mantener CSP de destino, sandbox, TLS, Safe Browsing y aislamiento estándar. Usar el mismo Profile permite cookies/sesiones de ese contexto; usar uno aislado cambia el contenido mostrado y necesita política propia. No prometer equivalencia autenticada y aislamiento de credenciales simultáneamente.
8. **Redirecciones, descargas y parámetros.** Reevaluar cada navegación/redirección; no basta filtrar extensión ni asumir GET inocuo. EphemeralTabMediator.canDownload devuelve false, enablePermissionRequests=false en la vista y su observador cierra ante navegación de descarga. Son bases útiles; deben verificarse descargas, popups, intents externos, audio, fullscreen, diálogos y navegación script. Redactar query/fragment y userinfo en logs. No registrar URL completa con tokens. Un redirect ya puede haber contactado al primer servidor aunque se bloquee después.
9. **Reutilización sin red.** Sí para datos locales ya existentes, particionados por perfil y con validez comprobada: favicon local, título conocido, bookmark y miniatura cacheada. No garantiza descripción ni snapshot de cualquier URL. No capturar o reparentar en vivo un tab existente solo por hover; una miniatura cacheada evita perturbarlo.
10. **Cancelar/destruir.** Cancelar tarea diferida en UI thread e invalidar generación; quitar observers, detener navegación, desasociar delegate/vista y destruir WebContents, ThinWebView, compositor y WindowAndroid que sean propios. La destrucción de ThinWebView no sustituye la de WebContents. EphemeralTab muestra ambas responsabilidades y limpieza diferida de WebContents. Aplicar también al cambiar tab/pane, scroll/fling, teclado, mouse down/drag, pérdida de foco de ventana, background, resize incompatible, cierre de Activity/perfil y memoria baja. Un callback que llega tras cancelar debe ser ignorado, no reabrir la preview.

## E. Arquitectura recomendada para una implementación futura

Un coordinador por ventana, con observadores por WebContents visible y como máximo una sesión auxiliar. Separar tres responsabilidades: elegibilidad/temporizador y gestos; proveedor de contenido; host flotante/lifecycle. El modelo de pestañas y el motor conservan su autoridad. No mezclar esta máquina con la selección visual de la sidebar ni con el controlador de parejas.

`IDLE → HOVER_PENDING → PREVIEW_VISIBLE → DISMISSED → IDLE`.

HOVER_PENDING solo tras URL elegible + puntero mouse/trackpad real, sin botones, scroll, drag, edición activa ni exploración táctil. Esperar **3000 ms**; no crear WebContents ni hacer red antes. Cancelar al salir o cambiar de objetivo; filtrar eventos mouse sintetizados por touch. Enlaces idénticos consecutivos y callbacks retrasados necesitan pruebas porque la URL puede no notificarse otra vez. Un pequeño movimiento dentro del enlace no debe reiniciar indefinidamente el timer; el umbral de movimiento sería una decisión de UX a aprobar.

La primera versión real recomendada sería **pasiva**, con origen visible, sin foco ni edición y descartada al abandonar el enlace/iniciar otra interacción. Entrar con el cursor en su área se considera salida y la cierra; debe aparecer desplazada para no capturar el hover del enlace. Si se quiere interactuar o mantenerla al cruzar hacia ella, hacen falta otra política de permanencia y una acción explícita para dar foco; eso no queda aprobado por el requisito actual. Evitar overlay consumidor que haga alternar enter/exit y cree parpadeo.

Exponer activación/desactivación; cualquier ajuste futuro del retardo conservará 3000 ms como valor acordado. Para contenido con red, exigir consentimiento explícito y explicar si se usa la sesión existente o una partición aislada. Deshabilitar red de preview en incógnito inicialmente hasta demostrar su política. No sustituir silenciosamente una preview real por tarjeta: estado de indisponibilidad claro o fallback elegido por el usuario.

**Punto crítico del compositor:** ThinWebViewFactory advierte que el overload que recibe el WindowAndroid compartido puede desconectar el compositor original. Usar como base el overload con IntentRequestTracker y WindowAndroid propio que utiliza EphemeralTabSheetContent. CompositorViewImpl puede usar SurfaceView o TextureView; supportsOpacity fuerza TextureView. No cambiar ese parámetro como workaround gráfico sin comparar orden, clipping, recursos y rendimiento. Para un popup pequeño sobre el contenido, el z-order con ambos paneles es un gate, no una propiedad garantizada por tener una View Android.

## F. Riesgos, privacidad y costo por alternativa

| Recurso/propiedad | Tarjeta local | Snapshot cacheado | Vista real |
|---|---|---|---|
| CPU | Lookup y bind acotados | Lectura/decodificación off-UI y escalado | Navegación, parse/layout, JS y raster; variable según destino |
| RAM | Metadatos e icono | Bitmap limitado por tamaño | WebContents, posiblemente renderer adicional y recursos de página; no se garantiza un proceso nuevo ni coste fijo |
| GPU | Dibujo UI ordinario | Textura de bitmap | Superficie/compositor, buffers y texturas adicionales |
| Red | Cero si proveedores locales verificados | Cero con cache hit; miss no carga | Contacto externo, cookies, redirects, terceros, posible streaming |
| Batería/fluidez | Bajo esperado, no medido | Bajo-medio esperado, no medido | Potencialmente alto; JS/animaciones pueden continuar mientras esté abierta |
| Lifecycle | Cancelar callbacks | Además liberar/reutilizar bitmap acotado | Stop, detach, destruir superficie/WebContents/observers con orden correcto |

**Bloqueos para aprobar preview real:** falta medir compositor/foco en Galaxy y split; establecer y comprobar política de historial/storage/credenciales; probar aislamiento y cancelación con procesos vivos; validar redirecciones y contenido activo sin efectos secundarios inadmisibles. No son pruebas de inviabilidad estructural, pero impiden un GO de implementación general.

Una allowlist inicial http/https excluye javascript:, data:, blob:, file:, content:, chrome: y esquemas externos; no garantiza inocuidad. Denegar userinfo, no abrir permisos, no ejecutar acciones del usuario ni automatizar cuentas. Los links relativos deben llegar resueltos por Chromium. Enlaces con query pueden ser legítimos: no inventar reglas que permitan asegurar que todos son seguros. Cookies e IP pueden transmitirse aunque se oculte la preview inmediatamente. Cancelar no revierte lo ya enviado.

No usar prerender indiscriminado, desactivar GPU, relajar políticas del navegador ni añadir bibliotecas gráficas para esta función. En páginas autenticadas, una vista aislada puede mostrar login: es una consecuencia de privacidad que debe comunicarse, no corregirse copiando credenciales. La fábrica de StoragePartition experimental encontrada requiere auditoría adicional antes de considerarla contrato reutilizable.

## G. Compatibilidad prevista y límites

Diseño apoyado en Android View, MotionEvent, WindowAndroid y WebContents, sin dependencias Samsung. La compatibilidad real **no se ejecutó** en esta auditoría.

- DeX/freeform y pantalla dividida: anclar a la ventana/pane, no a dimensiones globales; cerrar/reubicar al cambiar bounds, tab o pareja. El panel secundario puede recibir hover aunque no sea el tab activo: no cambiar selección por eso.
- Mouse y trackpad: EventForwarder distingue fuentes y herramientas, incluidas rutas relativas. Verificar SOURCE_MOUSE, TOUCHPAD y traducciones del fabricante; no depender solo de SOURCE_MOUSE ni activar con dedo/TalkBack.
- Pantalla externa: contexto/densidad del display de la Activity, insets actuales y conversión por vista; recalcular al mover entre displays. No guardar offsets absolutos entre sesiones.
- Android Desktop de otros fabricantes: probar resize, foco y superficie con APIs comunes. No asumir que un PASS DeX cubre todos los gestores de ventanas.
- Touch/accessibilidad: función opcional de puntero; las acciones explícitas existentes y descripciones accesibles siguen disponibles. Un tooltip no sustituye contentDescription.

No hay evidencia nueva de rendimiento en Adreno 830 ni de visibilidad real en este trabajo. Amazon sigue fuera de alcance como fallo gráfico no resuelto. QEMU permanece deshabilitado por el usuario; resultados históricos QEMU_ABI_BLOCKED no se transforman en PASS.

## H. Plan futuro por fases independientes, sujeto a autorización

1. **Refinamiento visual localizado.** Integrar con el alcance de sidebar ya registrado y con el diseño de múltiples parejas, sin implementarlo aquí. Matriz normal/hover/activo/foco/pinned/disabled, incluida activa+foco y ventana sin foco. Regresiones de pin/unpin, cierre/mover tab, reciclado, títulos/favicon y aislamiento de Spaces. No cambios de motor, geometría o branding.
2. **SPIKE de eventos y host vacío.** Tras aprobación, probar timer virtual 3000 ms, URL/puntero correlacionados, iframe/OOPIF, mismos href, scroll/drag/formularios, cancelación tardía, coordenadas y overlay vacío no consumidor. No red ni WebContents auxiliar todavía. Avanzar solo sin alteración de foco/entrada/TabModel.
3. **SPIKE de preview real controlada.** Fixture local autorizada, un WebContents auxiliar y compositor propio, sin cuentas personales. Probar ambos paneles, dialogs, surface loss/background/resize, redirecciones/descargas/intents y destrucción. Instrumentar Network/NetLog depurado, WebContentsObserver, trazas Perfetto/FrameTimeline, memoria de procesos y superficies. No tocar el pipeline gráfico principal. Si falla aislamiento, detener y documentar.
4. **Evaluación de privacidad y recursos.** Autorizar explícitamente cualquier destino externo y modo de storage; comprobar historial global, cookies, permisos y rechazo de ventanas/descargas. Comparar con baseline real de mismas páginas, ventana, orientación, Hz y escenario split sin preview. No extrapolar coste de una fixture vacía a Amazon u otras páginas complejas.
5. **Decisión de producto.** GO solo con gates siguientes y pruebas reales compatibles; si no, mantener SPIKE o limitar cobertura de forma explícita. Únicamente después preparar integración aprobada y compilación progresiva desde checkpoint verificado. No se solicita ni despacha una compilación por este informe.

### Instrumentos y umbrales propuestos, aún no medidos ni aprobados

| Gate futuro | Criterio propuesto frente al baseline |
|---|---|
| Activación/cancelación | Cero peticiones, cero WebContents auxiliares antes de 3000 ms; un único timer/session; ningún callback reabre tras cancelación. Solicitud de descarte al siguiente turno de UI, sin esperar la red. |
| Seguridad/estado | Cero cambios en TabModel, back stack principal o foco; cero descargas, permisos, intents externos o audio iniciados por preview. Historial/storage conforme a política explícita comprobada. |
| Fluidez | Provisional: p95 de duración de frame no empeora >10% y jank no aumenta >1 punto porcentual frente a baseline, medidos con FrameTimeline en scroll y split. Identificar Hz y presupuesto de frame real. |
| Memoria/lifecycle | Como máximo un WebContents/superficie auxiliar; cero vistas/observers huérfanos en 50 ciclos. Tras cerrar, liberar recursos propios y no observar crecimiento monotónico. Provisional: memoria estable tras ciclos dentro de 10% de baseline estabilizado; separar cache/proceso retenido legítimo de fugas. |
| Red/carga | Registrar bytes/peticiones/terceros por preview en fixtures autorizadas; no cargar otro destino antes de destruir la sesión anterior. Provisional: timeout de carga 5 s y vida máxima 15 s para el experimento, a aprobar; un timeout no garantiza un límite de bytes. |
| Corrección visual | Sin WebContents principal perdido, negros, recortes o preview detrás de superficies; capturas y trazas sincronizadas, sin interpretar frames perdidos como corrupción. |

Si esos números no son aceptables o realistas tras medir la línea base, se decide el presupuesto explícitamente antes de continuar; no se publican como resultados PASS. No se inventa un consumo en MB/CPU para el Galaxy sin mediciones.

## I. Decisión y siguiente acción

**Recomendación única:** aprobar primero un SPIKE aislado de la preview real reutilizando la arquitectura EphemeralTab/ThinWebView, con hover nativo de 3000 ms y compositor propio, manteniendo el refinamiento de sidebar como tarea independiente de bajo riesgo. Esto valida la propuesta solicitada sin comprometer la navegación principal ni asumir que una tarjeta la satisface.

No se implementó el SPIKE. No hay código de producción nuevo, APK, resultados RED/GREEN funcionales ni evidencia de dispositivo por esta auditoría. El siguiente paso requiere elegir y autorizar las propuestas; los pendientes de parejas y omnibox siguen con su estado previo.

[version]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/VERSION
[blink]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/third_party/blink/renderer/core/exported/web_view_impl.cc#L3391
[wcimpl]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/browser/web_contents/web_contents_impl.cc#L11014
[delegate]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/embedder_support/android/delegate/web_contents_delegate_android.cc#L323
[tabobserver]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/tab/java/src/org/chromium/chrome/browser/tab/TabObserver.java#L215
[contentview]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/embedder_support/android/java/src/org/chromium/components/embedder_support/view/ContentView.java#L267
[events]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/ui/android/java/src/org/chromium/ui/base/EventForwarder.java
[coordinates]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/public/android/java/src/org/chromium/content_public/browser/RenderCoordinates.java
[ephemeral]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/ephemeraltab/java/src/org/chromium/chrome/browser/ephemeraltab/EphemeralTabCoordinator.java#L275
[mediator]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/ephemeraltab/java/src/org/chromium/chrome/browser/ephemeraltab/EphemeralTabMediator.java
[sheet]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/ephemeraltab/java/src/org/chromium/chrome/browser/ephemeraltab/EphemeralTabSheetContent.java#L164
[factory]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/android/content/java/src/org/chromium/chrome/browser/content/WebContentsFactory.java
[thin]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/thin_webview/java/src/org/chromium/components/thinwebview/ThinWebViewFactory.java
[thinimpl]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/thin_webview/internal/java/src/org/chromium/components/thinwebview/internal/ThinWebViewImpl.java
[compositor]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/thin_webview/internal/java/src/org/chromium/components/thinwebview/internal/CompositorViewImpl.java
[thumbnails]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/tab_ui/android/java/src/org/chromium/chrome/browser/tab_ui/TabContentManager.java#L355
[favprovider]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/tab_ui/android/java/src/org/chromium/chrome/browser/tab_ui/TabListFaviconProvider.java
[largeicon]: https://github.com/chromium/chromium/blob/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/favicon/android/java/src/org/chromium/components/favicon/LargeIconBridge.java
