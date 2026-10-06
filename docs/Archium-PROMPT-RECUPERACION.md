Continúa el trabajo de Archium desde el estado guardado. No empieces de cero.

Alcance vigente del usuario: cerrar el siguiente run únicamente con Arc look alike
y contraseñas locales (guardar/actualizar/rellenar, gestor local e importar/exportar
CSV). Google Sync quedó descartado por decisión del usuario. Conserva funciones
nativas y el diseño aprobado. La política nueva de navegación desktop, zoom,
autosizing y la capa extra de teclado/mouse quedan para un update posterior.
Conserva el clasificador de ventanas y AUTO/ARC/MÓVIL, que ya están avanzados.

Está autorizado continuar implementando, verificar, preparar el commit/push necesario
y lanzar el run cuando ese alcance esté realmente integrado. No vuelvas a pedir
aprobación del plan. Tras lanzar el run FINAL: actualiza los monitores con el ID real,
verifica una consulta --once, guarda la información y ponte en pausa. No esperes la
compilación ni instales hasta que el usuario reanude. No anuncies éxito antes de que
termine la compilación; luego se necesita validación real de la APK.

## Recuperación inmediata

Workspace: /workspace/ChromiumDeXArc-work
Branch: feat/arc-desktop
Origin: https://github.com/Jorgeprdz/chromium-dex-arc.git
Chromium fijado: cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 (157.0.8086.0)
Paquete real: app.archium.android
Commit del código al escribir este prompt: 7ba0e586fa4cb79c8cec5de8f347bd25083db98a
Fecha UTC: 2026-10-06T04:05:25.689397+00:00

Lee primero docs/archium-current-handoff.md y docs/validation/local-passwords-results.md.
Después git status y git log; continúa los cambios existentes, no los sobrescribas.
Los documentos guardados son la memoria; diferencia implementación preparada,
pruebas host/SDK con stubs y pruebas reales de Chromium. No confundas esos niveles.

Este repo prepara un PATCH: no es un checkout completo de Chromium. Los nuevos
archivos upstream están en chromium/ (seguimiento git). Los cambios a originales
están en .source-modified/ y sus originales exactos en .source-reference/ (ignorados).
La entrega efectiva está en patches/archium-desktop.patch y upstream-files.json.
NO regeneres el patch con cachés originales/modificados ausentes o incompletos,
porque eliminarías modificaciones existentes del patch.

También hay un bundle git y un archivo de preparación en Download/Archium-documentos.
Si el workspace existe, conserva sus cambios y usa esos archivos como respaldo.
Si desapareció, importa el bundle en un repo nuevo y extrae el archivo de preparación
ahí; recupera .source-reference y .source-modified antes de regenerar el patch.
El checkout nativo completo lo prepara CI; no descargues cientos de GB sin necesidad.

## Estado real

1. Clave aleatoria de datos protegida por Android Keystore, AES-GCM y escritura
   verificada/durable del registro envuelto. Java Keystore en app temporal pasó,
   incluido reinicio y AtomicFile que oculta fallo de commit. Bloqueo real del
   dispositivo y proveedor C++ siguen pendientes de validación.
2. Backend local basado en LoginDatabase/Builtin, con cifrado obligatorio y sin
   borrado de registros ilegibles. Preserva decrypt legacy v10, no lo usa para
   escrituras nuevas. Account/Google no se fingen disponibles. No registra Sync
   PASSWORDS con delegado null. Tests C++ escritos, NO compilados/ejecutados aún.
3. Save/fill preparados usando rutas reales de PasswordManager; readiness rechaza
   tienda/clave no disponible. Settings usa prefs locales reales. Fixtures HTML
   en tests/runtime/passwords. NO validación save/fill de navegador todavía.
4. ArchiumPasswordCsv parse/write: 18 casos sintéticos JVM pasan. RFC quotes/BOM/
   Unicode, límites y errores sin valores sensibles. Aún NO está conectado a
   importación/exportación visible: faltan gestor/JNI, auth, SAF y review/confirm.
5. API de snapshot/revisión DB preparada para prevenir que un CSV viejo sobrescriba
   un guardado web pendiente. Revisión con token de sesión de DB, total_changes,
   data_version; se valida dentro de la transacción con lectura adquirida antes.
   Ruta async en helper/backend/store y WeakPtr para cierre. Seis nuevas regresiones
   C++ están escritas pero NO ejecutadas. Experimento SQLite local sólo validó
   contadores, no prueba la implementación Chromium.
6. ArchiumWindowClass usa constantes 600/840 dp de AndroidX fijado. WindowMetrics
   mide ventana útil actual; sin fabricante/DeX/display físico. JVM y app temporal
   física pasaron. No es implementación completa de política UA/RDS desktop.
7. AUTO/ARC/MÓVIL persistente y separado de navegación. Selector nativo preparado
   en MainSettings; diálogo real y cola UI pasaron en app temporal. Observer escucha
   preferencias y limpia callbacks. La recreación se cuenta con Activity de prueba,
   NO prueba restauración de pestañas/formularios en Chromium.
