# Prompt de continuación de Archium — respaldo al detenerse

ESTADO: DETENIDO por instrucción explícita del usuario: «ya guarda prompt de
continuacion, muy específico y detallado y detente». No lanzar un run ni seguir
implementando durante este cierre. Reanudar sólo cuando el usuario lo solicite.
Al recibir esa instrucción futura, continúa desde este estado; no empieces de cero.

Última instrucción adicional: después de lanzar el run FINAL, crear/actualizar el
script de seguimiento con el ID real y refresh automático cada 15 minutos
(900 segundos), verificarlo, dejarlo funcionando y ponerse en pausa.
El seguimiento automático continúa mientras el agente está detenido.
No activar ahora un seguimiento de un run nuevo: todavía no se ha lanzado.

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
Checkpoint del código antes del commit documental de cierre: e7563e4ed569a425ab587957c3dd32aa48b859cf
Fecha UTC: 2026-10-06T06:19:05.077162+00:00

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
   incluido reinicio y AtomicFile que oculta fallo de commit. Ahora un marcador
   no secreto en filesDir impide crear otra DEK cuando se pierden tanto KEK como
   registro envuelto después de inicializar. La nueva regresión falló antes y pasó
   después (9 casos reales + commit/reinicio). Bloqueo real del
   dispositivo y proveedor C++ siguen pendientes de validación.
2. Backend local basado en LoginDatabase/Builtin, con cifrado obligatorio y sin
   borrado de registros ilegibles. Preserva decrypt legacy v10, no lo usa para
   escrituras nuevas. Account/Google no se fingen disponibles. No registra Sync
   PASSWORDS con delegado null. Tests C++ escritos, NO compilados/ejecutados aún.
3. Save/fill preparados usando rutas reales de PasswordManager; readiness rechaza
   tienda/clave no disponible. Settings usa prefs locales reales. Auditoría corrigió GetError del backend,
   que no comprobaba disponibilidad de cifrado aunque la DB abriera. Ahora la
   exige en Android con flag local; regresión C++ escrita y pendiente. Fixtures HTML
   en tests/runtime/passwords. NO validación save/fill de navegador todavía.
4. ArchiumPasswordCsv parse/write: 21 casos sintéticos JVM pasan. RFC quotes/BOM/
   Unicode, límites y errores sin valores sensibles. Aún NO está conectado a
   importación/exportación visible: faltan UI/SAF y validar JNI/GN nativos. Se preparó
   ArchiumLocalPasswordManager (native core) que posee SavedPasswordsPresenter
   profile-only y DeviceAuthenticator real inyectado; serializa auth, lista sólo
   IDs/URL/usuario, invalida IDs al cambiar el store, revela/exporta tras auth,
   clasifica preview en ThreadPool, confirma con revisión/commit atómico y cancela
   callbacks al cerrar. Diez pruebas C++ escritas y registradas; NO compiladas ni
   ejecutadas. Se preparó el adaptador de perfil/JNI/factory del authenticator; faltan sus gates,
   pantalla, CRUD e IO SAF: NO es una importación/exportación usable.
   ArchiumPasswordManagerBridge.{h,cc}/.java conecta core con Profile original,
   profile store, AffiliationServiceFactory y ChromeDeviceAuthenticatorFactory con
   validez cero. Java tiene metadata sin password y transporte char[] limpiado.
   Export usa SecretRow/writeSecrets borrables sin password Strings nuevos; parser
   ahora pasa 21 casos sintéticos. Protocolo Java en Android temporal pasó con JNI
   y Profile simulados; NO JNI real ni C++ generado/compilado aún. El raw target
   archium_password_manager_tests también se compila/retiene en CI, aún no corrido.
   JNI bridge es Java/module normal con respuesta unavailable cuando flag off;
   CSV transporte puro se compila también flag off; Google no se sustituye.
   Archivos: chrome/browser/password_manager/android/archium_password_manager_bridge.*
   y java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordManagerBridge.java.
   Punto siguiente: implementar CRUD core y facade, fragment nativo en el módulo
   password_manager (ya tiene chrome/browser/settings:java + ChromeBaseSettingsFragment),
   SAF/auth/preview/confirm/export y routing PasswordManagerHelper/MainSettings/Arc.
   Evitar dependencia circular con chrome/android; fragment en módulo propio.
   SettingsNavigation acepta Class<Fragment>, no un String de nombre.

   SavedPasswordsPresenter.HasPasswordStoreReadError evita mostrar como vacío
   un almacén cuyo descifrado/lectura falló. Archivo native:
   chrome/browser/password_manager/android/archium_local_password_manager.{h,cc}.
   Para el consumidor UI del bridge preparado: store.ImportLoginsAtomically(..., revision), no llamar
   al método SQL ApplyImportedLogins desde UI. Auth factory con validez cero.
