## 2026-10-12 — Fix de fixture PAUSED tras run 38275213327 FAILED

Run [38275213327](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38275213327),
SHA `3c75be2c5fd0aff4a9616e218498886895f088ba`,
[job 114901953193](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38275213327/job/114901953193).
HEAD_START del retry: `44fae738b22428a49b2c8316efed76517eba1d75`.
El run se mantiene FAILED. S0/S1 pasaron, al igual que host 242/0/0,
recursos Chromium reales con optimización release y compilación de los 43/43
owners Java. Cinco suites Arc pasaron. El nuevo test toolbar obtuvo **6 PASS,
2 FAIL** (caso foreignWindow en API 29/37). El enlace libchrome no comenzó.

### Primera causa real y corrección

`gh run view --job ... --log`: exit 0 con output vacío; no se infiere éxito.
Lectura directa `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114901953193/logs`:
exit 0, 7381 líneas/580938 bytes. Primera aserción en línea **3789**,
16:39:08.6928613Z, `assertNotNull` de `ArcToolbarReparentingTest.java:122`.
El diálogo se muestra, pero en looper **LEGACY/PAUSED** su attachment está pendiente;
el test comprueba `windowToken` antes de ejecutar la cola. El log incluye
`UnExecutedRunnablesException`. Esto es un fallo de preparación del test,
no evidencia de otra regresión del código de producción.

Fix: procesar `shadowOf(Looper.getMainLooper()).idle()` después de `dialog.show()`
y tras `dismiss()`. Se conservan todas las aserciones: token no nulo, ventana
diferente y rect vacío. Ningún test deshabilitado/skip/expected-failure.
Producción, omnibox en sidebar, DeX, Portal y contraseñas DEPRECATED no cambian.

### RED/GREEN observado antes del siguiente dispatch

`python3 scripts/test-robolectric-arc-toolbar-fixture.py --classpath-file
/workspace/archium-r4-evidence/robolectric/classpath --java-home
/workspace/archium-r4-evidence/robolectric/jdk21/jdk-21.0.12.1+1 --work
/workspace/archium-r4-evidence/run-38275213327/robo-green`:
RED antes del fix exit 1, **8 tests/2 failures**; GREEN después exit 0,
**8 tests/0 failures/skips**, API29/36, 18.612 s.
`--remove-dialog-idle`: mutante negativo exit 1, **exactamente 2 failures**.
Métodos entregados y rect de producción extraídos sin modificar sus cuerpos;
ventanas y looper son Robolectric real. Construcción/resource IDs de Chrome usan
adaptadores explícitos. **No se confunde esta prueba con ChromeJUnit completo**;
API37 y runner Chromium siguen bloqueantes en S2 del retry, antes del enlace.
Warnings de agente Mockito/CDS observados, no ocultados como PASS.

Patch generado dos veces con hashes idénticos, 109 archivos:
`630ccb1435386d7c1852546ae17a36d7819417a5b8aab39d41ad6de3733befff`;
manifest `25eb76a1e217065f4094483b787bec6b6a557358b0797609e19d31f0707be2a7`.
Bash/sintaxis Python/actionlint/ShellCheck/diff check: exit 0.
Suite host integral repetida: **242 passed/0 failed/0 skipped**, 509.059 s, exit 0.
Aplicación final del patch + probes JVM/API SDK: exit 0. Logs/hash registrados
antes del push/dispatch.

### Avance recuperado y monitor

Checkpoint nuevo **archium-checkpoint-38275213327-1**, source SHA del run fallido,
25 partes/4 grupos, **26506123626 bytes**, expira 26 Oct 16:58–17:00 UTC.
Contiene los outputs Java reales recién compilados. API IDs:
11761207506/11760853238/11761855716/11760504441, no expirados, digests presentes.
Manifest leído mediante Range, **5381 bytes**, hash
`1771b7a6bda7be8c0b76bcb30cd04c0bc7202ec7a93f624a6245f29574e75004`;
SHA/tag/pin/workspace/count verificados. Integridad completa pendiente S1.
Disco local **75475378176 bytes**, **11612654 inodos**: insuficiente para
101506123626 bytes de política; no descarga masiva local ni reducción del umbral.
S0 del runner nuevo mide capacidad antes de descarga. En el run fallido el gate
real tuvo 114592665600 bytes y 18963648 inodos, PASS observado.

El monitor priorizaba authorize/cleanup cuando los timestamps de cierre empataban,
y no reconocía `0| java.lang.AssertionError` sin dos puntos. Ahora prioriza job
FAILED, normaliza prefijo de shard y muestra aserción/frame Chromium auténticos.
Regresión contra log real: RED 3 tests/2 failures; GREEN **3/3**, exit0.
Monitor instalado actualizado en /workspace/macdesk-maintenance/archium-r4-monitor.py;
[diff exacto](evidence/2026-10-12-robolectric-dialog/monitor-diagnostics.patch).
No cambia frecuencia, estilo, ni el gate de descarga/instalación.

[evidencia/primer error](evidence/2026-10-12-robolectric-dialog/first-error.txt),
[hashes/resultados/checkpoint](evidence/2026-10-12-robolectric-dialog/results.json).

## Dispatch del fix DeX y monitor nuevo: 38275213327 (2026-10-12 16:07–16:09 UTC)

