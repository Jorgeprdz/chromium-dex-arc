# Archium R4 — reparación y build, 2026-10-11

## Autoridad y plan

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
