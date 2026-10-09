# Archium R2 — reparación del preflight y monitor, 2026-10-09

Base `0ab41e74401bc16a22ebe3e4cee3ee4d63399780`, rama `feat/arc-media-only`, repositorio real `Jorgeprdz/chromium-dex-arc`. Run37956354345 falló en `Check repository before checkpoint restore`; restore y compilación se omitieron. No se creó un APK nuevo ni se instaló una actualización de ese run.

## Causa demostrada

El job113907753266 ejecutó294 pruebas en93.952s: un FAIL y3 omisiones por requisitos de SDK no disponibles. La prueba `test_focus_clipping_helper_compiles_with_android_sdk37` intentaba compilar usando el path local `/opt/android-sdk/platforms/android-37.0/android.jar` antes de que el workflow preparase Chromium/SDK. El runner no contiene esa ruta. El error es `package android.content does not exist`, seguido de los tipos de Android no encontrados. No es un fallo del compositor o de la reparación visual.

El check local anterior294/294 sí utilizaba Android37 disponible. Fue insuficiente para demostrar portabilidad del preflight a un runner sin esa API; esta reparación añade ese escenario.

## Corrección mínima

`tests/test_arc_native_overlay.py` resuelve el jar mediante `ANDROID_JAR`, después `ANDROID_HOME/platforms/android-37.0/android.jar`, después el default local. Cuando el jar no está disponible informa explícitamente `SkipTest` por requisito ausente antes de invocar javac. Los escenarios de comportamiento puro Java siguen ejecutándose. Con Android37 se realiza la compilación real contra tipos Android. No se cambia la implementación visual, el patch, el scope arc-media, passwords locales deshabilitados, el ancho manual o los modelos.

Añadidas regresiones: SDK configurado ausente se reporta con su path; SDK configurado presente compila `android.view.View`. RED: `SkipTest not raised` porque el helper antiguo ignoraba la configuración. GREEN:7 casos con SDK real;7 casos,2 omisiones explícitas en configuración sin SDK. Un preflight verde con esas omisiones no acredita compilación Android37 ni build integral; estos quedan separados del chequeo de repositorio.

`scripts/monitoring/monitor-archium-run.py` usa el estado terminal no exitoso de GitHub para mostrar `Instalación: No instalada: build fallido`, aunque el worker tenga información antigua o falte su estado. Se conservan el intervalo600s, panel compacto, confirmación verificada de instalación en runs exitosos y reintento durante runs activos. Las pruebas ejecutan el `main` real con respuestas de GitHub y archivos de estado controlados: RED en12 subcasos; GREEN22 pruebas del monitor/updater.

## Conexión del worker

El updater nativo registró reintentos de conexión a `api.github.com` después de su primera consulta válida. Durante el diagnóstico, tanto worker como root tienen las seis variables de proxy desactivadas. Probes a `rate_limit` y al endpoint exacto del run, lanzados por el mismo `RunCommandService → proot codexbox → bash -lc`, tuvieron éxito con entorno heredado y también limpiando proxies. UID10532 sin bloqueo de red efectivo y deviceidle ACTIVE en esa observación.

La causa histórica de esos fallos de conexión **no está demostrada ni reproducida actualmente**. No se modifica el wrapper por una hipótesis de proxy sin evidencia. El worker conserva los checks de SHA/run exitoso/artifact/firma/paquete/hash instalado y rechaza un run fallido antes de descargar o usar ADB. Se reiniciará para el nuevo run; la instalación sigue requiriendo acceso a GitHub y dispositivo disponible.

## Validación y publicación

Revisión independiente de los tres archivos: sin hallazgos críticos/importantes. El reviewer repitió7 casos de overlay con API37 y22 del monitor, PASS. Checks oficiales sobre el código final:

- `ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh`, Python3.12.15/JDK17.0.20.1 configurados como en el informe R2: **299/299 PASS**,193.611s, sin omisiones locales, `ARCHIUM_REPOSITORY_PREFLIGHT=PASS`.
- `ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar`: **PASS**,104 archivos/hash exacto, geometría y compilaciones contra SDK37,5 casos específicos PASS.
- `git diff --check`: **PASS**. Patch visual y sus hashes no cambian.
- SDK ausente simulado mediante configuración del jar:7 casos,2 omisiones explícitas por requisito SDK ausente; pruebas Java de comportamiento ejecutadas. Esto es un chequeo de portabilidad, no un PASS de compilación Android37 en ese entorno.
- Rechazo real del updater al consultar run37956354345: `stage=error`, `Build ended with failure`, sin descarga ni instalación. Estado nativo del mismo run actualizado por consulta real, sin fabricar marcador de instalación.

Dictamen: **READY FOR COMMIT** para la reparación del preflight/monitor. Build y aceptación visual del APK nuevo pendientes.

Evidencia privada: `.sync-audit/arc-next-polish-20261009/job-113907753266.log`, `run-37956354345-failed.json`, `preflight-sdk-{red,green,unavailable}.log`, `repository-preflight-repair.log`, `preparation-preflight-repair.log`. Probes nativos de red: `/workspace/.archium-install/native-network-probe.log` y `native-run-view-probe.log`. No se publica información de credenciales o valores de proxy.

La nueva publicación reutilizará checkpoint `archium-checkpoint-37905612954-1`, productor exacto `38326ef19f1e82548bf32ff412c0350374cdf3a6`, pin Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`. El checkpoint conserva23 partes verificadas con tamaños/digests remotos. Un solo nuevo run manual para el commit de esta reparación. Monitor y updater se apuntarán al run/SHA nuevos; después pausa.

La paridad visual y funcionamiento del APK nuevo siguen pendientes de build e inspección DeX. El display continúa desconectado; no se declara PASS de la aceptación visual.
