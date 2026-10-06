# Desktop Keyboard and Mouse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar interacción real de teclado/mouse conservando los controladores de Chromium y el diseño Arc aprobado.

**Architecture:** Reutilizar KeyboardShortcuts, MenuOrKeyboardActionController, TabModel y EventForwarder/Blink. Añadir únicamente integración de sidebar y gesto medio en rail; probar la cadena ya existente de zoom/dispositions/back-forward. No duplicar atajos ni interceptar eventos web globalmente.

**Tech Stack:** Chromium157 Java, KeyEvent/MotionEvent de Android, RecyclerView y modelos nativos, pruebas upstream/instrumentación.

**Spec:** `docs/superpowers/specs/2026-10-06-desktop-input-annex.md`; investigación `docs/investigacion-desktop-input-2026-10-06.md`.

## Global Constraints

- Revisión exacta `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
- Funciona con input hardware en cualquier ventana; solo comandos de sidebar requieren sidebar disponible.
- Mantener touch, drag/drop, incógnito, bookmarks, omnibox, extensions y sesiones. Sin JS/WebView/eventos web falsos ni servicios Samsung.
- F11 está marcado NOT_IMPLEMENTED_TOGGLE_IMMERSIVE; no introducir fake fullscreen.
- Nueva ventana depende de ruta real multiinstance/window manager; documentar restricciones.
- Después del run final, actualizar monitores, comprobar consulta y pausar; no esperar/installar automáticamente.

## Review Focus

- AltGr/layout internacionales no deben convertirse en comandos Ctrl+Alt.
- Atajos llegan a Chromium y conviven con shortcuts de extensiones/web donde upstream lo permite.
- Middle click afecta exactamente el tab bajo mouse, con protección de índice/modelo/incógnito y recyclerview recycled views.
- Eventos wheel/side buttons consumidos por página siguen semántica upstream; ningún interceptor global.
- Sidebar oculta debe liberar viewport real y poder volver con shortcut, sin fake overlay o pérdida de tabs.

### Task 1: Verificar y conservar comandos existentes; integrar sidebar

**Files:** Reuse KeyboardShortcuts.java y tests fijados; Modify `TabbedRootUiCoordinator.java`, `ArcDesktopCoordinator.java`/rail coordinator para acción real del sidebar y estado de layout; tests correspondientes.

**Interfaces:** Ctrl+Shift+B se resuelve mediante comando/controlador cuando sidebar Arc disponible; compacto conserva bookmark-bar command original. Ctrl+L/T/W/Shift+T/Tab/Shift+Tab/1–8/9/D/H/J/Shift+N/Alt+Left/Right/F5/R/Shift+R conservan rutas actuales. No copiar mapa de shortcuts.

- [ ] RED: shortcut muestra/oculta sidebar completa, actualiza anchura/viewport, persiste estado por ventana y restaura mediante atajo; compacto mantiene flujo upstream.
- [ ] Integrar comando native de UI Arc sin romper dispatcher de extensiones y prioridad upstream.
- [ ] Verificar shortcuts solicitados contra controladores reales, incluido contenido seleccionado en omnibox y pila real de tabs cerradas.
- [ ] GREEN tests de controlador e instrumentación; documentar F11/keys interceptadas por Android; commit.

### Task 2: Gesto medio en tabs y conservación del mouse web

**Files:** Rail RecyclerView/item binder actuales, TabProperties/TabActionButtonData y close controller existentes; pruebas de eventos mouse/drag/drop. No modificar Blink ni EventForwarder salvo falla real reproducida.

**Interfaces:** Mouse BUTTON_TERTIARY en ACTION_BUTTON_RELEASE del item -> callback de cierre ya enlazado al modelo del tab; no llamar performClick ficticio ni cerrar un índice stale. Link clicks/modificadores y Ctrl+wheel permanecen en EventForwarder -> Blink/WebContents -> delegate/ZoomController.

- [ ] RED de middle click en tab correcto, pinned/incognito, reciclaje y no disparo con touch/right button/drag.
- [ ] Integrar solo donde el binder conserva el ID/modelo; reusar action close y reglas pinned ya existentes.
- [ ] Probar middle link background, Ctrl+click, Shift+click con multiinstance real, side buttons después de renderer, wheel normal y Ctrl+wheel zoom persistente.
- [ ] Documentar restricciones de new window/OS y dispositivos sin side events. GREEN tests/patch y commit.

### Task 3: Entrega y pausa tras dispatch

**Files:** Changelog y results compartidos con desktop-policy plan; `scripts/vigilar-compilacion-arc.sh`, `/workspace/monitor-archium.sh`, `/workspace/macdesk-maintenance/monitor-archium-run.py`.

- [ ] Ejecutar pruebas pre-build y revisión final del conjunto (incluye contraseñas/Arc/desktop/input/build).
- [ ] Compilar APK mediante run final cuando implementaciones/gates estén listas; conservar artifact.
- [ ] Obtener ID/URL del run real, actualizar defaults y textos de todos los monitores del usuario, copiar versión solicitada a Download, verificar consulta one-shot.
- [ ] Pausar inmediatamente como pide el usuario. Reportar run iniciado y build pendiente, sin claim de success.
- [ ] Cuando usuario reanude: esperar conclusión, descargar/conservar artifact, verificar firmas, update sin borrar perfil, E2E y changelog final. No avanzar este paso durante pausa.
