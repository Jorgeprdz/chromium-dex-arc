# Investigación del anexo desktop, teclado y mouse — Chromium 157

Revisión exacta: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, 157.0.8086.0. Inspección del código fijado, no inferencia desde HEAD. Esta investigación confirma rutas existentes en el código; la validación funcional de la nueva APK sigue pendiente.

| Área | Capacidad existente | Integración requerida por Archium |
|---|---|---|
| Tamaño de ventana | Android Configuration/WindowMetrics; WindowAndroid ofrece bounds en dp; Chromium tiene umbral tablet de 600 dp | Una clasificación actual por ventana compartida para sitios y Arc; ninguna comprobación de Samsung/DeX |
| RDS/UA | DesktopSiteUtils, ContentSettings REQUEST_DESKTOP_SITE, NavigationController, TabImpl y observer nativo | Predeterminado automático >=600 dp; compacta vuelve a mobile; conservar preferencias explícitas por sitio; misma decisión para navegaciones Java y renderer |
| Adaptación upstream | RDS window setting existe, pero consulta atributos/display metrics; defaults y displays externos usan hardware/OEM | Sustituir esas rutas dentro del comportamiento Archium por tamaño actual de ventana, sin crear excepciones persistentes por cada resize |
| Page zoom | ZoomController y HostZoomMap, niveles por host y global; ProfileImpl crea ChromeZoomLevelPrefs | Reutilizar almacenamiento y controles; verificar 80/90/100/110/125/150%, reload/reapertura y aislamiento de incógnito |
| Teclado | KeyboardShortcuts tiene comandos y flujo real para los atajos solicitados y hard reload | Mantener dispatcher/acciones/extensiones; Ctrl+Shift+B cambia sidebar cuando está disponible y mantiene comportamiento upstream en compacto |
| F11 | NOT_IMPLEMENTED_TOGGLE_IMMERSIVE | No crear fullscreen visual falso; documentar limitación |
| Mouse en páginas | EventForwarder lleva botones/modificadores a Blink; dispositions distinguen background tab y new window | Verificar en runtime, mantener ruta native; ninguna modificación JS |
| Mouse Back/Forward | WebContents procesa mouse-up después del renderer | Reutilizar esta semántica para respetar páginas que consumen eventos |
| Ctrl+wheel | WebContents HandleWheelEvent -> ContentsZoomChange -> Java delegate -> ZoomController | Existe la ruta completa; verificar que la APK recibe eventos y persiste zoom; evitar interceptor global |
| Nueva ventana | NEW_WINDOW llega a TabModelJniBridge; MultiWindowUtils contiene soporte de instancias | Probar en los window managers disponibles; no confundir recepción del disposition con garantía de ventana independiente |
| Middle click en rail | Modelos/cierre nativos y RecyclerView existen; no se ha encontrado un handler del botón medio en la rail inspeccionada | Vincular gesto de mouse a acción de cierre existente, sin fabricar click táctil ni perder drag/drop |
| Text sizing | El código actual usa WebPreferences y text_size_adjust_enabled; RDS modifica viewport y existe AndroidDesktopWebPrefsLargeDisplays | Control por ventana + RDS real; no aplicar defaults físicos de desktop a una ventana compacta, ni desactivar accesibilidad móvil |

## Evidencias fijadas

- [DesktopSiteUtils.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/desktop_site/java/src/org/chromium/chrome/browser/desktop_site/DesktopSiteUtils.java)
- [request_desktop_site_web_contents_observer_android.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/content_settings/request_desktop_site_web_contents_observer_android.cc)
- [TabImpl.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/tab/TabImpl.java)
- [KeyboardShortcuts.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/KeyboardShortcuts.java)
- [ZoomController.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/ZoomController.java)
- [HostZoomMap.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/public/android/java/src/org/chromium/content_public/browser/HostZoomMap.java)
- [chrome_zoom_level_prefs.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/zoom/chrome_zoom_level_prefs.cc)
- [profile_impl.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/profiles/profile_impl.cc)
- [EventForwarder.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/ui/android/java/src/org/chromium/ui/base/EventForwarder.java)
- [web_contents_impl.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/browser/web_contents/web_contents_impl.cc)
- [TabWebContentsDelegateAndroidImpl.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/tab/TabWebContentsDelegateAndroidImpl.java)
- [window_android.h](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/ui/android/window_android.h)
- [DeviceFormFactor.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/ui/android/java/src/org/chromium/ui/base/DeviceFormFactor.java)
- [AppHeaderCoordinator.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/desktop_windowing/java/src/org/chromium/chrome/browser/ui/desktop_windowing/AppHeaderCoordinator.java)
- [MultiWindowUtils.java](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/multiwindow/MultiWindowUtils.java)
- [window_open_disposition_utils.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/ui/base/window_open_disposition_utils.cc)
- [tab_model_jni_bridge.cc](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/android/tab_model/tab_model_jni_bridge.cc)

## Estado y límites de la evidencia

- Se han inspeccionado el dispatcher de teclado y sus comandos, la configuración RDS en Java/C++, la cadena de zoom, los eventos mouse, el cierre de tabs y la infraestructura multiwindow/app header.
- 600 dp ya existe: `DeviceFormFactor.MINIMUM_TABLET_WIDTH_DP` en Java y `content::kAndroidMinimumTabletWidthDp` en C++. No crear otro 600 en producción.
- 840 dp distingue Tablet/Desktop como pide el anexo. Se verificó el AAR real de Window Core fijado por DEPS, instancia CIPD `sT3etXgwHmMgIIfG-lkBJlswQu9zgE_XvfXj_HaO-VsC`, leyendo únicamente el entry del archive. `javap` confirma `WindowSizeClass.WIDTH_DP_MEDIUM_LOWER_BOUND` y `WIDTH_DP_EXPANDED_LOWER_BOUND`. Reutilizar esas constantes/clases, sin otro 600/840 de producción. Su exportación GN debe verificarse en checkout completo; el target público Window depende de Window Core.
- Las pruebas upstream de KeyboardShortcuts y DesktopSiteUtils existen; todavía no se ejecutaron en la APK nueva.
- `emulator-5554` es un alias hacia el mismo teléfono físico que Wi-Fi ADB, según serial; no contarlo como validación en otro dispositivo.
- No hay resultado de APK del nuevo trabajo; ningún item de esta tabla es una declaración de entrega terminada.

API oficial de la clasificación: [AndroidX WindowSizeClass](https://developer.android.com/reference/androidx/window/core/layout/WindowSizeClass). La API usada se comprobó también en el artefacto fijado, no solamente en la documentación actual.
