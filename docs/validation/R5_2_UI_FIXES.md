# R5.2 — correcciones de interfaz y candidato con diálogos

Implementación: **0ab6204c9e785ef4d6ce1da456070f0a24f476fe**, rama local
`assistant/archium-r5-2-ui-fixes`, en el worktree forense existente.
Autorización: corregir pendientes fuera de Amazon y actualizar el TODO al final.
**Código verificado localmente; aceptación visual con APK nueva pendiente.**

## Correcciones demostradas

| Defecto | RED | Cambio mínimo / GREEN |
| --- | --- | --- |
| Sidebar ancha en ventana baja usa navegación compacta | Rail 216×500, presupuesto de colecciones cero: se perdían controles completos | Separar decisión de navegación y presupuesto de colecciones; la colección conserva su límite de altura. |
| Footer puede exceder su ancho | Rail 216, menú nativo 64, botones 88 e insets 8: presupuesto 84 en lugar de 56 | Reservar ancho medido del menú, insets y botones reales antes de asignar extensiones. |
| Footer pierde un píxel por redondeo | Densidad 2.625: dos botones de 44dp ocupan 232px, no 231px | Sumar el tamaño redondeado de cada botón: presupuesto 145 en lugar de 146px. |
| «+» descentrado en rail con insets | Fila 36px, rail 52px: padding 14 en lugar de 6 | Usar ancho real de fila, limitado al ancho disponible del rail y con fallback antes del primer layout. |
| Bounds antiguos durante colapso | Fila aún de 216px dentro de rail de 52px: padding 96 | Limitar por el ancho actual del rail; padding 14. |
| Hover/pressed/foco aparentes en controles deshabilitados | Drawable activo pese a state_enabled ausente | Exigir state_enabled para cada estado de interacción; preservar feedback de controles habilitados. |

Se reutiliza el listener de layout para actualizar el presupuesto tras medir el
menú y el centrado tras medir la fila. Ambos registros se retiran en destroy.
No hay recreación nueva de Activity, pestañas ni WebContents. No se modifican
modelos de pestañas, preferencias de usuario, paleta, fuentes ni recursos Portal.

## Pruebas ejecutadas

El runner nuevo extrae métodos y expresiones del consumidor real en
ArcDesktopCoordinator y usa Android Views/drawables bajo Robolectric. Construcción,
recursos y servicios Chromium se adaptan explícitamente: no es el runner de la APK.

- RED inicial: 12 casos, ocho fallos de aserción (cuatro defectos × SDK30/36).
- RED de colapso con bounds antiguos: 14 casos, dos fallos pertinentes.
- RED de presupuesto de colecciones: 16 casos, dos fallos pertinentes.
- RED de densidad fraccionaria: 18 casos, dos fallos pertinentes.
- GREEN final del runner nuevo: **18/18** en SDK30/36.

| Regresión | Resultado | Alcance |
| --- | --- | --- |
| Gate de diálogos nativos 5184755 | 18 PASS | Métodos fijados, Views reales bajo Robolectric; JNI/resources/inputs adaptados. |
| Transiciones sidebar/móvil, viewport e input | 12 PASS | Métodos entregados; Tab/JNI adaptados. |
| Frame, clipping y paleta | 10 PASS | Views/outline; compositor y window metrics adaptados. |
| Presupuesto de extensiones tras callbacks | 2 PASS | Métodos reales de asignación; consumidores adaptados. |
| Drawable de shell y fila nueva pestaña | 6 PASS | Métodos entregados; límites nativos explícitos. |
| Contratos estáticos de interfaz | 10 PASS | Comprobaciones de fuente, no renderizado. |
| Transición de parches/checkpoints | 17 PASS | Casos controlados del mecanismo; no restauración de un artefacto real. |
| Identidad/layout de pestañas | 4 PASS | Regresión local; no nueva prueba de drag físico. |
| Toolbar, omnibox y lifecycle | 6 PASS | JVM con límites explícitos de Chromium. |

Total de los seis grupos Robolectric: **66 PASS**. Los cuatro grupos Python de
la tabla suman **37 PASS**; no se volvió a ejecutar la suite completa de 325 tests.
La preparación verificó aplicación/hashes de **128 archivos**, políticas y estado
persistido, compilación aislada de adaptadores contra Android API37, acciones y
sesión nativa en límites sintéticos, más cinco tests de proyección de grupos.
No sustituye GN, JNI ni compilación Chromium.

El primer intento de los runners necesitó añadir al classpath el JAR Window Core
fijado ya disponible; ese error de preparación no se contó como RED de producto.
El harness corrigió también una geometría de prueba inconsistente y su parser de
whitespace antes de la ejecución final. Se conservan los logs RED/GREEN de las regresiones.

## Diálogos e integración

La rama candidata es descendiente de **51847556e761ca0600a4aa824531e40d200fdf17**;
el parche generado incluye ese arreglo. Se compararon sus tres archivos Java
contra ese commit: permanecen idénticos. No se repite ni sustituye ese fix.
La APK instalada del run 39296066030 **no contiene** esos cambios posteriores.
No se afirma que los diálogos ya estén reparados visualmente en Galaxy.

## Compilación y pendientes

No se despachó GitHub Actions, compiló Chromium ni instaló APK. La rama activa
permanece limpia en 3db367adff50d423b8c4475d10165d2790f6065a; no se modificó el
supervisor. No se limpiaron outputs ni checkpoints.
El pin y todos los hashes de originales del manifiesto permanecen iguales; sólo
cambia ArcDesktopCoordinator entre los payloads de este lote. Sin cambios de GN,
toolchain, C++, package ni firmas JNI. Se espera recompilación Java/dex según el
grafo real; antes de un build progresivo hay que verificar el checkpoint real y
su compatibilidad, no inferirla de estas pruebas locales.

Pendientes: APK con diálogos y estas correcciones; aceptación de alert/confirm/
prompt, foco y ventanas; geometría/hover/colapso/menú/extensiones en Galaxy;
cuña inferior y cierre completo de P0-03; calibración de viewport sin forzar zoom;
marcadores, descargas y persistencia completa con el navegador real.
QEMU sigue QEMU_ABI_BLOCKED. Amazon permanece excluido y sin cierre de su bloqueo.

[Recibo de pruebas](r52-ui/evidence.json). Logs privados:
`/workspace/macdesk-maintenance/archium-r52-ui/`. Reproducción del runner nuevo:

```sh
python3 scripts/test-robolectric-sidebar-geometry.py \
  --classpath-file /ruta/classpath.txt --java-home /ruta/jdk21 --work /tmp/sidebar-probe
```
