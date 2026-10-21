# R5.3 — revisión real de uso, Galaxy S25

20-oct-2026, aproximadamente 13:59–14:08 UTC (teléfono UTC−06:00).
Solicitud: recorrer Archium usando las pestañas existentes. Sin correcciones ni nuevo build.
APK instalada: run `39379198808`, SHA fuente `785ddf464c8a5260cad8d412840b5838e50be3d7`.
SHA256 leído directamente del APK instalado en Android:
`ade9b690df3d73aab85da10f24b0d0da3782ca728d2fb6269bfb7439a829f1fc`.
Paquete `app.archium.android`, versión 157.0.8086.0, versionCode 808600074.
Galaxy SM-S931B, Android 17, tarea existente 6766, display lógico 37, captura 2400×1350.
Se trajo al frente la tarea existente. No se borraron datos, perfiles ni pestañas del usuario.

## Fallos reproducidos

| ID | Estado | Reproducción y resultado |
|---|---|---|
| DEVICE-01 | FAIL | Con página web activa, pulsar la omnibox lateral: aparece el popup con placeholder y campo vacío. Se repite después de esperar la animación y tanto con visor simple como dividido. Falta la URL actual seleccionada para copiar/editar. |
| DEVICE-02 | FAIL | En split con dos pestañas existentes, activar el panel derecho → pulsar omnibox → escribir `example.com` → Enter. Se crea una pestaña adicional, se selecciona y desaparece la división; el panel derecho original conserva su URL. Contradice la navegación sobre el panel activo del diseño aprobado. |
| DEVICE-03 | OBSERVED | Al contraer la sidebar, la fila activa muestra una X sin favicon visible. Evidencia de geometría/legibilidad; no se pulsó esa X para evitar cerrar una pestaña del usuario. Riesgo de hit targets aún por medir. |

Capturas privadas clave: `16-omnibox-settled`, `17-typed-suggestions`,
`20-sidebar-collapse`, `24-right-back`, `26-omnibox-navigation`, `27-test-tab-removed`.
No se ha demostrado una causa raíz de código ni que DEVICE-01/02 sean independientes.
La hipótesis acotada es que la entrada «editar dirección actual» sigue semántica de nueva pestaña;
se requiere trazar la integración nativa antes de corregir. Los tests host anteriores no detectaron estos fallos reales.

## Comprobaciones reales y alcance

| Caso | Estado | Evidencia/alcance |
|---|---|---|
| Long press de pestaña y menú Pantalla dividida | PASS | Capturas 05–08; no se probó clic derecho. |
| Selectores nativos de split visibles | PASS | Ambos cuadros se ven; no equivale a toda la matriz JS/HTML/permisos. |
| Pareja de pestañas existentes | PASS | Captura 09: página GitHub y resultados Google visibles a la vez. |
| Activación por toque y selección en sidebar | PASS | Capturas 10/19: URL e indicador activo cambian al panel derecho. |
| Scroll del panel derecho | PASS | Capturas 10→11: cambia Google; GitHub conserva contenido. |
| Intercambiar y volver | PASS | Capturas 13/14: ambos contenidos intercambian lados y vuelven; se conserva posición de scroll observada. No se midió red ni recarga. |
| Ajustar separador | PASS | Captura 15: anchos cambian, ambos contenidos permanecen visibles. |
| Layout responsive al estrechar | PASS | GitHub redistribuye contenido con menor ancho. Cambio efectivo de UA móvil: NOT_TESTED. |
| Contraer/expandir sidebar | PARTIAL | Capturas 20/21: cambia ancho y conserva pareja; legibilidad de fila activa requiere corrección/medición. |
| Sugerencias al escribir | PASS | Captura 17: resultados nativos visibles al escribir `example.com`; no se declara cubierta toda búsqueda/IME. |
| Enlace público en panel derecho | PASS | Captura 23: abre Wikipedia en el mismo panel; GitHub permanece a la izquierda. |
| Atrás sobre panel activo | PASS | Captura 24: vuelve a Google; GitHub permanece. |
| Historial mediante pulsación prolongada | PASS | Captura 25: entrada Wikipedia y Mostrar historial completo visibles. No se recorrieron datos privados del historial. |
| Suavidad exacta de transición | NOT_TESTED | Se observaron estados finales, sin vídeo ni medición por frame. |
| Nueva pestaña desde selector split, restauración tras reinicio, presión de memoria, ventanas pequeñas | NOT_TESTED | Fuera de esta revisión breve. |
| Amazon y matriz completa GPU/DeX | NOT_TESTED | Amazon conserva UNRESOLVED_GRAPHICS_BLOCKER. Sin inferencias nuevas sobre GPU. |

## Preservación y evidencia

Se abrió una única pestaña de prueba Example Domain al reproducir DEVICE-02 y se cerró sólo esa pestaña.
Las siete pestañas originales siguen presentes; se restauró la selección original de GitHub, visor simple.
La navegación de prueba Google→Wikipedia→Atrás deja una entrada pública adicional en el historial;
no se modificaron cuentas, formularios ni ajustes. No se abrió el portal privado ni la página de repositorios de la cuenta.
Se canceló el borrador `example.com` en el primer ensayo; sólo el ensayo de Enter solicitó navegación.

37 archivos iniciales de evidencia, capturas, View hierarchy/dumpsys y Logcat auténtico del PID 14889,
almacenados fuera del repositorio en `macdesk-maintenance/archium-r53-device-review`.
`evidence-index.PRIVATE.json` registra tamaños, hashes y timestamps del host; Logcat usa hora local UTC−06:00.
El PID inicial/final fue el mismo y el fragmento final recogido no contiene FATAL EXCEPTION/Fatal signal;
no demuestra estabilidad prolongada ni cubre todos los procesos renderer.
UIAutomator no pudo obtener idle state: no se usan bounds de un dump inexistente ni se inventan resultados.
Capturas de transición tempranas 03/04 no se usan para establecer resultados estables.

Recomendación: corregir primero la ruta nativa «editar dirección actual», con regresiones separadas
para URL preseleccionada y navegación sobre el Tab activo dentro de split. Mantener sin cambios las rutas que sí respondieron.
No se inició CI, no se modificó producción, monitor ni checkpoints.
