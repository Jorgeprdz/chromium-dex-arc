# Archium — estado de implementación, 6 de octubre de 2026

Commit de implementación previo al selector de interfaz: `6df2d5bbbba658c53aebedd51fd0d4634f2f27da`. Rama: `feat/arc-desktop`.
Chromium: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0).
Este documento describe preparación; no es una entrega de APK ni aceptación funcional.

## Guardado y comprobado

- Planes aprobados para contraseñas locales, Arc Mac, compilación incremental,
  desktop adaptativo y teclado/mouse. Investigación y render guardados en Download.
- Política y persistencia de apariencia AUTO/ARC/MOBILE escritas y comprobadas
  en JVM y en la app de pruebas Android, incluida reapertura en otro proceso.
  El selector visible y las transiciones de UI del navegador siguen pendientes.
- Clasificación actual de ventana con constantes reales de AndroidX:
  compacta <600 dp, tablet 600–839 dp, desktop >=840 dp. Sin dependencia de Samsung.
- Keystore Android real: ocho casos, un regression test de commit fallido y
  reapertura en un nuevo proceso pasaron en el teléfono físico. La clave envuelta
  se sincroniza, se verifica después del commit y se sincroniza su directorio.
- Backend LoginDatabase local, importación atómica y readiness de save/fill escritos
  en el parche. Su compilación y ejecución nativas permanecen pendientes.
- CSV independiente: 18 casos sintéticos pasan. La pantalla, autenticación y
  conexión SAF/PasswordStore todavía faltan. No se ha leído el CSV personal.
- 28 pruebas Python de preparación/checkpoints/routing pasan. El parche de
  59 archivos aplica y coincide con sus hashes. Los checks
  aislados de Java/SDK no equivalen a compilar Chromium.
- Workflow preparado para restaurar un checkpoint anterior con commit explícito,
  conservar objetos/mtimes y compilar los targets modificados antes de la APK.

## Pendiente antes del run final

1. Terminar el gestor nativo de contraseñas: listado/CRUD, autenticación,
   preview y decisiones de duplicados, rechazo de preview desactualizado,
   confirmación atómica, exportación SAF e integración de ajustes/Arc.
2. Completar la interfaz Arc Mac: selector AUTO/ARC/MOBILE, sidebar, Spaces,
   favoritos/pinned/carpetas, omnibox y controles reales, clipping del viewport.
3. Conectar clasificación a RDS/UA, WebPreferences/text sizing, resize/display
   y preferencias de zoom nativas. Conservar overrides explícitos por sitio.
4. Integrar Ctrl+Shift+B/middle-click en la sidebar y verificar los comandos e
   interacciones de Chromium. F11 no se implementa como fullscreen ficticio.
5. Review del cambio completo y gates pre-build. Los gates nativos dependen del
   checkout completo de CI; no están marcados como pasados.

## Compilación y pausa

No se ha lanzado un run nuevo ni se han cambiado los monitores de run.
Checkpoint reutilizable: `archium-checkpoint-37255997027-7`.
Commit de ese checkpoint: `c8ffd13ee7fe1c6baab4913da6a01e8009febe18`.
Conservar validación estricta de identidad/revisión/rutas/hashes; no restaurar
ese checkpoint fingiendo que pertenece al commit nuevo. No se promete duración.

Tras lanzar el run FINAL: obtener su ID real, actualizar los monitores locales
 y el script del repositorio, ejecutar una consulta de monitor y pausar, según
la orden del usuario. No anunciar success con build pendiente. Instalación y
pruebas del navegador/desktop se retoman cuando el usuario reanude.

Monitores:
- `/workspace/monitor-archium.sh`
- `/workspace/macdesk-maintenance/monitor-archium-run.py`
- `scripts/vigilar-compilacion-arc.sh` (corregir también textos antiguos de APK base).

## Datos y pruebas

Destino autorizado del teléfono: `/sdcard/Download/Archium-documentos`.
ADB explícito: `192.168.101.105:44641`. `emulator-5554` es otro alias del mismo
Samsung físico, no cobertura separada de un emulador.
Los tests de Keystore usan `app.archium.keytests`; los tests de window metrics
usan `app.archium.windowtests`. No se cambió el PIN ni se limpió el perfil del usuario.
Las pruebas de formularios deben usar un APK/perfil aislado: jamás ejecutar
`clearAllPasswords()` en la aplicación instalada del usuario.

Resultados: `docs/validation/local-passwords-results.md`.
Formularios: `tests/runtime/passwords/README.md`.
Ledgers/briefs locales de tareas: `.superpowers/sdd/` (ignorados por Git).

## Ajuste de alcance del usuario (2026-10-06)

El siguiente run se limita a la interfaz Arc y las contraseñas locales/CSV.
Se conserva la clasificación efectiva de ventana y AUTO/ARC/MÓVIL ya avanzados,
porque gobiernan la interfaz. La nueva política automática de navegación desktop,
zoom/autosizing y la capa adicional de teclado/mouse se aplazan al siguiente update.
Los comandos e interacciones nativos existentes se conservan.
Esto no elimina los requisitos de contraseñas ni los controles reales de la interfaz.
No se ha lanzado el run final ni actualizado sus monitores.

Selector de interfaz preparado en Ajustes: diálogo nativo AUTO/ARC/MÓVIL,
resumen del modo, cierre al destruir Settings y observador de preferencias en
la ventana del navegador. Pruebas del diálogo real Android y cola UI pasan en
la app temporal. La recreación se contó con una Activity de prueba; todavía no
prueba restauración de pestañas/formularios en la APK Chromium ni la compilación
completa de MainSettings.
