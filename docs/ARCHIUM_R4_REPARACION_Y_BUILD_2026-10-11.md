# Archium R4 — reparación y build, 2026-10-11

## Autoridad y plan

Especificación: prompt ARCHIUM R4 del usuario. Ejecución autónoma, commits temáticos y push autorizados exclusivamente a assistant/archium-r3-visual-fixes; una corrida pesada condicionada a gates. Sin build limpio, borrado de outputs ni migración upstream. Se preserva Portal/DeX y feat/arc-desktop.

- [x] Reconocer local/remoto, pin, PRs, 30 commits, workflows, ocho logs y artifacts.
- [ ] ARC-F002: JVM -ea/-da, negativas y restore assert; runner Chromium con assertions.
- [ ] ARC-F001: display independiente de attach, API 30/fallback, JVM y Robolectric.
- [ ] ARC-F003: gate sobre recursos/manifests reales y APK optimizada; conservar assets.
- [ ] ARC-F004/F005: evidencia separada, dispatch explícito SHA, sin push pesado ni clean fallback.
- [ ] ARC-F006/F007: fixtures integridad/ENOSPC/mtimes/symlinks/transición/delta.
- [ ] ARC-F008: doble regeneración oficial, hashes y aplicación.
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