5. API de snapshot/revisión DB preparada para prevenir que un CSV viejo sobrescriba
   un guardado web pendiente. Revisión con token de sesión de DB, total_changes,
   data_version; se valida dentro de la transacción con lectura adquirida antes.
   Ruta async en helper/backend/store y WeakPtr para cierre. Seis nuevas regresiones
   C++ están escritas pero NO ejecutadas. Experimento SQLite local sólo validó
   contadores, no prueba la implementación Chromium.
   ArchiumPasswordImportPreview prepara clasificación nativa y decisiones por fila:
   usa una sola validación SavedPasswordsPresenter para caché/snapshot, omite
   duplicados, exige elegir una contraseña cuando el archivo discrepa, conserva
   formularios/notas al reemplazar y lleva la revisión a la confirmación futura.
   Nueve tests nativos escritos, target archium_password_import_tests registrado
   y retenido como artifact; NO compilados/ejecutados aún. Transporte JNI preparado;
   faltan consumidor UI/SAF y validación JNI real.
   Archivos principales: components/password_manager/core/browser/import/
   archium_password_import_preview.{h,cc,_unittest.cc} y ui/saved_passwords_presenter.
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
9. ArcTabActions/ArcCollectionsController pasaron JVM con comandos simulados.
   ArcCollectionsView pasó controles de UI reales en Android temporal: fijar,
   favorito, seleccionar, cambio de colecciones y limpieza. Regresión de datos
   dañados falló y pasó: error explícito, sin crash ni reemplazo de los bytes.
   ArcDesktopCoordinator AHORA construye ArcNativeTabSession con suppliers del
   modelo/creador/tab actual y rebind por incógnito; SDK pasó sólo con contratos.
   ArcSidebarState.setFavorite conserva ID al cambiar de favorito a fijado.
   FAVORITOS/FIJADOS/SPACES/CARPETAS están conectados en el patch, pero falta
   compilación y ejercicio real del perfil/TabModel/GN. El rail nativo de pestañas
   abiertas todavía es global, SIN FILTRADO por Space. La composición nav/address/
   omnibox/footer/frame Arc sigue incompleta; NO es visualmente idéntico aún.
   Archivos nuevos: ArcCollectionsController.java, ArcCollectionsView.java;
   tests/java/ArcCollectionsControllerTest.java y
   tests/android/window/ArcCollectionsViewTest.java.
10. FALTAN partes importantes antes del run: gestor de contraseñas visible seguro,
    validación del adaptador preparado de perfil/JNI/auth factory, SAF/import/export/CRUD y
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

Último estado: patch de 82 archivos se aplica y coincide con hashes. JVM/SDK-adapters
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
archium_login_database_tests, archium_password_import_tests, archium_password_manager_tests, archium_password_csv_java,
chrome/browser/password_manager:unit_tests. Compilar el source_set de tests del
cliente no es ejecutar esos tests. CUATRO binarios raw se conservan en artifact;
no se han ejecutado todavía.

