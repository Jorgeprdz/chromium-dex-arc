# R5 — recorte al estrechar Split View, 22-oct-2026

Estado: **LOCAL CANDIDATE / NOT COMPILED**. El usuario indicó «no compiles todavía». Sin Actions, compilación C++/Java ni instalación durante esta corrección. No se declara GREEN de Blink.

## APK instalada y reproducción física RED

Run39705469954 terminó SUCCESS e instaló el código78b370b5a3a2527c605c04d2645215933c13d615. Checksum de APK instalada13984de7e6704ac618d253336f9114997abe79c7482b56e93a065d5271d96ad0. Preflight, restauración, gates y build anteriores pasaron; QEMU skipped. Esto no acreditaba responsividad real.

El usuario confirma: el separador se mueve, la página queda recortada. Se midió mediante CDP de sólo lectura y arrastre Android sobre DeX. Se restauró la proporción50/50 y Termux al frente; no se navegaron ni recargaron las páginas. El primer intento de arrastre encontró Termux delante y NO cuenta como evidencia; la repetición con Archium delante sí cambió las dimensiones.

| Panel derecho, página LinkedIn | 50% | 25% | 50% restaurado |
|---|---:|---:|---:|
| Ancho nativo del viewport | 1058 | 527 | 1058 |
| innerWidth CSS | 980 | 488 | 980 |
| visualViewport.width | 980.008 | 488.151 | 980.008 |
| documentElement.clientWidth | 980 | 908 | 980 |
| matchMedia(max-width:700px) | false | **false** | false |
| visualViewport.scale | 1 | 1 | 1 |

DPR1.0795831680297852 y performance.timeOrigin constantes. La prueba demuestra que `setSize` sí llega al widget/viewport visible; el fallo pendiente es la divergencia con el layout usado por las media queries. No hubo zoom residual ni recarga en esta secuencia concreta. El otro panel recibió1589px al ampliar y volvió a1058px.

Evidencia privada: `/workspace/archium-evidence/r5-split-device/drag-metrics.json`, capturas y `device-red.log`. `scripts/check-split-viewport-trace.py` rechaza esta traza por la divergencia de layout y media query. No contiene emulación de tamaño ni cambia páginas.

## Ruta causal y candidato

En Chromium fijado cfd94726, `content/browser/web_contents/web_contents_impl.cc` ignora la meta viewport cuando la navegación usa Request Desktop Site. El mecanismo Android de viewport ancho continúa habilitado; `WebViewImpl::UpdateMainFrameLayoutSize` toma sus restricciones en vez del ancho real del widget. Esto explica la firma observada: viewport visible menor, layout ancho y media queries sin cruzar el breakpoint. La consulta adicional de UA de la pestaña agotó el plazo, por lo que la condición exacta de preferencias en runtime y una fixture independiente siguen pendientes de confirmación. No atribuir una validación completa del motor a esta auditoría.

Candidato localizado:

- `StaticTabSceneLayer` registra propietarios por WebContents sólo mientras el contenido pertenece a Split View. Usa WeakPtr; no retiene pestañas. El swap conserva pertenencia; reemplazar contenidos, limpiar la pareja y destruir la escena liberan la política. Dos propietarios no se pisan entre sí.
- `ChromeContentBrowserClient::OverrideWebPreferences` aplica el ajuste sólo a esos WebContents y sólo si Chromium ya ignora la meta viewport. Desactiva ese mecanismo de layout Android para usar el layout de escritorio basado en el tamaño real del widget. El modo móvil explícito conserva su tratamiento nativo de meta viewport.
- El hook participa en cada recomputación de preferencias. Entrar/salir recomputa los valores nativos actuales; no restaura snapshots obsoletos. No envía IPC repetidos por cada frame o drag.

No modifica UA/Client Hints, preferencia de sitio, ratios, metadatos de parejas, páginas externas, zoom mediante APIs, GPU, toolchain ni GN. Sólo se usan archivos C++ que ya pertenecen a targets existentes. La sincronización posterior al layout de78b370b se conserva: resuelve otra frontera, pero no bastó para este caso.

## Verificación y continuación

- RED físico instalado: **FAIL reproducido** por el validador de traza.
- Validador + contratos estáticos de integración: **5 PASS**; los dos contratos nuevos fallaron antes del candidato. No ejecutan C++ ni Blink. Las trazas positivas de esas pruebas son sintéticas.
- Conservación del rollback Mobile: **5 PASS** de invariantes estáticos.
- Regeneración reproducible del parche y aplicación sobre originales por archivo: ver recibo privado `reproducibility.json`. No equivale a un checkout completo ni a un build.
- Compilación C++, gates completos, pruebas de propiedad/lifetime nativas y GREEN en dispositivo del nuevo código: **NOT RUN**, respetando la pausa de compilación.

Antes de cualquier build: revisar/ejecutar pruebas nativas de entrada/salida, dos propietarios, swap, navegación, reemplazo y destrucción de WebContents; confirmar API/include/linkage reales. Después de autorización separada, una APK candidata debe pasar la fixture responsive y las dos secuencias50→25→50 y25→75→25 en ambos paneles. Contrastar CSS/visual viewport, media queries, formularios, scroll, selección móvil explícita, zoom de usuario y vuelta a vista individual. No lanzar automáticamente otra compilación.