**Código probado y publicado:** `3c75be2c5fd0aff4a9616e218498886895f088ba`.
Commits: [eaeac98](https://github.com/Jorgeprdz/chromium-dex-arc/commit/eaeac98)
y [3c75be2](https://github.com/Jorgeprdz/chromium-dex-arc/commit/3c75be2).
Push normal exit 0; comparación remota previa coincide con HEAD_START; sin PRs
abiertos ni runs pesados concurrentes. Protected feat/arc-desktop y main intactos.
Este registro posterior solo añade documentación; no cambia el código del run.

`gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc --ref
assistant/archium-r4-recovery -f expected_sha=3c75be2c5fd0aff4a9616e218498886895f088ba
-f source_checkpoint=archium-checkpoint-38203819481-1
-f source_commit=2de41680a42972253e8daf4cf818938dacf79a93 -f source_run_id=38203819481`:
exit 0. Run real [38275213327](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38275213327),
workflow_dispatch, created 2026-10-12T16:07:38Z, SHA exacto validado por API.
Authorize PASS, preflight en curso construyendo GN real al observar el handoff.
Native/restore/disco CI todavía no ejecutados; APK nueva inexistente.

Monitor nativo configurado con ese ID/SHA, `bash -n` exit 0. Nueva sesión **#2**
en NewTermux; `./m4` ejecutado en shell nuevo, sin escribir en la sesión Codex #1.
PID Python real **28715**, `/proc/.../cmdline` y `screen.txt` acreditan run/SHA.
Monitor muestra elapsed, ETA N/D, % de fases verificadas y tres eventos API mientras
GitHub no publica log. ASCII/color/bold/italic conservados; refresh 600 s, wake-lock,
r+Enter refresca, q+Enter sale. SUCCESS permite descargar/verificar/instalar solo
APK exacta, con Portal/package/ARM64/SHA256/firma/reporte. FAILED no instala.

**BUILD=INCOMPLETE, BUILD_STAGE=S0; ANDROID_RUNTIME del candidato=NOT_EXECUTED.**
La APK previa instalada continúa con runtime FAIL. Informe R3: 10 PARTIAL,
2 BLOCKED, sin PASS visual anticipado. Fuente checkpoint intacta; disco local
FAIL para descarga masiva, disco runner PENDING_S0 y hashes completos PENDING_S1.
Se detiene el trabajo del agente tras verificar monitor, por orden del usuario,
y se continúa con monitoreo manual. No se despacha un segundo workflow aquí.

Registro verificable: [dispatch-monitor.json](evidence/2026-10-12-dex-runtime/dispatch-monitor.json)
y [matriz R3](ARCHIUM_R3_VERIFICACION_2026-10-12.md).

## Dispatch probado y monitor en sesión nueva: 38210970891 (2026-10-12 06:06–06:09 UTC)

Commits temáticos, commit/push exit 0:

- [9b3f75a95bf629c537a59a8f2752bc88b45e2773](https://github.com/Jorgeprdz/chromium-dex-arc/commit/9b3f75a95bf629c537a59a8f2752bc88b45e2773): excepción de alias monocromo real, originales verificados y patch reproducible.
- [82b20b0b92a49da9efaf3bd87181deedf6516dcb](https://github.com/Jorgeprdz/chromium-dex-arc/commit/82b20b0b92a49da9efaf3bd87181deedf6516dcb): fixture y gate temprano de optimización release, regresiones y registro forense.

Código probado/publicado/run SHA **82b20b0b92a49da9efaf3bd87181deedf6516dcb**. Suite host **235 passed / 0 failed / 0 skipped**, 714.845 s, exit 0. Ref remoto comparado antes de push y otra vez antes de dispatch; SHA tomado directamente de `git rev-parse HEAD`. Fuente SHA tomado de API del run fuente y confrontado con el manifest validado. Consultas Actions `status=in_progress` y `status=queued`, **ambas vacías**, exit 0 antes de dispatch. Workflow manual real 374835814, inputs y concurrency conservados; no build pesado por push. Protegido/main comprobados otra vez después de lanzar, mismos hashes de la sección siguiente.

Comando real, exit 0 (variables obtenidas de Git/API, no SHA copiado manualmente):

```bash
archium_dispatch_sha=$(git rev-parse HEAD)
archium_checkpoint_run=38203819481
archium_checkpoint_sha=$(gh api "repos/Jorgeprdz/chromium-dex-arc/actions/runs/$archium_checkpoint_run" --jq '.head_sha')
gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc \
  --ref assistant/archium-r4-recovery -f expected_sha="$archium_dispatch_sha" \
  -f source_checkpoint="archium-checkpoint-$archium_checkpoint_run-1" \
  -f source_commit="$archium_checkpoint_sha" -f source_run_id="$archium_checkpoint_run"
```

[Run **38210970891**](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38210970891), creado **2026-10-12T06:06:50Z**, head_sha exacto **82b20b0b92a49da9efaf3bd87181deedf6516dcb**, evento `workflow_dispatch`. [Authorize 114684824020](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38210970891/job/114684824020) **SUCCESS**. [Preflight 114684854171](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38210970891/job/114684854171) **IN_PROGRESS**, actividad observada `Build genuine GN at Chromium DEPS pin`, a 06:08:25 UTC. S1–S5 nuevos todavía no ejecutados, ninguna APK nueva verificada/publicada/instalada.

Monitor configurado solo para este RUN/SHA. Nueva sesión nativa **#4** de NewTermux comprobada antes de escribir `./m4`; no se escribió en la sesión Codex #1. Proceso real **PID 5373**, `/usr/bin/python3 /workspace/macdesk-maintenance/archium-r4-monitor.py --run 38210970891 --sha 82b20b0b92a49da9efaf3bd87181deedf6516dcb`. Pantalla y estado `/workspace/.archium-install/38210970891/screen.txt` verificados: EN CURSO, elapsed 00:01:35, 0/6 fases verificadas, ETA N/D, eventos API diferenciados de logs todavía no publicados. Refresco 600 s, líneas continuas ASCII, colores, bold/italic, últimas tres líneas/eventos; solo SUCCESS con APK/manifest/ABI/Portal/firma/hash/report válidos permite descarga e instalación. Se usó pantalla nativa lógica 0 tras comprobar que DeX no estaba conectado; otras sesiones conservadas. Agente se detiene para seguimiento manual a petición del usuario; monitor y run continúan. Este commit posterior documenta el evento sin cambiar el código fijado en GITHUB_SHA.

**FASE=S0; SHA=82b20b0b92a49da9efaf3bd87181deedf6516dcb; RUN=38210970891; GATE=HOST_LOCAL_PASS/AUTHORIZE_PASS/CI_PREFLIGHT_RUNNING; CHECKPOINT=38203819481-1 REMOTE_PRESERVED; DISCO_CI=PENDING_S0; ERRORES_NUEVOS=NONE_OBSERVED; SIGUIENTE=S0→S1→RELEASE_RESOURCE_PROBE→S2/S3/S4/S5.** Build **INCOMPLETE**, APK artefacto/hash NONE, Android runtime NOT_EXECUTED. No se garantiza ausencia de fallos desconocidos. Contraseñas propias DEPRECATED.

## Run 38203819481 FAILED en S4: optimización de nombres no cubierta (2026-10-12)

HEAD inicial de esta reparación: `a904041dead58f4ebbd639a41cc99b66652e8876`. Rama `assistant/archium-r4-recovery`; protegido `feat/arc-desktop` = `51e5ed429661727156ab2534caac99a82ee9264b`, main = `6274c653bbe3992403a89b1531d0c1f91646bf6d`, comprobados contra remoto y sin cambios. PRs abiertos: ninguno. No runs activos al comenzar la revisión; no escrituras concurrentes observadas. Contraseñas propias siguen **DEPRECATED**, config false; identidad visual aprobada intacta.

[Run 38203819481](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203819481), source `2de41680a42972253e8daf4cf818938dacf79a93`, FAILED, 01:03:22, terminó 05:30:18 UTC. [Job build 114664052206](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203819481/job/114664052206). Comando `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114664052206/logs`, exit 0; log `/workspace/archium-r4-evidence/run-38203819481-build.log`, SHA256 `5bd575500e2fd2aae2225549a3274e66f8e91a520a0732e0dd440fc111400623`.

| Evidencia real del run | Estado / línea del log |
|---|---|
| S0 disco antes de descarga | PASS, 293: 115530907648 bytes / 18975260 inodos |
| S1 restore/transición | PASS, sin build limpio |
| Host en PATH restaurado | 230 passed / 0 failed / 0 skipped, 203.834 s, 2955–2958 |
| Recursos reales Chromium sin optimizar | PASS, 2982 |
| Robolectric temprano, runner Chromium | 605 ejecuciones PASS, 31100 |
| Biblioteca APK / símbolos JNI | PASS, 31131 |
| Robolectric ampliado, runner Chromium | 1351 ejecuciones PASS, 65450 |
| `chrome_public_apk` incremental | **Build Succeeded**, 1180 pasos / 9m39.41s / 152384 nodos reutilizados, 67842 |
| Verificación final Portal | **FAIL**, primer error 67852, `ValueError: APK is missing registered launcher resources: drawable/themed_app_icon` |
| Publicación APK / firma / ABI final / instalación | NOT_EXECUTED; no APK verificada ni artefacto APK publicado |
| Checkpoint | 25 fragmentos, cuatro grupos publicados; outputs de S4 conservados |

**CAUSA_CONFIRMADA por reproducción real AAPT2:** el gate S2 verificaba el `.ap_` anterior a la optimización. La fixture host solo usaba `--shorten-resource-paths`. El optimizador oficial además usa `--collapse-resource-names`; conserva tipos mipmap/id desde R.txt y las excepciones `chrome/android/aapt2.config`. La configuración original protege los dos launcher drawables pero no `themed_app_icon`; el verificador final exige ese alias registrado. No hubo fallo de compilación C++/Java en S4: falló el contrato de nombre entre optimización y verificador. La reproducción aislada demuestra la transformación; no pretende sustituir la inspección de la APK del checkout remoto.

Originales consultados exclusivamente en pin `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, mediante HTTPS `chromium.googlesource.com/chromium/src/+/PIN/PATH?format=TEXT`: `build/android/gyp/optimize_resources.py`, SHA256 `02e006ca42cf7eeda3f8dffb305f968bc66b6e9d942983ac15c32317b7968730`; `chrome/android/aapt2.config`, SHA256 `bef6fb84d20ee92cca00731a4a1dfbd33f50c5c5777430028699b2ab40f6c572`; `build/config/android/internal_rules.gni`. El original exacto aapt2.config se añadió al mecanismo oficial `.source-reference`, su delta a `.source-modified`.

**Fix mínimo:** una línea `drawable/themed_app_icon#no_collapse` en la configuración real. Sigue el mecanismo de las excepciones launcher de Chromium; no cambia XML, píxeles, iconos, manifest, dependencias, GN args o toolchain y no desactiva la optimización. El verificador estricto se conserva sin modificaciones.

**Corrección del gate:** la fixture hace conversión proto, collapse + short paths con configuración real y conversion binary. Los negativos de manifest ajeno y seis alteraciones del vector también pasan por el optimizador antes del rechazo. En S2, `check-portal-chromium-resources.py` obtiene la acción optimizadora y args de GN reales; ejecuta el script oficial fijado sobre el recurso `.ap_` real y su R.txt/configs, con outputs temporales separados de Siso/Ninja, y exige verificación antes de Java/link. No ejecuta la dependencia final-dex del target para este probe. La optimización después de R8/shrinking sigue verificada en la APK final; no se anticipa como PASS.

**RED observado antes del fix:** `ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar python3 -m unittest discover -s tests -p test_portal_optimized_alias.py -v`, exit 1, 1 test, 29.954 s; mismo ValueError exacto. Log `portal-collapse-red.log`. La prueba negativa adicional conserva el original upstream sin excepción y exige ese rechazo incluso después del fix. Cuatro contratos Python de args/output/config del probe pasan (0.008 s), sin acreditarlos como integración Chromium.

**GREEN:** misma prueba AAPT2 después del fix y del refuerzo negativo, exit 0, **2 passed / 0 failed / 0 skipped**, **344.401 s**. Compilación real de 18 recursos, variantes PNG y WebP con flags Chromium, nombres colapsados y rutas cortas. La configuración upstream sin excepción reproduce el rechazo; configuración corregida pasa; manifest ajeno y seis cambios de vector son rechazados tras optimización. Hash logs RED `9da2fcba3267afa14c37d9ffc1e526d8c20123e27c8beefd98de42ef1a41828e`, GREEN `d773adba4b2f1a6fbd4c06bfaf84cfb1939cb16a904f5a165dc26f9a94dc4c9a`. Reporte de preparación hash `d093e11c507962070dde173850dc2ea265a1d2b0fe939040488d0880f19968d6`.

**Patch:** generación oficial dos veces, exit 0, `cmp` exit 0, 103 archivos. SHA256 patch `69d23d6f75c8b1c73a5577c9927b88710b622657c8214c935b201200a631dac9`, manifest `6a7a9c6c90d7eb30510a2d340feb45ae40247a8344aeef4ef2be6855c039b014`. `check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-36/android.jar`, exit 0; los 103 archivos aplicados y hashes comprobados. Diff-check, Bash, ShellCheck, compileall y actionlint exit 0. La suite integral nueva y AAPT2 GREEN quedan registradas al finalizar, antes de publicar código o dispatch.

**Suite integral final:** `GITHUB_ACTIONS=true GITHUB_REPOSITORY=Jorgeprdz/chromium-dex-arc GITHUB_REF_NAME=assistant/archium-r4-recovery GITHUB_REF=refs/heads/assistant/archium-r4-recovery GITHUB_SHA=2de41680a42972253e8daf4cf818938dacf79a93 GITHUB_RUN_ID=38203819481 ARCHIUM_TEST_GN=/usr/bin/gn ARCHIUM_TEST_NINJA=/workspace/archium-r4-evidence/ninja-query/pinned-arm64/ninja ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar python3 -m unittest discover -s tests -p 'test_*.py' -v`, **exit 0**, **235 passed / 0 failed / 0 skipped**, **714.845 s**. Log `portal-collapse-full-ci-env.log`, SHA256 `7d083ede7635d8b609b5aeb97985ca9fc4f8f800e212801b85e4711f31bd5cfb`. Identidad CI reproducida del run fallido; código ejecutado es el delta local completo que se publica después. Tres perfiles GN reales (arm64/baseline/x64) PASS, negativos de checkpoint/routing/disco y recurso PASS. Esto acredita Python host/fixtures JVM y GN/AAPT2 aislados; el nuevo probe en checkout completo, Robolectric/JNI y APK nuevos siguen bloqueantes dentro de CI.

| Gate previo / nuevo run | Estado | Evidencia o requisito |
|---|---|---|
| STATIC_PASS | PASS | diff-check, Bash, ShellCheck, compileall, actionlint |
| PYTHON_HOST_PASS | PASS | 235/235, sin skips |
| GN_REAL_PASS | PASS | tres escenarios con GN real; GN pin exacto se repite en CI |
| AAPT2 aislado release | PASS | RED/GREEN + variantes PNG/WebP + negativos optimizados |
| AAPT2 real checkout con probe nuevo | PENDING | S2 tras restore, antes de Java/link |
| PATCH_REPRODUCIBILITY | PASS | 103 archivos, dos hashes idénticos y aplicación comprobada |
| CHECKPOINT_METADATA | PASS | API/range/source/pin/expiry/count; no transferencia grande local |
| CHECKPOINT_ALL_BYTES | PENDING | SHA256 de cada fragmento en S1 |
| DISK_PREFLIGHT local | FAIL | insuficiente para restore masivo; no se usa para descargar |
| DISK_PREFLIGHT CI nuevo | PENDING | medición S0 antes de descarga, requisito bloqueante |
| ROBOLECTRIC_PASS nuevo | PENDING_POST_RESTORE | suites reales obligatorias; anterior 605 + 1351 PASS |
| JNI_LINK_PASS nuevo | PENDING_POST_RESTORE | libchrome real y símbolos; anterior PASS |
| APK_VERIFIED nuevo | PENDING | paquete, ABI, recursos/contenido, firma y SHA256 S4 |

### Checkpoint preferido recuperable

`archium-checkpoint-38203819481-1`, source `2de41680a42972253e8daf4cf818938dacf79a93`. API autenticada inventory exit 0, cuatro grupos no expirados, 26510091404 bytes totales (partes comprimidas: 26510082500), fecha mínima de expiración 2026-10-26T05:26:47Z.

| Grupo | Artifact ID | Bytes | SHA256 artifact |
|---|---:|---:|---|
| 00 | 11727898692 | 8589940572 | 29ef26b8c295d1c496418e7bef50d5af21d3ca878845b67850efb477dd4538b0 |
| 01 | 11728410183 | 8589935970 | 6518b8c5f6a048514dbb12f356ace84d5f5b5b60ee7762be2ffe0459520ed870 |
| 02 | 11728395785 | 8589935970 | e0b9c43983fa0ded21bf6e7dd9afb0b012b0300def3ca2dd7af3ee8d32ed8d99 |
| 03 | 11727764299 | 740278892 | d7f8b060cb36ded695571284e858a2bad99f6a205eb2f2186bd92e13e76427f9 |

Manifest obtenido por HTTP Range autenticado, solo 5381 bytes; schema/pin/SHA/tag/workspace y 25 fragmentos validados exit 0. Manifest SHA256 `c9c1ee1436df108c8c3a167bf47980e250ad73123bdf7507eb8c2b476448b02c`. Integridad completa de cada fragmento PENDING_POST_DOWNLOAD, bloqueante S1. Disco local medido 78020317184 bytes / 11623170 inodos, menor que el mínimo 101510091404: **no descarga masiva local**, no eliminación de outputs válidos. CI vuelve a medir capacidad S0 antes de descargar; no reutiliza una medición vieja como garantía de capacidad nueva. Fuentes 38194736077 y anteriores también conservadas.

**Revisión de los fallos repetidos:** los fixes previos avanzaron gates concretos, pero la cobertura dejó diferencias entre host y checkout restaurado, y entre recursos sin optimizar y release. Los tests de routing prueban corte de etapas; no acreditan Java/link/recursos. El porcentaje 2/6 del monitor refleja pasos visibles de Actions, no objetos compilados: en este run los logs demuestran S2/S3 completos y S4 compilado antes del fallo final. No existe garantía de cero fallos desconocidos ni APK verificable todavía. La siguiente ejecución solo procede tras gates baratos verdes, con SHA obtenido directamente de Git, checkpoint compatible reciente y sin otro run activo, conforme a la autorización posterior de corregir/reintentar.

# Archium R4 — reparación y build, 2026-10-11

## Recuperación relanzada: 38203819481 y monitor sesión #5 (2026-10-12 04:26–04:28 UTC)

Fix publicado [**2de41680a42972253e8daf4cf818938dacf79a93**](https://github.com/Jorgeprdz/chromium-dex-arc/commit/2de41680a42972253e8daf4cf818938dacf79a93), commit/push exit 0, suite **230/230**, sin skips, mismo patch/config/toolchain nativo. Nueva fuente **archium-checkpoint-38194736077-1**, source **3c2d5f689ffc9314806c725699778482795f8231**, con libchrome realmente enlazado y guardado. Los hashes/metadata y el primer fallo están en la sección siguiente.

**Error de operación reconocido:** primer dispatch [38203753670](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203753670) envió por copia manual `expected_sha=2de41686ba0588070937c921990a501dce74bc39`, diferente del SHA real `2de41680a42972253e8daf4cf818938dacf79a93`. [Job authorize 114662580978](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203753670/job/114662580978) rechazó `test EXPECTED_SHA = GITHUB_SHA`, exit 1, **04:25:59–04:26:03 UTC**. Log auténtico `gh run view 38203753670 --log-failed`, exit 0, `/workspace/archium-r4-evidence/run-38203753670-sha-guard.log`. Preflight y build no se ejecutaron, sin descarga/checkpoint/compilación. El run quedó FAILED; no se borró ni se convirtió a PASS. La corrección toma SHA directamente de Git y compara el remoto antes del dispatch; no se relajó ninguna puerta.

Dispatch corregido, exit 0:

```bash
archium_dispatch_sha=$(git rev-parse HEAD)
test "$archium_dispatch_sha" = 2de41680a42972253e8daf4cf818938dacf79a93
test "$(git ls-remote origin refs/heads/assistant/archium-r4-recovery | cut -f1)" = "$archium_dispatch_sha"
gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc \
  --ref assistant/archium-r4-recovery -f expected_sha="$archium_dispatch_sha" \
  -f source_checkpoint=archium-checkpoint-38194736077-1 \
  -f source_commit=3c2d5f689ffc9314806c725699778482795f8231 \
  -f source_run_id=38194736077
```

Run [**38203819481**](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203819481), creado **2026-10-12T04:26:56Z**, headSha exacto **2de41680a42972253e8daf4cf818938dacf79a93**. Authorize [114662785000](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203819481/job/114662785000) **SUCCESS**, SHA/branch/concurrencia comprobados. Preflight [114662806609](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38203819481/job/114662806609) **IN_PROGRESS**, iniciado **04:27:05Z**. Monitor observó `Build genuine GN at Chromium DEPS pin` a **04:28:00 UTC**. No se acredita restore/JNI/APK nuevo antes de su ejecución.

Monitor **PID 1904** en **nueva sesión #5** de NewTermux, lanzado por `./m4` después de verificar el shell nativo vacío, sin escribir en Codex u otras apps. Args reales `--run 38203819481 --sha 2de41680a42972253e8daf4cf818938dacf79a93`, existencia y proceso comprobados; screen `/workspace/.archium-install/38203819481/screen.txt`: EN CURSO, elapsed **00:01:04**, **0/6**, ETA N/D. Refresco 600 s, líneas ASCII, colores/bold/italic y últimas tres líneas disponibles; eventos API diferenciados de log aún no publicado. Nueva pantalla DeX lógica **16** identificada antes de abrir la actividad; otras sesiones intactas. Solo descarga/instala ante SUCCESS y APK/SHA/manifest/ABI/Portal/firma verificadas. Se detiene el agente para seguimiento manual por petición del usuario.

**FASE=S0; SHA=2de4168; RUN=38203819481; GATE=AUTHORIZE_PASS/PREFLIGHT_RUNNING; CHECKPOINT=38194736077-1 REMOTE_PRESERVED; DISCO_CI=PENDING_S0; ERRORES_ACTUALES=NONE_OBSERVED; SIGUIENTE=S0→S1→HOST_ANTES_DE_NATIVE→S2/S3/S4/S5 CON GATES.** Los PASS de libchrome/605 Robo/recursos anteriores pertenecen a la fuente recuperable 3c2d5f6. Build actual todavía no terminado, APK nueva NONE, runtime NOT_EXECUTED. Contraseñas propias mantienen estado DEPRECATED.

## Run 38194736077 FAILED: enlace recuperable y entorno Ninja corregido (2026-10-12 04:08–04:24 UTC)

[Run 38194736077](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38194736077), source **3c2d5f689ffc9314806c725699778482795f8231**, terminó FAILED a **04:07:46 UTC**, elapsed **01:57:30**. [Job build 114635793824](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38194736077/job/114635793824). No APK publicada ni instalación. HEAD inicial reparación **6d1be54a571c7f186de88a7ee126e0c8d1cc1193**.

Log final auténtico: `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114635793824/logs`, exit 0, `/workspace/archium-r4-evidence/run-38194736077-latest-build.log`, SHA256 **173f7c5675d7b8e53fc1c9e7c4f930d9099034627aafdbbb3abc192fee84572f**. Primer fallo reportado línea **37961**, `test_query_failure_stops_fanout_and_requests_quiescent_checkpoint`; línea **37970**, causa concreta: wrapper `third_party/ninja/ninja` de la fixture intentó ejecutar `third_party/ninja/python-bin/python3`, inexistente, **exit 127**. Segunda falla, `test_siso_query_uses_pinned_binary_without_writing_incremental_state`, mismo motivo (37982). Suite host S3 **227 tests, 225 passed / 2 failed / 0 skipped**, **174.938 s**, exit 1; gate real corta etapas posteriores (38005).

**CAUSA_CONFIRMADA:** `archium-test-gates.py` fijaba GN, AAPT2 y Android jar pero omitía `ARCHIUM_TEST_NINJA`. En el checkout restaurado, PATH contiene `depot_tools`; las dos fixtures que ejecutan Bash completo seleccionaron su launcher por `shutil.which('ninja')` y lo enlazaron en un directorio sintético. El launcher calcula `python-bin` relativo a su ruta de invocación, produciendo el error observado. En preflight/local se usaba `/usr/bin/ninja` o una variable explícita al binario real, por eso no apareció antes. SHA `bbbb...` pertenece a la fixture, no al código entregado. No fue un fallo de linker ni un build limpio.

### Avance real conservado

| Gate / trabajo | Estado observado y evidencia |
|---|---|
| Restore fuente | PASS, línea 365; download 5m47s, restore/transición 14m44s |
| Ninja query completo | PASS, 25612 manifests, 2840; fix UTF-8 anterior funciona |
| Contraseñas propias | DEPRECATED, flag efectivo false y deps ausentes, 2865 |
| Recursos Portal reales Chromium | PASS, 3044 |
| Java owners actuales | PASS, 37/37 fuentes y 8 acciones reales, 3045 |
| Recursos / Java / JUnit | Build Succeeded: 75 / 104 / 731 pasos, 3042/3282/4774 |
| Robolectric temprano | PASS, nueve grupos, 605 ejecuciones, 37572 |
| `libchrome` real | Build Succeeded: **137 pasos**, **21m57.14s**, 37877; Siso `skip:131650` |
| Linker | SOLINK entre 03:04:04 y 03:22:23, **18m17.65s**, 37876; ningún fallo ld.lld |
| JNI symbols reales de APK | **PASS**, 37878, library real + llvm-nm |
| Host S3 / Robolectric ampliado / APK | Host FAIL; Robolectric ampliado y APK NOT_EXECUTED |
| Checkpoint nuevo | staged **25 partes**, 38007; cuatro grupos publicados SUCCESS |

El log parcial obtenido mientras corría terminaba a las 03:00. El log final demuestra que después hubo trabajo efectivo de enlace, no un atasco confirmado. Una parte importante del elapsed tras fallar correspondió a empaquetar y publicar el checkpoint: **03:25:36→03:58:24**, luego uploads hasta **04:05:15**. El tiempo sin APK fue real; los outputs de compilación quedaron guardados.

### Fix mínimo, regresión y detección temprana

`archium-test-gates.py` valida y fija el Ninja genuino del checkout (`third_party/ninja/ninja`), imprime su versión y propaga `ARCHIUM_TEST_NINJA` a toda la suite host. Agrega modos explícitos `host-preflight` y `robolectric`; `host` conserva ambos para compatibilidad. Python/SDK/GN ejecutan antes del primer trabajo nativo, bajo el PATH restaurado; las mismas once suites Robolectric siguen bloqueantes en S3 después de sus outputs. Ningún test crítico se convierte a skip ni se acredita Robolectric por mocks.

Regresión real: el test ejecuta las dos pruebas que fallaron con un launcher en PATH que reproduce el cálculo de `python-bin`; dependencia SDK/Robo se simula explícitamente y no acredita integración Chromium. RED **exit 1**, dos fallas internas con el mismo **127**; GREEN **2/2 outer tests**, exit 0, **7.138 s**, con Ninja CIPD genuino 1.12.1. Logs `ninja-query/host-ninja-{red,green}.log`, SHA256 RED **485db8366c420789aaafaa798df332ee2b93014ce7832bdea7363131dc702b6c**, GREEN **857d59481db99b5a0e9237047b20fa5299d2fa2656803dfdc28541b9a322d250**.

Bash: `host-preflight` se ejecuta antes de `chrome_public_apk__compile_resources`, Java, JUnit y libchrome. Prueba negativa RED **exit 1 / 3.832 s**, mostró cuatro comandos nativos antes del fallo host; tras moverlo GREEN **exit 0 / 2.941 s**, ningún comando nativo. Si ese gate temprano falla sin trabajo nativo nuevo, conserva el checkpoint fuente remoto y no empaqueta otra copia idéntica: regresión RED **exit 1 / 3.070 s**, GREEN **exit 0 / 2.916 s**, ningún pack. El timeout conserva exit 124; no ejecuta APK. Los gates posteriores conservan guardado quiescente y el primer exit code. Regresión adicional: fallo de Robolectric final sigue bloqueando APK tras libchrome.

Suite integral final **230 passed / 0 failed / 0 skipped**, **443.856 s**, **exit 0**, identidad CI real y herramientas GN/Ninja/AAPT2/SDK auténticas. Log `/workspace/archium-r4-evidence/ninja-query/pinned-host-full-ci-env.log`, SHA256 **472406603d4f6bfb8949e4e1e4dca301b0e5a034a2f75cbb8e6fb19d82f9564a**. Durante esa suite se fortaleció la regresión para prohibir repack temprano; esa aserción nueva se ejecutó también separadamente RED/GREEN con los valores anteriores. El resto de la suite ejercitó el Bash actualizado. Comando:

```bash
GITHUB_ACTIONS=true GITHUB_REPOSITORY=Jorgeprdz/chromium-dex-arc \
GITHUB_REF_NAME=assistant/archium-r4-recovery GITHUB_REF=refs/heads/assistant/archium-r4-recovery \
GITHUB_SHA=3c2d5f689ffc9314806c725699778482795f8231 GITHUB_RUN_ID=38194736077 \
ARCHIUM_TEST_GN=/usr/bin/gn \
ARCHIUM_TEST_NINJA=/workspace/archium-r4-evidence/ninja-query/pinned-arm64/ninja \
ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 \
ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar \
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Static gates diff-check/Bash/ShellCheck/compileall/actionlint exit 0. Doble generación oficial 102 files, hashes idénticos y **sin cambios**: patch **e757f5723d2f199a658c50039355009af217b118da977c4a34f0a012bc93aa66**, manifest **9f848493ea7e5e1c2a223959fe9f1de9a9d649c109de9d01bb37085b03bdd621**. No cambiaron fuentes Chromium, GN args, toolchain, pin, iconos o la exclusión DEPRECATED de contraseñas. Se puede reutilizar el delta compilado; la siguiente corrida todavía debe comprobar sus gates reales y APK, sin prometer recompilación cero.

### Fuente preferida: checkpoint 38194736077

**archium-checkpoint-38194736077-1**, source **3c2d5f689ffc9314806c725699778482795f8231**. Metadata actual no expirada, expiración **2026-10-26 03:58–04:05 UTC**.

| Grupo | Artifact ID | Bytes | SHA256 artifact |
|---|---:|---:|---|
| 00 | 11726002555 | 8589940572 | 07a24b19d409254cd6ebabb07fb12417a9babe0468df7d162873b9c4d0ed3c54 |
| 01 | 11725893252 | 8589935970 | 7f4bd37269156e6e5ae427fb202598b8a94abff5ec8a1d1929e48f4e78e45562 |
| 02 | 11725743633 | 8589935970 | e2f00c9975c8bf34e1e08ef4440e85a2117cba8f8fd394986bddacfdd36ca535 |
| 03 | 11725893432 | 377020333 | 5c7f1f0e7f099130a9d09523d6f5a83f92f3d2b5e58e58fc8d928308dbb463c0 |

Total **26146832845 bytes**. Lectura autenticada HTTP Range solo **5381 bytes**, manifest hash **ed7c5b5a10e62aae873f8864bb3de781e7dbf3935b8cb0840c7987ea925cb4d0**, schema/pin/source/tag/workspace/count **PASS**, exit 0; integridad de cada fragmento **PENDING_POST_DOWNLOAD** bloqueante S1. No descarga masiva local: **78479921152 bytes / 11624247 inodos** observados; umbral **101146832845 bytes**, local FAIL, CI debe medir su disco S0 antes de transferir. Fuente anterior y remoto nuevo no se borran. Ninguna corrida concurrente/en cola antes de publicación; protegido/main mantienen sus SHA.

Estado de esta reparación: host/static/patch PASS; metadata/remoto PASS; integridad completa/restore nuevo/Robolectric ampliado/APK/runtime pendientes. Nueva corrida autorizada por la instrucción posterior de corregir/reintentar; se publicará solo el fix probado y se fijará SHA exacto antes del dispatch.

## Run nuevo y monitor activo: 38194736077 (2026-10-12 02:10–02:12 UTC)

Publicación verificada, commits y push exit 0:

- [8a8e00e8a59c29d9ec165f153893e20461b645e8](https://github.com/Jorgeprdz/chromium-dex-arc/commit/8a8e00e8a59c29d9ec165f153893e20461b645e8): lectura/manifiesto/stdout/stderr de Ninja preservan bytes, sin imponer UTF-8.
- [3c2d5f689ffc9314806c725699778482795f8231](https://github.com/Jorgeprdz/chromium-dex-arc/commit/3c2d5f689ffc9314806c725699778482795f8231): contraseñas propias **DEPRECATED**, owners propios condicionados fuera del build, settings estándar, gates sobre biblioteca real APK, consulta adelantada y regresiones.

HEAD inicial de esta reparación `d0274c8c0e43f6cf85a523099e8c608455eaa407`; SHA de código probado/push/run **3c2d5f689ffc9314806c725699778482795f8231**. El commit posterior de este registro solo añade documentación y no cambia el SHA fijado del run. Rama activa exclusiva `assistant/archium-r4-recovery`; protegido y main comprobados sin cambios después del dispatch. Suite **227/227**, 0 fallas/0 skips, exit 0; detalles, comandos y hashes en la sección siguiente.

Dispatch manual real, exit 0, una sola llamada (no repetida):

```bash
gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc \
  --ref assistant/archium-r4-recovery \
  -f expected_sha=3c2d5f689ffc9314806c725699778482795f8231 \
  -f source_checkpoint=archium-checkpoint-38186699186-1 \
  -f source_commit=d69a14e7e698c4dc125cada4b4f490c177fb3069 \
  -f source_run_id=38186699186
```

Run [**38194736077**](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38194736077), creación **2026-10-12T02:10:16Z**, event `workflow_dispatch`, headSha exacto **3c2d5f689ffc9314806c725699778482795f8231**. Authorize [114634801002](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38194736077/job/114634801002) **SUCCESS**: SHA/branch y concurrencia comprobados. Preflight [114634827696](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38194736077/job/114634827696) **IN_PROGRESS**, iniciado 02:10:27Z; monitor observó `Build genuine GN at Chromium DEPS pin` a **02:12:32 UTC**. Todavía no se acredita restore nuevo, JNI, APK o runtime. No hay artefacto APK nuevo.

Monitor nativo iniciado mediante **./m4** en una **nueva sesión #4** de NewTermux; PID genuino **15334**, argumentos `--run 38194736077 --sha 3c2d5f689ffc9314806c725699778482795f8231` verificados en proceso. Evidencia local `/workspace/.archium-install/38194736077/r4-monitor.pid` y `screen.txt`: EN CURSO, elapsed **00:02:16**, **0/6** fases completadas, ETA **N/D**, eventos API identificados explícitamente porque log activo no está publicado. Refresco **600 s**, líneas ASCII continuas/separadores, colores, bold/italic; descarga/instalación automática exclusivamente con SUCCESS y reporte/SHA/recursos/firma/ABI verificados. Se conserva el monitor viejo y las otras sesiones. DeX estaba desconectado (solo display 0); se usó la actividad nativa normal del teléfono para crear el shell. Un intento de traer la actividad volvió a seleccionar la sesión Codex: se corrigió seleccionando el shell nuevo antes de escribir, sin repetir dispatch. El monitor queda en ejecución aunque el usuario use otras apps; agente se detiene para monitoreo manual conforme a su instrucción.

**FASE=S0; SHA=3c2d5f6; RUN=38194736077; GATE=AUTHORIZE_PASS/PREFLIGHT_RUNNING; CHECKPOINT=38186699186-1 REMOTE_PRESERVED; DISCO_CI=PENDING_S0; ERRORES_NUEVOS=NONE_OBSERVED; SIGUIENTE=S0→S1→S2→S3→S4→S5 SOLO SI GATES PASS.** Contraseñas propias=DEPRECATED/OUT_OF_SCOPE; APK/JNI/runtime nuevos=NOT_EXECUTED. Esta entrega de código y monitor no se presenta como BUILD_PASS ni como APK terminada.

## Fallo 38186699186 y retirada de contraseñas propias (2026-10-12)

Run [38186699186](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38186699186), source `d69a14e7e698c4dc125cada4b4f490c177fb3069`, FAILED. Authorize y preflight SUCCESS. [Job 114611828079](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38186699186/job/114611828079), primera falla auténtica línea **36867**: `NINJA_QUERY=FAIL: 'utf-8' codec can't decode byte 0xc3 in position 1253: invalid continuation byte`; gate exit **1**, etapas posteriores bloqueadas. El enlace/compilación anterior terminó `Build Succeeded: 12 steps` en línea 36866. Recursos reales Chromium PASS (2998); nueve suites tempranas de Robolectric PASS (36814, 605 ejecuciones agregadas); JNI `llvm-nm`, S3 y APK NO EJECUTADOS. No se acredita la entrega como exitosa.

Log descargado por `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114611828079/logs`, exit 0, SHA256 `f1402c0d434565e9c0942ccdc210d727f873fc78cf7b96d9f1fecbbae724a7d6`; archivo local `/workspace/archium-r4-evidence/run-38186699186-build.log`.

**CAUSA_CONFIRMADA:** el helper nuevo imponía UTF-8 tanto al leer manifiestos (`read_text`) como al capturar stdout/stderr (`text=True`). Una fixture válida con byte `c3 28` falla exactamente con el mismo diagnóstico, mientras el Ninja genuino fijado acepta el grafo. El log CI no incluye traceback/nombre de archivo: el manifiesto específico y la llamada exacta que disparó la excepción quedan **NO_VERIFICABLE**, sin inventarlos. Esta diferencia no impide reproducir el defecto de la interpretación UTF-8.

Regresión RED: seis tests, dos FAIL, exit 1, 13.675 s (`ninja-query/utf8-red.log`). Después se agregó el requisito de consultar antes de toda compilación: tres FAIL, exit 1, 14.051 s (`utf8-early-red.log`). Fix: parsear únicamente directivas ASCII sobre bytes, `os.fsdecode` para comprobar rutas preservando los bytes, subprocess binario y reporte binario idéntico a stdout real; stderr completo conserva bytes y exit code. No usar `ignore`/`replace`, no limpiar logs ni alterar outputs restaurados. Se adelantó la consulta al inicio S2, antes de fanout/Robolectric. GREEN inicial: **6/6**, exit 0, 7.255 s (`utf8-green.log`), Ninja CIPD 1.12.1 real y GN real; incluye error real en include inexistente, target inexistente, rechazo de escapes y preservación exacta de bytes/mtime.

### Cambio de alcance explícito: DEPRECATED

Durante esta reparación el usuario corrigió el alcance: «solo contraseñas» y «ya queda deprecated». Se registró en [ARCHIUM_CONTRASENAS_DEPRECATED.md](ARCHIUM_CONTRASENAS_DEPRECATED.md), spec y plan. Sustituye el requisito anterior de habilitar el gestor propio y sus targets nativos. No es un skip ni test retirado acreditado como PASS.

Cambios acotados: `config/archium-args.gn` flag false; Java/JNI/CSV y puente nativo propios solo se incorporan cuando el flag true (actualmente prohibido por gate); settings usa las rutas originales Chromium; Arc abre autofill estándar. Se conservan fuentes y pruebas históricas. El workflow exige el flag efectivo false y ausencia de los targets propios en dependencias reales de APK; Java preflight separa cinco fuentes explícitamente DEPRECATED y falla si cualquier acción javac aún las compila. Se reemplazan gates nativos propios por `//chrome/android:libchrome`, target real usado por el template upstream de `chrome_public_apk`; payments owner y comprobación de símbolos continúan bloqueantes. No se desactiva pagos, ni se ocultan undefined symbols. UI Arc, colores, DeX, iconos y pin no cambian.

RED de exclusión: GN genuino arm64/x64 mostraba flag true y routing todavía compilaba targets propios (3 fallas, además del gate aún no implementado). Después del cambio, **3/3** pruebas de deprecación pasan (6.956 s, exit 0); **6/6** pruebas de selección Java pasan (0.082 s, exit 0), incluidas ausencia de cobertura ficticia y rechazo de fuente retirada aún compilada. Un primer intento local de routing encontró seis fallas por un nombre incorrecto de la biblioteca en la fixture; se corrigió esa fixture. Dos ejecuciones parciales compartieron por error el mismo archivo de log; ese archivo **NO se usa como evidencia final**. La suite integral final usa un log independiente.

### Checkpoint más reciente conservado

El guardado tras falla sí se ejecutó: línea 36870 `ACTIONS_CHECKPOINT_STAGED=PASS parts=24`; uploads 00/01/02 SUCCESS. Fuente preferida próxima: **archium-checkpoint-38186699186-1**, source **d69a14e7e698c4dc125cada4b4f490c177fb3069**.

| Grupo | Artifact ID | Bytes | SHA256 artifact |
|---|---:|---:|---|
| 00 | 11720954154 | 8589940404 | 75667b6ba242b835212024282011e40ebb0c430741cef2e12a9cb23ee205c03d |
| 01 | 11721956194 | 8589935970 | 78ace732e1c3fbf92d4e1eee1959f29dff97f152a13bcfd670059310f80b8acf |
| 02 | 11722036029 | 8431166172 | 36387a47251ba0d10673df8803247ee401a705fcfb348ebff444d0e9885aa40e |

Metadata API observada: tres grupos, no expirados, expiración **2026-10-26 01:28–01:30 UTC**. Total **25611042546 bytes**. Lectura remota autenticada HTTP Range de solo **5213 bytes**, manifest hash **42dc50aa458bedaacf72cc75f4476feb6ab3e90f8646546429fef32846c640fd**; schema/tag/source/pin/workspace/count validados con el mecanismo oficial, exit 0. Integridad de cada fragmento **PENDING_POST_DOWNLOAD**, bloqueante S1. No se descargaron 25 GB localmente: disco local observado **79619993600 bytes**, **11630340 inodos**, FAIL para descarga masiva (requiere **100611042546 bytes**). El runner CI mide su propio disco en S0 antes de transferir; no se bajó ningún umbral. Cambiar el flag requiere GN gen y recompilar delta; no clean fallback y remoto íntegro preservado.

Static gates (`gn format --dump-tree=json` en ambos BUILD editados, Bash/ShellCheck, compileall, actionlint, diff-check), exit 0. Generador oficial dos veces, 102 files, SHA idénticos: patch **e757f5723d2f199a658c50039355009af217b118da977c4a34f0a012bc93aa66**, manifest **9f848493ea7e5e1c2a223959fe9f1de9a9d649c109de9d01bb37085b03bdd621**. `check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-36/android.jar`, exit 0; API/stubs y pruebas históricas NO acreditan Robolectric/JNI/contraseñas de APK. Monitor: 4 pruebas fases + 3 pruebas primer fallo/caché, exit 0.

Suite host integral final: **227 passed / 0 failed / 0 skipped**, **574.606 s**, exit **0**. Log independiente `/workspace/archium-r4-evidence/ninja-query/deprecated-full-host-ci-env.log`, SHA256 **3e2ece22cd7ca1d79ea270429c09ad08d063c674ad24477a7c8a13f0528f828b**. Comando real:

```bash
GITHUB_ACTIONS=true GITHUB_REPOSITORY=Jorgeprdz/chromium-dex-arc \
GITHUB_REF_NAME=assistant/archium-r4-recovery \
GITHUB_REF=refs/heads/assistant/archium-r4-recovery \
GITHUB_SHA=d69a14e7e698c4dc125cada4b4f490c177fb3069 GITHUB_RUN_ID=38186699186 \
ARCHIUM_TEST_GN=/usr/bin/gn \
ARCHIUM_TEST_NINJA=/workspace/archium-r4-evidence/ninja-query/pinned-arm64/ninja \
ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 \
ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar \
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

| Gate nuevo | Estado | Alcance real / prueba pendiente |
|---|---|---|
| STATIC_PASS | PASS | GN parser de ambos BUILD, Bash/ShellCheck, compileall, actionlint, diff-check |
| PYTHON_HOST_PASS | PASS | 227/227 sin skips; fronteras de routing explícitamente simuladas |
| GN_REAL_PASS media | PASS | Tres perfiles genuinos con contexto acotado, no GN completo Chromium |
| Contraseñas DEPRECATED | LOCAL_PASS / PENDING_CI_GRAPH | GN arm64/x64 flag false; APK deps y javac owners completos bloqueantes S2 |
| Ninja query UTF-8 | PASS_ACOTADO / PENDING_CI_GRAPH | Bytes y stderr reales Ninja, logs/mtime preservados; grafo completo tras restore |
| Patch reproducible | PASS | Generación oficial doble, aplicación/hash en check-arc-preparation |
| AAPT2_REAL_RESOURCES nuevo SHA | PENDING_POST_RESTORE | Fixtures reales PASS; merge Chromium nuevo SHA aún no ejecutado |
| ROBOLECTRIC_PASS nuevo SHA | PENDING_POST_RESTORE | Suite Chromium ejecutará en S2/S3; 605 anteriores solo acreditan source d69 |
| JNI_LINK_PASS nuevo SHA | PENDING_POST_RESTORE | Enlace real libchrome + llvm-nm antes de APK, sin ejecutar aún |
| Checkpoint metadata/read/manifest | PASS | Tres grupos y lectura autenticada acotada; SHA256 partes bloqueante S1 |
| DISK_PREFLIGHT | LOCAL_FAIL / CI_PENDING_S0 | No descarga masiva local; CI medirá bytes/inodos antes de descargar |
| APK_VERIFIED / runtime | NOT_EXECUTED | Ninguna APK nueva, no instalación |

Preflight histórico run 38186699186: **220/220 en 200.403 s**, job114610468261 SUCCESS, log SHA256 **b9787937de0b235ad6fb0bd58c16008688f0f69b6372372c2c6cd686e2cf1a15**. Nueva fuente tiene los outputs realmente compilados, pero cambio de flag obliga a GN gen/recompile delta. Autorización posterior vigente: corregir y relanzar tras los gates sin otra pregunta. Ninguna corrida activa/en cola observada antes de publicación; protegido `51e5ed429661727156ab2534caac99a82ee9264b` y main `6274c653bbe3992403a89b1531d0c1f91646bf6d` sin cambios.

Referencia upstream leída de la revisión fijada: `chrome/android/BUILD.gn:3399` declara `libchrome`; [chrome_public_apk_tmpl.gni](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/chrome_public_apk_tmpl.gni) usa esa biblioteca y su registro JNI (558–561). `chrome_common_shared_library.gni` y `third_party/jni_zero/jni_zero.gni` se descargaron acotadamente del mismo pin para confirmar que se mantiene el target JNI genuino, no un ejecutable inventado. Los gates sobre checkout completo nuevo y su APK siguen pendientes CI.

## Nuevo run observado: 38186699186 (2026-10-12 00:05:37 UTC)

Fix publicado: [d69a14e7e698c4dc125cada4b4f490c177fb3069](https://github.com/Jorgeprdz/chromium-dex-arc/commit/d69a14e7e698c4dc125cada4b4f490c177fb3069), `fix(build): isolate Ninja query from Siso output state`. Commit y push exit 0; comparación remota anterior `a92735a7a7d8db1808d9d43a39f20389617b02a9`, sin cambios concurrentes. Suite host actual 220/220 exit 0, cuatro regresiones de query con GN/Ninja genuinos y tres regresiones del monitor PASS. Ningún cambio Java/GN/iconos/pin/patch. Ramas protegida y main conservan sus SHA anteriores.

Dispatch real, exit 0: `gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc --ref assistant/archium-r4-recovery -f expected_sha=d69a14e7e698c4dc125cada4b4f490c177fb3069 -f source_checkpoint=archium-checkpoint-38165289963-1 -f source_commit=dcbd868ea42ffd0991c01c2872adce01316a9768 -f source_run_id=38165289963`. API confirma [run 38186699186](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38186699186), SHA fuente **d69a14e7e698c4dc125cada4b4f490c177fb3069**, branch `assistant/archium-r4-recovery`, `in_progress`. No otros runs nativos en curso/cola antes del dispatch. Checkpoint fuente tres grupos no expirados, tamaños y digests originales intactos.

[Authorize 114610449118](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38186699186/job/114610449118) SUCCESS, guards SHA/concurrencia. [Preflight 114610468261](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38186699186/job/114610468261) en curso. Estado de este snapshot: `BUILD_STAGE=S0`, `BUILD=INCOMPLETE`, `APK_PACKAGE=NONE`, `APK_SHA256=NONE`, `APK_ARTIFACT=NONE`, `ANDROID_RUNTIME=NOT_EXECUTED`. Los PASS de recursos y 605 ejecuciones Robolectric inferiores corresponden al run anterior fallido; deberán volver a bloquear la ejecución nueva en sus etapas.

Monitor confirmado en sesión nativa Termux **#4**, PID `2866`, comando exacto `/usr/bin/python3 /workspace/macdesk-maintenance/archium-r4-monitor.py --run 38186699186 --sha d69a14e7e698c4dc125cada4b4f490c177fb3069`. Launcher habitual actualizado, `bash -n` exit 0; inició con shortcut `./m4`. Archivo `/workspace/.archium-install/38186699186/screen.txt` observado UTC `00:08:39`: run EN CURSO, elapsed `00:03:02`, ETA N/D, actividad GN real, 0/6 fases completadas. Pantalla nativa confirma separadores con colores, bold/italic y tres eventos API identificados. Refresco 600 s; APK solo se descarga/instala tras success y hashes/package/ABI/firma/Portal verificados. No nueva instalación en este snapshot. Se detiene el trabajo interactivo tras confirmar el monitor, conforme a la orden de monitoreo manual; autorización persistente de fix y retry sigue registrada.

## Fallo S2 observado en 38180906742: diagnóstico Ninja sobre estado Siso

[Run 38180906742](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38180906742), source SHA `f84a0998b4af4d0a5c06a6f2b339e82f7c1f1f1f`, FAILED. [Job 114594471563 build/build](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38180906742/job/114594471563), primer error auténtico líneas 27328–27332: `depot_tools/ninja.py: out/Archium contains Siso state file.`, exit 1. El paso de compilación inmediatamente anterior terminó `Build Succeeded: 12 steps` (línea 27326). Las líneas finales de cleanup/Node deprecation que mostraba el monitor no eran la causa del fallo.

**CAUSA_CONFIRMADA:** `scripts/build-archium-recovery.sh` llamaba `ninja -C out/Archium -t query archium_password_manager_tests` desde PATH, que seleccionaba el wrapper de depot_tools. Se leyó `ninja.py` del pin real `8a5434051036b32412a2ecb10c213a72e3f3ccb9`: su whitelist de herramientas no incluye `query`; `check_out_dir()` rechaza `.siso_deps` antes de ejecutar Ninja. Se ejecutó esa función upstream auténtica sobre una fixture diminuta y devolvió exit 1 con el mismo diagnóstico. No se ejecutó la sugerencia upstream de `gn clean`.

Evidencia completa: `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114594471563/logs` exit 0, log local `/workspace/archium-r4-evidence/run-38180906742-build.log`, SHA256 `c213b636c4b39fad6df368f594e69620f4d5cca3143c2fc2140cb34a2fb10435`. Preflight job `114593098065` SUCCESS: 216 passed, 0 failed, 0 skipped en 196.311 s; log SHA256 `bb136478e427f312fb8b433ec9c58a8a85586763a9e0f633085f451334a28a09`.

### Gates auténticos observados antes del fallo

| Gate | Estado | Evidencia del build log |
|---|---|---|
| Disco CI antes de transferir | PASS | línea 293: 115531063296 bytes, 18975266 inodos libres |
| Integridad/restore checkpoint | PASS | líneas 364–365, restore valida SHA256 de todas las partes antes de extraer |
| Transición y GN real | PASS | línea 2812, mtimes preservados; línea 2815, 93144 targets / 4922 files |
| Disco posrestore/preparación | OBSERVED | línea 2817: 52637491200 bytes libres; 17268484 inodos |
| Media/GN check | PASS | bloque 2842–2869, effective args reales y Header dependency check OK |
| Recursos reales Chromium | PASS | línea 2997: `AAPT2_REAL_RESOURCES=PASS scope=Chromium_merged_manifest_resource_target` |
| Java owners | PASS | línea 2998: 42/42 sources, 11 javac actions |
| Robolectric Chromium temprano | PASS | nueve grupos: 9+14+6+6+4+2+294+208+62 = 605 ejecuciones; línea 27272 PASS |
| Targets password/login | BUILD_SUCCEEDED | línea 27326; verificación `llvm-nm` posterior todavía NOT_EXECUTED |
| JNI symbols / S3 / APK / runtime | NOT_EXECUTED | query falló antes de esos gates; ninguna APK nueva |

API artifacts del run: `total_count=0`. No se publicó un checkpoint nuevo; el runner efímero ya terminó. La fuente `archium-checkpoint-38165289963-1` conserva sus tres grupos remotos no expirados. El próximo run restaurará esa fuente compatible; no hay clean fallback. Este registro no convierte el run FAILED en PASS.

### Reparación con preservación demostrada del output

La primera regresión RED ejecutó el Bash real con la frontera del wrapper que reprodujo su rechazo, exit 1; dos tests fallaron. Una primera prueba con el binario Ninja directo detectó además que `-t query` puede borrar un `.ninja_log` inválido. Por eso se descartó consultar el output restaurado directamente: no se debilitó la prueba ni se alteraron logs del checkout real.

Fix final: `scripts/archium-ninja-query.py` copia **solo manifiestos `.ninja`** a una carpeta temporal independiente y ejecuta allí el `third_party/ninja/ninja` del checkout fijado. No copia ni abre `.ninja_log`, `.ninja_deps`, `.siso_deps` originales para escritura; no ejecuta compilación. Rechaza includes/builddir que escapen del snapshot. El Bash comprueba el binario antes del fanout y usa el helper como gate; un fallo de query corta las siguientes etapas y solicita checkpoint después de los builds ya quiescentes. Se conservan errores, versión del toolchain y backend Siso.

Pruebas nuevas: consulta real y preservación de bytes/mtime; target inexistente bloquea fanout y solicita pack; manifiestos producidos por GN real funcionan con Ninja real; rutas de logs/includes fuera de snapshot se rechazan. Ninja usado en verificación local proviene del paquete CIPD que exige DEPS: `infra/3pp/tools/ninja/linux-arm64`, `version:3@1.12.1.chromium.4`, binario `1.12.1`. Download acotado 2814884 bytes, SHA256 ZIP `6f7c6cc12315c80e1ab819def849c5b68c0cf65504bb36cd438ac4f6325350bb`; no cambio de toolchain en Chromium. Comando `ARCHIUM_TEST_NINJA=/workspace/archium-r4-evidence/ninja-query/pinned-arm64/ninja ARCHIUM_TEST_GN=/usr/bin/gn python3 -m unittest discover -s tests -p test_recovery_ninja_query.py -v`, exit 0, **4/4 en 9.704 s**. Logs `ninja-query/regression-red.log`, `regression-green.log`, `pinned-gn-green.log`.

Monitor local: nueva regresión con el log auténtico FAILED antes del fix porque mostraba cleanup; tras reconocer el prefijo del wrapper devuelve `PRIMER ERROR REAL` y `Siso state file`. Tres tests pasan, exit 0 en 0.393 s (`ninja-query/monitor-{red,green}.log`). No cambia el criterio de descarga/instalación.

Static gates diff/Bash/ShellCheck/compileall/actionlint exit 0. Patch oficial regenerado dos veces, 102 files, hashes idénticos y ningún diff: patch `bcc1fa363379e9851da4ef7d2611aadfaf604064dcfb21ec51cc5b0bb9c55e75`, manifest `b5fbe0b0169636108a5bc84ac52aaf6020f6cfb048fee92f2b2ce9998b8f0f84`. Java, identidad Portal y GN/JNI quedan sin cambios.

Suite host integral terminada: **220 passed / 0 failed / 0 skipped**, 451.807 s, exit **0**. Comando bajo identidad CI real; los probes GN/Ninja/AAPT2/JVM usan herramientas auténticas:

```bash
GITHUB_ACTIONS=true GITHUB_REPOSITORY=Jorgeprdz/chromium-dex-arc \
GITHUB_REF_NAME=assistant/archium-r4-recovery \
GITHUB_REF=refs/heads/assistant/archium-r4-recovery \
GITHUB_SHA=f84a0998b4af4d0a5c06a6f2b339e82f7c1f1f1f GITHUB_RUN_ID=38180906742 \
ARCHIUM_TEST_GN=/usr/bin/gn \
ARCHIUM_TEST_NINJA=/workspace/archium-r4-evidence/ninja-query/pinned-arm64/ninja \
ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 \
ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar \
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Los tests de routing siguen simulando sus fronteras nativas explícitamente; solo los probes declarados ejecutan herramientas reales. Log `/workspace/archium-r4-evidence/ninja-query/full-host-ci-env.log`, SHA256 `47b8b3f87c3afe5f1d653efa08be1b22618e8238793a47ab93e02a8c7c4f3812`. Nueva corrida autorizada tras publicación del fix; todavía no se afirma APK PASS. Antes de publicar, HEAD remoto `a92735a7a7d8db1808d9d43a39f20389617b02a9`, rama protegida y main intactas; ninguna corrida en curso o en cola. Fuente checkpoint completa conservada.

## Autorización renovada y nuevo dispatch: run 38180906742

Orden posterior del usuario: «cada que tengamos runs fallidos aplica fix y manda el run inmediatamente». Esta autorización sustituye el límite anterior de una sola corrida y la necesidad de pedir permiso tras cada fallo. Se conservan la verificación del fix, gates bloqueantes, ausencia de compilaciones concurrentes, checkpoints compatibles, límite de slices, prohibición de clean fallback y ramas protegidas. No se convierte un run fallido en PASS ni se despacha sin una reparación respaldada por evidencia.

Run real [38180906742](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38180906742), creado `2026-10-11T22:33:38Z`, source SHA **f84a0998b4af4d0a5c06a6f2b339e82f7c1f1f1f**, rama `assistant/archium-r4-recovery`, workflow `374835814` (`baseline-build.yml`). Comando real, exit 0:

```bash
gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc \
  --ref assistant/archium-r4-recovery \
  -f expected_sha=f84a0998b4af4d0a5c06a6f2b339e82f7c1f1f1f \
  -f source_checkpoint=archium-checkpoint-38165289963-1 \
  -f source_commit=dcbd868ea42ffd0991c01c2872adce01316a9768 \
  -f source_run_id=38165289963
```

Antes del dispatch: árbol limpio, HEAD local/remoto iguales; ningún run in_progress o queued. Tres grupos checkpoint unexpired con tamaños/digests intactos. `feat/arc-desktop` sigue `51e5ed429661727156ab2534caac99a82ee9264b`; `main` sigue `6274c653bbe3992403a89b1531d0c1f91646bf6d`. Fix preflight publicado y suite integral 216/216 exit 0 bajo identidad CI real (registro inferior).

Snapshot observado por API: `RUN=in_progress`, `BUILD_STAGE=S0`, `BUILD=INCOMPLETE`. Job [114593069927 authorize](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38180906742/job/114593069927) SUCCESS, SHA y concurrencia comprobados. Job [114593098065 preflight](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38180906742/job/114593098065) en curso, construcción GN real. No se declara restore/JNI/ChromeJUnit/APK PASS. El SHA del run permanece fijado; este registro posterior solo cambia documentación.

Monitor arrancado en nueva sesión nativa Termux **#3**, launcher `/data/data/com.termux/files/home/archium-r4-monitor-termux.sh` actualizado con RUN/SHA exactos. Se usó un shortcut local `./m4` para evitar introducir una ruta larga mientras cambia el foco de DeX. PID observado `26006`: `/usr/bin/python3 /workspace/macdesk-maintenance/archium-r4-monitor.py --run 38180906742 --sha f84a0998b4af4d0a5c06a6f2b339e82f7c1f1f1f`. `bash -n` launcher exit 0. Archivo real `/workspace/.archium-install/38180906742/screen.txt`, UTC 22:37:33: run EN CURSO, elapsed 00:03:55, ETA N/D, 0/6 fases completadas; actividad suite host CI. GN real e instalación SDK ya completados en API. Refresco 600 s; líneas de color, bold/italic, tres eventos API explícitamente etiquetados hasta publicación del log. Mantiene descarga/instalación condicionadas a éxito y verificación de APK; ningún APK descargado ni instalado en este snapshot.

## Resultado observado: run 38177451098 FAILED en S0

Este apartado sustituye el estado provisional del snapshot de dispatch inferior. La API confirma [run 38177451098](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38177451098) terminado con `failure`, source SHA `0514027dd41ddb568d033152c8faec76a388ba84`. La autorización de SHA y concurrencia pasó en job `114582731650`. El job [preflight 114582753899](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38177451098/job/114582753899) falló en `Execute complete host suite and JVM API probes`: 215 tests en 154.941 s, 192 passed, 23 failed, 0 skipped. El job build `114583898229` quedó skipped, sin steps. La API de artifacts devuelve `total_count=0`. No hubo descarga del checkpoint, restore, compilación nativa, APK ni instalación.

**CAUSA_CONFIRMADA:** las fixtures de `tests/test_build_routing.py` copiaban `os.environ`, fijaban un SHA ficticio pero heredaban `GITHUB_REF_NAME=assistant/archium-r4-recovery` del job real. El dispatcher de `scripts/build-archium.sh` elegía correctamente el runner nuevo por esa rama; su protección rechazaba el SHA ficticio. Las 23 fallas pertenecen a estas fixtures antiguas. El SHA del dispatch real era correcto; no es un fallo demostrado de compilación Chromium.

Brecha de validación previa: las pruebas locales anteriores no se ejecutaron con la rama ambiental de Actions, por lo que sus resultados no detectaron esta contaminación. La repetición local de la suite reparada fija ahora esa identidad real además de GN y SDK reales; sigue siendo una comprobación host local, no un nuevo PASS de GitHub Actions.

Evidencia auténtica: `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114582753899/logs` exit 0, archivo local `/workspace/archium-r4-evidence/run-38177451098-preflight.log`, SHA256 `5fc0cdf10406e52b3f9a3657984151a69284e63c4cac679a2fc2160d3c0a94d9`. Primera falla línea 719; detalle líneas 947–952, `test_changed_args_force_gn_even_for_current_checkpoint`, test source línea 274: `AssertionError: 2 != 0 : Dispatch SHA differs from the explicitly authorized SHA.` Resumen líneas 1153–1155. Instalación SDK y construcción de GN real pasaron; generación doble del patch posterior a la suite no se ejecutó en este run.

### Reparación mínima y prueba negativa

Archivos: `tests/test_build_routing.py` fija explícitamente su propia rama/ref antiguas; nuevo `tests/test_build_fixture_environment.py` ejecuta el Bash real de esa fixture bajo la identidad ambiental del run de recuperación y verifica también que el entorno padre no cambia. GN/native/artifacts de esa fixture son boundaries simulados; esta prueba no acredita compilación ni JNI. No se cambian scripts de producción, protección SHA, workflows, Java, iconos ni patch generado.

Reproducción antes del fix: `GITHUB_REF_NAME=assistant/archium-r4-recovery GITHUB_REF=refs/heads/assistant/archium-r4-recovery GITHUB_SHA=0514027dd41ddb568d033152c8faec76a388ba84 python3 -m unittest discover -s tests -p test_build_routing.py -k real_java_preflight_precedes -v`, exit 1, mismo rechazo SHA. Regresión nueva RED: `python3 -m unittest discover -s tests -p test_build_fixture_environment.py -v`, exit 1, `AssertionError: 2 != 0`, archivo `recovery-ci-env-red.log`. Tras el fix, mismo comando GREEN, exit 0, 1 passed en 1.930 s, archivo `recovery-ci-env-green.log`.

Verificación integral terminada: comando siguiente, exit **0**, **216 passed / 0 failed / 0 skipped**, 433.838 s. Las 23 fallas originales pasan, al igual que la regresión nueva, los tres perfiles GN reales, JVM release/debug y AAPT2 acotado real. La suite incluye boundaries nativos simulados que no se cuentan como compilación Chromium. Log `/workspace/archium-r4-evidence/recovery-ci-env-full-host.log`, SHA256 `b911724aad6fc164dca80b6b05c6e27065177949b3093ba8b3c3a49054f38d4b`.

```bash
GITHUB_ACTIONS=true GITHUB_REPOSITORY=Jorgeprdz/chromium-dex-arc \
GITHUB_REF_NAME=assistant/archium-r4-recovery \
GITHUB_REF=refs/heads/assistant/archium-r4-recovery \
GITHUB_SHA=0514027dd41ddb568d033152c8faec76a388ba84 GITHUB_RUN_ID=38177451098 \
ARCHIUM_TEST_GN=/usr/bin/gn \
ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 \
ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-37.0/android.jar \
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

`git diff --check` y `python3 -m compileall -q tests` exit 0. Ningún diff en `scripts`, workflows o patch; hashes del patch y manifest siguen `bcc1fa363379e9851da4ef7d2611aadfaf604064dcfb21ec51cc5b0bb9c55e75` y `b5fbe0b0169636108a5bc84ac52aaf6020f6cfb048fee92f2b2ce9998b8f0f84`. Refs remotas antes de publicar: rama activa `7bb0f87288147bbd233d77c6d90c2ed0b35c253b`, protegida `51e5ed429661727156ab2534caac99a82ee9264b`, main `6274c653bbe3992403a89b1531d0c1f91646bf6d`. No runs en curso ni en cola. API confirma tres grupos del checkpoint no expirados, con tamaños y digests anteriores intactos; vencen el 25 de octubre.

Estado actual: `HOST_TESTS=PASS_LOCAL_CI_ENV`, `GN_MEDIA_3_CASES=PASS`, `BUILD_STAGE=S0`, `BUILD=FAIL`, `WORKFLOW_RUN=38177451098`, `AAPT2_REAL_RESOURCES=PENDING_POST_RESTORE`, `ROBOLECTRIC=NOT_EXECUTED_CHROMIUM`, `JNI_LINK=NOT_EXECUTED_NEW_RUN`, `APK_PACKAGE=NONE`, `APK_SHA256=NONE`, `APK_ARTIFACT=NONE`, `ANDROID_RUNTIME=NOT_EXECUTED`. Los resultados previos de Robolectric aislado no equivalen a integración Chromium. El próximo gate pendiente es repetir S0 remoto con el fix publicado; S1–S5 requieren una nueva autorización de corrida pesada.

Publicación observada: commit [ba7a340212d3f79ea170b050f09cab9a72d5039f](https://github.com/Jorgeprdz/chromium-dex-arc/commit/ba7a340212d3f79ea170b050f09cab9a72d5039f), `fix(tests): isolate legacy routing from recovery CI branch`, commit exit 0. Comparación remota inmediatamente anterior al push: `7bb0f87288147bbd233d77c6d90c2ed0b35c253b`, sin escritor concurrente. `git push origin HEAD:refs/heads/assistant/archium-r4-recovery` exit 0; API/git remoto confirman `ba7a340212d3f79ea170b050f09cab9a72d5039f` y status limpio. Refs protegida y main siguen idénticas. `gh run list` confirma únicamente el run fallido con su SHA fuente original; el push no disparó otro build. Este registro posterior es documentación, sin nuevo cambio de código.

Riesgo: los tests históricos deben ejercer su rama declarada; los tests del runner nuevo siguen validando su autorización de forma independiente. El run fallido permanece FAILED. El checkpoint fuente `archium-checkpoint-38165289963-1` se conserva remoto. La capacidad local medida es 80,935,174,144 bytes, inferior al margen requerido de 100,420,496,293; no se descarga ni elimina ningún output válido. No se lanza automáticamente otro workflow pesado: la autorización de una corrida ya fue consumida.

## Dispatch observado (2026-10-11 21:42 UTC)

RUN=[38177451098](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38177451098), sourceSHA=`0514027dd41ddb568d033152c8faec76a388ba84`, branchassistant/archium-r4-recovery, workflowID374835814 baseline-build.yml. Comando real `gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc --ref assistant/archium-r4-recovery -f expected_sha=0514027dd41ddb568d033152c8faec76a388ba84 -f source_checkpoint=archium-checkpoint-38165289963-1 -f source_commit=dcbd868ea42ffd0991c01c2872adce01316a9768 -f source_run_id=38165289963` exit0. API confirma mismoSHA/statusin_progress. Job114582731650authorize SUCCESS (SHA y concurrencia). Job114582753899preflight/preflight en curso. S0; todavía sin restore/native/APK. No segundo dispatch. La actualización de este informe es solo documentación, posterior alSHA fuente fijado y no altera el checkout delrun.

```text
REPO=Jorgeprdz/chromium-dex-arc
BRANCH=assistant/archium-r4-recovery
ORIGINAL_WORK_BRANCH=assistant/archium-r3-visual-fixes PRESERVED
PROTECTED_BRANCH=feat/arc-desktop UNTOUCHED
HEAD_START=51e5ed429661727156ab2534caac99a82ee9264b
HEAD_FINAL_SOURCE=0514027dd41ddb568d033152c8faec76a388ba84
CHROMIUM_PIN=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
P0_DEX_DISPLAY=PASS (isolated real Robolectric)
P0_JAVA_ASSERT=PASS (real JVM sparse fixture)
AAPT2_REAL_RESOURCES=PENDING (new run actual merge; SDK37 bounded fixture PASS)
GN_MEDIA_3_CASES=PASS (genuine GN,pinned GNI,synthetic platform)
PATCH_REPRODUCIBILITY=PASS
CHECKPOINT_SOURCE=archium-checkpoint-38165289963-1
CHECKPOINT_INTEGRITY=BLOCKED_LOCAL_PENDING_S1_ALL_BYTES
DISK_PREFLIGHT=FAIL_LOCAL_CI_PENDING_S0
HOST_TESTS=PASS (215passed/0failed/0skipped,208suite+7final)
ROBOLECTRIC=NOT_EXECUTED_CHROMIUM (isolated39/39PASS)
JNI_LINK=NOT_EXECUTED_NEW_RUN
COMMITS=5fe80ea,37e15c0,c87e295,87be1ed,fad1703,0514027
PUSH=PASS
WORKFLOW_RUN=38177451098 https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38177451098
BUILD_STAGE=S0
BUILD=INCOMPLETE (RUN_IN_PROGRESS)
APK_PACKAGE=NONE
APK_SHA256=NONE
APK_ARTIFACT=NONE
ANDROID_RUNTIME=NOT_EXECUTED
BLOCKERS=native/realmerge/ChromeJUnit/all-byte integrity pending blocking CI; local disk insufficient
```

## Estado actual: recuperación desde el respaldo protegido

La orden posterior del usuario autoriza reescribir los cambios en una rama nueva y lanzar UNA corrida manual después de los gates. Rama activa `assistant/archium-r4-recovery`, base `51e5ed429661727156ab2534caac99a82ee9264b`; la rama antigua queda como evidencia. `feat/arc-desktop` y `main` no se han modificado. Los apartados históricos inferiores describen ejecuciones previas y NO acreditan el build nuevo.

Código preparado: `fad1703` (full SHA en git); commits temáticos `37e15c0` JNI, `c87e295` interfaz/P0, `87be1ed` Portal, `fad1703` CI. No hay migración Chromium: pin `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`. Nueva APK todavía inexistente. Workflow actual manual `baseline-build.yml`: authorize → preflight → único job recovery/native con restore único. Push no lanza build ni preflight duplicado. Dos slices máximo de75min, presupuesto total y reservas para checkpoint/upload; nunca clean fallback.

### Gates de recuperación antes del dispatch

| Gate | Estado observado | Prueba / alcance |
|---|---|---|
| STATIC_PASS | PASS | diff-check, Bash, compileall, ShellCheck nuevo runner, actionlint1.7.7, exit0 |
| PYTHON_HOST_PASS | PASS |208/208 suite completa exit0 en387.209s;7/7 regresiones finales exit0. Descubrimiento actual215 coincide exactamente con ambos conjuntos.0fail/0skip. No se etiqueta mock como ejecución Chromium |
| GN_REAL_PASS media3 | PASS |GN/usr/bin/gn1000(5e19d2f),10tests, tres perfilesARM64/baseline/x64;importsGNI fijados y contexto plataforma sintético. GN de checkout real vuelve a bloquear enS2 |
| JVM guard release/debug | PASS |4/4 exit0, -da/-ea y mutantes; método producción extraído, fixture mínima, NO Chromium integración |
| Robolectric componentes | PASS |39/39 exit0 con JDK21/Robolectric4.16.1/API29/30/36; código actual recompilado. FrameworkAndroid real, boundaryTab/API/R aislados; ChromeJUnit aún PENDING_POST_RESTORE |
| AAPT2 acotadoSDK37 | PASS |18 recursos aprobados, compile/link reales; manifest sintético. MergeChromium PENDING_POST_RESTORE bloqueante enS2 |
| PATCH_REPRODUCIBILITY | PASS |generador oficial102sources dos veces,index y árbol finales; patchbcc1fa363379e9851da4ef7d2611aadfaf604064dcfb21ec51cc5b0bb9c55e75; manifestb5fbe0b0169636108a5bc84ac52aaf6020f6cfb048fee92f2b2ce9998b8f0f84 |
| Checkpoint metadata/lectura | PASS |fuente38165289963-1,source dcbd868ea42ffd0991c01c2872adce01316a9768;3grupos/24partes;5213bytes leídos porHTTPRange. Manifest8fed39ac234c85804407670881835cf61ea02327de6733ee7262cc289fab07ac; expiración25octubre |
| Integridad todos bytes | PENDING |NO descargados~25GB localmente. Restauración valida todos SHA256 antes de extracción; gateS1 |
| DISK_PREFLIGHT local | FAIL |80.97GB libres <100420496293bytes ZIPs+75GB. NO download ni borradooutputs; medir capacidad runnerS0 ANTES de25GB |
| JNI_LINK_PASS nuevo | PENDING |owners/rawAPK/move-only idénticos byteporbyte a entradas verificadas en última corrida. gn desc/check/query/llvm-nm/link reales bloqueantesS2 |
| APK_VERIFIED nuevo | PENDING |gatesS0–S3 deben pasar antes deAPK; apksigner/aapt2/Portal/zipinfo/SHA256/S5 metadata, instalador monitor rechaza fallo |
| ANDROID_RUNTIME | NOT_EXECUTED |NO APK nueva instalada; aceptaciónDeX/visual/blur pendiente |

### Reescritura y regresiones (evidencia real)

- ColorDraft nuevo11JVM PASS; Picker14Robolectric PASS:8presets,RGB/HEX, validación, preview,apply/cancel/reset sin persistir borradores. Mutante persistencia anticipada falla6casos.
- FrameDispatch nuevo6Robolectric PASS; mutante omitir elegibilidad al ejecutar falla2casos. Navegación6Robolectric PASS con TabObserver real de pin contrastado, removerobserver, ignorartab anterior y desactivar trasdestroy.
- FocoCollections:4Robolectric inicialmenteFAIL en `after.hasFocus()`; regeneración restaura identidad/tag por grupo,4/4GREEN. No reescribeTabModel.
- Geometría: JVM con AndroidXWindowCore pinSHA verificado; REDtop-left indebidamente cuadrado → GREENsolo bottom-leftcuadrado,clamp radio/API33, presupuesto colecciones reservado para caption/control/native tabs.
- DesktopAppearance nuevo: RED9tests4fallos (display0 ancho no basta); GREEN9/9, API29/30/36, displayexterno antes/despuésattach, null/fallback y multiwindow, modos usuario conservados. ArcDesktopPolicy no cambia elegibilidad porvendor.
- Portal: blobsPNG/SVG aprobados inmutables; gates contenido real rechazan alias/manifests/píxeles/themedvectores alterados, namespaces despojados porChromium y WebP lossless sin-exact.
- Runner nuevo25casos routingPASS (24suite+1timeout), boundariesGN/native/CI simulados explícitos. JVM real scoped-ea pasa antes dejavac; mutante exportglobal provocaexit83 stderr`Picked up JAVA_TOOL_OPTIONS` y se rechaza. Outputs no cuentan como APK real.
- Revisión independiente readonly: detectó falta env`ARCHIUM_CHECKPOINT_STORAGE=artifact`/`ARCHIUM_SOURCE_RUN_ID` que enviaba restore a Releases. REDCLI real tinyarchive con fallback bloqueadoexit71→GREEN restore+pack reales Actions exit0. Detectó pack tras timeoutTERM sin quiescencia; RED→GREENexit124sin pack, remoto preservado. CeroCritical/Important restantes en archivos finales inspeccionados.
- Publicación:metadata helper4testsPASS; omisión deliberada del guard falla6checks negativos (4subtests+2casos; primer contador esperado3 era incorrecto y se corrigió a6). S5 compruebaID/digest/tamaño/expiry/source SHA víaAPI; no claims remotos hastaejecutarlo.
- Preparación oficialSDK37: aplicaciónpatch/check originalshashes/JVM/puremodel yjavacSDK real exit0; dependencias de adaptadores stubbed y NO GNlink real.

Warnings observados y NO ocultados: APIsdeprecadas fallback/tests, carga dinámica agenteMockito y CloseGuardSurface de Activity mínima deRobolectric. Exit0/39tests no acredita render limpio ni dispositivo. Tests registrados en ChromeJUnit y bloqueantes realesCI. Minor diferido:READMEassets todavía describe integración como futura (documentación histórica). Rulings:seguir orden userautónoma sin repetir permisos; nueva rama en lugar de publicarfix puntualviejo; reusar solo blobs/utilidades conprocedencia; casos imposibles local quedanPENDINGCI; mantener ledger y checkpoints; pushsinCIautomatic paraevitar duplicarpreflight; el build/ejecución/blur en dispositivo sigue sinverificarse y se exige en su fase correspondiente.

### Evidencia local reproducible

`/workspace/archium-r4-evidence/recovery-host-second.log`(208/208); `recovery-host-final-coverage.json`(215/215 coberturaexacta), `recovery-review-artifact-green.log`, `recovery-review-timeout-green.log`, `recovery-routing-third.log`, `recovery-api-sdk37-final.log`, `recovery-aapt2-sdk37.log`, `recovery-patch-{first,second}.sha256`, `recovery-source-{artifacts,manifest}-current.json`, `recovery-color-robolectric/{display-red,display-green,focus-red,focus-green,combined-final}.log`. Archivos no contienen tokens/URLsfirmadas. Manifest/actionsmetadata incluye solo IDs,digests,fechas públicos.

Monitor: `/data/data/com.termux/files/home/archium-r4-monitor-termux.sh`, estiloASCII,separadorescoloreados,bold/italic,600s,elapsedreal,ETA=N/D(no inventado), fasesobservadas,3últimaslíneas reales oeventosAPI etiquetadoscuando log no publicado; falla→sin descarga/instalación; éxito→hash+package+ABI+Portal+firma antes deinstall-r yhashinstalledbaseAPK. Monitor adaptado a nuevosjobnames;6regresionesPASS de fase/cache/primerstderr. RUNnuevo todavía PENDING_DISPATCH en este snapshot; suSHA se fijará antes del dispatch y el registroposterior mantendrá eseSHA como fuente inmutable.

---

## Registro histórico R3/R4 (antes de la recuperación)

Especificación: prompt ARCHIUM R4 del usuario. Ejecución autónoma, commits temáticos y push autorizados exclusivamente a assistant/archium-r3-visual-fixes; una corrida pesada condicionada a gates. Sin build limpio, borrado de outputs ni migración upstream. Se preserva Portal/DeX y feat/arc-desktop.

- [x] Reconocer local/remoto, pin, PRs, 30 commits, workflows, ocho logs y artifacts.
- [x] ARC-F002: JVM -ea/-da, negativas y restore assert; runner Chromium con assertions programadas.
- [x] ARC-F001: display independiente de attach, API 30/fallback, JVM y Robolectric aislado.
- [ ] ARC-F003: gate sobre recursos/manifests reales y APK optimizada; conservar assets.
- [x] ARC-F004/F005: evidencia separada, dispatch explícito SHA, sin push pesado ni clean fallback.
- [x] ARC-F006/F007: fixtures integridad/ENOSPC/mtimes/symlinks/transición/delta.
- [x] ARC-F008: doble regeneración oficial, hashes y aplicación.
- [ ] Gates baratos y commits/push; una corrida S0–S5 solo si autorizada por evidencia.

## Reconocimiento

HEAD_START=4ed6a99abc32bcde52076fecfab5c5c90aa3ab14, confirmado git ls-remote.
Pin real=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 (build/generador/transición/manifest).
Protegida remota=51e5ed429661727156ab2534caac99a82ee9264b.
Checkout protegido local limpio /workspace/ChromiumDeXArc-work=f71df252ccdac629dd721e215e8e84cdd6cf44bc, intacto.
Worktree autorizado /workspace/Archium-R4 creado mediante fetch/worktree add, exit 0. Sin AGENTS.md ni los cuatro informes antecedentes solicitados en workspace. Sin PRs abiertos; 30 runs recientes completed; ps sin compiladores ni escritores concurrentes observados.

## Gates iniciales

| Gate | Estado | Evidencia pendiente |
|---|---|---|
| Identidad/pin/aislamiento | PASS | Recomparar remoto antes del push |
| STATIC_PASS | PENDING | diff/Bash/compileall/actionlint |
| PYTHON_HOST_PASS | PENDING | Suite completa sin skips críticos |
| GN_REAL_PASS media | PASS | 10 passed, 0 failed, 0 skipped; GN Debian 1000 (5e19d2f), contexto sintético; árbol Chromium/pinned GN pendientes CI |
| P0_JAVA_ASSERT | FAIL | HEAD throw incondicional; JVM release prueba falla |
| P0_DEX_DISPLAY | FAIL | HEAD depende de attach; negativos display externo |
| AAPT2_REAL_RESOURCES | PENDING | Manifest y recursos reales; APK optimizada |
| PATCH_REPRODUCIBILITY | PENDING | regeneración doble y aplicación |
| CHECKPOINT_METADATA | PASS | grupos SHA/digest/expiración |
| CHECKPOINT_INTEGRITY | UNVERIFIED | manifiesto/hashes completos/restore |
| DISK_PREFLIGHT local | FAIL | 83.373.178.880 libres < 100.154.627.252 requeridos |
| ROBOLECTRIC_PASS | PENDING | PENDING_POST_RESTORE Chromium real |
| JNI_LINK_PASS | PENDING | outputs/links reales |
| APK_VERIFIED | PENDING | APK R4 firmada/arm64 |

## Logs auténticos

`gh run view --log` devolvió exit 0, cero bytes: no evidencia. ZIPs completos recuperados por gh api /actions/runs/ID/logs y guardados en /workspace/archium-r4-evidence/ID. Un EOF inicial del 38028097362 se recuperó al repetir lectura, exit 0. SHA256 abajo permite identificar cada log. Líneas cuentan el TXT descomprimido.

### Run [38076326818](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38076326818)

SHA `4ed6a99abc32bcde52076fecfab5c5c90aa3ab14`; CAUSA_CONFIRMADA observable: `2026-10-10T19:40:58.5810344Z ValueError: APK launcher does not use the native adaptive icon alias`. Job/log `13_stage1 _ build.txt`, línea 68875; SHA256 `9e92a5d046348c3ccaca248639f5930cf3914b440b0e4d6784adcb54ddaff669`.

### Run [38075496273](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38075496273)

SHA `ad228b44d7a8e86594974deacdfea3a3b36f66de`; CAUSA_CONFIRMADA observable: `2026-10-10T18:22:41.2274512Z -  "patch_sha256": "fa8ec0777e2e0fdc89ce6bcc8983d8b0f5705284acebe81d8d9498c7bbaddde2"`. Job/log `15_r3-final-gates.txt`, línea 205; SHA256 `5de28632536d6053195346c6f074d295bdd58bc65f015661cf14161e2c6c1a45`.

### Run [38070564185](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38070564185)

SHA `7dcf4cc6a75d33f607541f74976dc76261477bed`; CAUSA_CONFIRMADA observable: `2026-10-10T17:42:03.7097377Z  0| java.lang.AssertionError: Expected exception: java.lang.AssertionError`. Job/log `13_stage1 _ build.txt`, línea 60998; SHA256 `63b02423820b0025acdc8f99b0adbd1b9a11925edf2f74089b3e5277fe18d559`.

### Run [38061011260](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38061011260)

SHA `5f8abc4811d35035a8ea03311801da8416cabc95`; CAUSA_CONFIRMADA observable: `2026-10-10T15:11:44.3850395Z  1| Caused by: java.lang.UnsupportedOperationException: Tried to obtain display from a Context not associated with one. Only visual Contexts (such as Activity or one created with Context#createWindowContext) or ones created with Context#createDisplayContext are associated with displays. Other types of Contexts are typically related to background entities and may return an arbitrary display.`. Job/log `13_stage1 _ build.txt`, línea 15292; SHA256 `d726dd6995e0e996813c2e9329521cf984a091abcd72b4b1ec641cdebcbfef4a`.

### Run [38028097362](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38028097362)

SHA `ce7e0c93f7526b37caf3b2a0f2efebd2b2ba2ac4`; CAUSA_CONFIRMADA observable: `2026-10-10T06:00:19.3332942Z ERROR: test_arm64_enables_native_media_and_preserves_open_codecs (test_media_config.PinnedMediaConfigurationTests.test_arm64_enables_native_media_and_preserves_open_codecs)`. Job/log `13_stage1 _ build.txt`, línea 2957; SHA256 `d8098f6c67ed405f25acb80abcceee88b7fa71e54f54d2d826ef1021af778943`.

### Run [38024276820](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38024276820)

SHA `2553d698933b028f185c03015ab2eea8f2817d26`; CAUSA_CONFIRMADA observable: `2026-10-10T04:38:22.4299765Z Insufficient disk space after cleanup: 90512818176 bytes`. Job/log `13_stage1 _ build.txt`, línea 210; SHA256 `771109bb6c90769d188da21a9d5d837b74be8f54039dcf534b2ad7dc25634900`.

### Run [38018166249](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38018166249)

SHA `507f28e1265fb98551d3bc1a66f4739fb48d2625`; CAUSA_CONFIRMADA observable: `2026-10-10T03:46:06.9714129Z ld.lld: error: undefined symbol: Muxed_org_chromium_chrome_browser_payments_ServiceWorkerPaymentAppBridge_getSourceIdForPaymentAppFromScope`. Job/log `13_stage1 _ build.txt`, línea 6117; SHA256 `6c75abfe855212450e40b1a30a8cdf3cb500ebe3e55f9c67a0ec34cab487fef2`.

### Run [38013133434](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38013133434)

SHA `7cec89a5fd7c78b28b576c5fc3564fdf050ee538`; CAUSA_CONFIRMADA observable: `2026-10-10T01:54:37.7487977Z ld.lld: error: undefined symbol: jni_zero::internal::cached_jclasses`. Job/log `13_stage1 _ build.txt`, línea 4569; SHA256 `842b403fe6ed5d23f8d8bf11a36414a77a346ff1f17b7c4fa43da8a491f2eab4`.

38076326818: el compilador anunció Build Succeeded (1193 steps), luego falló el verificador de alias; no es evidencia de error aapt2 compile/link. Hipótesis: nombres ZIP acortados por Chromium; comprobar tabla/manifest reales antes de reparar. 38028097362: tres errores fixture GN (exit 2, stderr oculto), no demuestra códecs rotos; HEAD ya revela stdout/stderr y los tres casos pasan GN real local. 38061011260: Context no visual en Robolectric; causa antigua distinta del gate attach introducido después. JNI/payments histórico 38018166249: símbolos reales; no reabrir sin evidencia actual del árbol/output.

## Checkpoint remoto preservado

Único checkpoint Actions disponible en listado completo: archium-checkpoint-38018166249-1, source 507f28e1265fb98551d3bc1a66f4739fb48d2625. Total 25.154.627.252 bytes; tres grupos expired=false, expiran 2026-10-24. No hay checkpoint Actions más reciente. Credenciales gh lectura metadata funcionan (exit 0); hashes completos pendientes, no descargados.

| Grupo | ID | Bytes | SHA256 remoto ZIP |
|---|---:|---:|---|
| archium-checkpoint-38018166249-1-00 | 11659095001 | 8589940404 | sha256:63758d866748b35110ce723b1c824fd0a0daa2d087920accbeda704d234fadcc |
| archium-checkpoint-38018166249-1-02 | 11659005312 | 7974750878 | sha256:a6ee39a0bdfbb4a84f1e0899201d57b1ce462f263e8905e87faf9cfcf7903a30 |
| archium-checkpoint-38018166249-1-01 | 11659000212 | 8589935970 | sha256:9d9ae0e6b65df4359e473c34a6c056ea5ea48075375381e189abc5381ddf65f3 |

Local df inicial: 83.373.178.880 bytes / 11.660.047 inodos libres. Política existente: ZIP 25.154.627.252 + 75.000.000.000 extracción/reserva; faltan 16.781.448.372 bytes para restore local. No se baja umbral ni se limpia output. Último runner observado 115.666.358.272 libres; no prueba espacio de un próximo runner. No workflow pesado iniciado.

## Registro de comandos y evidencia

- git status/branch/log -30/ls-remote/worktree list: leídos; árbol limpio inicial.
- gh auth status: permisos repo/workflow; no secretos registrados.
- gh run list/pr list/API jobs/artifacts: exit 0, metadata en /workspace/archium-r4-evidence.
- ARCHIUM_TEST_GN=/usr/bin/gn python3 -m unittest discover -s tests -p test_media_config.py -v: exit 0; 10 passed, 0 failed, 0 skipped (tres perfiles GN reales sobre imports media fijados, plataforma sintética).
- python3 -m unittest discover -s tests -p test_tab_list_layout_guard.py -v antes del fix: exit 1, 4 tests, 2 failures. Release con throw crash artificial; detalle assert-red.log.

Este informe no acredita Robolectric Chromium, JNI ni APK mediante fixtures host.

## ARC-F002 — aserción de producción

Causa: commit 44df401 sustituyó assert de upstream por throw siempre activo para satisfacer prueba sin -ea. Log 38070564185 muestra Expected exception: AssertionError; fuente oficial del runner fijado `_CreateJvmArgsList` no incluye -ea. Fix mínimo restaura assert y suministra JAVA_TOOL_OPTIONS=-ea solo a ejecución de tests reales (early y host).

Prueba JVM ejecuta método extraído literalmente de fuente real con dependencias mínimas; NO integración Chromium. RED: exit 1, 4 tests/2 failures; GREEN: exit 0, 4 passed/0 skipped, JVM -ea/-da y mutantes throw/sin assert. Logs assert-red.log/assert-green.log. Robolectric real queda PENDING_POST_RESTORE. Generador oficial dos veces y cmp SHA256 exit 0; Bash/compileall/diff check exit 0. Riesgo pendiente: comprobar assertions del runner Chromium con Robolectric.

## ARC-F001 — detección de display

Causa confirmada en HEAD: decor.isAttachedToWindow descartaba display externo antes del attach. Se sustituye por Activity.getDisplay en API >=30, capturando únicamente UnsupportedOperationException (context no visual observado en run 38061011260), con fallback WindowManager.getDefaultDisplay null-safe. ArcDesktopPolicy/ArchiumWindowMetrics no modificados. Referencias API oficiales: https://developer.android.com/reference/android/app/Activity#getDisplay() y https://developer.android.com/reference/android/view/WindowManager#getDefaultDisplay().

RED JVM: exit 1, external display before attach expected true got false. GREEN: 14 escenarios de método real contra stubs; no integración Chromium. Robolectric genuino aislado: producción Appearance/Policy/WindowMetrics/WindowClass, AndroidX Window Core CIPD fijado, Mockito y framework 4.16.1; JUnitCore Java21: exit 0, 9 tests, 0 failures/skips (API29/30/36; ShadowDisplayManager y ShadowDisplay; default/externo, antes/después attach, fallback no visual, null y multiwindow). Mutante attach: exit 1; final recompilado exit 0, 9/9. Evidencia /workspace/archium-r4-evidence/robolectric/display-{mutant-red,final-green}.log.

Primeros intentos de entorno: Java17 incompatible API36; Conscrypt/nativeruntime Linux aarch64 no disponibles. Se ejecuta JDK21 proveedor firmado/hash verificado, conscrypt OFF como runner Chromium, GraphicsMode/SQLiteMode LEGACY para tests de display sin SQL/render. No casos deshabilitados. Bare Activity API36 se representa como contexto UI mediante spy para probar elegibilidad de ancho sin alterar WindowMetrics. Warnings observados: uso de API obsoleta fallback y carga dinámica de agente Mockito; NO ocultados. Test registrado en chrome/android/junit/BUILD.gn; runner Chromium sigue PENDING_POST_RESTORE. Adapter javac excluye carpeta junit (compilación real separada). Riesgo: GN/JUnit Chromium completo pendientes.

## ARC-F003 — alias Portal y recursos reales

Log 38076326818, stage1/build, línea 68875: ValueError APK launcher does not use the native adaptive icon alias, después de Build Succeeded 1193 steps. No error de recursos AAPT2 demostrado. APK Chromium histórica run 37968167514 (ad55bbeb..., feat/arc-media-only) descargada de artifact existente, no R4: badging real package app.archium.android, icon res/r21.xml, ABI arm64-v8a. Ese run no demuestra Portal actual; solo comportamiento de empaquetado. Intento inicial con ID histórico incorrecto devuelve 404; metadata suministra ID correcto, descarga exit 0.

Causa reproducida con AAPT2 SDK 37 genuino vía qemu (aapt2 2.20-15087165): compile+link de 18 Portal assets aprobados, optimize --shorten-resource-paths. Verificador original RED exit 1 exactamente mismo ValueError; fix valida resource IDs icon/roundIcon del manifest compilado, ruta real de la tabla y todos los pixels/layers/vector. GREEN exit 0. Manifest sintético, no se declara fusión Chromium. Se añade negativo con manifest icon @mipmap/app_icon rechazado. AAPT2 Debian 2.19 no soporta resource table del SDK36; fallo registrado y se usa SDK37 genuino existente, no se omite gate. Output compilación ZIP portable.

Inventario pin remoto leído con Gitiles JSON: res_base drawable ic_launcher/ic_launcher_round; res_chromium_base drawable themed_app_icon; mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi} app_icon/layered_app_icon/layered_app_icon_background; mipmap-nodpi layered_app_icon_foreground.xml. BUILD.gn original incluye overlay chrome_public_apk_base_module_resources; sin otros calificadores en esos roots. No assets ni identidad visual modificados. Inventario completo de árbol y manifest merge obligatorios tras restore mediante scripts/check-portal-chromium-resources.py y target REAL chrome_public_apk__compile_resources. PENDING_POST_RESTORE: GN outputs auténticos .ap_ (excluyendo variante proto), manifest merged, aliases/chain/pixels verificados antes de enlaces. Estructura upstream rules.gni del pin comprobada.

## ARC-F006/F007/F008 — recuperación y reproducibilidad

Lectura remota mediante rangos HTTP de ZIP grupo00, sin transferencia 25GB: 5212 bytes; checkpoint.json leído y validado source/tag/pin/workspace, 24 fragmentos, compressed 25.154.618.684 bytes. SHA256 manifest leído 0d1d3ff28b9cc9936e92ee89826d1406460f1aa583c01d2429644352e8123079. Workspace fuente /home/runner/work/_temp/chromium-archium. Hashes completos de fragmentos y restore real siguen PENDING; no se declara integridad completa por metadata.

Fixture Actions restore real tiny: roundtrip mantiene .ninja_log nanosegundos, symlinks/modos; corrupción rechazada antes de extraer. Nuevos tests ENOSPC (inyección errno28) y tar realmente inválido con hashes válidos: fallan restore y preservan TODOS los fragmentos/manifest; 5/5, exit0. Transition: 17/17 exit0, rollback ENOSPC conserva bytes/modos/mtimes/receipt y Ninja REAL recompila solo shared.txt cambiado, unchanged.out y mtime intactos. No corresponde a recompile Chromium.

Causa ARC-F006 adicional reproducida: validate_manifest aceptaba SHA no hexadecimal y bool como tamaño; RED 8 tests/1failure, GREEN 8/8 con regex SHA y tipo int exacto. Restore fuente legacy compatible preservado. Workflow obliga checkpoint; sin clean fallback. En restore CI quedan bloqueantes checkout pin/depot pin/build.ninja/args de origen antes de transición y fingerprint GN/clang. No outputs/caches válidos borrados.

Generación oficial reproducida dos veces por cada reparación Java, cmp SHA256 exit0; 95 archivos actuales manifest. Patch se aplica realmente en check-arc-preparation (exit0), valida originals y bytes modificados. Pin cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.

## ARC-F004/F005 — evidencia y dispatch

Preflight distingue STATIC_PASS, PYTHON_HOST_PASS, GN_REAL_PASS con scope media_fixture; Robolectric/JNI quedan PENDING_POST_RESTORE y APK PENDING. GN ausente y javac ausente ahora FALLAN; no skips críticos. Host con outputs reales ejecuta Robolectric antes de marcar ROBOLECTRIC_PASS. Test coverage routing captura marcadores de mocks para no publicarlos como evidencia de Chromium.

baseline-build.yml: solo workflow_dispatch, expected_sha obligatorio igual GITHUB_SHA, rama exclusiva autorizada, concurrency global archium-build-staged cancel=false, chequeo de otras corridas activas. Source inputs explícitos con defaults checkpoint compatible vigente; sin markers ni push pesado. Se eliminan stages nuevos con restore repetido: stage1 permite máximo dos slices sobre MISMO checkout/output, respetando límites históricos 75m/slice, 7200s presupuesto global y 180m job (no se extiende presupuesto). Terminal BUILD_INCOMPLETE visible si tiempo agotado. Mock ejecutable confirma un restore/dos intentos y bloqueo de APK; NO prueba compile nativo. Checkpoint obligatorio en workflow, clean fallback deshabilitado.

Metadata de releases remotos también inventariada (gh api paginate exit0): el más reciente release checkpoint es archium-checkpoint-37905612954-1, 2026-10-09T08:56:22Z, más antiguo que Actions source elegido 2026-10-10. No releases/checkpoints borrados.

## Revisión independiente y corrección de empaquetado

Habilidad requesting-code-review: revisión read-only de diff completo, sin subdelegación. Un Important encontrado, ningún Critical/Minor material: Chromium elimina extensiones de imágenes y convierte lossless WebP; verificador solo PNG rechazaría recursos reales. Se verifica contra código exacto del pin compile_resources.py y APK histórica real: mipmap/app_icon -> res/80 (RIFF WEBPVP8L), layered foreground/background extensionless.

Nueva prueba negativa: gate viejo RED (8 tests; 1 failure, 1 error) sobre WebP lossless sin extensión y pixels ajenos. Fix lee rutas reales de tabla y decodifica WebP genuino mediante Pillow/libwebp, compara RGBA/dimensiones contra assets aprobados. GREEN 8/8, exit0. No se cambian assets ni optimización Chromium. Se instala decoder python3-pil para VALIDACIÓN host explícita; prueba features.check(webp) bloqueante, no dependencia nueva del browser. Fixtures AAPT2 van a representar conversión/strip además del shorten.

Revisor declinó acreditar: restore/integridad real, GN completo/recursos Chromium, Robolectric Chromium, JNI, APK R4 firmada y Android dispositivo. Se conservan pendientes hasta evidencia; fixtures no los acreditan.

Suite host primera ejecución tras cambios: 175 tests, 1 failure y 2 errors, exit1. Causas reproducidas en fixtures: symlinks herramientas no idempotentes, test que esperaba stage2 eliminado al conservar output, SDK resolver mocked incompleto. Se corrigen fixtures conservando restricciones y añadiendo firma/ABI negativas; no dispatch con gate fallido. Detalles host-final.log.

## 2026-10-11 14:20 UTC — gates antes de publicación

Segunda suite completa host-complete.log: 177 tests, 1 failure/1 error, exit1. Una edición concurrente propia del script invalidó un proceso que ya lo estaba leyendo (syntax error temporal; Bash final y caso aislado pasan); no se acepta esa ejecución. Error independiente: test_host_gate_coverage dejó ARCHIUM_TEST_AAPT2 apuntando a su SDK temporal eliminado. Se corrige aislamiento mediante patch.dict(os.environ), sin mockear AAPT2 de la prueba real posterior.

Ejecución estable: `ARCHIUM_TEST_GN=/usr/bin/gn ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar python3 -m unittest discover -s tests -p 'test_*.py' -v`: exit0, **177 passed, 0 failed, 0 skipped**, 220.375s, host-stable.log. Incluye GN genuino tres perfiles, JVM -ea/-da, dos AAPT2 compile/link/optimize reales (PNG y WebP sin extensión), negativos de manifest/pixels, restore/corrupción/ENOSPC/mtimes/symlinks/delta y control de etapas con mocks explícitos. No acredita enlace Chromium ni runner Chromium.

Verificación 14:20 UTC: git diff --check, bash -n (build-archium/build-baseline/dispatch), python3 -m compileall -q scripts tests y actionlint 1.7.7 sobre TODOS los workflows: exit0. Ajuste final dependencia de verificación: baseline S0 instala python3-pil antes de importar suite Portal, igual que preflight/host. actionlint y guardrails dispatch 2/2 repetidos exit0; no invalida lógica de la suite estable. Generator oficial doble + cmp + git diff --exit-code: exit0.

Hashes finales: patch 93813d3fa8831e1bcc5283f124bdbb7157ab8483f6ff4de5bfc6d9337a9bbc10; manifest 6cce6232029b0ec2f355b1ae31dd869dd509fd79750176b53df1f3479543a0e5. Preparación sparse real anterior: exit0 y aplicación correcta; 95 archivos, pin conservado.

Commits temáticos locales verificados: fc9f0b2741de07ac6b96ea72af1f373dcbca626f (assert), 3274d78060d213f30d7bc4040ca9c4e97ea3d754 (display), 0fb329ee4f4c10e53d9603d4af9b39de91d42403 (aliases AAPT2), 92a092158f348ea6c99d38a4ed8bbb01d21114db (checkpoint), 2e411ec1a776b8caf098405bbb864adff58ee07d (WebP). Riesgos pendientes: compilación GN completa, fusión recursos Chromium, assertions Robolectric Chromium, JNI real, margen CI real y APK actual. No cambios payments/branding/pin.

| Gate antes de push | Estado | Alcance |
|---|---|---|
| STATIC_PASS | PASS | diff/Bash/compileall/actionlint reales |
| PYTHON_HOST_PASS | PASS | 177/177, cero skips |
| GN_REAL_PASS | PASS | arm64/baseline/x64, imports media fijados en fixture plataforma; GN Chromium pendiente |
| P0_JAVA_ASSERT | PASS | método JVM real extraído -ea/-da + mutantes; original Robolectric bloqueante CI |
| P0_DEX_DISPLAY | PASS | producción Robolectric aislado 9/9 + mutante; Chromium bloqueante CI |
| AAPT2_REAL_RESOURCES | PENDING | fixtures AAPT2 PASS; árbol/manifest reales bloqueantes tras restore |
| PATCH_REPRODUCIBILITY | PASS | doble generación y aplicación sparse |
| CHECKPOINT_METADATA/READ | PASS | tres grupos no expirados, manifest remoto leído por rangos |
| CHECKPOINT_INTEGRITY | UNVERIFIED | 24 hashes completos y tar bloqueantes S1 |
| DISK_PREFLIGHT local | FAIL | 81.454.604.288 bytes; no descarga local |
| DISK_PREFLIGHT CI | PENDING | bytes/inodos reales antes de transferencia; STOP sin descarga si insuficiente |
| ROBOLECTRIC/JNI/APK Chromium | PENDING_POST_RESTORE | gates bloqueantes del único run; no PASS por mocks |

Destino del restore es runner CI descartable, no disco local insuficiente. El gate S0 del mismo flujo debe demostrar margen **antes** de transferir 25GB; no se presume espacio por runner histórico ni se reduce reserva. Si preflight remoto falla, no se despacha compilación. La ruta seleccionada conserva checkout/out, dos slices como máximo, y checkpoints de fallos quiescentes con run FAILED.

## 14:21–14:26 UTC — push, preflight remoto y único dispatch

Push sin force, branch exclusiva: exit0, 4ed6a99 -> 5895d4a80510114ef12a89927c19667d4defeb27. SHA protegida permanece 51e5ed429661727156ab2534caac99a82ee9264b, checkout protegido local limpio f71df252ccdac629dd721e215e8e84cdd6cf44bc. Recomparación remota antes/después exit0. Push inicia únicamente [preflight 38146842592](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38146842592), SUCCESS. Logs ZIP auténticos descargados, 0_preflight.txt:486 GN 10 tests; :947 full177 tests/93.214s; :1007 STATIC/PYTHON_HOST/GN_REAL_PASS; :1008 Robolectric/JNI pendientes. GN exacto del DEPS construido, fixture media tres perfiles PASS. Local actionlint repetido con ShellCheck0.9.0 ahora disponible: exit0.

Antes de dispatch: remoto SHA esperado exacto, no builds nativos activos (API100runs lista vacía), metadata checkpoint actual expira Oct24, concurrency workflow global. Comando `gh workflow run baseline-build.yml --repo Jorgeprdz/chromium-dex-arc --ref assistant/archium-r3-visual-fixes -f expected_sha=5895d4a80510114ef12a89927c19667d4defeb27 -f source_checkpoint=archium-checkpoint-38018166249-1 -f source_commit=507f28e1265fb98551d3bc1a66f4739fb48d2625 -f source_run_id=38018166249`: exit0, **UNA sola ejecución** [38147216573](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38147216573), event workflow_dispatch, SHA exacto confirmado por API. Ningún segundo dispatch autorizado/intentado. BUILD_SOURCE_SHA=5895d4a80510114ef12a89927c19667d4defeb27; commits posteriores de informe no alteran código ejecutado.

## 14:30 UTC — S0 del único run PASS

Jobs r3-final-gates 114492995182 y r3-pre-native-gates/preflight 114493095601 SUCCESS. Logs reales descargados por endpoint jobs/logs: run-38147216573-s0-final-gates.log :151 metadata3grupos PASS; run-38147216573-s0-preflight.log :493 GN10tests, :953 host177tests/68.456s, :1013 PASS static/host/GN fixture, :1014 Robolectric/JNI pendientes. Ningún skip crítico. Stage1/build 114493740808 comienza verificación de disco/identidad **antes de transferencia**. Intento único de leer log del job aún activo devuelve HTTP404 (exit1); no hay evidencia de bytes CI todavía, no se imputa causa de build a ese 404 de observabilidad.

## 14:49 UTC — S1 y entrega a monitoreo manual solicitado

Usuario solicita nueva sesión Termux, refresco 600s, elapsed/ETA/%/tres líneas de log y descarga+instalación solamente tras éxito; después pide detener el agente y seguir monitoreo manual. Esta instrucción cambia el cierre de sesión: se entrega monitor independiente, no se afirma terminación del build. Run 38147216573 sigue IN_PROGRESS, stage1/build Restore checkpoint and prepare Chromium. Gate disco/metadata pretransfer y descarga SUCCESS por API; hashes/tar/identidad todavía no acreditados hasta fin de restore/log. Source remoto archium-checkpoint-38018166249-1 conservado.

Monitor adaptado fuera del repo Chromium (sin cambios a código del SHA ejecutado): /workspace/macdesk-maintenance/archium-r4-monitor.py; lanzador nativo /workspace/archium-r4-monitor-termux.sh. Nueva sesión Termux #2 confirmada por captura termux-monitor-final-compact.png, PID4878 independiente de Codex. Primer intento RunCommandService exit255 requiere permiso; se usa UI/atajo Termux para crear #2, sin nuevos permisos. Un comando de relanzamiento entró al chat #1; se corrige seleccionando y verificando #2 antes de ejecutar. Panel final inspeccionado: ASCII, líneas continuas cyan/violet/blue/green, negrita/cursiva, bloques cortos y últimas3 líneas recortadas. r+Enter refresca, q+Enter detiene monitor; intervalo automático600s. Wake-lock solicitado en lanzador.

Elapsed usa timestamps reales. % = fases acreditadas /6, no porcentaje de objetos Ninja ni estimación por tiempo. S0PASS/S1pendiente:16.7%. ETA=N/D porque API no publica contadores vivos del job; no estimaciones históricas ficticias. Si log activo devuelve404, panel etiqueta EVENTOS API y muestra últimos3 eventos reales, sin disfrazarlos de stderr. Cuando log real disponible muestra últimas3 líneas y conserva archivo completo. En S0 existe warning Node20 de checkout forzado a Node24; log completo conservado, no acreditado como ausencia de warnings.

Autoentrega configurada (NO EJECUTADA aún): exige mismo run/SHA final exitoso, artifact vigente y único, BUILD_REPORT source_sha/pin/APK_VERIFIED, SHA256SUMS, aapt2 ABIarm64, Portal real de APK descargada y apksigner real. Reutiliza updater existente para package app.archium.android, Samsung, instalación adb -r sin desinstalar, versionCode y hash del base.apk instalado. Copia APK a /sdcard/Download/Archium-R4-38147216573-arm64.apk y verifica hash remoto. Si build FAILED/INCOMPLETE no descarga ni instala; nunca inicia otro workflow. Errores de verificación bloquean instalación y quedan registrados. Marker instalado solo después de prueba auténtica. Pruebas negativas del monitor5/5 exit0: SHA/pin/APK_VERIFIED incorrectos rechazados; slice incompleto no100%. py_compile/Bashsyntax exit0. Instalación/Android runtime todavía NOT_EXECUTED; no APK R4 disponible al cerrar este turno.

Estado al traspaso:
```text
REPO=Jorgeprdz/chromium-dex-arc
BRANCH=assistant/archium-r3-visual-fixes
PROTECTED_BRANCH=feat/arc-desktop UNTOUCHED
HEAD_START=4ed6a99abc32bcde52076fecfab5c5c90aa3ab14
BUILD_SOURCE_SHA=5895d4a80510114ef12a89927c19667d4defeb27
CHROMIUM_PIN=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
P0_DEX_DISPLAY=PASS
P0_JAVA_ASSERT=PASS
AAPT2_REAL_RESOURCES=PENDING
GN_MEDIA_3_CASES=PASS
PATCH_REPRODUCIBILITY=PASS
CHECKPOINT_SOURCE=archium-checkpoint-38018166249-1
CHECKPOINT_INTEGRITY=BLOCKED
DISK_PREFLIGHT=PASS
HOST_TESTS=PASS
ROBOLECTRIC=NOT_EXECUTED
JNI_LINK=NOT_EXECUTED
PUSH=PASS
WORKFLOW_RUN=38147216573 https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38147216573
BUILD_STAGE=S1
BUILD=INCOMPLETE
APK_PACKAGE=NONE
APK_SHA256=NONE
APK_ARTIFACT=NONE
ANDROID_RUNTIME=NOT_EXECUTED
BLOCKERS=Evidencia S1 pendiente mientras run sigue activo; no fallo observado. Monitoreo del agente detenido por solicitud del usuario.
```

CHECKPOINT_INTEGRITY=BLOCKED aquí significa acreditación completa pendiente del restore activo, no fragmentos corruptos observados. DISK_PREFLIGHT=PASS refiere runner CI/gate pretransfer; local permaneceFAIL y nunca descargó25GB. P0PASS corresponde a pruebas reales aisladas descritas arriba; ROBOLECTRIC=NOT_EXECUTED refiere runner completo Chromium. BUILD=INCOMPLETE es estado actual EN CURSO, no éxito ni falla. HEAD_FINAL se obtiene del commit documental posterior a esta captura y se comunica en entrega; el run mantiene BUILD_SOURCE_SHA exacto anterior. Ninguna corrida pesada adicional.

Hashes del monitor entregado:
/workspace/macdesk-maintenance/archium-r4-monitor.py: 6ccc6ce4541cb05995d4eb2f56226d653505818f358430a21ec36ccd423d3daa
/workspace/archium-r4-monitor-termux.sh: 959d0a143184384d453d8cb5996238ae0dab23ca65baba185b9beec5d6d94ea0

## 15:14–16:48 UTC — único run FAILED, diagnóstico y barrido pedido

El estado anterior era una captura EN CURSO, no la conclusión del run. La API ahora confirma [38147216573](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38147216573) COMPLETED/FAILURE, source SHA 5895d4a80510114ef12a89927c19667d4defeb27. Stage1/build job 114493740808; step compile comenzó 14:54:28 y falló 15:14:17. Se descargó el log completo auténtico, no solo resumen: `/workspace/archium-r4-evidence/run-38147216573-stage-final.log`, 6267 líneas, SHA256 `0e3445c1ebb564973941bd7fd86566c39bd908baa96b608554d64d1714597eab`.

| Evidencia del log | Estado observado |
|---|---|
| :201/:204 | Pretransfer: 18.975.585 inodos libres, 115.667.193.856 bytes disponibles, exigidos 100.154.627.252; PASS antes de descarga |
| :288 | Posdescarga: 90.512.273.408 bytes >= reserva 75.000.000.000 |
| :292 | ACTIONS_CHECKPOINT_RESTORE=PASS: 24 fragmentos SHA256, tar e identidad validados |
| :293/:296 | Posrestore: 54.858.973.184 bytes; pin Chromium conservado y depot_tools 8a5434051036b32412a2ecb10c213a72e3f3ccb9 |
| :2884/:2906/:2907 | Media GN real PASS; entrada S2; GN header check OK |
| :2951 | Compilación/link de recursos Chromium reales: Build Succeeded, 8 steps |
| :2952–2963 | Primer traceback auténtico: `ValueError: Wrong Portal pixels under mipmap/app_icon: res/mipmap-hdpi-v4/app_icon` |
| :2964–2966 | Work exit1; checkpoint quiescente; STAGED=PASS, 24 fragments. Run mantiene FAILED |

CAUSA_CONFIRMADA: el gate de contenido rechazó el recurso empaquetado; no falló AAPT2 compile/link ni ocurrió un enlace JNI posterior. Ningún gate de recursos completo PASS, Robolectric Chromium, JNI o APK se acredita con esta ejecución. Los warnings Node20/Node24 y punycode/urlparse están conservados; no son el primer fallo. La APK no existe como entrega verificada de este run.

Reproducción dirigida: leído `build/android/gyp/compile_resources.py` de **exactamente** cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 (copia de evidencia SHA256 `5e472cd0a584aeed1f08a86b4429b6d06945fa0b048dd781405ab7fde9e63aee`). `_ConvertToWebPSingle` invoca `cwebp -m 6 -q 100 -lossless`, sin `-exact`, y elimina la extensión. Ejecutadas las funciones reales extraídas por AST con cwebp 1.2.4 y los cinco PNG aprobados: cambiaron 62/32/567/567/1545 píxeles respectivamente, **todos con alpha cero**; diferencias de RGB visible/alpha: cero. La fixture anterior usaba `exact=True` y ocultaba esa diferencia. No se extrajo el `.ap_` fallido del runner: la atribución de sus bytes concretos a esta conversión sigue HIPÓTESIS hasta revalidación del árbol real; el defecto del verificador sí está reproducido con el convertidor fijado.

Fix mínimo: canonicalizar únicamente RGB cuando alpha == 0. Mantener comparación exacta de dimensiones, cada alpha y RGB con alpha > 0; sin modificar iconos aprobados. Negativos conservan rechazos de colores visibles, semitransparencia y alpha cambiado de cero a uno. `portal-transparent-red.log`: exit1, 12 tests/1 error antes del fix; `portal-transparent-green.log`: exit0, 12/12. La fixture usa ahora cwebp genuino con los flags exactos de Chromium, no `-exact` ni un encoder simulado. `portal-cwebp-aapt2-green.log`: compile/link/optimize reales PNG/WebP y manifest ajeno rechazado, exit0.

### Barrido de código y tres hallazgos adicionales reproducibles

Inventario inicial mediante `git ls-files`, incluyendo `.source-reference` y `.source-modified`: 435 archivos versionados, 311 de código/configuración; 116 Java, 47 C++, 25 headers, 26 GN, 12 GNI, 11 XML, 60 Python, 7 Bash y 7 workflows. Revisores independientes read-only de CI/recursos, Java y nativo; ningún escritor concurrente. No se afirma revisión/compilación completa de los millones de líneas upstream ausentes del workspace.

* **Validación monocromática incompleta (confirmado):** tres búsquedas de cadenas admitían `M 177 760 L 0 0 Z` y escalas incorrectas. Test negativo `vector-identity-red.log`: exit1, 1 failure. Fix compara toda la jerarquía, atributos, pathData completo, fill, viewport, dimensiones y transformaciones contra XML aprobado; normaliza números al float32 compilado. `vector-identity-green.log`: exit0, 18/18. `sweep-real-vector-aapt2.log`: exit0, AAPT2 SDK37 compila/enlaza los seis mutantes (path, scale, translation, viewport, fill, elemento extra) y el gate rechaza todos; el vector aprobado real pasa. Esto prueba fixture AAPT2 real, no sustituye recursos Chromium postrestore ni inspección final APK.
* **Presupuesto inseguro (confirmado por límites):** job180m permitía trabajo7200s + pack3600s sin descontar transferencia, startup ni uploads. Tests negativos `job-deadline-red.log`: exit1, 2 failures. Fix inicia deadline absoluto antes de descarga, reserva startup300s/upload1200s/pack3600s; preparación, slices y pack respetan tiempo restante. No aumenta timeout ni reduce reservas de disco; conserva máximo dos slices y 75m por slice. `job-deadline-green.log`: exit0, 2/2; agotamiento impide autoninja/prepare y conserva source remoto. Pruebas de routing son mocks y NO acreditan compilación/checkpoint de 25GB real.
* **Test de defaults obsoleto (confirmado):** esperaba tag 38018166249 tras seleccionar checkpoint nuevo. `post-failure-host-full.log`: exit1, 181 tests, 180 passed/1 failed/0 skipped. Se actualizan expectativas para tag/run/source SHA como unidad; suite focal 5/5 exit0. No se convierte fallo en skip.

Ruta heredada `dispatch-archium-r3-1-build.sh` retirada explícitamente (exit2, sin llamadas gh): usaba push puente e inputs incompletos, y ya fallaba cerrada. No fue causa del run 38147216573. Negativo con gh de fixture: RED exit1 antes, GREEN exit0 después. Único dispatcher válido continúa siendo baseline-build.yml/workflow_dispatch con expected_sha obligatorio y rama autorizada; push no dispara build pesado.

Barrido Java: archivos entregados/manifest coinciden, API30 getDisplay guardado y fallback null-safe, registro del test Chromium y dependencias WindowCore existentes; 28 strings/arrays y referencias de toolbar/drawables cotejadas con fuentes fijadas. Barrido nativo: pin y 95 fuentes/patch coinciden, owners de KeyProvider/PasswordString/StoredCredential/DeviceAuthenticator y pagos/JNI cotejados; tests APK conservan use_raw_android_executable=false. No nuevos Critical/Important confirmados en Java/C++. `gn desc` completo, javac/ErrorProne/NullAway/recursos generados, ninja query/símbolos actuales y enlace real permanecen UNVERIFIED/NOT_EXECUTED. No se toca payments ni política desktop sin evidencia.

### Checkpoint más reciente preservado, sin descarga local costosa

Source seleccionado: `archium-checkpoint-38147216573-1`, run 38147216573, SHA 5895d4a80510114ef12a89927c19667d4defeb27. Pack quiescente STAGED=PASS con 24 hashes completos en CI; uploads de los tres grupos completados. Grupos 03–07 no requeridos no se cuentan como pruebas ni artifacts existentes.

| Grupo | Artifact ID | Bytes ZIP | Digest remoto | Expira UTC |
|---|---|---|---|---|
| 00 | 11706169112 | 8589940404 | sha256:c36b173b5f1ab4b3e029462b456ccea86a0384a21502835348bc1cdae6c9f8cb | 2026-10-25T15:14:17Z |
| 01 | 11706452374 | 8589935970 | sha256:d1140ab37de91f2b1b56d187cccd51566727db3e6f21a8ddc0d78a2fb14e59ca | 2026-10-25T15:15:38Z |
| 02 | 11706437557 | 7964015208 | sha256:62b46a6967aa930106d8ce0096640d4221fddcfed119f6c68de821205ce8902f | 2026-10-25T15:16:57Z |

Total ZIP 25.143.891.582 bytes, expired=false. Lectura remota autenticada por rangos HTTP206 estrictos: 5213 bytes para manifest, no descarga repetida de25GB ni tokens/URL firmadas en informe. Manifest `new-checkpoint-38147216573.json`, SHA256 `5ef4e0623496a467c49be46b81ea7aabc08b9e5ec77900bbe87659dfa862d981`: pin/source/tag/workspace correctos, 24 fragmentos, compressed25143883014. Integridad nueva acredita hashes al empaquetar en CI y metadata/manifiesto remoto; **restore remoto completo de este checkpoint nuevo aún NO EJECUTADO**. El checkpoint anterior también sigue recuperable, sin borrado.

Disco local medido nuevamente: 81.153.990.656 bytes y 11.654.856 inodos libres, inferior al requisito aproximado100.143.891.582 bytes: FAIL local; no se descarga ni restaura aquí. DISK_PREFLIGHT=PASS de la ejecución refiere únicamente mediciones CI registradas antes de transferencia. Ningún umbral bajado ni output válido borrado.

Monitor corregido fuera del repo: al detectar job FAILED muestra **primer error real** del log, no últimas líneas de limpieza. Su SHA256 actualizado es `5f4a40ea6f34dd99c8068f8dbc697dd92ff05643c166f0f172936bf1fe844340`. Run fallido bloquea automáticamente descarga/instalación. No se instala una APK inexistente ni se fabrica ETA.

Verificaciones estáticas congeladas: git diff --check, bash -n de los7 scripts, compileall scripts/tests, ShellCheck0.9.0 de scripts/*.sh y actionlint1.7.7 de los7 workflows: exit0. Generador oficial dos veces + cmp + diff --exit-code: exit0; patchSHA256 `93813d3fa8831e1bcc5283f124bdbb7157ab8483f6ff4de5bfc6d9337a9bbc10`, manifestSHA256 `6cce6232029b0ec2f355b1ae31dd869dd509fd79750176b53df1f3479543a0e5`, 95 archivos. No cambios Java/C++/assets/GN en esta reparación posterior al fallo. La suite integral final se registra debajo cuando termine; ninguna corrida pesada adicional lanzada.

16:47 UTC, suite final estable: `ARCHIUM_TEST_GN=/usr/bin/gn ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar ARCHIUM_TEST_CWEBP=/usr/bin/cwebp python3 -m unittest discover -s tests -p 'test_*.py' -v`: **exit0, 190 passed, 0 failed, 0 skipped**, 537.863s; evidencia `sweep-host-final.log`. Incluye tres perfiles GN genuinos, AAPT2 genuino PNG/WebP con seis vectores alterados rechazados, JVM -ea/-da, integridad/ENOSPC/restore/delta de fixtures pequeñas, y negativos de presupuesto/dispatcher. No acredita compilación JNI, Chrome Robolectric ni APK nueva. La suite anterior181/1failure permanece registrada y no se presenta como PASS.

## 16:48–16:55 UTC — publicación y preflight remoto SUCCESS; parada solicitada

Recomparación antes de push: work branch remoto 4bc1c0a6fefa81def53f00ceb18124f71fe925f5, protegida 51e5ed429661727156ab2534caac99a82ee9264b. Tres commits pequeños publicados sin force, push exit0 hasta 1bd016c8408784340730765cc388d6c5c66465ad:

* [098c516bc78669b9e8b8aecf331684fd91c7c8d9](https://github.com/Jorgeprdz/chromium-dex-arc/commit/098c516bc78669b9e8b8aecf331684fd91c7c8d9): visible RGBA, identidad vector completa, fixture cwebp real, negativos y dependencia host.
* [ac6cd00b5b29f3fd3a6cfe7ba6c6a9bf3c01021f](https://github.com/Jorgeprdz/chromium-dex-arc/commit/ac6cd00b5b29f3fd3a6cfe7ba6c6a9bf3c01021f): presupuesto absoluto, defaults checkpoint coherentes, retirada dispatcher viejo y regresiones.
* [1bd016c8408784340730765cc388d6c5c66465ad](https://github.com/Jorgeprdz/chromium-dex-arc/commit/1bd016c8408784340730765cc388d6c5c66465ad): evidencia del run fallido y barrido.

Solo se disparó automáticamente el preflight barato [38156969002](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38156969002); **SUCCESS**, mismo SHA 1bd016c, job114521836204. Log auténtico `sweep-preflight-38156969002.log`: :486 GN10tests/0.165s y :488 OK; :704 AAPT2 genuino SDK36 fixture PASS; :980–984 **190 passed, 0 failed, 0 skipped**, 192.543s, dos fixtures AAPT2 PASS; :1042 STATIC_PASS/PYTHON_HOST_PASS/GN_REAL_PASS, scope media_fixture. Doble generación/cmp y actionlint CI también SUCCESS. Chrome Robolectric/JNI/APK permanecen pendientes, según log :1043. No se relanza build pesado ni se convierte el run fallido en success.

Usuario pide abrir mismo monitor y detener agente. Nueva sesión Termux #2 creada mediante atajo, seleccionada y verificada antes de teclear; monitor lanzado con `--run 38156969002 --sha 1bd016c8408784340730765cc388d6c5c66465ad --preflight`, PID16565. Mismo diseño ASCII/colores/bold/italic/600s; porcentaje refiere 8 checks requeridos y nunca fases nativas. Captura `termux-preflight-monitor-launched.png`: 4/8,50%, preparación/suite host activa. status.json y screen.txt posteriormente acreditan preflight_pass,8/8,100%,APK_VERIFIED=NOT_EXECUTED. Una captura final encontró otra app en primer plano: no se acredita inspección visual final100% ni se vuelve a interferir con el dispositivo. Al terminar el monitor espera Enter; no descarga/instala APK de un preflight. ETA=N/D. Tres tests del guard preflight: exit0,3/3 (success/failure/workflow distinto jamás llaman install); primera fixture falló por leer status en directorio equivocado y se corrigió, sin fallo de producción ocultado. py_compile/Bashsyntax exit0.

Hashes finales del monitor: Python `11506d368a29a391abe363fa363a66abcce14a066b097e930633907c877b5758`; lanzador `996ad151f74be15133c4cb1b017ff5424ad136d333f8ff9e21823327bdd4a465`. Observer gh run watch detenido localmente, sin cancelar CI. Monitoreo del agente termina por solicitud expresa; no nuevas pruebas/builds al cerrar. APK/package/hash/artifact/runtime=NONE/NOT_EXECUTED.

Estado final verificable: HOST_TESTS=PASS (190 locales y190 CI); GN_MEDIA_3_CASES=PASS; PATCH_REPRODUCIBILITY=PASS; P0 display/assert PASS en los alcances aislados previamente documentados. **BUILD=FAIL, BUILD_STAGE=S2, WORKFLOW_RUN=38147216573**; AAPT2_REAL_RESOURCES=FAIL refiere gate completo de ese run (compile/link sí pasó; validación contenido falló). Fix nuevo pasa fixture real, revalidación de Chromium fusionado PENDING. CHECKPOINT_SOURCE=archium-checkpoint-38147216573-1, CHECKPOINT_INTEGRITY=PASS al empaquetar/metadata remota; restore completo del nuevo pendiente. DISK_PREFLIGHT=PASS en CI anterior, FAIL local. ROBOLECTRIC Chromium/JNI_LINK/ANDROID_RUNTIME=NOT_EXECUTED. Protegida remota/local sin cambios. HEAD final será el commit documental de este cierre, comunicado por git después de publicarlo; código probado es 1bd016c. Bloqueo: única corrida pesada autorizada ya utilizada; se necesita nueva autorización expresa para otra corrida incremental, nunca clean build.

## 17:07–17:08 UTC — nueva autorización expresa, compilación y monitor

Usuario: «pero no era el run de compilación? lanza el run de compilación y monitor y stop». Esta instrucción autoriza **una nueva corrida incremental** y sustituye el bloqueo por la corrida anterior consumida; conserva todas las salvaguardas y solicita detener al agente después del lanzamiento/monitor. No se relanza automáticamente una tercera corrida ni se autoriza clean build.

Antes de dispatch: checkout limpio, branch assistant/archium-r3-visual-fixes, HEAD local/remoto `e386986c2831b2778bc11afdbd8020750ee77a88`; protegida remota permanece `51e5ed429661727156ab2534caac99a82ee9264b`. Comparación con SHA del preflight SUCCESS38156969002: solo cambió este documento; código y190 pruebas aprobadas no invalidados ni repetidos. API100runs devuelve cero workflows activos. Pin cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 conservado en script/manifest; los tres artifacts fuente vigentes/digests/sourceSHA correctos se revalidan por API. Manifiesto compatible leído previamente; no nueva transferencia local25GB. Disco CI se verificará antes de descarga dentro del run, PENDING ahora; local sigue insuficiente.

Comando exacto, exit0, **una sola llamada**:
```bash
gh workflow run baseline-build.yml --repo Jorgeprdz/chromium-dex-arc --ref assistant/archium-r3-visual-fixes -f expected_sha=e386986c2831b2778bc11afdbd8020750ee77a88 -f source_checkpoint=archium-checkpoint-38147216573-1 -f source_commit=5895d4a80510114ef12a89927c19667d4defeb27 -f source_run_id=38147216573
```

Run real [38158297048](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38158297048), created2026-10-11T17:07:05Z, event workflow_dispatch, path .github/workflows/baseline-build.yml, headSHA exacto e386986. API confirma IN_PROGRESS; job r3-final-gates114525712130 ejecutando verificación Portal en S0. Intento de listar con `gh run list --event` devolvió exit1 por flag no soportado en el CLI instalado; se usa endpoint API runs?event=workflow_dispatch, exit0. Es fallo de observabilidad CLI, no de CI ni motivo para repetir dispatch.

Monitor real relanzado en Termux #2 después de seleccionar/verificar prompt nativo; `/workspace/archium-r4-monitor-termux.sh` llama Python con `--run 38158297048 --sha e386986c2831b2778bc11afdbd8020750ee77a88`, **sin --preflight**. PID8321 confirmado vivo; captura `termux-build-monitor-38158297048-launched.png` inspeccionada muestra nuevo ID, EN CURSO, S0/0 de6 fases, elapsed00:00:56 y ETA N/D. Intervalo600s, r+Enter refresca, q+Enter sale; mismo ASCII/colores/bold/italic. API aún no publica log activo: panel etiqueta eventos API reales, no los presenta como stderr. Autoentrega mantiene gates originales de artifact, SHA/pin/report, Portal/aapt2, ABI, firma y hash antes de instalación; FAILED/INCOMPLETE bloquean instalación. APK/runtime siguen NOT_EXECUTED al traspasar.

Bashsyntax/py_compile exit0. Hash lanzador actualizado `4daffc2a39c6a0c2a5495f0009a52ca20a9b2cf25e740eff299167f631159590`; Python sin cambios `11506d368a29a391abe363fa363a66abcce14a066b097e930633907c877b5758`. Este nuevo commit documental posterior no cambia BUILD_SOURCE_SHA=e386986 ni genera build pesado. Estado al detener agente: WORKFLOW_RUN=38158297048, BUILD_STAGE=S0, BUILD=INCOMPLETE (en curso), CHECKPOINT_SOURCE=archium-checkpoint-38147216573-1 preservado, DISK_PREFLIGHT CI=PENDING, errores CI nuevos no observados, APK_PACKAGE/APK_SHA256/APK_ARTIFACT=NONE. Monitoreo queda independiente y manual como solicita usuario; no se afirma éxito de compilación.

## 17:29–18:36 UTC — segundo run FAILED y reproducción exacta barata

El run [38158297048](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38158297048), source e386986c2831b2778bc11afdbd8020750ee77a88, terminó FAILED; no se acredita compilación exitosa. API confirma S0 SUCCESS (jobs114525712130/114525998982), stage1/build114527154000 FAILURE, incomplete-budget skipped por needs fallido. Log completo auténtico `run-38158297048-stage-final.log`, SHA256 `62f605001e651adf41cc11dfcd2d734366b3e5eb399111f83f5cfce5e5c3b47f`.

| Línea/log real | Evidencia |
|---|---|
| :212–213 | Pretransfer PASS: 115.667.161.088 bytes disponibles, exigidos100.143.891.582; 18.975.584 inodos libres |
| :304/:308/:309 | Posdescarga90.523.103.232 bytes; restore completo PASS; posrestore54.917.693.440 bytes |
| :312 | Identidad pin Chromium/depot_tools conservada |
| :2938–2962 | S2, GN header check OK; recursos `ninja: no work to do`, Build Succeeded **0 steps**, 9.74s |
| :2963–2976 | Primer traceback real del gate, verify_themed_vector: `ValueError: Themed glyph has an unexpected attribute` |
| :2978–2979 | Checkpoint quiescente guardado, STAGED=PASS parts24,17:48:48Z; fallo permanece exit1 |

La anterior comparación RGB transparente ya no bloqueó: el código alcanzó el último vector después de comprobar los tres recursos de imagen y ambas cadenas adaptive-icon. No hubo trabajo nativo nuevo ni enlace JNI en este run. Tiempo perdido en restauración/verificación/guardar checkpoint, no en recomputar miles de objetos. Eso no convierte los45:25 de elapsed en éxito.

**CAUSA_CONFIRMADA por reproducción equivalente:** mi fixture anterior no reproducía los flags completos de Chromium y el parser exigía namespace textual. Fuente oficial exacta `build/android/gyp/compile_resources.py` del pin, :817–823: `--no-version-vectors --no-xml-namespaces`. `build/config/android/config.gni` del mismo pin confirma tools37.0.0/platform37.0. SDK37 AAPT2 real compiló/enlazó el vector aprobado con esos flags: dump produce `A: height(0x01010155)=108.000000dp` y los demás atributos sin prefijo, conservando IDs Android. El parser anterior produce el mismo ValueError que CI. No se extrajo el `.ap_` de este runner; el repro es genuino y acotado, no una afirmación sobre bytes que no se descargaron.

Pruebas RED antes del fix: `namespace-stripping-red.log` exit1,6 tests/1failure; `namespace-identity-red.log` exit1,8 tests/3failures (vector aprobado rechazado, ID foráneo con prefijo aceptado, atributo sin ID ignorado); `namespace-aapt2-red.log` exit1, fixture real con mismos flags falla en mismo gate. Nuevo fix acepta atributo sin namespace únicamente con **nombre e ID framework correctos**, comprueba lo mismo cuando tiene namespace y rechaza formatos/IDs desconocidos. Conserva comparación completa de estructura/transformaciones/fill/path; añade nombre/ID/ruta al error. No cambia iconos, XML aprobado, Java/C++, GN ni flags de Chromium.

`namespace-stripping-green-final.log`: exit0,9/9. Un intento intermedio de GREEN devolvió6errors por rsplit(':',1)[1] sobre nombre sin prefijo; se corrige a[-1]. `namespace-aapt2-green.log` conserva el fallo intermedio de un proceso que había importado ese parser antes de la corrección; su traceback leyó luego fuente actual mediante linecache. **No es PASS** ni evidencia de los archivos finales. La suite integral posterior queda congelada y es la evidencia válida; no se edita código durante ella.

Fixture genuina congelada `tests/fixtures/portal/themed-vector-sdk37-no-namespaces.xmltree.txt`, SHA256 `77bdc93b207f04b7b9fdb5c3c29bbd25784ad251c40b63dcd956877c45679d39`, con README/procedencia. Positivos PNG/WebP y todos los negativos AAPT2 usan ahora los dos flags reales. Los adapters Python ya no inventan IDs0x1. Preflight instala AAPT2 SDK37 (antes36), con SDK36 framework para estos atributos comunes; Chromium framework37/fusión completa sigue gate bloqueante separado, sin PASS anticipado. Test namespace también entra en r3-final-gates antes del restore.

Intento adicional con APK histórica ya disponible, SHA256 `76a91700048f20150c9b785e2ee339bd9955316df1f11664f5fd0b9ffa58cf3d`, devuelve exit1 porque carece de drawable/themed_app_icon. No sirve para probar el vector actual; no se descarta la verificación ni se marca PASS. Ninguna APK nueva descargada o instalada.

Revisión independiente read-only del diff final: no Critical/Important confirmados. Verifica IDs+namespaces, contenido completo, flags en cada link positivo/negativo, SDK37, gates antes de restore/native/APK y defaults coherentes. Señala correctamente suite integral aún en curso y limitaciones framework36 fixture/Chromium37 fusionado, Robolectric y native pendientes. No revisión adicional ni cambios especulativos por ausencia de evidencia.

### Checkpoint más reciente y preservación

`archium-checkpoint-38158297048-1`, source e386986c2831b2778bc11afdbd8020750ee77a88; pack CI verificó24 fragments y los tres uploads terminaron. Metadata remota y manifest leídos autenticadamente con solo5213 bytes por rangos HTTP206, exit0. Manifest SHA256 `efcc6eb063b1ae660ca97ea2928479c21f36e46e61da51c099f1837a8fb2a511`; pin/tag/source/workspace correctos, compressed25.143.564.170 bytes. Defaults workflow/test tag/run/source actualizados juntos a este source compatible; checkpoints anteriores conservados.

| Grupo | Artifact ID | ZIP bytes | Digest remoto | Expira UTC |
|---|---|---|---|---|
| 00 | 11710641789 | 8589940404 | sha256:4c6b562c5476b474b8df0ad481c5b2f5ebdf9c658854dd145d422348b1274d57 | 2026-10-25T17:48:49Z |
| 01 | 11710472129 | 8589935970 | sha256:2a36dc8a22dd01b965898b01b87d98d32bb49dc40dcd825564fa53fc2008b5b8 | 2026-10-25T17:49:39Z |
| 02 | 11710647071 | 7963696364 | sha256:ce045a65da299ed37c1b0ace3189829bb5108064ce93b020c8dd797d16636f38 | 2026-10-25T17:50:30Z |

TotalZIP25.143.572.738, expired=false. Integridad acreditada al empaquetar y metadata remota, no restore completo del nuevo checkpoint. Disco local80.858.398.720 bytes/11.653.507 inodos libres, insuficiente para~100.143.572.738 bytes: FAIL local, sin descargar25GB. CI deberá medir antes de transferir; ningún umbral reducido ni output/checkpoint borrado.

18:31:30 UTC, código congelado: git diff --check, compileall scripts/tests, bash -n todos scripts, ShellCheck y actionlint todos workflows: exit0. Generator oficial dos veces/cmp/diff exit0, patch93813d3fa8831e1bcc5283f124bdbb7157ab8483f6ff4de5bfc6d9337a9bbc10, manifest6cce6232029b0ec2f355b1ae31dd869dd509fd79750176b53df1f3479543a0e5. Suite integral con GN real/SDK37 AAPT2/cwebp en curso: `namespace-host-final.log`; resultado se añadirá al terminar. Todavía sin nuevo dispatch en esta reparación.

Usuario exige revisar antes de relanzar monitor y detener agente. Se explica que no es posible garantizar cero errores JNI/Robolectric sin ejecutar esos outputs reales; solo se acreditan gates observados, y próximos gates permanecen bloqueantes. Contingencia pedida: **si la siguiente corrida vuelve a fallar**, identificar último build exitoso verificable y crear nueva rama desde él para definir una reescritura. Esta es autorización condicional futura, no creación de rama ahora ni permiso de borrar checkpoints/Portal o modificar feat/arc-desktop. Alcance concreto de reescritura se definirá con evidencia, sin asumir reconstrucción de Chromium entero.

18:38 UTC, suite final congelada `namespace-host-final.log`: **exit0,199 passed,0 failed,0 skipped**,424.786s. Comando: `ARCHIUM_TEST_GN=/usr/bin/gn ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2 ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar ARCHIUM_TEST_CWEBP=/usr/bin/cwebp python3 -m unittest discover -s tests -p 'test_*.py' -v`. Dos fixtures reales PNG/WebP PASS con flags exactos, seis vectores alterados rechazados y manifest ajeno rechazado; GN genuino tres perfiles, JVM release/assert, checkpoint/corrupción/ENOSPC/mtime/symlink/delta y límites de routing. Revisión y resultados permiten publicar el fix, no acreditar JNI/Robolectric completos ni APK. La petición de relanzar después de revisar se interpreta como una nueva corrida incremental controlada **solo tras preflight remoto PASS**; no garantías ficticias de ausencia de errores ni reintentos automáticos posteriores.

## 18:40–18:50 UTC — preflight exacto SUCCESS y nuevo monitor de compilación

Push autorizado sin force: exit0, HEAD8234ab3 -> `dcbd868ea42ffd0991c01c2872adce01316a9768`. Commits [3923a3e0172f4b1dbe04aed0124970b812ad24a4](https://github.com/Jorgeprdz/chromium-dex-arc/commit/3923a3e0172f4b1dbe04aed0124970b812ad24a4) (parser IDs/namespaces + fixtures/negativos), [1abc09b0d8ec25ae3883112c38ff24b5638a6057](https://github.com/Jorgeprdz/chromium-dex-arc/commit/1abc09b0d8ec25ae3883112c38ff24b5638a6057) (SDK37/gates/defaults source), [dcbd868ea42ffd0991c01c2872adce01316a9768](https://github.com/Jorgeprdz/chromium-dex-arc/commit/dcbd868ea42ffd0991c01c2872adce01316a9768) (informe). Comparación remota antes de publicar/dispatch, protegida sigue51e5ed429661727156ab2534caac99a82ee9264b; checkout protegido local limpio, sin writers ajenos observados.

[Preflight38164764634](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38164764634), headSHA dcbd868, SUCCESS, job114544916334,6m23s. Log auténtico `namespace-preflight-38164764634.log`: :694 SDK37 install, :705 fixture real PASS, :713 herramienta real build-tools/37.0.0; :990 **199 passed,0 failed,0 skipped**,196.694s; :993–994 ambas fixtures reales PASS; :1052 static/host/GN PASS; :1053 ChromeRobo/JNI/APK pendientes. GN exacto con tres perfiles también SUCCESS; actionlint/doble generación/cmp exit0. Advertencia Node20/Node24 conservada, no presentada como ausencia de warnings. Solo después de este resultado se autoriza iniciar la ruta costosa.

API100runs sin workflows activos antes de dispatch; tres grupos último checkpoint vigentes/sourcee386/digests correctos revalidados. HEAD remoto esperado dcbd868 exacto. **Una sola llamada nueva**, exit0:
```bash
gh workflow run baseline-build.yml --repo Jorgeprdz/chromium-dex-arc --ref assistant/archium-r3-visual-fixes -f expected_sha=dcbd868ea42ffd0991c01c2872adce01316a9768 -f source_checkpoint=archium-checkpoint-38158297048-1 -f source_commit=e386986c2831b2778bc11afdbd8020750ee77a88 -f source_run_id=38158297048
```

Run real [38165289963](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38165289963), created2026-10-11T18:47:31Z, workflow_dispatch, baseline-build.yml, sourceSHA dcbd868. API confirma IN_PROGRESS; r3-final-gates114546481647 SUCCESS, r3-pre-native-gates/preflight114546776609 en curso S0. No descarga grande ni recursos fusionados nuevos acreditados al cerrar; disco CI PENDING pretransfer. Checkpoint38158297048 preservado como fuente, más los anteriores; cero clean builds.

Monitor existente relanzado en Termux #2, PID27792 real y argv `--run 38165289963 --sha dcbd868ea42ffd0991c01c2872adce01316a9768`, sin preflight mode. Prompt #2 verificado antes de escribir; transición de app requirió esperar animación antes de seleccionar (primer intento no seleccionó Termux correctamente). El estado almacenado y stdout real muestran nuevo ID/EN CURSO,elapsed00:02:26,0/6 fases,S0 GN FIJADO + TRES PERFILES; ETA=N/D. Captura durante inicio muestra el comando ejecutado; una posterior encontró otra app en primer plano, por lo que no se acredita inspección visual final del panel nuevo. Proceso y screen.txt sí están verificados. Monitor sigue en #2 mientras se utilizan otras apps.

Intervalo600s, ASCII/separadores/colores/bold/italic mantenidos, últimos3 eventos API cuando log activo no publicado; primer error auténtico si falla. Gates de SHA/pin/report, Portal, ABI, firma y hash siguen obligatorios antes de descarga/instalación exitosa; ningún artifact ni app nueva instalada ahora. No segunda llamada automática de compilación tras este dispatch. Hash lanzador `bf601bfa4995ccf069f30f18c5332417f46f546db391ac488582eb285d97ec58`; Python sin cambios `11506d368a29a391abe363fa363a66abcce14a066b097e930633907c877b5758`; bash -n/py_compile exit0.

Estado al parar agente por solicitud del usuario: BUILD_SOURCE_SHA=dcbd868ea42ffd0991c01c2872adce01316a9768, WORKFLOW_RUN=38165289963, BUILD_STAGE=S0, BUILD=INCOMPLETE (EN CURSO), HOST_TESTS/GN_MEDIA/PATCH=PASS; AAPT2_REAL_RESOURCES=PENDING para nuevo árbol fusionado, ROBOLECTRIC/JNI_LINK/ANDROID_RUNTIME=NOT_EXECUTED, APK_PACKAGE/APK_SHA256/APK_ARTIFACT=NONE. CHECKPOINT_SOURCE=archium-checkpoint-38158297048-1; integridad pack/metadata PASS, restore nuevo pendiente; DISK_PREFLIGHT CI=PENDING y localFAIL. HEAD final es commit documental de este traspaso, sin alterar código ejecutado ni desencadenar build pesado. Contingencia de nueva rama/rewrite solo si esta nueva corrida vuelve a fallar; no ejecutada ahora.


## 2026-10-11 20:12 UTC — tercer run fallido y recuperación desde el respaldo

Run real: https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38165289963
SHA compilado: `dcbd868ea42ffd0991c01c2872adce01316a9768`; job fallido
`stage1 / build` (`114547865034`). HEAD de trabajo al iniciar esta reparación:
`95e33b6bbf24a0afbbd1e8a6f3225e8abd2edc7e`.

**CAUSA_CONFIRMADA:** el export global de `JAVA_TOOL_OPTIONS= -ea`, añadido
para activar assertions en Robolectric, contaminó el siguiente compilador Java.
Primer bloque fallido, líneas 32033–32042 del log completo: target
`archium_password_manager_tests__apk__compile_java`, `compile_java.py
--chromium-code --warnings-as-errors`, stderr `Picked up JAVA_TOOL_OPTIONS: -ea`
y `Command failed because it wrote to stderr.` No error semántico de Java ni
undefined symbol observado en ese bloque. No se desactivan warnings ni assertions.

Log auténtico descargado con `gh api repos/Jorgeprdz/chromium-dex-arc/actions/jobs/114547865034/logs`
(exit 0), 35.430 líneas, SHA256
`3d4a61d99d5f5cd53aa7b6316bc722737384cd928ed153e69356ef11ce9158af`.
Copia local: `/workspace/archium-r4-evidence/run-38165289963-stage-final.log`.

Evidencia previa al fallo: línea 2963 `AAPT2_REAL_RESOURCES=PASS` sobre el
manifest fusionado real de Chromium. Línea 31997: gate temprano Robolectric PASS.
Contadores de las seis invocaciones reales: 2, 9, 2, 294, 208 y 62 = **577 tests**,
todos PASS. Incluyen detección de display y assert de TabListMediator. Esto no
acredita las suites host/Robolectric posteriores, que aún no se ejecutaron.
Líneas 32016–32017: terminó el enlace de
`libarchium_password_manager_tests__library.so`; el gate JNI completo, incluido
login_database y examen final de símbolos, quedó pendiente por el fallo siguiente.
La cola Mockito/VRI mostrada por el monitor no era la causa del fallo.

Corrección mínima en `scripts/build-archium.sh`: pasar `JAVA_TOOL_OPTIONS` mediante
`env` exclusivamente a cada runner Robolectric, sin exportarlo al shell de
compilación. `scripts/archium-test-gates.py` también usa un entorno de subprocess
separado, preservando opciones preexistentes. No cambian Java de producción,
GN args, pagos, iconos, patch ni toolchain.

Regresión con Java/javac auténticos en `tests/test_build_routing.py`: assertions
activas en cada JVM de prueba y ausencia de stderr del siguiente javac. Solo el
routing GN/checkpoint/native es simulado: no equivale a integración Chromium.
RED: exit 1, test fallido, proceso de build exit 83 con el mismo banner observado
(`java-env-red.log`). GREEN: exit 0, 1/1, 9,950 s (`java-env-green.log`).
Otra regresión comprueba que el gate Python conserva el entorno padre y las
opciones anteriores de la JVM; RED exit 1, GREEN exit 0.
El monitor local ahora reconoce el primer bloque Siso `FAILED:` y su stderr;
prueba sobre el log completo real: RED exit 1, GREEN exit 0 (1/1). No se
publica APK ni se instala una app al fallar el run.

Checkpoint preservado: `archium-checkpoint-38165289963-1`, fuente `dcbd868...`.
24 partes; 25.420.487.725 bytes comprimidos; grupos remotos 00/01/02 con IDs
11714115905, 11713197836 y 11713586345, no expirados, expiración 2026-10-25.
Manifest leído mediante HTTP Range (5.213 bytes transferidos, sin descarga total),
SHA256 `8fed39ac234c85804407670881835cf61ea02327de6733ee7262cc289fab07ac`.
Cada parte declara SHA256 y bytes; pack quiescente del CI PASS y uploads PASS.
**La restauración y verificación de todos los bytes de este nuevo checkpoint
no se ejecutaron localmente**. Disco antes de las consultas: 80.896.225.280 bytes,
11.653.029 inodos libres; FAIL para descargar ~25 GB y conservar la reserva de
75 GB. Fallback limpio prohibido; fuente remota aún recuperable.

Contingencia autorizada por el usuario: crear una rama de recuperación. Primero
se verificó el último build exitoso real 37968167514, SHA `ad55bbebf4429d4b61e4f43c7aa4dd575b0367f1`,
variante Arc/media **sin contraseñas locales**, anterior a Portal R4. Artifact
11640295535, 154.703.969 bytes, no expirado (2026-10-16), checksum remoto coincide
con APK local `76a91700048f20150c9b785e2ee339bd9955316df1f11664f5fd0b9ffa58cf3d`.
`apksigner verify --verbose` exit 0: firma v2 válida; `aapt2 dump badging` exit 0:
`app.archium.android`, ARM64. **Esta APK histórica no es la APK R4 final**.
Su pin también coincide con `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
Se conserva una referencia local `assistant/archium-r4-recovery-from-success`.

El usuario aclaró después que la base elegida es el respaldo protegido R3
`51e5ed429661727156ab2534caac99a82ee9264b`. Se creó y publicó (exit 0) la nueva rama
[`assistant/archium-r4-recovery`](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery)
desde ese SHA, sin cambios de código todavía. `feat/arc-desktop` permanece en
51e5ed4; `main` permanece en `6274c653bbe3992403a89b1531d0c1f91646bf6d`.
La rama R3/R4 conserva todo su trabajo. No reset, force-push, merge ni borrado.

Alcance de conservación confirmado por el usuario: sidebar y geometría Arc,
translucidez y preferencias de color, pestañas/favoritos/espacios, omnibox,
foco/hover/accesibilidad, Android Desktop/DeX y recursos Portal aprobados.
Blur/vibrancy real y validación en dispositivo siguen pendientes; no se declaran
implementados por existir código. Recuperación significa preservar y portar
cambios verificados y rehacer el flujo necesario, no reconstruir Chromium limpio.
El workflow de la base histórica todavía permite clean build y 12 etapas:
**NO es apto para dispatch R4 hasta portar las salvaguardas**. Su push pesado solo
escucha `feat/arc-desktop` + `.archium-final-dispatch`; publicar esta nueva rama
no dispara el build. No se lanzó ninguna nueva corrida pesada.

Verificación barata nueva: `git diff --check`, `bash -n`, `python3 -m compileall -q
scripts tests`, actionlint 1.7.7 y shellcheck: exit 0. Suite host completa:
PENDING al escribir esta entrada; se registrará su resultado al terminar.


## Recuperación: aclaración del usuario y cambio exclusivo de implementación

El usuario pidió reescribir los cambios posteriores al respaldo, no continuar
compilando la rama fallida. Desde esta aclaración solo se implementa en
`assistant/archium-r4-recovery`, base 51e5ed4. La reparación puntual de la rama
antigua no se publicó; sus pruebas 200/200 (sin fails/skips) quedan como oráculo
y diagnóstico. Ninguna nueva compilación Chromium está en curso.
Se reutilizan individualmente herramientas verificadas de checkpoint/transición
y recursos; no se copia el orquestador ni el conjunto de cambios de la rama vieja.
Plan y especificación: docs/superpowers/{plans,specs}/2026-10-11-archium-recovery.md.

## 2026-10-12 — Crash DeX posterior a la primera APK instalada

HEAD_START=`91e5937ffd57cc85b45418e22c3e0ef5fb5ae6f7`.
La APK del [run 38210970891](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38210970891)
se compiló e instaló; sus bytes instalados coinciden con el artifact:
`c4e48452380320867a7b8fad7711ea5e3b7d5683963b997a253a46b8eebefc3a`.
Package `app.archium.android`, ARM64, versión 157.0.8086.0 / 808600074.
La prueba del usuario confirma crash al abrir DeX: **ANDROID_RUNTIME=FAIL** para
esa APK. No se convierte el build exitoso en aceptación del navegador.

### Investigación y procedencia

`adb -s emulator-5554 logcat -b crash -d -v threadtime` y captura del log general:
exit 0. A las 07:24:29.164 aparece NPE en `pkg.onResult`, `tcg.e(boolean)`;
a las 07:45:35.120 aparece `ViewRootImpl cannot be cast to View` en `a7i.e`,
`q5h.s`, `l4h.f`. Líneas originales del crash buffer: **187175** y **187204**.
Se filtran exclusivamente las excepciones de Archium en
[excerpts](evidence/2026-10-12-dex-runtime/archium-exception-excerpts.txt).
El buffer completo permanece local; no se publican otros apps ni datos privados.

Se extraen classes.dex/classes2.dex de la APK real y se inspeccionan con
`dexdump -d` real del SDK bajo QEMU: exit 0. Los métodos/bytecode identifican
`ToolbarLayout.getLocationBarContentRect` y el callback de vertical tabs con
`TabStripTransitionCoordinator` nulo. No hubo mapping R8 disponible ni se inventó
uno. Se comparan clases fuente y tests descargados del pin exacto de Googlesource.

La corrección de estos casos ya existía en
[`1255da5`](https://github.com/Jorgeprdz/chromium-dex-arc/commit/1255da5745e3cd1453ff17f3b237cd3f97a24b58)
y la de posición de sugerencias en
[`a1f3f2b`](https://github.com/Jorgeprdz/chromium-dex-arc/commit/a1f3f2bb5d2e50437aca5b47c63014e38fa998a8).
Se habían omitido en la recuperación actual. Se recuperan los hunks concretos,
no el historial completo ni un refactor de la sidebar. **La omnibox sigue siendo
la LocationBar nativa en la sidebar.** El contrato de ancestro se adapta a
coordenadas de la ventana compartida; detach/otra ventana invalida el rect/lista.
ToolbarPhone no espera una transición horizontal inexistente; el callback limpia
estado/observadores. El caso tablet conserva suppress/unsuppress y resume.

`git fetch origin feat/arc-desktop`, exit 0, revela una referencia local obsoleta:
el local protegido tenía f71df25, mientras el remoto real sigue en 51e5ed4.
Se actualiza solamente origin/FETCH_HEAD. `git merge-base HEAD origin/feat/arc-desktop`
devuelve `51e5ed429661727156ab2534caac99a82ee9264b`. No se mueve la rama protegida.
`main` remoto sigue `6274c653bbe3992403a89b1531d0c1f91646bf6d`.

Se lee el prompt protegido R3 completo y se contrasta con implementación viva:
[matriz de 12 requisitos](ARCHIUM_R3_VERIFICACION_2026-10-12.md).
El color de selección normal incumplía la cápsula blanca; se reproduce y repara
solo ese estado, con contraste correcto y ramas mobile/incógnito/multi-select
conservadas. Tooltip de nueva pestaña compacta/navegación usa la etiqueta existente.
**Blur/vibrancy real no implementado**: fallback opaco configurable explícito;
WindowManager del teléfono muestra mBlurEnabled=false tras desconectar DeX,
lo que no prueba una limitación permanente del compositor externo.

### Comandos, RED/GREEN y gates

| Comando | Resultado observado | Alcance |
|---|---|---|
| `python3 -m unittest discover -s tests -p test_arc_toolbar_runtime.py -v` | RED exit 1; GREEN exit 0, 6 tests/12 escenarios | Métodos reales; doubles de servicios, no integración Chromium |
| `python3 scripts/test-android-arc-toolbar.py --device emulator-5554 --sdk /opt/android-sdk --platform-version 37.0 --build-tools-version 37.0.0 --display-id 17 --original` | RED exit 1 con ViewRootImpl real; sin `--original`: GREEN exit 0 | Instrumentación acotada en Samsung, display DeX |
| Mismo probe con `--original-dropdown` | RED exit 1, fallo de coordenadas de sugerencias en display 17 | Mismo contrato de ancestro de upstream |
| Probe final en display 17 tras desconectar DeX | Exit 1, SecurityException al lanzar en display ausente | Bloqueo de entorno, no PASS ni skip |
| Probe final `--display-id 0` | Exit 0: captura+sugerencias reparent/descendiente/detach/otra ventana | Android real; no navegador completo ni validación final DeX |
| `python3 -m unittest discover -s tests -p test_r3_active_tab_color.py -v` | RED exit 1: ffffffff != ffcacccf; GREEN exit 0 | Binder real ejecutado en límite JVM |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` con GN/Ninja/SDK reales | Exit 0, **242 passed / 0 failed / 0 skipped**, 481.682 s | PYTHON_HOST_PASS y GN_MEDIA_3_CASES PASS; no Robolectric/JNI PASS adelantado |
| `python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-36/android.jar` | Exit 0 | Aplicación patch/hash + Java puro + API SDK acotada |
| `python3 scripts/generate-arc-patch.py` dos veces + SHA256 | Exit 0, 109 files, hashes idénticos | PATCH_REPRODUCIBILITY=PASS |
| `git diff --check`, `bash -n`, `python3 -m compileall -q scripts tests`, ShellCheck y actionlint | Exit 0 cada uno | STATIC_PASS |

Patch SHA256 `455f96daed8a222c1769253bc8886feb95e36f5d816c91ce8d5bda9c0129dd8b`.
Manifest SHA256 `034955d92e9f5ec6d69de2b3da1e0ff12fd5f9e11b30b06afa36878d1408f276`.
Hashes de evidencias en [results.json](evidence/2026-10-12-dex-runtime/results.json).
No se toca payments, pin, toolchain, identidad Portal, preferencias de ancho ni
la deprecación del backend propio de contraseñas.

ChromeJUnit nuevo/ampliado se registra y ejecuta como gate fatal antes de libchrome:
`ArcToolbarReparentingTest`, `ArcTabSelectionTest`,
`TabbedRootUiCoordinatorUnitTest`, `OmniboxSuggestionsDropdownEmbedderImplUnitTest`.
También se incluye en la batería final de S3. **ROBOLECTRIC=PENDING_POST_RESTORE**,
**JNI_LINK=NOT_EXECUTED** para este candidato. Una regresión aborta enlace/APK.
Los resultados del run anterior no se trasladan como PASS al código nuevo.

### Checkpoint, disco y conectividad

El run exitoso 38210970891 solo publicó la APK, no checkpoint. Se mantiene la
fuente compatible más reciente: **archium-checkpoint-38203819481-1**,
source `2de41680a42972253e8daf4cf818938dacf79a93`, 25 fragmentos/4 grupos,
**26510091404 bytes** de artifacts; no expirados, 2026-10-26 05:26–05:29 UTC.
API IDs: 11727898692 / 11728410183 / 11728395785 / 11727764299.
Inventario, digests y permisos de lectura verificados. HTTP Range del manifest:
solo **5381 bytes**, hash
`c9c1ee1436df108c8c3a167bf47980e250ad73123bdf7507eb8c2b476448b02c`.
SHA/tag/pin/25 partes correctos; checksum completo de fragmentos PENDING_S1.

Disco local medido con statvfs: **75389485056 bytes**, **11614339 inodos**.
Requiere **101510091404 bytes** según política vigente. Gate CLI oficial local:
exit 1 por disco insuficiente, antes de descargar. **No se descargan 26 GB en
el teléfono, no se baja el umbral, no clean fallback.** La capacidad del runner
se mide como gate S0 del mismo workflow antes de S1; estado PENDING_S0 hasta
observar ese resultado remoto. Checkpoint fuente permanece recuperable.

Al salir de DeX/cambiar red hubo un fallo DNS transitorio en lectura Range,
exit 1; repetición posterior exit 0 con manifest coincidente y gh API/ls-remote
correctos. La compilación ocurre en GitHub; el monitor nativo Termux mantiene
wake-lock y refresco de 600 s. Mantener Termux sin optimización de batería y
con datos de fondo; no se promete supervivencia si Android mata el proceso.
Antes del dispatch se verifica ausencia de runs nativos activos, SHA remoto y
workflow manual/concurrency existente. El ID exacto se registra después del
dispatch autorizado. No se declara APK/runtime nuevo antes de ese resultado.

Revisión independiente read-only (superpowers:requesting-code-review): cero
Critical/Important establecidos; APIs y package visibility contrastados con pin.
Minor corregido: descripción del test de color precisada a su alcance real.
Minor pendiente de APK: posición vertical final del dropdown bajo la omnibox;
se incluye explícitamente en la aceptación DeX. Cambio final es comentario,
sin invalidar los 242 tests; patch regenerado dos veces, hashes finales arriba.
Termux ya figura en whitelist de batería y tiene PARTIAL_WAKE_LOCK activo,
observados con adb; no se cambian permisos ni configuración celular.

Runtime fix commit: `eaeac984687e999b86a4e6129e97698dd8721c77`; preparación final de patch
y API SDK repetida tras precisar comentario: exit 0. La batería 242/0/0
precede solo a ese cambio de comentario, sin cambio de comportamiento.

## 2026-10-12 — APK 38285899318 verificada; crash nuevo al enfocar la omnibox

Se retoma desde `7da34209c78510ae13e128765c6eb21bde955c88`, rama autorizada de
recuperación `assistant/archium-r4-recovery`. El usuario pausó la ejecución para
reunir defectos y luego autorizó «esos puntos + lo que ya habíamos señalado.
procede a fix y siguiente build». El respaldo `feat/arc-desktop` y `main` se
conservan. No se reinician contraseñas propias, pin, toolchain o identidad Portal.

Run [38285899318](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38285899318)
SUCCESS, 17:41:36–18:27:39 UTC, fuente exacta `7da3420`.
Los logs auténticos de build registran restore compatible, recursos reales,
enlace JNI y APK; 2090 ejecuciones de tests en 28 invocaciones ChromeJUnit
(incluyen la repetición temprana/final de suites; no son 2090 tests únicos).
Artifact `Archium-for-Android-arm64`, ID `11765172162`, 154869365 bytes,
vence 2026-10-19 18:25:16 UTC. ZIP SHA256
`c42c94cad2d21dceaa0dc9fa470d2cea97dbbf0d3084c9beda295fe5d3960d25`.
APK SHA256 `bdf31fe1c860b06821951d5c2f633248b02f6c46797e3e4e18f64fab0fc6c9ff`;
`sha256sum -c` y hash del `base.apk` instalado coinciden. `aapt2 dump badging`
exit 0: `app.archium.android`, exclusivamente `arm64-v8a`, versión 157.0.8086.0.
`apksigner verify --verbose` exit 0, firma v2 válida, certificado SHA256
`32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.

En teléfono arranque COLD observado PASS. En DeX display lógico 18 abre la
sidebar, pero tocar la omnibox produce FATAL EXCEPTION a las 13:15:53.929 del
teléfono, PID 14178: `LocationBarTablet` pasa el toolbar anterior a
`ViewUtils.getRelativeLayoutPosition`; al buscar ese ancestro que ya es un
hermano se llega a `ViewRootImpl`, y el cast a `View` falla. La causa es distinta
del bridge de Window.Callback reparado antes. Se conserva un
[extracto filtrado](evidence/2026-10-12-sidebar-fixes/omnibox-crash-excerpt.txt),
sin logs de otras aplicaciones, URLs de usuario ni capturas privadas.
Por tanto, BUILD anterior PASS y ANDROID_RUNTIME anterior FAIL son estados
compatibles; el APK candidato nuevo aún no existe.

### Fixes concretos tras la nueva autorización

| Causa raíz | Archivos y cambio mínimo | Regresión observada |
|---|---|---|
| Foco y fusebox usan ancestro obsoleto | Overlay `LocationBarTablet.java`: resolver contenedor real para headroom, márgenes y activation chip; conservar rutas nativas de ancestro y ventana | Código fijado anterior falla 10/14 ejecuciones; nuevo 14/14 PASS |
| Collection scroll reserva altura exacta | `ArcCollectionsView`: WRAP_CONTENT con tope AT_MOST; ocultar tira vacía de favoritos | Robolectric mide contenido corto sin panel reservado |
| Falta eliminación de espacio/carpeta | `ArcSidebarState`, `ArcCollectionsController`, vista y strings: confirmar, conservar tabs/pins/favoritos/IDs, promover hijos; persistir antes de notificar | Escritura fallida deja estado/comandos intactos; último espacio protegido |
| Favoritos pierden mosaico/tinte real | `ArcCollectionsView`: tiles cuadrados, favicon sin filtro; estilo propio después de refresh | Dimensiones y drawable reales; no se migra a ciegas el almacén de bookmarks Chromium |
| Color casi imperceptible y preview dividido | `ArcDesktopPolicy`/`ArcDesktopAppearance`/coordinator/binder: paleta perceptible, draft por ventana, cápsula tenue con contraste | JVM rechaza la mezcla anterior; Android prueba preview compartido, aislamiento, aplicar/cancelar |
| Padding del rail sigue blanco | `ArcDesktopCoordinator`: rail y frame reciben el mismo ColorDrawable; conservar padding y backgrounds móviles originales | Mutante con rail blanco falla 2/6; candidato 6/6 PASS |
| Compacto deja favicon/URL descentrados | Nuevo `ArcCompactOmnibox`: centrar icono nativo, restaurar edición en foco/expandir; preservar el control real y su touch | Mutante con hit bounds de URL falla; nuevo helper 28/28 PASS |
| Restauración compacta usa visibilidad antigua | Helper guarda estado nativo y estado aplicado; no sobrescribe cambios posteriores de Chromium | Helper anterior falla cinco métodos; 28/28 SDK29/36 tras fix |
| Acciones pedidas y trabajo repetido al animar | Coordinator: esfera multicolor, header como tiles, quitar Autofill; cachear paleta y texto sin cambiar animación nativa/viewport | API SDK real compila; fluidez y geometría final de nueva APK requieren dispositivo |

Se registran `ArcCompactOmniboxTest` en GN y el nuevo overlay del test upstream
`LocationBarTabletUnitTest`. Ambos son gates ChromeJUnit **antes de libchrome**,
además del gate final. El contrato host de suites se amplía: su mutante que
retira esas dos invocaciones falla con exit 1 y enumera ambas ausencias; el
contrato correcto pasa 2/2. No se elimina ningún test ni se convierte un fallo
en skip. Revisión independiente de lectura cerró el hallazgo de visibilidad;
cero Critical/Important pendientes establecidos, sin afirmar pruebas que el
revisor no ejecutó.

### Evidencia barata y límites de los PASS

[results.json](evidence/2026-10-12-sidebar-fixes/results.json) conserva comandos,
hashes de logs y alcance. Probes locales genuinos Robolectric SDK29/36:
foco 14/14, compacto 28/28, colecciones 14/14, frame 6/6; exit 0 cada uno.
Ejecutan código de producción/métodos verbatim y ventanas/vistas Android,
con adaptadores explícitos de recursos y servicios Chromium. **No equivalen
al runner completo ChromeJUnit ni a una APK corregida en DeX.** El SDK37 del
runner acotado local no está soportado: UNVERIFIED local, no PASS ni skip.

Comandos reproducibles de los probes de foco/compacto/frame son los scripts
`scripts/test-robolectric-location-bar-tablet-fixture.py`,
`scripts/test-robolectric-compact-omnibox.py` y
`scripts/test-robolectric-arc-frame.py`, con `--classpath-file`, `--java-home`
y directorio `--work` reales. Foco agrega `--view-utils-source` del pin.
Las opciones negativas conservadas permiten ejecutar la referencia anterior
o mutantes: `--source-stage reference`, `--unsafe-container-mutant`,
`--keep-url-hit-bounds`, `--white-rail-mutant` según el script correspondiente.

`python3 scripts/check-arc-preparation.py --android-jar
/opt/android-sdk/platforms/android-36/android.jar`: exit 0 después del helper
final; Java puro, contratos API SDK acotados y aplicación de los 113 archivos.
`git diff --check`, `bash -n`, `python3 -m compileall -q scripts tests` y
actionlint 1.7.7: exit 0. Generador oficial ejecutado dos veces, exit 0,
hashes idénticos: patch
`29470240438f48e3bbf03f8e0b1d40eb7420896e070231d1ba93cd6ae2711fdf`,
manifest `517fe16669d4f7dbfca314efc905f85619d02f78ccfa01112775895cf36e75b6`.
El resultado integral host se registra al completar la batería, no antes.

### Checkpoint y siguiente run

Se prioriza **archium-checkpoint-38275213327-1**, fuente
`3c75be2c5fd0aff4a9616e218498886895f088ba`. El run exitoso 38285899318 no publicó
otro checkpoint. Metadata remota fresca: cuatro grupos, 25 partes,
26506123626 bytes de artifacts, ninguno expirado; expiración más temprana
2026-10-26 16:58:07 UTC. IDs 11761207506 / 11760853238 / 11761855716 / 11760504441.
Lectura autenticada HTTP Range exit 0, solo 5381 bytes; SHA/tag/pin y hashes de
partes del manifest correctos. Manifest SHA256
`1771b7a6bda7be8c0b76bcb30cd04c0bc7202ec7a93f624a6245f29574e75004`.
Ese mismo checkpoint superó checksum/restore íntegro en 38285899318; los bytes
descargados por el siguiente run se verificarán de nuevo en S1.

Disco local medido: 74358464512 bytes libres, 11611025 inodos; insuficiente para
la política de 101506123626 bytes. No se descarga el checkpoint al teléfono ni
se reduce el umbral. **DISK_PREFLIGHT local FAIL; capacidad runner PENDING_S0**,
bloqueante antes de la descarga masiva. Remoto fuente conservado recuperable.
Consulta Actions antes de publicar: ningún run activo. Workflow real
`baseline-build.yml` (ID 374835814), solo workflow_dispatch, cuatro inputs
expected_sha/source_checkpoint/source_commit/source_run_id, needs secuencial,
concurrency común sin cancelación. Un solo dispatch nuevo tras gates y push.
SHA final/ID/URL se registran al observarlos; no se inventa actividad ni APK.

DeX puede desconectarse: logs y capturas necesarias ya están guardados. Se
requiere reconectar para aceptar el runtime de la próxima APK. El monitor
debe fijar el nuevo ID y SHA, refrescar cada 600 s, y descargar/instalar solo
después de SUCCESS y verificación de APK. Después del handoff se detiene el
trabajo automático, como pidió el usuario.

### Cierre de gates antes del push del candidato

Primera batería host: exit 1, 243 tests / 242 passed / 1 failed / 0 skipped,
627.388 s. Único fallo: expected filter set del contrato host faltaba ampliar
para las dos suites nuevas. Se corrige el contrato conservando ambas invocaciones
reales; gate dirigido 2/2 PASS, mutante con invocaciones retiradas exit 1.
Repetición completa tras congelar el código: **exit 0, 243 passed / 0 failed /
0 skipped, 537.243 s**, GN/Ninja/AAPT2/SDK reales. GN arm64, baseline y x64 PASS.
Avisos JDK/Mockito/deprecación de probes permanecen visibles en logs; no se
convierten en skips ni se ocultan. Los cinco scripts Bash se verifican por
separado con `bash -n`, exit 0; ShellCheck sobre recovery exit 0.

STATIC_PASS=PASS; PYTHON_HOST_PASS=PASS; GN_REAL_PASS=PASS (tres perfiles en
fixture real GN); PATCH_REPRODUCIBILITY=PASS; AAPT2_REAL_RESOURCES=PENDING_S2;
ROBOLECTRIC_PASS=PENDING_POST_RESTORE para el runner completo Chromium;
JNI_LINK_PASS=NOT_EXECUTED; APK_VERIFIED=NOT_EXECUTED; ANDROID_RUNTIME nuevo
NOT_EXECUTED. Los 62 tests Robolectric acotados locales tienen su alcance
propio explícito y no cambian esos estados nativos.

Los commits se agrupan en foco, colecciones y paleta/compacto. Cada snapshot
del índice regenera su patch/manifest mediante el generador oficial; el working
tree validado permanece congelado. Solo se publica el HEAD final completo y
solo ese SHA puede despacharse. No se realizan ediciones manuales del patch.

### Dispatch y handoff observados — run 38302845518

Tres commits temáticos probados y publicados, push exit 0 sin force:

- [Foco ee09fb5](https://github.com/Jorgeprdz/chromium-dex-arc/commit/ee09fb57738ed911579f790fac5cf6a0ae85896d).
- [Colecciones 0b90997](https://github.com/Jorgeprdz/chromium-dex-arc/commit/0b90997f454a80d67ae6f55949018d245d3ae23a).
- [Paleta/compacto 109c9c5](https://github.com/Jorgeprdz/chromium-dex-arc/commit/109c9c5b8d30416e8122a8f17ef43c3832a5c7ad).

Generación oficial de cada snapshot del índice: 111 / 111 / 113 archivos,
patch y manifest coherentes en cada commit. Working tree probado sin cambios
durante el agrupamiento. HEAD remoto vuelve a comprobarse antes del push.
`feat/arc-desktop` remoto `51e5ed429661727156ab2534caac99a82ee9264b` y `main`
`6274c653bbe3992403a89b1531d0c1f91646bf6d` permanecen intactos.
Triggers inspeccionados: el push a recovery no dispara compilación pesada.

`gh workflow run 374835814 --repo Jorgeprdz/chromium-dex-arc --ref
assistant/archium-r4-recovery -f expected_sha=109c9c5b8d30416e8122a8f17ef43c3832a5c7ad
-f source_checkpoint=archium-checkpoint-38275213327-1
-f source_commit=3c75be2c5fd0aff4a9616e218498886895f088ba
-f source_run_id=38275213327`: **exit 0**, un solo dispatch, 2026-10-12T20:13:52Z.
Run real [38302845518](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38302845518), SHA exacto verificado por API.
Authorize PASS; preflight en progreso, actividad observada Build genuine GN
at Chromium DEPS pin. Ningún otro run estaba activo antes de despachar.
No se presume PASS de preflight remoto, restore, JNI, recursos o APK futuros.

Monitor nativo abierto y observado en **sesión Termux #4**, PID **29885**,
cmdline exacta con RUN/SHA; pantalla real con separadores coloreados, bold e
itálica. Refresco de 600 s, elapsed y 0/6 fases verificadas, ETA N/D. Antes de
publicarse logs, muestra explícitamente eventos API; después usa log auténtico
con tres líneas/primer error real. Descarga e instala solo ante SUCCESS del
SHA fijado y verificación de la APK; un fallo no instala nada. Las sesiones
#1/#2/#3 se conservan. `bash /data/data/com.termux/files/home/archium-r4-monitor-termux.sh`
y `./m4` apuntan a este run. Este registro posterior solo modifica documentación;
el SHA probado y usado por CI sigue siendo `109c9c5b8d30416e8122a8f17ef43c3832a5c7ad`.
Se entrega el monitor y se detiene trabajo automático según petición del usuario.

Estado del **código despachado**, a la entrega (no resultado final del run):

```text
REPO=Jorgeprdz/chromium-dex-arc
BRANCH=assistant/archium-r4-recovery
PROTECTED_BRANCH=feat/arc-desktop UNTOUCHED
HEAD_START=7da34209c78510ae13e128765c6eb21bde955c88
HEAD_FINAL=109c9c5b8d30416e8122a8f17ef43c3832a5c7ad (HEAD final de código antes del dispatch)
CHROMIUM_PIN=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
P0_DEX_DISPLAY=UNVERIFIED (integración nueva programada; detección previa observada)
P0_JAVA_ASSERT=PASS (ejecución JVM host de debug/release, alcance acotado)
AAPT2_REAL_RESOURCES=PENDING (S2 del nuevo run; fixture aislada PASS)
GN_MEDIA_3_CASES=PASS
PATCH_REPRODUCIBILITY=PASS
CHECKPOINT_SOURCE=archium-checkpoint-38275213327-1
CHECKPOINT_INTEGRITY=PASS (fuente validada en 38285899318; transferencia nueva pendiente S1)
DISK_PREFLIGHT=FAIL (local; runner PENDING_S0 antes de descarga)
HOST_TESTS=PASS (243 passed / 0 failed / 0 skipped)
ROBOLECTRIC=NOT_EXECUTED (Chrome completo nuevo; probes reales locales 62 PASS)
JNI_LINK=NOT_EXECUTED
COMMITS=ee09fb57738ed911579f790fac5cf6a0ae85896d,0b90997f454a80d67ae6f55949018d245d3ae23a,109c9c5b8d30416e8122a8f17ef43c3832a5c7ad
PUSH=PASS
WORKFLOW_RUN=38302845518 https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38302845518
BUILD_STAGE=S0
BUILD=INCOMPLETE (en curso)
APK_PACKAGE=NONE
APK_SHA256=NONE
APK_ARTIFACT=NONE
ANDROID_RUNTIME=NOT_EXECUTED
BLOCKERS=NONE observado nuevo; gates nativos/recursos/disco de runner pendientes y bloqueantes
```

## 2026-10-12 — Run 38302845518 SUCCESS, APK verificada e instalada

Usuario entrega pantalla del monitor con SUCCESS / 6 de 6 fases / instalación
installed. Se comprueba de nuevo por API: authorize, preflight y build SUCCESS,
SHA fuente exacto `109c9c5b8d30416e8122a8f17ef43c3832a5c7ad`. No se despacha otro workflow ni se abre
el navegador automáticamente. [Run real](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38302845518).

Log auténtico descargado del job 114991500347, 10138838 bytes. Evidencia:
S0 DISK_PREFLIGHT PASS, 114592133120 bytes libres / 18963627 inodos;
restore del checkpoint fuente PASS; host CI 243/0/0, 215.594 s;
Robolectric temprano y final PASS, 2322 ejecuciones OK (incluye repetición de
suites, no tests únicos), cero marcadores FAILED/SKIPPED. Las suites nuevas
ArcCompactOmniboxTest y LocationBarTabletUnitTest ejecutan casos reales del
runner Chromium, incluidas las regresiones de foco/ancestry y visibilidad.
JNI_LINK_PASS PASS a las 21:03:47 UTC; libchrome real enlazada y símbolos
payments verificados. Gate final Portal PASS, firma APK v2 válida y metadata
remota del artifact PASS. Los gates del script son fatales y preceden la
publicación; no se trasladan estados de un mock a estos resultados.

[Artifact APK](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38302845518/artifacts/11773513326): ID 11773513326,
154881489 bytes, expira 2026-10-19T21:14:32Z.
Digest ZIP metadata remoto `sha256:379091b54cc1c43e2d7fc2f3f5bd109ed4f7ab3091ce3beda4b5d8591e5380aa` (no se repite su descarga).
APK local 366977536 bytes, paquete `app.archium.android`, SHA256:

```text
75983bf7af3d6a6fb039a2a91a6263aa59ef8a764f60d5e3333691739f344ff9
```

El monitor verificó manifest/Portal, firma/checksum y realizó instalación -r.
Se vuelve a calcular SHA256 de la APK descargada y del base.apk instalado:
**idénticos**, exit 0. ZIP contiene ocho bibliotecas exclusivamente arm64-v8a;
se leen sus headers ELF y se verifica clase 64 bits/machine AArch64 (183), PASS.
No se reinstala por segunda vez ni se borran datos. Registro verificable en
[build-success.json](evidence/2026-10-12-sidebar-fixes/build-success.json).

BUILD=PASS; APK_VERIFIED=PASS; PUSH=PASS; ROBOLECTRIC=PASS; JNI_LINK=PASS;
GN_MEDIA_3_CASES=PASS; AAPT2_REAL_RESOURCES=PASS; PATCH_REPRODUCIBILITY=PASS;
CHECKPOINT_INTEGRITY=PASS; DISK_PREFLIGHT del runner=PASS;
APK_PACKAGE=app.archium.android; APK_ARTIFACT=https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38302845518/artifacts/11773513326;
ANDROID_RUNTIME=NOT_EXECUTED para esta nueva APK. La instalación no prueba
que desapareció el crash ni valida la fluidez/colores/geometría en DeX.
Se conserva el checkpoint remoto fuente; este run exitoso publica solo la APK.
Contraseñas propias continúan DEPRECATED. Feat/main no se modifican.

Siguiente aceptación manual: conectar DeX, enfocar/editar la omnibox varias
veces, comprobar sugerencias y navegación; expandir/colapsar la sidebar;
preview/aplicar/cancelar colores y contrastes; mosaicos y eliminación con
confirmación de carpetas/espacios. Eliminar espacios/carpetas solo si el
usuario decide probarlo: no se realizan acciones sobre sus datos aquí.
# Verificación física DeX posterior al run 38302845518 — 2026-10-12

APK instalada de source SHA `109c9c5b8d30416e8122a8f17ef43c3832a5c7ad`;
hash `75983bf7af3d6a6fb039a2a91a6263aa59ef8a764f60d5e3333691739f344ff9`.
La compilación sigue SUCCESS, pero la aceptación visual en dispositivo es **FAIL**.
Registro curado: [runtime-dex.json](evidence/2026-10-12-sidebar-fixes/runtime-dex.json).
No se modificó código de producción ni se despachó otra compilación durante esta revisión.

El Samsung físico está conectado a DeX, display lógico 19, 1920×1080.
Se capturó el proceso principal 28931 con `adb logcat --pid=28931 -v threadtime -T 1`.
`adb shell pidof app.archium.android` mantuvo el mismo PID después de las acciones;
el registro capturado no contiene `FATAL EXCEPTION`, `Fatal signal` ni `ClassCastException`.
Esto demuestra ausencia de esos fallos en la sesión observada, no ausencia universal de crashes.
Persisten advertencias no fatales de permisos de localización y de `requestLayout`.

Secuencia verificada, aproximadamente 22:02–22:15 UTC:

- Omnibox expandida: enfocar, `input -d 19 keycombination 113 29` (Ctrl+A),
  `input -d 19 text https://example.org/`, `input -d 19 keyevent 66`: exit 0.
  Antes de cada evento de teclado se comprobó `mCurrentFocus` de Archium mediante
  `dumpsys window displays`. La captura final muestra example.org cargado.
  Los intentos anteriores con foco cambiado a Termux o texto concatenado no acreditan fallo de navegación.
- Colapsar/expandir: el icono nativo queda centrado y no se produjo crash.
  El `+` de nueva pestaña es invisible; pulsar su área crea una pestaña real.
  `dumpsys activity app.archium.android` muestra su TextView VISIBLE, bounds
  locales `0,132–52,176`; no se ha demostrado todavía por qué deja de dibujarse el texto.
- Selector: seed actual `#DA886B`; preview lavanda cambia marco y rail.
  Cancelar restaura RGB `(229,176,157)` en ambos. Se conservó el color del usuario.
- Carpeta temporal `R4_TEST_FOLDER_38302845518`: crear → pulsación larga →
  Eliminar carpeta → confirmación. La carpeta desapareció. No se probó en dispositivo
  una carpeta con hijos; ese contrato conserva su evidencia de tests, no un PASS físico nuevo.
- Espacio temporal `R4_TEST_SPACE_38302845518`: crear → eliminar con confirmación →
  retorno a Personal. Su pestaña abierta permaneció visible. El menú bloquea eliminar
  Personal cuando es el último espacio.
- Favorito temporal: añadir example.org → menú de pulsación larga → quitar.
  El estado se actualiza, pero el mosaico no tiene superficie visual distinguible:
  su fondo usa el mismo `mSurface` que la sidebar. El placeholder de una URL sin favicon
  no permite acreditar la conservación de colores de un favicon real.
- Limpieza: se retiraron carpeta, espacio y favorito de prueba, y las tres pestañas
  creadas por nuestras pruebas. Se conservaron las tres pestañas restantes y el color actual.
  El colector de logcat se cerró deliberadamente con SIGINT (exit 130).

Defectos reproducidos, todavía sin corregir en esta APK:

| Defecto | Observación | Estado de causa raíz |
| --- | --- | --- |
| Omnibox no sigue el color | Fondo RGB `(230,232,239)` frente a marco `(229,176,157)` | CAUSA_CONFIRMADA en el código: `tintHeader` excluye `mLocationBarHost`; los fondos nativos mantienen su esquema Chrome. |
| Barra blanca sobre el contenido | Aproximadamente 55 px sobre páginas web; no se ve igual en NTP nativa | HIPÓTESIS: textura de toolbar compuesta sigue activa. Se oculta ToolbarTablet y se retira su layer del stack, pero eso no equivale a suprimir `TopToolbarOverlayMediator`. |
| Cuña inferior entre visor y sidebar | Persiste expandido/colapsado y en página nativa/web, dentro del gap de 8 px | HIPÓTESIS: discrepancia entre outline/hole de SurfaceView y clip del holder; requiere prueba gráfica, no basta el contrato matemático host. |
| `+` colapsado invisible | Acción nativa funciona al pulsar la zona vacía | UNVERIFIED: geometría y visibilidad del TextView existen; falta identificar la causa de dibujo. |
| Mosaico de favorito sin contraste | Icono aparece directamente sobre la sidebar | CAUSA_CONFIRMADA en estilo: tile y rail usan la misma superficie. |

Se descargaron únicamente dos fuentes pequeñas de Gitiles en el pin exacto
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, sin checkout/build nuevo:
`TopToolbarOverlayMediator.java` SHA256
`c34294cdd30ecacdb75e7f7efa456e1782f766d441fa1724dd49a062af7325d5`
y `TopToolbarOverlayCoordinator.java` SHA256
`54ade314d8c003edb1f062e7a3cd8a85e1266d01b9765d8d4315b942285139af`.
El método `updateVisibility()` de la revisión fijada no toma View.GONE como señal
de supresión del overlay. La hipótesis de barra necesita aún una regresión que
falle con el comportamiento actual antes de acreditar el fix.

`uiautomator dump` devolvió exit 0 con `ERROR: could not get idle state`; esa salida
se considera **UNVERIFIED**, no PASS. Las capturas, dumps y logs sin filtrar se
conservan fuera de Git por contener pantalla e historial del usuario; el JSON
publicado guarda nombres y hashes sin publicar su contenido.

No se han verificado aquí cold start, sugerencias de autocomplete ni frame pacing.
Los PASS específicos de esta sesión no convierten la aceptación completa de Android
ni la paridad visual R3 en PASS mientras persistan los defectos anteriores.

## 2026-10-12 — Corrección de defectos físicos y Acerca de Archium

HEAD_START `9e56a8d817320ad09b0815bc5aa49a0558ecb5e1`. El usuario autoriza reparar,
lanzar build incremental y continuar hasta instalar. Se usa un solo agente, logo
aprobado existente, versión real de PackageManager y ningún cambio de contraseñas.
Registro de gates: [next-build-preflight.json](evidence/2026-10-12-sidebar-fixes/next-build-preflight.json).

La barra superior se trata mediante la señal de supresión del overlay de ToolbarManager,
combinada con XR y auto-hide por anchura; GONE y retirar TopControlsStacker no bastaban.
Regresión JVM ejecuta la expresión de producción: mask=4 falla antes (exit 1) y los
8 estados booleanos pasan después (exit 0). Se conservan las señales existentes.

La omnibox conserva drawables nativos, focus ring y hover, tintando fondos normales
y popup hacia la superficie Arc. El tinte combina 35% del fondo Chrome y 65% del
marco para mantener las familias de tonos claro/oscuro. Se restaura al dejar Arc.
La inspección detectó antes de CI que LocationBarTablet no es pública; se expone
el hook en LocationBarLayout, con comportamiento original en teléfono.
Hay dos regresiones nuevas en LocationBarTabletUnitTest, bloqueantes dentro del run.

El + compacto utiliza ic_add_24dp nativo con padding centrado; deja de depender del
glifo del TextView. Los mosaicos favoritos usan activeTabSurface y mantienen el
favicon sin filtro. Holder y SurfaceView reciben un clip rectangular además del
outline; los límites originales se restituyen. La hipótesis de hole punch todavía
necesita confirmación física posterior al build. No se han empleado APIs ocultas.

Acerca de Archium se abre con un botón informativo en el footer; muestra el icono
real de aplicación y versionName/versionCode, y libera su diálogo al destruir el
coordinator. La prueba del diálogo pasa en API29/36 (2 ejecuciones); un mutante que
usa «R4» como versión falla en ambos perfiles. El nuevo test se registra en GN y
en ambos puntos de ejecución bloqueante de Robolectric, sin skips.

Pruebas locales acotadas: frame 8/0, shell 6/0, about 2/0. Se ejecutan Android
views/drawables reales con adaptadores explícitos de Chromium. No equivalen al
runner completo de Chromium ni prueban SurfaceFlinger. Las negativas previas
detectaron falta de clip, drawable ausente, mosaico sin distinción y color ignorado.

La primera suite host completa dio 244 tests, 3 fallos, 0 skips (exit 1): inventario
de suites sin About y dos tests AAPT2 sin ARCHIUM_TEST_ANDROID_JAR. Se añade About
al inventario esperado, sin debilitar la comparación, y se repite con Android37.0
y aapt2 37.0.0 reales. No se lanzó CI con ese gate rojo.

Patch regenerado dos veces; aplicación completa sobre archivos originales del pin
y comparación de todos los hashes modificados: PASS. Es un árbol de referencia
acotado, no una compilación GN de Chromium. Bash, compileall, actionlint 1.7.7 y
diff-check pasaron. La aplicación y recursos del checkout completo quedan bloqueantes
tras restore, así como Java real, Robolectric y enlace nativo.

Checkpoint compatible más reciente: archium-checkpoint-38275213327-1, source
3c75be2c5fd0aff4a9616e218498886895f088ba; 4 grupos, 26,506,123,626 bytes.
Expira el 26 de octubre. Lectura autorizada, metadata y manifest: PASS; lectura
remota acotada 5,381 bytes; SHA256 de manifest
1771b7a6bda7be8c0b76bcb30cd04c0bc7202ec7a93f624a6245f29574e75004.
No se descarga el checkpoint localmente. El workflow mide bytes/inodos reales
antes de transferir y valida todos los fragmentos en S1; ese resultado sigue pendiente.
No hay clean fallback ni eliminación de fuentes/outputs compatibles.

Host final: 244 passed / 0 failed / 0 skipped, 561.765 s, exit 0. Los tres perfiles
GN reales y las dos regresiones AAPT2 con SDK37.0 pasan. El último manifest se
comparó con cada fuente; aplicaciones/hashes de patch completos coherentes.
La incorporación de Objects.requireNonNull en el drawable conocido evita
desreferenciar un Drawable nullable; no cambia el recurso nativo elegido.
Los diagnósticos de tar/HTTP de fixtures negativas son esperados; no se ocultan
como un supuesto stdout sin advertencias.

## 2026-10-12 — Primer dispatch nuevo, fallo barato y reparación

Commit ca48f6a0267ecb576634d83bcbd04c5943aed2a5,
[run 38319319640](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38319319640),
[job 115043392253](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38319319640/job/115043392253).
S0 falló en javac a las 22:58:25Z; build SKIPPED. No se descargó ni restauró el
checkpoint ni se ejecutó trabajo nativo. No hay output nativo nuevo que recuperar.

CAUSA_CONFIRMADA, log API del job (67,933 bytes), líneas 667 en adelante: siete
errores, LocationBarLayout ausente en los contratos de la fixture, ic_add_24dp
ausente en R sintético, y ArcDesktopPolicy sin import en ArcCollectionsView.
El entrypoint check-arc-preparation.py no se ejecutó antes del primer dispatch;
la suite unittest anterior no cubría esa compilación aislada completa.

Se añade el import real de producción y se actualizan exclusivamente los contratos
de tipo de la fixture con el hook público entregado y el drawable del XML fijado.
Una negativa exige autoridad del hook público y rechaza un drawable inventado;
el probe javac ejecutado ahora referencia también ic_add_24dp. Los contratos
sintéticos no prueban runtime Chromium ni recursos finales.

La negativa local reproduce los mismos siete errores (preparation-red-local.log,
exit 1). Después del import/contratos, el entrypoint completo termina exit 0
(preparation-green-local.log); se vuelve a ejecutar con la validación de autoridad
adicional antes de publicar. Un intento local con patch sin regenerar fue rechazado
como Stale patch: ArcCollectionsView; se regeneró por el script oficial antes de
continuar. Se mantiene bloqueado el enlace pesado hasta finalizar todos los gates.

El segundo host completo terminó 245 tests / 1 fail / 0 skips, 736.695 s,
exit 1: test_global_cut_waits_for_ninja_sigint_flush_before_packing produjo exit 9
del pack al no existir el log de flush. Ejecutado aislado dio 1/0/0, exit 0.
Una reproducción controlada consume los 4 s en restore: exit 9 y cero llamadas
a autoninja, mismo stderr; confirma que el límite de la fixture puede vencer
antes de llegar al comportamiento que pretende comprobar. La carga concurrente
como explicación del caso original es HIPÓTESIS; no hay evidencia de un defecto
en el timeout nativo de producción.

La fixture permite 12 s de preparación/trabajo y mantiene al Ninja sintético
esperando 60 s: SIGINT real sigue siendo obligatorio antes de que termine.
Se exige explícitamente que haya arrancado autoninja, complete=false y el contenido
exacto «flushed after SIGINT» antes de aceptar el pack. No se cambian slices,
reservas ni budgets de los scripts de producción. Se repite la suite completa
sin probes concurrentes. Los resultados fallidos anteriores permanecen registrados.

Host final de la reparación: 245 passed / 0 failed / 0 skipped, 641.061 s, exit 0,
SDK36 y aapt2 37.0.0 como CI. La suite incluye los tres perfiles GN reales.
Entrypoint completo check-arc-preparation: exit 0, 117 archivos aplicados y hashes
coherentes; Android adapters compilados con dependencias sintéticas declaradas.
AAPT2 fixture independiente: exit 0, 18 recursos; no es la fusión final de Chromium.

Doble generación: patch 121256adbdb0ff92319465c8239a2e02086b505c42829e63f216211bf6f815e0;
manifest 456bcfadeb7f9df2b2f74ec186a2dd484d167da582e109072e3a4c7fae1093dd.
Metadata remota reconsultada: 4 grupos válidos no expirados, 26,506,123,626 bytes.
El checkpoint remoto permanece disponible; no se ha descargado localmente.

## 2026-10-13 — Build incremental verificado e instalado

[Run 38322756782](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782):
SUCCESS, 57 min 48 s. Código del APK: 39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3.
El primer run barato fallido permanece registrado; este cierre no lo convierte en PASS.
[Datos verificables](evidence/2026-10-12-sidebar-fixes/build-38322756782-final.json).

S0: host 245/0/0, 188.105 s; GN real y javac aislado PASS. Gate de disco
23:42:15Z: 114,591,092,736 bytes y 18,963,612 inodos disponibles.
S1: checkpoint descargado una vez, restore y transición PASS. No clean build.
S2–S3: host restaurado 245/0/0, 153.669 s. Recursos fusionados, manifest y
optimización reales AAPT2 PASS (log línea 3210). Acerca de pasó en API29/36
en suites temprana y final (5594/5609 y 38297/38312). Robolectric final PASS
(línea 85540); enlace libchrome y símbolos JNI reales PASS (38277).
S4: APK Portal, paquete app.archium.android, ABI arm64-v8a y firma verificados.
S5: [artifact 11780994923](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782/artifacts/11780994923),
154,881,336 bytes comprimidos, no expirado al comprobarlo. APK: 366,979,888 bytes.
Versión 157.0.8086.0, versionCode 808600074. SHA256:
05a097adb97802d81bb97e65b46dbca2c60e559adcc53990d492d92c831eede6.

El monitor registró installed a las 00:35:43Z. Verificación posterior por ADB
de base.apk: mismo SHA256 que el archivo descargado (exit 0). Se conservaron
los datos de aplicación. No se lanzó otro run al reanudar tras la pausa.
feat/arc-desktop y main mantienen sus hashes protegidos. Contraseñas sigue
DEPRECATED y sus tests de función están OUT_OF_SCOPE, como declara el reporte
del APK. Los tests nativos de Chromium no acreditan aceptación física en DeX.

ANDROID_RUNTIME=NOT_EXECUTED para este APK. La revisión visual de barra superior,
triángulo inferior, color de omnibox, + compacto y diálogo en el dispositivo
queda pendiente de prueba manual; no se declara stable ni listo para producción.
Este commit de cierre contiene únicamente documentación y evidencia curada;
no cambia el SHA de código con el que se produjo el APK.