Cuando esté integrado el alcance, commit/push y workflow_dispatch según el plan
incremental. Confirma el ID devuelto y actualiza:
/workspace/monitor-archium.sh (default run actual viejo 37255997027)
/workspace/macdesk-maintenance/monitor-archium-run.py (mismo run viejo)
/workspace/macdesk-maintenance/start-archium-monitor.sh
scripts/vigilar-compilacion-arc.sh (run viejo 37231453817 + textos antiguos BASE).
Actualiza también textos para no afirmar features ya validadas cuando sólo comienza
el build. Consulta --once con el nuevo ID, guarda link/commit/checkpoint en Download
Configura TODOS los seguimientos utilizados a 900 segundos (15 minutos), sin
bucles paralelos duplicados. El monitor Python ya acepta --interval 900, pero
su default actual es 600; monitor-archium.sh espera 600 y vigilar-compilacion-arc.sh
usa 180. Son valores ANTIGUOS: se deben corregir DESPUÉS de lanzar el nuevo run.
start-archium-monitor.sh debe pasar --run ID_REAL --interval 900 al Python o usar
sus defaults actualizados. Conserva una consulta --once previa de verificación,
logs/estado persistentes y salida final al terminar/fallar el run.
Deja el script activo en background de forma persistente; verificar PID/log/ID
sin esperar 15 minutos ni bloquear al agente. Guardar script e instrucciones de
seguimiento en Download si se usa desde Termux. No inventar porcentajes de build.
Y PONTE EN PAUSA, por instrucción explícita del usuario. El script queda activo;
el agente no debe continuar trabajo ni esperar activamente la compilación.

## Download y cuota

Documentos y render anteriores: /sdcard/Download/Archium-documentos.
Este prompt: /sdcard/Download/Archium-PROMPT-RECUPERACION.txt.
El render es conceptual; no prueba que esa UI ya exista en la APK.
Actualiza este prompt y su copia tras cada milestone si el trabajo sigue sin run.
El último porcentaje reportado fue 13%; el usuario iba a avisar al 3%.
Ahora ordenó guardar un prompt detallado y detenerse, sin esperar otro umbral. La sesión NO tiene una
herramienta que lea su porcentaje: no inventes monitoreo/alertas automáticas ni
lo confundas con contexto o token budget. Ya se guardó preventivamente antes del
umbral. No existe detector automático de cuota. No continuar después de guardar.

Para renovar los respaldos tras actualizar este documento:
python3 scripts/save-archium-recovery.py --device 192.168.101.105:44641
El script no monitoriza cuota. Verifica SHA-256 de cada copia. El JSON del respaldo
registra HEAD y los cambios pendientes; tar conserva la preparación/WIP mientras
el bundle conserva la historia committed.


## Orden exacto de continuación (sólo al recibir autorización de reanudar)

1. Leer este prompt completo, el handoff, resultados y planes. Ejecutar git status,
   git log -5, inspeccionar patches/upstream-files.json y el JSON de respaldo.
   Mantener rama feat/arc-desktop. No reset, clean -fdx ni regeneración con caches
   ausentes. El HEAD final de respaldo está en Archium-respaldo-estado.json;
   puede ser un commit documental posterior al checkpoint de código de arriba.
2. Implementar CRUD real en ArchiumLocalPasswordManager y bridge Java/JNI:
   agregar/editar/eliminar vía comandos existentes de SavedPasswordsPresenter /
   PasswordStore. Revalidar identidad y estado después de auth. Comprobar el
   resultado de escritura real; no anunciar success por despachar un comando.
   Mantener profile-only, readiness/cifrado, IDs opacos, callbacks de cierre,
   incógnito y flag-off. Core actual tiene metadata/reveal/export/preview/confirm,
   CancelImport/Shutdown; NO tiene CRUD add/edit/delete aún.
3. Crear pantalla nativa de gestor en el módulo password_manager, que ya depende
   de //chrome/browser/settings:java. ChromeBaseSettingsFragment está en
   chrome/browser/settings/android/java/src/..., NO chrome/android/java/src.
   SettingsNavigation usa Class<Fragment>, no String con nombre de clase.
   Evitar dependencia circular entre chrome/android y password_manager. Conectar
   listado, acciones sensibles con DeviceAuthenticator real, preview sin secretos,
   decisiones de conflictos, confirmar/cancelar y mensajes de errores reales.
