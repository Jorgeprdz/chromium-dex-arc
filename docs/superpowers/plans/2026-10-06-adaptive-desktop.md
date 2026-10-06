# Adaptive Desktop Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Estado de ejecución:** El usuario aplazó las partes no implementadas al próximo update el 2026-10-06. Se conserva el clasificador de ventana ya implementado para la interfaz Arc.

**Goal:** Activar comportamiento real desktop por tamaño de ventana, conservando móvil compacto y preferencias por sitio.

**Architecture:** Un módulo pequeño de clasificación/metrics con constantes AndroidX ya fijadas alimenta RDS y Arc. DesktopSiteUtils conserva el almacenamiento de content settings; el observer native y TabImpl usan la misma resolución por URL/ventana. Zoom conserva HostZoomMap y ChromeZoomLevelPrefs.

**Tech Stack:** Chromium157 fijado, Java/Android Configuration/WindowMetrics, AndroidX Window Core fijado, JNI existente, C++ WebPreferences y RDS.

**Spec:** `docs/superpowers/specs/2026-10-06-desktop-input-annex.md`; investigación `docs/investigacion-desktop-input-2026-10-06.md`.

## Global Constraints

- Revisión `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; mantener planes anteriores activos.
- Compacta <600 dp; Tablet 600–839; Desktop >=840. Reutilizar WindowSizeClass fijado: no nuevas constantes numéricas duplicadas de producción.
- Sin fabricante/DeX, root/Shizuku/ADB como dependencias del app; sin JS, UA string fija o CSS zoom.
- Preferencia por sitio gana. No escribir excepciones por cada resize. Incógnito no filtra historial/estado al perfil normal.
- No cambiar el diseño Mac aprobado. Compartir clasificación para UI y navegación; UI móvil y sesiones nativas se conservan.
- Run final después de gates pre-build; actualizar monitor y pausar justo después de dispatch. Build pendiente no es success.

## Review Focus

- Context application/Activity en display externo: jamás usar display primario para inferir ventana.
- Navegación renderer/browser y restauración no deben decidir UAs diferentes.
- Sitio explícitamente mobile en ventana grande sigue mobile; explícitamente desktop en compacta sigue desktop.
- Resize durante submit/carga no debe destruir modelos o formularios por recargas/recreaciones redundantes.
- Incógnito y múltiples ventanas usan contexto/profile correcto; zoom nativo conserva su semántica upstream.

### Task 1: Clasificación compartida y métricas actuales

**Files:** Create `chrome/browser/desktop_policy/android/BUILD.gn`, Java `ArchiumWindowClass.java`, `ArchiumWindowMetrics.java` en ese módulo. Modify `chrome/browser/ui/vertical_tabs/BUILD.gn`, `ArcDesktopPolicy.java`, `ArcDesktopAppearance.java`; tests de política y Android metrics.

**Interfaces:** Window class COMPACT/TABLET/DESKTOP; classify(widthDp) usa constantes WindowSizeClass reales. currentWidthDp(Context) utiliza contexto actual de Activity y Configuration/WindowMetrics; sin tamaño de panel. Arc AUTO consume la clasificación; ARC/MOBILE manual del plan visual conserva su contrato independiente de UA.

- [ ] RED: 580/599 compact;600/620/839 tablet;840/900 desktop;520->700 cambia clase. Marca/modelo/orientación no son argumentos de elegibilidad.
- [ ] Verificar API contra JAR real extraído del CIPD fijado; clases Android SDK no prueban GN completo.
- [ ] Implementar módulo y enlazar Arc sin referencias semDesktopMode/FEATURE_PC para elegibilidad.
- [ ] Android: Configuration contextual 580/620/900, rotación con ancho constante, metrics/insets coherentes en Activity real.
- [ ] GREEN política/metrics; verificar GN target público AndroidX y visibilidad en checkout completo; commit.

### Task 2: Request Desktop Site y preferencias de render dinámicas

**Files:** Modify `DesktopSiteUtils.java` y tests fijados; `TabImpl.java`, `tab_android.{h,cc}`, `request_desktop_site_web_contents_observer_android.cc`, `chrome_content_browser_client.cc` según interfaces encontradas; `ArcDesktopWindowObserver.java` y coordinator visual.

**Interfaces:** Resolver UA por URL desde REQUEST_DESKTOP_SITE primero (excepción o global explícita), luego política adaptativa/default. TabImpl calcula UA en cargas/restauración/preloading; native observer debe consumir la misma decisión mediante interfaz existente de TabAndroid. Exponer elegibilidad actual del Tab/context al browser client para WebPreferences. Lifecycle/layout recalculan sin escribir content settings. Preferencias futuras adaptive enabled/always desktop accesibles por módulo, sin pantalla adicional obligatoria.

- [ ] RED: site BLOCK en620 no cambia; site ALLOW en520 desktop; global automático compacto mobile; browser/renderer/navigation/restored/background tab misma decisión.
- [ ] Usar infraestructura UA de Chromium, no string nueva. Quitar OEM/display físico del camino Archium.
- [ ] Aplicar render/text-size preferences desktop solo con clase elegible y RDS real; preservar accesibilidad/defaults móviles y actualizar preferencias dinámicamente.
- [ ] Recalcular al resize/reparent/display y al activar/restaurar tab. Evitar Activity recreation; si UI upstream lo exige, verificar estado en save/restore.
- [ ] GREEN tests Java/native y sesiones sintéticas de resize; generar/verificar patch; commit.

### Task 3: Zoom persistente mediante capacidades ya existentes

**Files:** Reuse HostZoomMap.java, ZoomController.java, PageZoomManager/Preference, ChromeZoomLevelPrefs. Modify solo puntos de exposición/integración que las pruebas demuestren necesarios; tests con perfil real y página sintética.

**Interfaces:** Zoom de host > default global > nivel0=100%; presets nativos existentes incluyen80/90/100/110/125/150. La opción global usa almacenamiento native. Ctrl+wheel sigue ContentsZoomChange.

- [ ] Tests previos de persistencia host tras reload y cierre/reapertura, default y perfiles. Determinar RED real antes de editar capacidades existentes.
- [ ] Conservar controles nativos o exponerlos de forma mínima en Arc sin rediseño ni otro almacenamiento.
- [ ] No reemplazar escala accesible del usuario por100%;100 solo nuevo default/fallback.
- [ ] Verificar en APK real; registrar capacidades reutilizadas vs cambios necesarios; commit si hubo modificaciones.

### Task 4: Matriz y changelog

**Files:** `docs/validation/archium-desktop-input-results.md` y changelog final con las siete categorías solicitadas.

- [ ] Verificar matriz window/display/split/freeform, tablet/desktop diferenciados, transiciones y conservación de tabs.
- [ ] Ejecutar gates nativos/Java disponibles antes del APK final; anotar pruebas físicas que dependan de la APK nueva como pendientes hasta terminación.
- [ ] Copiar documentos/resultados a Download. No declarar entrega terminada mientras build o runtime estén pendientes.
