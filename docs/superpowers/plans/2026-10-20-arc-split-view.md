# Arc Split View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Dos pestañas reales lado a lado, con foco independiente, separador ajustable e intercambio mediante cápsula blanca.

**Architecture:** Conservar TabModel como propietario y un solo compositor; ampliar la presentación nativa para dos contenidos vivos. Un controlador de pareja separa estado, lifecycle y controles visuales. No se entrega el menú hasta que exista integración completa de presentación e input.

**Tech Stack:** Chromium 157 Android, Java, C++, cc::slim, JNI, JUnit/Robolectric.

**Spec:** `docs/superpowers/specs/2026-10-20-arc-split-view-design.md` (diseño aprobado).

## Global Constraints

- No WebView, iframes, bitmaps de pestañas ni ventanas Android separadas.
- Máximo dos paneles por ventana; no mezclar normales/incógnito ni perfiles.
- Preservar fix de diálogos `5184755` y orden/identidad de pestañas existente.
- Cápsula blanca redondeada, flechas oscuras → / ← apiladas; intercambio sin recarga; transición de 180 ms respetando animaciones desactivadas.
- No modificar Chromium pin, GN args ni toolchain; ningún build limpio ni purge.
- No despachar un build como parte de preparar este plan.
- QEMU_ABI_BLOCKED no equivale a ejecución Android PASS.

## Review Focus

- Cerrar o trasladar una pestaña mientras hay diálogo: nunca operar sobre otro WebContents (tareas 2/4).
- IME, selección y permisos del panel inactivo: adquirir foco antes de asociar acciones (tarea 4).
- Ventana estrecha, RTL y densidad: conservar identidad y coordenadas físicas correctas (tareas 3/5).
- Restauración nativa de IDs incompleta: no resucitar pestañas ni perfiles (tarea 2).
- Presión de memoria/superficie perdida: recuperar ambas o salir de división conservando pestañas (tareas 3/6).

## Task 1: Verificar contrato de dos contenidos vivos

**Files:** código original fijado de `CompositorViewHolder`, `StaticTabSceneLayer`, `StaticLayout`, `TabContentManager`, `ContentLayer`; informe `docs/validation/R5_3_SPLIT_VIEW.md`.
**Interfaces:** establecer ruta de actualización del compositor y ownership de vistas/input antes de cambiarla.

- [x] Trazar `StaticLayout → StaticTabSceneLayer → ContentLayer` y el cambio de Tab activo; documentar métodos exactos de visibilidad, attachment y bounds de ambos WebContents.
- [x] Verificar que promover la segunda pestaña no esconde la primera y que el delegado de input permite distinguir ambos rectángulos. Documentar la modificación mínima requerida en cada contrato.
- [x] Si no puede conservarse ese contrato en un solo compositor, registrar bloqueo; no implementar un menú inoperante ni introducir un segundo compositor sin revisar el diseño.

## Task 2: Estado de pareja y autoridad de pestañas

**Files:** crear `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSplitState.java` y JUnit correspondiente en `chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/`.
**Interfaces:** `boolean start(int leftId, int rightId)`, `boolean activate(int tabId)`, `void swap()`, `void setRatio(float ratio)`, `void remove(int tabId)`, `void exit()`; getters de IDs, activo, proporción y existencia de pareja. Validar perfil/modelo en controlador, no inferirlos de IDs.

- [x] RED: A/B válidos; mismo ID rechazado sin perder pareja previa; swap dos veces conserva activo/proporción; cerrar uno deja el otro; salir no cierra tabs; ratio NaN/infinito rechazado y valores fuera de rango no producen bounds negativos.
- [x] Implementar estado puro, sin crear/cargar/destruir WebContents; añadir casos de reconciliación con IDs restaurados, sin crear pestañas faltantes.
- [x] GREEN con JUnit; registrar comandos/resultados y commit del componente.

## Task 3: Presentación nativa y resize

**Files:** modificar versiones fijadas de `chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java`, `compositor/layouts/StaticLayout.java`, `compositor/scene_layer/StaticTabSceneLayer.java`; `chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.{cc,h}`. Entregar cambios mediante `.source-modified` y patch generado.
**Interfaces:** añadir en el holder `setArcSplitTabs(Tab left, Tab right, float ratio, int activeId)` / `clearArcSplitTabs()` y propagar ambos IDs/bounds a la actualización de escena, con JNI coherente y validación de tarea 1.

- [x] RED: integración mantiene dos IDs visibles, capas vivas distintas, clipping no solapado y viewport propio; activar B no destruye/oculta A. Casos de RTL, resize y superficie perdida.
- [x] Ampliar la escena existente con segunda ContentLayer; conservar ruta de un solo tab al salir. Actualizar visibilidad de ambos IDs, attachments y viewport sin modificar DSF ni flags gráficos.
- [x] GREEN de contratos nativos y Java; comprobar JNI/build graph y garantizar que no se toma una captura de tab como contenido vivo. Los píxeles y el input reales quedan gate Android pendiente hasta APK.