4. Conectar SAF ACTION_OPEN_DOCUMENT / ACTION_CREATE_DOCUMENT. Hacer parse/IO
   fuera del hilo UI; decoder UTF-8 con CodingErrorAction.REPORT. No leer CSV
   personal durante tests. Auth de export después de elegir URI destino, antes
   de recuperar/escribir secretos; cerrar streams y SecretRow en finally. Secret
   char[] de reveal es prestado y se borra al terminar callback. Export SecretRow
   pertenece al consumidor, que debe cerrarlo. Import consume/borra char[][].
   Parser aún usa Strings inmutables para secretos: no afirmar borrado total de
   memoria. Tratar cancelación de picker, auth y cierre/profile destruction sin
   callbacks tardíos. No cancelar ciegamente al onStop si es el propio picker.
5. Conectar routing PasswordManagerHelper / MainSettings / botón de contraseñas
   Arc al gestor local cuando isLocalEnabled; revisar antes del launcher Google.
   Flag off debe preservar rutas originales. Google login/sync no se simulan.
6. Terminar composición Arc aprobada: controles reales de navegación/omnibox,
   marco, footer, sidebar/collapse/resize, favoritos/fijados/carpetas/Spaces y
   estados del perfil activo. Rail actual de tabs abiertas sigue global. Integrar
   filtrado/asignación de Space con TabModel/GroupFilter reales, sin duplicar
   pestañas ni romper grupos, extensiones, drag & drop o restauración. Preservar
   UI móvil compacta y separación de perfiles/incógnito. Concept render en
   docs/references/archium-arc-mac-concept-v1.png NO es captura de APK terminada;
   referencia oficial docs/references/arc-mac-pinned-tabs.png. Falta comparación
   visual del conjunto/footer/collapse y validación real del navegador.
7. Revisar hipótesis pendientes, no tratarlas como bugs ya probados: PreviewImport
   cancela import previo antes de verificar busy; revisar si una petición rechazada
   invalida un preview aceptado. Revisar reentrancia si on_changed destruye dueño.
   Revisar cancelación del diálogo native pin/ungroup, inicialización profile y
   restauración. ArchiumPasswordImportPreview aún recorre snapshot por fila;
   medir archivos grandes antes de optimizar. No hay RED/GREEN C++ local.
8. Validar JNI generado, GN deps/converters, Chromium EXACTO fijado y flag off.
   Bridge observa ProfileWillBeDestroyed y llama Shutdown; no omitir lifecycle.
   Revisar core read-error: SavedPasswordsPresenter.HasPasswordStoreReadError y
   backend GetError exigen lectura/cifrado disponible. C++ store snapshot lleva
   sesión + total_changes + data_version y se verifica dentro de transacción.
   Confirmar import por store.ImportLoginsAtomically(..., revision), jamás desde
   UI directo a LoginDatabase ni fallback de escrituras parciales por fila.
9. Ejecutar gates apropiados (comandos arriba), review completa y pruebas nativas
   en checkout completo. Tests de protocolo Android usan JNI/Profile SIMULADOS;
   no sustituyen runtime JNI. Cuatro raw test suites deben ejecutarse cuando haya
   runner Android compatible; compilar chrome/browser/password_manager:unit_tests
   es compilar source_set, NO ejecutar Chrome unit tests. Save/update/fill y SQL
   roundtrip/ciphertext/key-failure aún requieren ejecución real. No dar aceptación
   de APK hasta build terminado y pruebas de navegador, bajo nueva instrucción.
10. Sólo al tener integración concreta revisar plan incremental, commit/push y
    dispatch. No saltar identidad/hashes/rutas del checkpoint anterior. Registrar
    URL/ID/commit/checkpoint reales. Actualizar seguimiento a 900 segundos según
    última instrucción, hacer --once, dejarlo activo, respaldar en Download y
    PAUSAR. No instalar ni seguir trabajo mientras el usuario no reanude.

## Contratos que ya existen y no se deben duplicar

- ArchiumLocalPasswordManager: statuses 0 success, 1 unavailable, 2 auth failed,
  3 busy, 4 stale, 5 invalid, 6 write failed. Metadata URL/user/id sin password.
- Preview: kinds 0 new, 1 exact, 2 store conflict, 3 invalid, 4 file duplicate,
  5 file conflict; decisiones 0 skip, 1 import, 2 replace. Múltiples aceptadas
  para el mismo identity se rechazan; no elegir secreto arbitrariamente.
