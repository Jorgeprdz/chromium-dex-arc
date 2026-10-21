# Recuperación de sesión — 21 octubre 2026

Se recuperó el transcript `/root/.codex/sessions/2026/10/19/rollout-2026-10-19T05-28-19-01a152a1-d181-7932-a637-93d941e6c41b.jsonl` y los dos transcripts de workers del 21 de octubre, 02:11 y 02:12 UTC.

La última actividad registrada del controlador fue 02:19:26 UTC; los workers terminaron abruptamente a 02:19:31–33 UTC. No consta cierre normal ni entrega de la tanda. Había varios procesos Robolectric simultáneos. Esto permite localizar la interrupción, pero no atribuirla a memoria sin log de Android. ADB sólo enumeró un dispositivo offline, por lo que no se obtuvo logcat ni registro ApplicationExitInfo.

Trabajo autorizado recuperado: parejas persistentes, candidato primer clic omnibox y siete refinamientos visuales GO. Se conservan los worktrees, cambios y checkpoints. Amazon y Hover Preview continúan excluidos. No se lanza build ni Actions en esta fase, siguiendo el plan ya guardado.

La recuperación ejecuta pruebas Android secuencialmente con heap acotado y conserva logs. No constituye una corrección de Termux ni aceptación de una APK nueva.

## Candidato recuperado

Worktree: `/workspace/Archium-R5-split-pairs`; rama `assistant/archium-r5-persistent-split-pairs`. La rama base y el otro worktree se conservan. Se completó el código de la tanda, sin integración remota ni APK nueva.

- Registro por TabModel y perfil; varias parejas con orden, ratio y panel activo independientes. Suspender presentación no disuelve la asociación. Migración del formato anterior y restauración sin forzar selección nativa.
- Proyección nativa de una fila por pareja, también en listas fijadas y grupos compatibles. Selección, contexto, cierre del miembro activo y drag usan IDs vigentes. Los dos títulos tienen presupuesto de ancho independiente; los dos iconos conservan artwork/fallback nativos y callbacks con identidad/generación.
- Refinamientos GO: estados de selección/hover/foco; regiones y borde interior físico de un píxel, sin espacio adicional; tooltips nativos; ajuste de favicons; Space actual identificado desde estado existente; fade de borde de 100 ms cancelable al reciclar, cambiar estado o desacoplar, respetando animaciones desactivadas.
- Candidato de primer clic omnibox recuperado y verificado con los eventos de regresión. Falta confirmar el recorrido real de mouse del Galaxy.

Cambios de producción concentrados en `ArcSplitPairStore`, `ArcSplitViewCoordinator`, `ArcSplitPairProjection`, `ArcSplitPairVisuals`, `ArcDesktopAppearance`, `ArcDesktopCoordinator`, `ArcCollectionsView`, `ArcSidebarState`, `TabListMediator`, `TabProperties`, los coordinadores/binders/drag de vertical tabs, menú nativo y `LocationBarLayout`. Las listas GN sólo registran fuentes nuevas; no cambian argumentos, pin ni toolchain.

## Evidencia de la recuperación

Logs persistentes: `/workspace/macdesk-maintenance/archium-r56-batch/recovery/`.

| Gate | Resultado | Límite |
| --- | --- | --- |
| Controlador de split | GREEN 78, SDK30/36; RED previo registrado | Límites nativos del compositor adaptados; no prueba renderizado web |
| Binding de parejas | GREEN 12, SDK30/36 | Vistas Android y métodos entregados; modelo/fetch scheduling adaptados |
| Apariencia | GREEN 20, SDK30/36 | Incluye reciclado, foco, cancelación, detach, filas deshabilitadas y animaciones desactivadas |
| Visuales de pareja | GREEN 4, SDK30/36 | LEGACY verifica presupuesto/truncado, no glifo de elipsis |
| Omnibox | GREEN 24, SDK30/36 | Vistas/touch reales; callback de foco nativo adaptado |
| Proyección, grupos y drag | GREEN 16 | Métodos entregados sobre TabModel sintético; no gesto en dispositivo |
| Helper de proyección | 15 escenarios y 1000 snapshots | JVM, sin RecyclerView real |
| Preparación SDK37.2 | PASS: parche de 157 archivos, hashes, fuentes nuevas y adapters | Compilación aislada con contratos stub; no compila todo Chromium |
| Parche regenerado dos veces | PASS, mismos hashes | No constituye build |

138 ejecuciones Android del candidato pasan. La persistencia mantiene el alcance existente por tarea/ventana del primer perfil normal; otros TabModel conservan asociaciones en memoria y no leen ni sobrescriben las preferencias de ese perfil. Incógnito permanece sólo en memoria. No se acredita persistencia completa entre tareas o reinicios. Robolectric NATIVE no admite Linux aarch64 en este entorno; el intento quedó registrado, no se sustituyó por una afirmación de validación gráfica. No hay dispositivo ADB online.

## Revisión y decisiones

La revisión independiente encontró un defecto importante: con orden nativo B,C,A y pareja A/B, la dirección del drag se calculaba con índice del representante y no con el orden de unidades proyectadas. Se añadió RED del método onMove real y se corrigió la dirección mediante IDs/unidades actuales. La segunda revisión dio el hallazgo por resuelto y no encontró nuevos defectos importantes.

Se resolvió además una ambigüedad de contrato: pinning/grupo/Espacio temporalmente incompatibles suspenden la presentación pero conservan el vínculo hasta separación explícita. Cerrar, destruir o trasladar realmente un miembro sí disuelve sólo esa pareja. Costo: para reutilizar un miembro incompatible se debe separar su pareja.

El guard estático anti-Canvas se acotó a geometría de contenido/compositor: la decoración aprobada de sidebar puede dibujar sus líneas en su propio foreground. El clipping nativo permanece intacto. Costo: aún hace falta aceptación visual de esa decoración en APK.

La autorización se interpreta como la tanda acordada, no todo el histórico del TODO. Amazon y Hover Preview siguen excluidos; no se despacha build en esta fase.

## Gates pendientes

La suite host amplia se ejecuta con herramientas nativas aarch64. La primera ejecución se canceló al detectar que el wrapper AAPT2 de SDK37 usaba QEMU x86; no se inició un emulador Android. El AAPT2 Debian nativo 2.19 no puede leer la tabla de recursos del SDK37.2: dos pruebas de Portal/optimización fallan también sobre la rama base, con idéntico error `Failed to load resources.arsc`. No se modifica el toolchain para ocultarlo. El chequeo estático de Canvas inicialmente falló por abarcar toda la clase y pasó tras acotarlo al contenido nativo.

Quedan pendientes el gate de recursos con la herramienta compatible, el runner Chromium completo/JNI, build incremental compatible y pruebas con APK en Galaxy/DeX: primer clic, split, menús, reorder, hover/foco, scroll, diálogos y lifecycle. No se declara corrección del cierre de Termux: sólo se recuperó su punto de trabajo y se acotó la ejecución de pruebas.

### Suite host amplia

La ejecución nativa terminó: 376 pruebas, un fallo estático y dos errores de recursos. El fallo estático anti-Canvas se corrigió con el alcance descrito y su grupo completo pasó 10/10 en una ejecución posterior. Los dos errores AAPT2 se reprodujeron en la base sin los cambios de esta tanda; siguen pendientes, por lo que no se declara PASS global host. Las nuevas regresiones de dirección de drag pasan por separado junto a proyección/grupos: 16/16. No se altera ni se salta el gate que bloqueará el build cuando corresponda.
