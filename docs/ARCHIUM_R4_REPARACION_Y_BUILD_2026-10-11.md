# Archium R4 — reparación y build, 2026-10-11

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