- Bridge Java: constructor(Activity,Profile,Listener), isLocalEnabled, start,
  refresh, reveal, export, previewImport, confirmImport, cancelImport, destroy.
  Listener onMetadata/onSecret/onExport/onPreview/onOperation. destroy invalida
  pointer/listener y borra buffers; callbacks native tardíos usan WeakPtr.
- Auth: ChromeDeviceAuthenticatorFactory::GetForProfile con DeviceAuthParams
  TimeDelta cero / kPasswordManager. No aceptar boolean de auth desde Java/UI.
- Clave: AES256 KEK no exportable + DEK32 aleatoria envuelta AESGCM; apw1. Marcador
  filesDir protege pérdida conjunta; legacy v10 sólo decrypt. OSCrypt global puede
  afectar cookies: probarlas también. No reemplazar clave corrupta automáticamente.
- Sidebar: commit persistencia antes de publicar modelo. Datos corruptos conservan
  bytes y muestran error. OTR en memoria. Cerrar tab no borra pin/canonical URL.

## Paths exactos de artifacts de tests preparados

Dentro de out/Archium/obj/:
- chrome/browser/password_manager/android/archium_key_provider_tests/archium_key_provider_tests
- components/password_manager/core/browser/password_store/archium_login_database_tests/archium_login_database_tests
- components/password_manager/core/browser/import/archium_password_import_tests/archium_password_import_tests
- chrome/browser/password_manager/android/archium_password_manager_tests/archium_password_manager_tests

El script conserva copias en archium-output/native-tests. Hasta ahora NO se han
compilado/ejecutado estos binarios. No hay una APK nueva de este trabajo. APK previa
local: .archium-install/artifact/Archium-for-Android-arm64.apk (~348 MB).

## Restaurar si desaparece el workspace

Copiar desde Download/Archium-documentos a una máquina de trabajo el bundle,
Archium-preparacion.tar.gz y Archium-respaldo-estado.json. En una ruta NUEVA:

```bash
git clone -b feat/arc-desktop /ruta/al/Archium-codigo.bundle /ruta/nueva/ChromiumDeXArc-work
tar -xzf /ruta/al/Archium-preparacion.tar.gz -C /ruta/nueva/ChromiumDeXArc-work
git -C /ruta/nueva/ChromiumDeXArc-work status --short
```

Revisar el JSON: el tar puede traer WIP que no está en HEAD. Restaurar origin al
URL de arriba si se necesita push; clone desde bundle tendrá origin local. No
limpiar caches ni sobrescribir WIP. .sync-audit/.test-build son ignorados y NO se
incluyen íntegros en tar; resultados relevantes están descritos en estos docs.
Ledgers .superpowers/sdd Markdown sí se incluyen. Nunca se incluyó CSV personal.

## Inventario completo del patch al detenerse

Paths relativos al checkout upstream; M = original modificado, A = archivo nuevo.
Los hashes exactos y la revisión están en patches/upstream-files.json.

