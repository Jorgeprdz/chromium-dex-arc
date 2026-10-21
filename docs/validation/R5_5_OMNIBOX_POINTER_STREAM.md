# R5.5 — clic intermitente de omnibox

Estado: corrección local candidata, sin nueva APK ni GREEN en dispositivo.
Base de producto: `cb9822aa0a4a0e4a5d5609bd80da470b0d4db325`.
Worktree: `Archium-R5-split-pairs`, rama `assistant/archium-r5-persistent-split-pairs`.

## Evidencia y alcance

El usuario reporta que necesita varios intentos para copiar, seleccionar o escribir. Precisó que sucede con el mouse y que el popup no llega a abrirse. Falta distinguir si ocurre con la ventana ya activa o principalmente al volver desde otra app.

Se demostró un defecto del dispatch: `LocationBarLayout.mArcConsumesAddressGesture` se activa al abrir el popup en ACTION_DOWN y sólo se limpia con UP/CANCEL. Si esa vista no recibe la liberación del gesto anterior, el siguiente DOWN también se consume sin invocar el abridor. El traslado del editor entre jerarquías es un contexto posible; no se ha capturado todavía ese evento perdido en el Galaxy ni se atribuyen todos los incidentes reportados a esta causa.

La nueva regresión reproduce deliberadamente un stream sin UP/CANCEL. Comprueba reapertura con otro DOWN, edición nativa dentro del popup y llegada del clic secundario al dispatcher nativo. No prescribe que Android entregue un clic secundario real al listener del editor: puede procesarlo antes como contexto.

## Cambio mínimo

Restablecer el estado de consumo al inicio de un ACTION_DOWN nuevo. Seguir consumiendo los eventos restantes del gesto que abrió el popup para no enviar su liberación al editor trasladado. No forzar foco, reabrir Activities, recrear WebContents, vaciar texto ni sustituir sugerencias nativas.

Se añaden dos regresiones a LocationBarTabletUnitTest, ya incluido en el gate Chromium: reapertura después de stream incompleto (toque/mouse primario) y primer gesto de edición. El probe local compila los métodos entregados de LocationBarLayout con vistas Android reales y límites explícitos para la clase Chromium y el callback de foco. La opción --source-ref permite repetir las regresiones contra el SHA anterior exacto.

## Comprobaciones realizadas

- RED contra cb9822a:24 casos,6 fallos de las tres regresiones × SDK30/36.
- GREEN con el cambio:24/24, incluidos botones auxiliares/anidados, cancelar, clic secundario, URL/selección y Ctrl+T vacío.
- Helpers R5:50/50 PASS; semántica nativa de dirección/navegación:6/6 PASS.
- Preparación SDK37:PASS. Patch regenerado; diff-check:PASS.
- Suite host completa y runner Chromium completo:pendientes de los gates del conjunto antes de integración/build. No se presentan estos resultados focalizados como ejecución de toda la suite.
- Dispositivo:NOT_TESTED con el cambio. Sólo se comprobó conexión ADB y foco observable; no se ejecutaron clics ni se recogió Logcat nuevo para este incidente.

## Entrega pendiente

Cambios de producto limitados a Java de omnibox y sus pruebas; sin cambios de compositor, pin, GN args, toolchain o package. Mantener este candidato aislado de la rama de la APK instalada. No se despachó ningún run ni se modificó el monitor. La futura integración debe conservar los checkpoints y ejecutar sólo compilación incremental compatible.

Repetir en la APK nueva: clic primario estando Archium ya enfocada; regreso desde otra app; apertura/cierre sucesivos con mouse; seleccionar/copiar/editar URL; Ctrl+L/Ctrl+T; ventana normal y pareja dividida. Capturar el primer evento defectuoso si persiste, sin registrar texto privado. Hasta ese GREEN, la incidencia permanece abierta.
