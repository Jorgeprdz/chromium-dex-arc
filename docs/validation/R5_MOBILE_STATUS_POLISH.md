# R5 — Mobile status polish

23-oct-2026, America/Mexico_City. Rama `assistant/archium-r5-desktop-native-mobile`.
Base exacta: `a4d9bf7a37b78172763a2158af736c437d445e75`, árbol limpio al iniciar. No se volvió a una rama antigua. El run40024565967 fue cancelado por el usuario antes de esta iteración.

## Auditoría y diseño conservado

Referencia principal inspeccionada: `/sdcard/DCIM/Screenshots/Screenshot_20261023_150306_Archium for Android.jpg`, copia `phone-status-polish/user-approved-latest.jpg` en evidencia. Texto de la web atraviesa la zona del reloj; cápsulas y fondo naranja inferior se conservan. El screenshot actual del teléfono era Termux; no se confundió con Archium.

La producción móvil aceptada proviene de1298b31/run40004797899; a4d9bf7 agrega únicamente material e intensidad Desktop, conservados como antecedente. Revisados a3841bc (system bars),76e7934 (owner raíz/insets y readback),052c55a (safe area/progreso/menús),1298b31 y a4d9bf7. No se modificó su geometría ni materiales de píldoras.

Owners existentes: ToolbarManager selecciona Phone y recibe configuración, foco, pausa/resume y FullscreenManager; StatusBarColorController elige apariencia; EdgeToEdgeSystemBarColorHelper mantiene contraste frente a updates de delegates/insets. EdgeToEdgeControllerImpl/InsetObserver ya comunican safe area superior sin reservar viewport. ToolbarPhone conserva editor y sugerencias nativas; BottomControlsCoordinator conserva IME/fullscreen/gestos.

Defectos demostrados: no existía fade detrás de indicadores; el color de contraste normal ignoraba la paleta de página y se basaba sólo en el tema. Además, la opción de status flotante se mantenía habilitada aunque la Activity estuviese pausada/en fullscreen. En foco se retiraba el override de contraste: un refresh posterior podía elegir iconos claros desde un backing transparente. El probe con la expresión real anterior falla al entrar en foco; el nuevo conserva backing y libera el override al salir de Phone.

## Cambios mínimos

- `ArcPhoneStatusFade`: Drawable con LinearGradient en overlay de decor, exclusivamente dentro del inset real de status bar. No es una View; no intercepta toques, foco, accesibilidad ni gestos. No crea padding, listeners de insets competidores, bitmap, capturas ni llamadas al renderer. 85%→80%→0%; fondo blanco o202124 con histéresis de luminancia .18/.30. El color proviene de la paleta Chromium; oscuro/incógnito nativos tienen prioridad. No se afirma muestreo del fondo real: el degradado proporciona el fallback contrastado.
- Se eligió altura igual al inset de indicadores, en lugar de60dp fijos, para terminar antes de la omnibar y conservar sus colores/sombras. El fallback SDK29 usa insets legacy;30+ usa statusBars(), separado de IME/navigation.
- `StatusBarColorController`: integra fade/limpieza, reutiliza helper y paleta existentes, escribe transparencia una vez en vez de primero color opaco y después transparente. El backing se conserva también en editor/NTP Phone; colores nativos de scrim, indicadores y foco mantienen sus owners. No añade modo oscuro paralelo.
- `ToolbarManager`: retira contraste impuesto por plataforma sólo mientras glass está activo (el fade aporta protección), conservando/restaurando el valor original para evitar un segundo scrim. La activación del status treatment sigue `floating` (resume/no fullscreen), bajo el guard Phone existente. No se cambian selección Desktop/Phone, layout ni geometría de controles.
- GN, gates, runner y tests registran el código y suite reales. Sin dependencias nuevas.

La safe area existente expone el espacio de indicadores a sitios que la usan. Un sitio que no respete safe areas puede seguir dibujando al hacer scroll detrás del sistema: se protege visualmente esa región; no se promete reescribir su layout ni impedir todo dibujo. Formularios, navegación y final de página no se alteraron.

## Evidencia y límites

Directorio `/workspace/archium-evidence/phone-status-polish/`.

- RED inicial de integración (`red.log`); GREEN tras conectar owner/lifecycle. Mutante que omite añadir drawable rechazado por dos ejecuciones (`missing-overlay-red/red.log`); detecta ausencia de overlay visible aunque exista lógica de colores.
- `focus-contrast-red.log` y `focus-contrast-green.log`: expresión real de owner ejecutada con fronteras explícitas; pérdida en foco y liberación Desktop reproducibles.
- Primera suite Android150: dos fallos del fixture de toque, cuyo click estaba posteado sobre View no adjunta. Se verifica entrega real de DOWN/UP al contenido, sin shadows nuevos ni alterar producción para tests. Segunda150 PASS. La suite final `robolectric-delivery.log` incluye SDK29/30/36 según caso:153 ejecuciones PASS, política original76 métodos PASS. Incluye cambio de shader claro/oscuro sin reemplazar overlay ni contenido.
- Preparación inicial detectó patch stale después de editar el test; se regeneró y repitió, sin relajar el check.
- La primera invocación host se inició antes de terminar la actualización del contrato estático de escritura única; su resultado se conserva y no se presenta como PASS. Resultado final/recibos se agregan al terminar.