```text
M chrome/android/chrome_java_resources.gni
M chrome/android/chrome_java_sources.gni
M chrome/android/features/tab_ui/java/res/values/dimens.xml
M chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java
M chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListViewBinder.java
M chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabRailLayout.java
A chrome/android/java/res/values/arc_strings.xml
M chrome/android/java/res_chromium_base/values/channel_constants.xml
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcAppearanceDialog.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsController.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopWindowObserver.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcNativeTabSession.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSidebarProfiles.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSidebarState.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSidebarStore.java
A chrome/android/java/src/org/chromium/chrome/browser/arc/ArcTabActions.java
M chrome/android/java/src/org/chromium/chrome/browser/settings/MainSettings.java
M chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java
M chrome/browser/BUILD.gn
M chrome/browser/autofill/android/BUILD.gn
A chrome/browser/autofill/android/java/src/org/chromium/chrome/browser/autofill/ArchiumAutofillPolicy.java
M chrome/browser/autofill/android/java/src/org/chromium/chrome/browser/autofill/AutofillClientProviderUtils.java
M chrome/browser/browser_process_impl.cc
A chrome/browser/desktop_policy/android/BUILD.gn
A chrome/browser/desktop_policy/android/java/src/org/chromium/chrome/browser/desktop_policy/ArchiumWindowClass.java
A chrome/browser/desktop_policy/android/java/src/org/chromium/chrome/browser/desktop_policy/ArchiumWindowMetrics.java
M chrome/browser/password_manager/BUILD.gn
M chrome/browser/password_manager/android/BUILD.gn
A chrome/browser/password_manager/android/archium_local_password_manager.cc
A chrome/browser/password_manager/android/archium_local_password_manager.h
A chrome/browser/password_manager/android/archium_local_password_manager_unittest.cc
A chrome/browser/password_manager/android/archium_password_key_provider.cc
A chrome/browser/password_manager/android/archium_password_key_provider.h
A chrome/browser/password_manager/android/archium_password_key_provider_unittest.cc
A chrome/browser/password_manager/android/archium_password_manager_bridge.cc
A chrome/browser/password_manager/android/archium_password_manager_bridge.h
A chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordCsv.java
A chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordKey.java
A chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordKeyBridge.java
A chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordManagerBridge.java
M chrome/browser/password_manager/android/password_manager_android_util.cc
M chrome/browser/password_manager/android/password_manager_android_util.h
M chrome/browser/password_manager/chrome_password_manager_client.cc
M chrome/browser/password_manager/chrome_password_manager_client_unittest.cc
M chrome/browser/password_manager/factories/password_manager_settings_service_factory.cc
M chrome/browser/password_manager/factories/password_store_backend_factory.cc
M chrome/browser/password_manager/factories/profile_password_store_factory.cc
M chrome/browser/prefs/browser_prefs.cc
M chrome/browser/sync/BUILD.gn
M chrome/browser/sync/sync_service_factory.cc
M chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarTablet.java
M chrome/browser/ui/vertical_tabs/BUILD.gn
A chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java
A chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java
M chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java
M components/password_manager/core/browser/BUILD.gn
M components/password_manager/core/browser/buildflags.gni
M components/password_manager/core/browser/import/BUILD.gn
A components/password_manager/core/browser/import/archium_password_import_preview.cc
A components/password_manager/core/browser/import/archium_password_import_preview.h
A components/password_manager/core/browser/import/archium_password_import_preview_unittest.cc
M components/password_manager/core/browser/password_store/BUILD.gn
A components/password_manager/core/browser/password_store/archium_login_database_unittest.cc
A components/password_manager/core/browser/password_store/archium_password_import_snapshot.h
M components/password_manager/core/browser/password_store/login_database.cc
M components/password_manager/core/browser/password_store/login_database.h
M components/password_manager/core/browser/password_store/login_database_async_helper.cc
M components/password_manager/core/browser/password_store/login_database_async_helper.h
M components/password_manager/core/browser/password_store/login_database_posix.cc
M components/password_manager/core/browser/password_store/password_store.cc
M components/password_manager/core/browser/password_store/password_store.h
M components/password_manager/core/browser/password_store/password_store_backend.h
M components/password_manager/core/browser/password_store/password_store_built_in_backend.cc
M components/password_manager/core/browser/password_store/password_store_built_in_backend.h
M components/password_manager/core/browser/password_store/password_store_interface.h
M components/password_manager/core/browser/password_store_factory_util.cc
M components/password_manager/core/browser/password_store_factory_util.h
M components/password_manager/core/browser/ui/saved_passwords_presenter.cc
M components/password_manager/core/browser/ui/saved_passwords_presenter.h
M components/signin/public/android/java/src/org/chromium/components/signin/NullAccountManagerDelegate.java
```

## Checkpoints de la sesión

- e7563e4: puente de perfil/JNI y buffers autenticados; preparación, no aceptación nativa.
- 38bc6c2: core de gestor local y readiness por lectura; preparación, no aceptación nativa.
- cbde9df: colecciones Arc conectadas al perfil/tab session; preparación, no aceptación nativa.
- 3294d6f: preview nativo CSV/conflictos/validación compartida; preparación, no aceptación nativa.

Último avance comunicado: estimación 40–45% de implementación, compilación nueva 0%.
Es una estimación, no métrica automática. Hay trabajo considerable pendiente.
