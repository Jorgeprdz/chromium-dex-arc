# R5 — Mobile aprobado: navegación y menú

> Actualización: run39781720300 compiló e instaló92c24df con verificación. El candidato posterior Floating UI y su auditoría Light/Dark están en [R5_FLOATING_MOBILE_LIGHT_DARK.md](R5_FLOATING_MOBILE_LIGHT_DARK.md); todavía no tiene APK. El resto registra tandas anteriores.

Fecha: 2026-10-22. Rama: `assistant/archium-r5-desktop-native-mobile`.
Base de esta tanda: `2f7152bb52ce3439422a28d6359066d062a9d414` (candidato Split View conservado, sin compilar).

## Alcance aprobado e implementado en código

Los dos renders aprobados están en Download del teléfono: `Archium_Mobile_Render_01_Navegacion.png` y `Archium_Mobile_Render_02_Menu.png`. La aprobación posterior sustituye la decisión anterior de retirar toda presentación móvil propia, exclusivamente para navegación inferior y menú. Se conservan eliminados ArcMobileControls, ArcMobileHomeView y sus overlays antiguos.

- Omnibar y barra de título superiores: sin cambios. Ningún editor ni omnibar en el menú inferior.
- ArcPhoneNavigation reemplaza el delegate del slot inferior nativo: Inicio, Nueva, Pestañas con contador y Menú. No añade una segunda barra. La geometría e insets pertenecen a BottomControlsCoordinator.
- BottomBarHostManager permite al Hub reutilizar la misma vista; al devolverla restaura la reserva nativa. El gestor de pestañas y sus previews siguen siendo Chromium.
- Menú mediante BottomSheetController/BottomSheetContent, con cabecera estática favicon/dominio, información del sitio, Fijar/Desfijar, Buscar y Compartir. Marcador, zoom real mediante HostZoomMap, sitio de escritorio, descargas y Más opciones delegan en APIs/acciones nativas. Configuración del sitio abre Page Info nativo, desde donde se accede a permisos/configuración; no es una pantalla nueva.
- Sin IA, servicios ficticios, métricas de bloqueo, reemplazo de NTP ni controles nuevos de Spaces. Más opciones conserva acceso al menú Chromium completo.
- Acabado: superficies suaves, radios superiores de 28dp, iconos ligeros y botón + destacado. Sin contornos de controles; separadores de baja opacidad sólo entre grupos. Paleta clara/oscura procedente del tema de Activity, con tratamiento oscuro incógnito. Haptic de sistema discreto y animación del sheet desactivada cuando el sistema desactiva animadores.
- Cierre/gestos/scrim y teclado se delegan al contenedor nativo. Callbacks de menú verifican identidad de pestaña y destrucción. No se crean WebContents, capturas ni bitmaps de previews.

## Archivos y ownership

Nuevo `ArcPhoneNavigation.java` y su test; hooks acotados en ToolbarManager, ChromeTabbedActivity y TabbedRootUiCoordinator. Registros Java/JUnit, strings y filtros del gate actualizados. Sin modificaciones de LocationBarLayout, Desktop, NTP, seguridad, branding ni contenido web en esta tanda. Las ramas Desktop existentes del toolbar se conservan.

El harness de preparación reutiliza fronteras explícitas de interfaces nativas para compilar aisladamente el delegate. Esto no sustituye compilar Activity/Toolbar completos contra Chromium.

## Evidencia local

Logs: `/workspace/archium-evidence/mobile-approved-implementation/`.

| Comprobación | Resultado / alcance |
| --- | --- |
| Vistas ArcPhoneNavigation, SDK30/36 | PASS: 30 ejecuciones Robolectric; controlador, acciones y fronteras nativas simulados |
| Ownership inferior / ausencia de editor inferior | PASS: 4 contratos fuente; RED previo conservado en red.log |
| Gates host | PASS: 2 pruebas, incluido rechazo de wrapper Ninja |
| Legacy rollback | PASS: 5 invariantes de overlays retirados |
| Split layout viewport | PASS: 5 contratos/validador; no ejecución Blink/C++ |
| Preparación SDK37.2 | PASS: compilación aislada, adapter sintético y aplicación del parche |
| Parche y manifest | PASS: 162 archivos, dos regeneraciones con SHA256 idéntico; preparación verifica aplicación |
| Suite host completa / build nativo | NOT RUN en esta tanda |
| Aceptación física, rendimiento y memoria | NOT RUN |

Pendiente en APK: aspecto premium frente a renders, teléfonos/orientación/tablet, teclado/insets/gestos, fullscreen, Hub y devolución de barra, controles de acceso y navegación privada, zoom/pin/compartir reales, Desktop↔Phone y estado de sesión. No se atribuye aceptación gráfica a Robolectric.

## Compilación y continuación

