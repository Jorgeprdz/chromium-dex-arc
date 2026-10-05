# Arc Desktop Implementation Plan

**Goal:** Preparar código nativo y parches reproducibles del diseño aprobado mientras corre el baseline.
**Architecture:** Extender las pestañas verticales existentes; una política de ventana y paleta compartida controla elegibilidad y color. Un coordinador del navegador añade favoritos reales y apariencia sin reemplazar el motor ni los modelos de pestañas.
**Tech Stack:** Java Android, GN, Python para validar/aplicar parches.
**Spec:** `docs/superpowers/specs/2026-10-05-arc-google-design.md`.
**Execution:** Inline; el usuario indicó «ahora sí, go» después de revisar y corregir el diseño.

## Global Constraints

Revisión `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; solo escritorio/DeX; teléfono tradicional incluso horizontal; rail 240/52 dp; color personalizable persistente; contenido web sin tinte. No modificar el run baseline activo ni descargar el checkout completo al teléfono. No simular Chrome Sync ni forzar disponibilidad del backend de contraseñas.

## Review Focus

Teléfono ancho en horizontal: no activar Arc. Display sin configuración DeX confirmada: conservar UI tradicional. Colores extremos: contraste de texto mínimo 4.5. Marcadores asincrónicos: no actualizar vistas destruidas. Parches incompatibles: rechazar antes de mutar el checkout.

### Task 1: Política de escritorio y paleta

Files: `chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java`, `ArcDesktopAppearance.java`; `tests/java/ArcDesktopPolicyTest.java`.
Interfaces: política pura `isDesktopWindow(boolean phoneDisplay, boolean dexWindow, boolean pcDevice)`; paleta `surface(int seed, boolean dark)`, `foreground(int background)`, `contrast(int, int)`; adaptación Android con configuración de ventana y preferencias propias.
- [x] Escribir y ejecutar pruebas Java contra política todavía ausente (RED).
- [x] Implementar política/paleta y persistencia Android.
- [x] Ejecutar pruebas Java con teléfonos, escritorio y colores RGB extremos (GREEN).

### Task 2: Integración nativa Arc

Files: `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java`; `patches/archium-desktop.patch`.
Interfaces: recibe Activity, rail existente, BookmarkModel, perfil y navegación a través del Tab actual; ciclo destroy elimina observadores. Usa la política/paleta de Task 1.
- [x] Revisar contratos exactos de BookmarkModel y lifecycle en la revisión fijada.
- [x] Integrar elegibilidad escritorio, rail 52 dp con recursos ajustados, encabezado de marcadores, color y acciones Google/autocompletado, conservando modelos existentes.
- [x] Añadir guardas de lifecycle/configuración y comprobación de recursos/GN; preparar diff contra originales.
- [x] Compilar Java con SDK y clases dependientes disponibles; distinguir compilación aislada del build APK completo.

### Task 3: Aplicación segura y revisión

Files: `scripts/apply-arc-patches.py`, `scripts/check-arc-preparation.py`, `tests/test_patch_application.py`, `docs/arc-preparation.md`.
Interfaces: aplicar únicamente sobre revisión fijada, validar todos los parches antes de mutar. El baseline no consume estos parches automáticamente.
- [x] Pruebas RED de revisión incorrecta, cambios conflictivos y aplicación real en checkout pequeño de prueba.
- [x] Implementar validación/aplicación y verificación de recursos/parches.
- [x] Ejecutar suite completa, revisar diff y documentar límites de pruebas.
- [x] Guardar trabajo en rama aislada; no publicar ni instalar APK sin build validado.

## Validación pendiente del constructor

El baseline y el build del fork son gates diferentes. La suite local puede verificar lógica y aplicación de parches, pero no reemplaza GN, javac con todas las dependencias Chromium, el enlace nativo ni las pruebas de DeX/Autofill con la APK propia. Si Google Autofill no entrega credenciales, mantenerlo como bloqueo del criterio de navegador predeterminado.
