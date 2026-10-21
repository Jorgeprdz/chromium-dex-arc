# R5.3 — omnibox lateral y pop-up nativo

Base: `5b8694a07f328128e1267262780e6996b0ba4509` (Chromium 157.0.8086.0).
Trabajo aislado: `assistant/archium-r5-3-omnibox-split`.

## Evidencia y decisión

La APK instalada fue leída por ADB autorizado: SHA256 de `base.apk`
`9db795ddf861a008e0181a60c52bbdf96e91c070c3464ae2b85913f545e6dc37`, idéntico al run 39338037898.
En DeX, la entrada lateral y Ctrl+T se probaron con el mismo texto no enviado,
sin navegar ni modificar cuentas. Las ventanas y captura se correlacionaron:
frame estable [402,218,1700,1095]. El listado nativo era VISIBLE y medía 216×352
en la entrada lateral, pero no aparecía visualmente. En Ctrl+T medía 760×299
y los resultados sí eran visibles. Esto no demuestra causa de GPU o z-order.
Una captura previa con bounds obsoletos queda descartada como evidencia.

Por petición explícita del usuario se reutiliza el pop-up funcional de Ctrl+T
al pulsar la dirección lateral, con la URL completa seleccionada para copiar
o editar; Ctrl+T conserva entrada vacía. No se aplica un parche especulativo
al compositor ni se reemplazan las sugerencias nativas.

## Cambio y alcance

- `ArcCommandBar.openAddress(Runnable)` admite la sesión de foco nativa existente.
- `ArcDesktopCoordinator` conecta clic y Ctrl+L en modo lateral; restaura primero
  cualquier popover nativo y conserva la instancia para liberar el callback al destruir.
- `LocationBarLayout` enruta el gesto de dirección; los botones nativos, clic
  secundario y edición dentro del pop-up conservan dispatch original.
- Pruebas de toque usan los métodos entregados sobre Android Views; construcción
  de Chromium y callback de foco son adapters explícitos, no una APK ejecutada.

## RED/GREEN y regresiones

`test-robolectric-address-popup.py --baseline` usa fuentes del commit base inmutable:
16 casos, 10 fallos de aserción pertinentes. Harness final sobre el cambio: 18 PASS (añade dos casos de botones anidados).
La regresión anidada produjo 2/18 fallos antes de preservar el segmento auxiliar completo.
`test-robolectric-r5.py`: 44 PASS finales (38 de controles/omnibox y 6 de estado split), incluye URL completa/selección, reentrada sin
perder edición, Ctrl+T vacío, Escape y restauración del holder.
`test-robolectric-compact-omnibox.py`: 28 PASS.
`test-robolectric-r5-runtime.py`: 14 PASS de puentes nativos/política Fusebox.
Los adapters del gate de preparación verifican autoridad de la API entregada;
no prueban linkage JNI ni píxeles del dispositivo.

## Pendientes

Validación visual con APK que incorpore este cambio: PENDING_DEVICE_VALIDATION.
QEMU: QEMU_ABI_BLOCKED. Amazon: UNRESOLVED_GRAPHICS_BLOCKER, fuera de este cambio.
La vista dividida y su cápsula blanca/transición se ejecutan bajo el plan aprobado;
este informe no afirma que estén implementadas ni que exista un nuevo build.
Los originales con historial/títulos permanecen en almacenamiento privado, fuera del repo.


## Historial aprobado

Pulsación prolongada de Atrás/Adelante reutiliza `NavigationPopup` de Chromium,
con el NavigationController de la pestaña de origen y su Profile. Los clics
simples mantienen navegación normal. El menú se descarta al ocultar, destruir,
cambiar de pestaña o mutar el historial; no se conserva un índice de otro Tab.
Regresión inicial: API inexistente en compilación de tres tests nuevos;
implementación: seis casos nuevos PASS (dos SDK), dentro de los 38 del runner.
Las firmas de fábrica se contrastaron con el fuente fijado de NavigationPopup;
el gate sintético verifica tipos, no ejecuta el menú real de Chromium.
La visibilidad del menú y navegación por entradas quedan pendientes de APK.