8. Modelo de sidebar/almacén preparado: IDs, Spaces, Favorites compartidos, carpetas
   anidadas, fijados con URL tras cierre y reconciliación de tab IDs. JVM pasó.
   ArcSidebarProfiles usa UserPrefs + ProfileKeyedMap OWN_INSTANCE: off-the-record
   conserva sólo memoria. Su ciclo de vida nativo aún no está validado.
9. FALTA conectar ArcTabActions con TabModel/TabCreator y renderizar/componer Arc.
   El coordinador actual todavía es la cabecera antigua; NO es Arc terminado ni
   visualmente idéntico. Chromium ya tiene TabModel.pinTab/unpinTab: reutilízalos.
   No sustituyas tabs nativas ni inventes ventanas/fullscreen/controles falsos.
10. FALTAN partes importantes antes del run: gestor de contraseñas visible seguro,
    JNI/SavedPasswordsPresenter, autenticación nativa, SAF/import/export/CRUD y
    composición Arc (sidebar/nav/address/controles/frame/modelos/estados reales).
    Luego revisar toda la integración, patch, GN y compilar. NO despaches esto
    como entrega completa simplemente porque el patch se aplica.

## Planes y ledger

Spec: docs/superpowers/specs/2026-10-06-archium-local-arc-design.md
Plans: docs/superpowers/plans/2026-10-06-local-passwords.md,
2026-10-06-arc-mac.md, 2026-10-06-incremental-build.md.
Anexo/investigación desktop-input se conserva pero se aplazó el trabajo nuevo.
Ledgers: .superpowers/sdd/<basename-del-plan>/progress.md.
La ejecución elegida es inline (executing-plans), sin implementer subagents.
Los tasks con gates nativos pendientes NO están completos. Se dejó explícito
por qué RED/GREEN nativo no se puede correr aquí; nunca presentes stubs como GN.
Se requiere una revisión completa final (skill permite un reviewer fresco).

## Comandos de verificación y evidencia

python3 scripts/generate-arc-patch.py
python3 scripts/check-arc-preparation.py
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check -- . ':!patches/archium-desktop.patch'
.sync-audit/actionlint .github/workflows/baseline-build.yml .github/workflows/archium-stage.yml
bash -n scripts/build-archium.sh

Último estado: patch de 66 archivos se aplica y coincide con hashes. JVM/SDK-adapters
pasan; estos últimos usan contratos Chromium stubbed. 28 Python tests pasaron.
Tests físicos: scripts/test-android-password-key.py y test-android-window-policy.py
con --device 192.168.101.105:44641. SDK /opt/android-sdk, android-36/build-tools36.
Logs de esta sesión están en .sync-audit/ y compiladores/apps en .test-build/.

ADB: /usr/bin/adb. Teléfono físico 192.168.101.105:44641.
Otra entrada emulator-5554 es ALIAS DEL MISMO Samsung S25, no otro emulador.
Nunca borres perfiles, CSV personal, contraseña, PIN ni datos de app del usuario.
Pruebas con datos inventados y paquetes app.archium.keytests/windowtests o futura
APK variante .tests. No instalar con firma incompatible ni desinstalar para forzar.

## Compilación incremental y pausa

NO HAY RUN NUEVO. El anterior 37255997027 terminó stage8.
Checkpoint reutilizable archium-checkpoint-37255997027-7.
Commit origen del checkpoint c8ffd13ee7fe1c6baab4913da6a01e8009febe18.
24 assets, ~24 GB comprimidos. La transición de parches ya tiene verificación de
identidad/hashes/paths y rollback; no saltes controles de checkpoint ni caches.
Workflow baseline-build.yml usa etapas de 2 horas/checkpoints. No prometas duración
corta: se intentará incremental pero todavía no se midió el nuevo build.
Targets nativos preparados: archium_key_provider_tests, archium_key_java,
archium_login_database_tests, archium_password_csv_java,
chrome/browser/password_manager:unit_tests. Compilar el source_set de tests del
cliente no es ejecutar esos tests. Binarios de las dos suites se conservan en artifact.

Cuando esté integrado el alcance, commit/push y workflow_dispatch según el plan
incremental. Confirma el ID devuelto y actualiza:
/workspace/monitor-archium.sh (default run actual viejo 37255997027)
/workspace/macdesk-maintenance/monitor-archium-run.py (mismo run viejo)
/workspace/macdesk-maintenance/start-archium-monitor.sh
scripts/vigilar-compilacion-arc.sh (run viejo 37231453817 + textos antiguos BASE).
Actualiza también textos para no afirmar features ya validadas cuando sólo comienza
el build. Consulta --once con el nuevo ID, guarda link/commit/checkpoint en Download
Y PONTE EN PAUSA, por instrucción explícita del usuario.

## Download y cuota

Documentos y render anteriores: /sdcard/Download/Archium-documentos.
Este prompt: /sdcard/Download/Archium-PROMPT-RECUPERACION.txt.
El render es conceptual; no prueba que esa UI ya exista en la APK.
Actualiza este prompt y su copia tras cada milestone si el trabajo sigue sin run.
El usuario reportó 18% de cuota y pidió respaldo al 2%. La sesión NO tiene una
herramienta que lea su porcentaje: no inventes monitoreo/alertas automáticas ni
lo confundas con contexto o token budget. Ya se guardó preventivamente antes del
umbral. Si el usuario informa 2%, actualiza y verifica la copia inmediatamente.