## Task 4: Foco, lifecycle y selección

**Files:** crear `ArcSplitViewCoordinator.java` en el directorio Arc de tarea 2; modificar `ArcDesktopCoordinator.java`, holder y conexiones existentes de selección de Tab.
**Interfaces:** `boolean enter(Tab first, Tab second)`, `void activate(int tabId)`, `void swap()`, `void exit()`, `void destroy()`; controller usa ArcSplitState y API del holder de tarea 3.

- [x] RED: pulsar B dirige omnibox, back/forward/reload y diálogos a B; pulsar A recupera A; cambio de perfil, cierre/movimiento de tab y destroy desacoplan observers. Tabs incompatibles no alteran la pareja anterior.
- [x] Implementar selección por identidad nativa y routing de coordenadas, teclado/IME, permisos y foco. Observar cierre/destrucción y cambios de modelo; liberar presentación sin cerrar pestañas.
- [x] GREEN: selección repetida, diálogo abierto durante cierre, recreación de Activity y ausencia de observers retenidos; no ocultar fallos mediante recreación global.

## Task 5: Menú y cápsula blanca

**Files:** `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java`; crear `ArcSplitDividerView.java` y JUnit en directorios Arc; recursos Arc existentes.
**Interfaces:** menú entrega Tabs nativos a `ArcSplitViewCoordinator.enter`; divisor recibe callbacks `Runnable swap` y `Consumer<Float> ratioChanged`.

- [x] RED: clic derecho y long press abren menú sin romper drag; elegir existente o nueva conserva el primer Tab; cancelar no crea tabs; modelo/perfil equivocado rechazado.
- [x] Conectar menú nativo a selector de pestañas abiertas y creación nativa de nueva, sin compartir incógnito con normal. Añadir salida de división que mantiene ambos Tabs.
- [x] RED: botón swap ejecuta una vez, drag sólo cambia ratio; TalkBack tiene acción de intercambio; teclado Enter/Space acciona botón; en ventana estrecha se preserva pareja.
- [x] Implementar cápsula blanca pequeña con flechas oscuras apiladas y objetivo táctil accesible; separar gesto de arrastre del clic. Sin blur inicial ni efectos que alteren superficies web.
- [x] RED/GREEN: transición de intercambio de 180 ms, sin reload, termina en posiciones finales válidas; animaciones desactivadas aplican estado final inmediato; segundo intercambio, resize y destroy cancelan animaciones sin dejar input o bounds desfasados. Verificar URL/scroll/estado e identidad activa, ratio y RTL.

## Task 6: Gates, TODO y aceptación Android

**Files:** `scripts/generate-arc-patch.py`, manifiesto/patch resultantes, runners/test targets existentes, `TODO.md`, `docs/validation/R5_3_SPLIT_VIEW.md`.
**Interfaces:** entregar patch aplicable al pin vigente y evidencia separada por host/Android/dispositivo.

- [x] Integrar fuentes/tests en los targets existentes; regenerar patch y ejecutar preparación, tests de estado/controlador, omnibox, navegación, diálogos y orden de pestañas afectados. No repetir suites ajenas sin motivo.
- [x] Verificar restauración de pareja sólo tras restauración nativa; documentar límites si no existe soporte comprobado. Marcar TODO por subfunción, no por éxito de build.
- [ ] Antes de cualquier futura compilación, verificar checkpoint compatible, presupuesto vigente y autorización de despacho. Recompilar sólo dependencias invalidadas.
- [ ] Con APK futura: dos páginas independientes, navegación/scroll/formulario no privado, diálogos por panel, swap sin recarga, resize/orientación, background/foreground, cierre y recuperación de superficie. Sin esta ejecución, mantener aceptación visual PENDING.

## Estado de revisión

Fuente implementada y conectada. Revisión independiente de rama completa atendida en una sola pasada; cinco Important corregidos, sin Critical establecido. 68 pruebas split, 340 host, 44 helpers y 18 omnibox PASS; preparación y registros de fuentes/tests verificadas. Los checkboxes de tareas 1–5 acreditan implementación/contratos de fuente y adaptadores; no certifican interacción Android, GPU, IME, permisos ni píxeles. Estas aceptaciones, incluida recreación de Activity, requieren la APK y permanecen pendientes en tarea 6 y TODO. JNI/GN reales se comprueban durante build incremental; no declarados PASS por javac aislado. Detalles y rulings en docs/validation/R5_3_SPLIT_VIEW.md.

## Solicitud adicional aprobada — panel estrecho
Cada panel publica su ancho real al WebContents para CSS responsive. Bajo 600 dp usa temporalmente UA móvil por pestaña; restaura escritorio original a 640 dp o salida, con histéresis y sin recarga automática, zoom/DSF ni preferencias globales. Páginas con variante móvil de servidor pueden requerir navegación explícita; preservar formularios. Tests de independencia, histéresis, móvil original, override explícito, restauración e integración con ratio.
