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
  74 archivos aplica y coincide con sus hashes. Los checks
  aislados de Java/SDK no equivalen a compilar Chromium.
- Workflow preparado para restaurar un checkpoint anterior con commit explícito,
  conservar objetos/mtimes y compilar los targets modificados antes de la APK.

## Pendiente antes del run final

1. Terminar el gestor nativo de contraseñas: listado/CRUD, autenticación,
   preview y decisiones de duplicados, rechazo de preview desactualizado,
   confirmación atómica, exportación SAF e integración de ajustes/Arc.
2. Completar la interfaz Arc Mac: integrar selector ya preparado, sidebar, Spaces,
   favoritos/pinned/carpetas, omnibox y controles reales, clipping del viewport.
3. APLAZADO por el usuario: conectar clasificación a RDS/UA, text sizing y zoom
   en el próximo update; conservar sólo el clasificador ya implementado para UI.
4. APLAZADO por el usuario: capa adicional de teclado/mouse para el próximo
   update. Conservar comandos e interacciones nativas existentes.
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

Modelo de sidebar y almacenamiento preparados: identidades estables, Spaces, Favorites compartidos, carpetas anidadas, fijados que conservan URL al cerrar su pestaña, recuperación de asociación ausente y persistencia versionada. Pruebas JVM de modelo/almacenamiento pasan. El adaptador utiliza UserPrefs y ProfileKeyedMap OWN_INSTANCE; el almacenamiento privado es en memoria. Todavía falta conectar TabModel, renderizar las colecciones y verificar el ciclo de vida nativo/perfiles. No se ha compilado otra APK.

Preparada la API de snapshot/revisión de importación en la DB y su ruta async. Seis nuevas regresiones C++ escritas, pendientes de compilación/ejecución. Ver `docs/validation/local-passwords-results.md`. El gestor visible, autenticación y SAF siguen sin implementar. No hay run nuevo.

Preparados ArcTabActions y ArcNativeTabSession: selección/reapertura sin duplicar
una pestaña tras error de metadata, cierre confirmado conservando canonical URL,
comandos nativos createNewTab/pinTab/setIndex/remover/cancelTabClosure, scope del
modelo activo y limpieza de observers. El controlador pasó JVM con frontera de
comandos simulada; adapter sólo pasó SDK con contratos stubbed. Todavía NO se
construyen desde el coordinador Arc y faltan pruebas dentro de Chromium.

Actualización de clave: marcador no secreto de inicialización en filesDir evita regenerar una DEK después de perder simultáneamente KEK y registro. RED/GREEN real en app temporal Android (9 casos + commit/reinicio). Backend GetError también exige disponibilidad de cifrado en el fork Android; regresión C++ pendiente.

Vista previa nativa preparada: `ArchiumPasswordImportPreview` clasifica mediante
la misma validación de `SavedPasswordsPresenter`, evita elegir arbitrariamente
entre contraseñas distintas del CSV, omite duplicados y conserva cada formulario
existente y sus notas al reemplazar. Mantiene la revisión DB para el commit
atómico futuro. Nueve pruebas C++ escritas, no compiladas/ejecutadas; se registró
`archium_password_import_tests` y su retención como artifact. Regresión de
retención observada RED y luego GREEN; suite Python 28 pasa. Patch de 74 archivos
aplica/hashes coinciden. Gestor, JNI, auth, SAF y UI siguen pendientes.