### Dispositivo: baseline, no candidato

Galaxy físico RFCY203Q5TK/SM_S931B identificado; versión instalada157.0.8086.0, code808600074. Capturas propias `baseline-browser.png`, `baseline-omnibar-first-tap.png`, `baseline-editor-stable.png`, `baseline-ime-closed.png`, `baseline-editor-dismissed.png`. Un toque abre editor y teclado instalado, sugerencias visibles; Back oculta IME y segundo Back sale del editor. No se navegó, cerró ni creó una pestaña. Se regresó a Termux y se avisó al usuario.

En la edición instalada, reloj/iconos pierden contraste y queda dirección/flecha tenue arriba; `baseline-focused-windows.txt` muestra apariencia sin LIGHT_STATUS_BARS sobre superficie clara. El override de contraste se corrige localmente; **la dirección tenue no se atribuye ni declara corregida sin más evidencia**. Validación instalada del candidato y de ese residuo: PENDIENTE.

| Caso | Local | Candidato en Galaxy |
|---|---|---|
| Fade claro/oscuro, contraste teórico y fallback | Pruebas Android | PENDIENTE |
| Insets repetidos/IME/rotación, sin padding duplicado | Pruebas Android y host | PENDIENTE |
| Drawable no interactivo, retiro Phone/Desktop/destroy | Pruebas Android | PENDIENTE |
| Metadata, histéresis, transición de color | Pruebas Android | PENDIENTE |
| Omnibar primer toque/teclado/Back | Baseline físico observado | PENDIENTE |
| Teclado del sistema/otro IME | SKIP físico adicional | PENDIENTE |
| YouTube/HTML5, orientación/minimizar en fullscreen | SKIP físico; lifecycle auditado | PENDIENTE |
| Gestos laterales, cuatro controles, scroll rápido | Controles con acciones nativas en runner existente | PENDIENTE |
| Desktop/DeX, Split View/Spaces | Código visual/modelo sin cambios respecto a4d9bf7 | PENDIENTE regresión instalada |

Amazon y diálogos pendientes ajenos al alcance no se tocaron ni se declaran resueltos. No hay aceptación gráfica del candidato por pruebas JVM.

## Build

Autorizado un único dispatch incremental nuevo tras gates, sin clean build ni reintentos. Fuente39829306775-1, SHA198fe8a, pin cfd94726b7b5fb48aedcc32662f2f3fbdbadec35: inventario4 grupos/25 partes y manifest conocido verificados nuevamente con lectura acotada. Hashes de todas las partes y capacidad: gate CI antes de restaurar. No se borraron checkpoints. No se modifica main ni se publica release de producción.

Run/SHA final/resultado/artefacto se registran en recibo externo al lanzar, para no mover el SHA exacto compilado. Monitor nuevo CDMX600s, sin relanzamientos. Aceptación física pendiente de APK.

## Cierre de gates locales

- Android153 PASS/política76 métodos; preparación aislada SDK37.2/JDK21 PASS (`preparation-final.log`). No compila aquí todos los owners Chromium con JNI; lo hará CI.
- Suite host completa:426 ejecutadas,425 PASS y1 FAIL en `PhoneFloatingNativeContractTests.test_transparent_status_bar_keeps_native_overlays_and_icon_contrast`. Era la aserción antigua de una segunda escritura transparente, cargada antes de editar el test. Se sustituyó por exigir una sola escritura y el backing en foco, sin retirar cobertura de scrim/indicadores. Suite afectada repetida completa6 PASS (`native-contract-final.log`); nuevos probes4 PASS. No se afirma que la primera suite completa pasó ni que se repitió completa después.
- Insets2, composición2, safe area1, owner de contraste1 y cobertura de gates2 PASS en recibos finales. Controles/sugerencias nativos conservan sus pruebas dentro de Android153.
- Patch/manifest192 archivos: regeneración idéntica y hashes finales comprobados. Transición sparse desde198fe8a PASS,151 timestamps sin cambios conservados; no restaura todos los bytes del checkpoint. Píldoras, ToolbarPhone, Desktop, WebContents owner e insets de renderer comparados byte a byte contra a4d9bf7 y sin cambios.
- Recibo resumido: `candidate-local-verification.json`, sin representar local como aceptación gráfica. Fase local preparada para un único build integrado. Build/APK/gráfica real pendientes al crear este commit.