No se ha disparado GitHub Actions, compilado una APK ni instalado este candidato. Sigue vigente «no compiles todavía». El fallo físico Split View de la APK anterior y el candidato C++ están descritos en [R5_SPLIT_LAYOUT_VIEWPORT_FOLLOWUP.md](R5_SPLIT_LAYOUT_VIEWPORT_FOLLOWUP.md).

Antes del único build autorizado posteriormente: enviar SHA exacto, preflight completo, verificar bytes y compatibilidad del checkpoint incremental, sin clean ni reintentos. No publicar/instalar sin verificar artefacto, checksum, firma, package y conservar respaldo.

## Consulta de cuota Actions

Repositorio público; workflow baseline/preflight/stage usa `ubuntu-24.04` estándar. Los runners estándar en repositorios públicos no consumen minutos facturables según [GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions). El saldo de almacenamiento/artefactos/cache no pudo consultarse: las APIs de billing devolvieron 404 y requisito de scope `user`; no se amplió el token. No se afirma un saldo numérico disponible ni se eliminaron checkpoints.


## Run39721663072 — fallo Java y corrección localizada

El único intento autorizado ejecutó SHA82b37ed: authorize y preflight SUCCESS; restauración verificada por CI; suite host de S2: **398 PASS**. Falló el target `chrome_java__compile_java`, antes de APK, por la declaración `private @Nullable ArcPhoneNavigation.Host mArcPhoneHost;` en ToolbarManager: `Nullable` es TYPE_USE y el tipo anidado requiere `ArcPhoneNavigation.@Nullable Host`.

La preparación aislada anterior compilaba el nuevo delegate pero no ToolbarManager; por eso no detectó esta integración. Se añade una prueba host que extrae la declaración entregada y la compila con javac y una anotación exclusivamente TYPE_USE. RED reproduce el error, GREEN acepta la corrección de una línea. Los otros cuatro contratos de ownership siguen PASS. Preparación aislada SDK37.2 PASS y parche/manifest reproducibles en dos generaciones; diff sin errores de whitespace. No se cambia comportamiento, UI, dependencias ni gates para ocultar el fallo.

Logs y receipt: `/workspace/archium-evidence/mobile-approved-implementation/run-39721663072/`. El checkpoint `archium-checkpoint-39721663072-1` fue publicado; receipt declara `checkpoint_verified=true`, `pack_verified=true`, `outcome=BUILD_FAILED`, `recoverable=false`. No es una continuación automática autorizada. La disponibilidad, capacidad, compatibilidad y hashes de bytes se deben volver a validar antes de una futura restauración; no se hizo esa restauración localmente.

No se generó APK ni se instaló actualización. La versión anterior permanece instalada. No se relanzó Actions: otro intento requiere autorización nueva. Candidato corregido pendiente de compilación nativa completa; no se afirma que hayan desaparecido posibles errores posteriores que javac no alcanzó a reportar.


## Run39729088298 — corrección de buffer nativo

El intento autorizado con SHA7c4ece8 pasó authorize, preflight y restauración. La suite host de S2 registró399 PASS y `chrome_java__compile_java` terminó correctamente: el defecto Nullable anterior quedó superado en compilación nativa integrada. El primer error causal posterior fue Clang en `static_tab_scene_layer.cc`: dos accesos `ids[i]` sobre `const int32_t ids[]`, rechazados por `-Wunsafe-buffer-usage` tratado como error. El build se detuvo sin APK.

Corrección localizada: `std::array<int32_t, 2>` y su include explícito. No se cambia el algoritmo, no se suprimen warnings y no se modifican flags, GN, toolchain o GPU. El compilador integrado es LLVM24; para verificar la corrección se usó el Clang21.1.8 ya instalado en Termux, sin instalar dependencias.

Evidencia `/workspace/archium-evidence/mobile-approved-implementation/run-39729088298/`: `buffer-red.cc` extrae el método exacto anterior y reproduce ambos errores con `-std=c++23 -Wunsafe-buffer-usage -Werror`; `buffer-green.cc` extrae el método corregido, compila con esos mismos flags y ejecuta aserciones de attach/swap/detach, IDs negativos, pestaña ausente, WebContents ausente y reasignación. Las fronteras WebContents/TabManager/WeakPtr de ese ensayo están simuladas: no es aceptación Blink, ni validación de destrucción real de objetos Chromium. Logs `buffer-red.log`, `buffer-green.log`. Contratos existentes Split5 PASS y Mobile ownership5 PASS. Aplicación del parche7 PASS, transición17 PASS y reproducibilidad de patch/manifest PASS.

Checkpoint publicado `archium-checkpoint-39729088298-1`, commit7c4ece8. Receipt BUILD_FAILED/recoverable=false; checkpoint_verified y pack_verified true. No se descargaron/restauraron todos los bytes localmente. Un intento manual posterior debe verificar nuevamente metadatos, capacidad, compatibilidad y hashes antes de restaurar. No hay relanzamiento automático, APK nueva ni instalación. El candidato completo sigue pendiente de build integrado y aceptación física.
