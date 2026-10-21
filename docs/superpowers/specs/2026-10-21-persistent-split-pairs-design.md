# Varias parejas de vista dividida y sidebar conjunta

Fecha: 21-oct-2026. Base: `cb9822aa0a4a0e4a5d5609bd80da470b0d4db325`.
Estado: implementación candidata recuperada el 21-oct-2026; pruebas host registradas en R5_6_TERMUX_RECOVERY.md. Nueva compilación y aceptación APK pendientes.

## Resultado acordado

El usuario solicita varias parejas independientes por ventana. Cada pareja contiene dos pestañas nativas existentes y conserva sus posiciones izquierda/derecha, proporción y último panel activo al visitar otra pestaña o pareja. En la sidebar aparece una sola fila por pareja: «Título 1 | Título 2» expandida, y dos favicons separados por una línea fina en compacto.

Ejemplo: formar A/B y D/E, ajustar sus proporciones, visitar C y volver alternativamente a cada pareja. Deben reaparecer las dos páginas correctas, con su geometría y sin recargas ni creación de WebContents. No implica renderizar todas las parejas simultáneamente: sólo la seleccionada ocupa el visor.

## Causa del fallo actual

`ArcSplitViewCoordinator.mModelObserver.didSelectTab` llama a `exit()` si `mState.activate()` rechaza una pestaña externa. `refresh()` también llama a `exit()` cuando la selección no pertenece a la pareja. `exit()` disuelve la única pareja y `persist()` elimina su asociación. Cambiar de selección se trata incorrectamente como una salida explícita del split.

Es evidencia de código coherente con el fallo reportado. Todavía no se ha ejecutado una regresión RED de ese recorrido ni existe GREEN de su corrección.

## Enfoque elegido y alternativas

Se propone un registro de parejas separado de la pareja que se está presentando. Reutiliza el compositor, controles y objetos Tab/WebContents actuales. Corregir sólo la suspensión de la pareja única no permite conservar varias. Usar grupos nativos de Chromium como parejas cambiaría semánticas de grupos, sincronización y cierres ajenas a este pedido, por lo que se descarta.

## Estado y selección

- Registro por ventana y TabModel/perfil: identificador estable de pareja → IDs izquierdo/derecho, ID activo y proporción. Índice inverso de Tab ID → pareja. Una pestaña sólo pertenece a una pareja.
- Seleccionar una pestaña normal termina las animaciones pendientes contra la pareja anterior y retira su presentación. Conserva todas las asociaciones; no roba el foco ni vuelve a seleccionar una pestaña de la pareja.
- Seleccionar una fila de pareja restaura su último panel activo y presenta ambos miembros. Seleccionar directamente un miembro mediante un mecanismo nativo activa ese miembro y recupera su pareja.
- Las acciones del visor operan únicamente sobre la pareja presentada. Intercambio y resize actualizan sólo su entrada. Conservar los atajos, navegación, diálogos y adaptación móvil ya aceptados.
- Crear A/B y después D/E no sustituye la primera. El selector de segunda pestaña excluye miembros de otras parejas, con indicación del motivo; para reutilizarlos se separa antes su pareja. No disolver parejas de forma implícita.
- Cambiar de perfil no comparte títulos, favicons ni registro. Incógnito conserva parejas sólo en memoria. Mover un miembro a otra ventana o cerrar/destruir un miembro disuelve exclusivamente esa pareja; el superviviente queda como pestaña normal. No cambia la selección si se cierra un miembro de una pareja inactiva.
- Se conserva el alcance de restauración existente: estado normal ligado a la ventana/tarea y reconciliado con IDs nativos tras completarse su restauración. Migrar el formato de una pareja; rechazar entradas inválidas individualmente, sin reconstruir pestañas ni afirmar persistencia completa entre tareas/reinicios todavía no probada. Cargar asociaciones no debe forzar la selección guardada sobre la selección nativa actual.

## Sidebar y acciones

La proyección de la lista nativa conserva ambos IDs de cada pareja, pero emite una sola fila estable y no duplica sus miembros. La identidad de fila no depende del panel activo ni del orden físico tras intercambiar. La selección de la fila representa la pareja; el foco dentro del visor sigue perteneciendo a un Tab nativo real.

En expandido, ambos títulos tienen espacio limitado y elipsis independiente, conservando el separador visible. En compacto, ambos favicons permanecen visibles, con fallback cuando falte uno y tooltip accesible con los dos títulos. Respetar el color, altura, foco y hover del rail actual; no añadir otro marco pesado. Las respuestas asíncronas de títulos/iconos deben comprobar identidad y generación antes de actualizar una fila reciclada.

- Clic en la fila: restaurar pareja. Clic alterno/pulsación larga: menú nativo referido al miembro activo, con acción explícita «Separar pestañas».
- X de la cápsula del visor o «Salir de vista dividida»: separar sólo esa pareja y conservar ambas pestañas, como hoy.
- X de cierre de una fila expandida: conservar el cierre nativo del miembro activo, con tooltip inequívoco; el otro queda normal. En compacto, cierre desde menú, sin sustituir los dos logos por una X. No se incorpora un cierre simultáneo nuevo.
- Arrastrar una fila mueve la unidad visual usando los IDs vigentes; no dos índices de adaptador memorizados. Se mantienen los límites nativos de sección y la regresión de reordenamiento previa.
- No reasignar automáticamente Espacios, pinning ni grupos de Chromium para formar una pareja. En esta tanda, formar/reordenar una pareja requiere una sección de presentación compatible para ambos miembros; si no puede representarse una fila única sin alterar esa organización, indicar incompatibilidad y conservar el estado anterior. Cubrir esta restricción en selector y menú de enlaces. No mostrar datos de otro perfil como fallback.

## Integración técnica prevista

`ArcSplitState` sigue describiendo una pareja; un registro acotado conserva varias. `ArcSplitViewCoordinator` selecciona/suspende la presentación y observa el cierre/traslado de todos los miembros registrados, no sólo los dos visibles. `ArcDesktopCoordinator` conecta snapshots y notificaciones de cambios con la lista nativa.

En `TabListMediator`, `VerticalTabListCoordinator` y los binders verticales se integra una proyección de pareja con IDs explícitos para selección, cierre, contexto y drag. No superponer filas por encima del RecyclerView ni cambiar el TabModel por un modelo paralelo propietario de pestañas. Notificar cambios del registro para actualizar la sidebar incluso si el único cambio es un intercambio o una separación.

## Pruebas y condiciones de aceptación

1. RED: A/B → C → A/B mantiene ambos IDs, orden, proporción y activo, repetido varias veces.
2. RED: A/B y D/E → C → D/E → A/B conserva el estado independiente y no recarga páginas.
3. Filas: una por pareja, sin duplicados, títulos e iconos correctos al expandir/contraer, navegar, intercambiar, reciclar y reordenar. Selección nativa, menús y drag resuelven los IDs actuales.
4. Cerrar uno, separar una pareja inactiva, mover de ventana y cambiar de perfil no afectan a las otras parejas ni cambian la pestaña normal seleccionada. Cancelar un selector no modifica nada.
5. Preservar omnibox, enlaces Ctrl+Alt, diálogo por panel, proporción magnética, restauración de foco y comportamiento móvil. Probar suspensión de superficie con asociaciones conservadas.
6. Migración y lectura de estado: IDs ausentes, duplicados, restauración incompleta, ratios inválidos e incógnito. No recrear páginas ni seleccionar asociaciones obsoletas.

Usar el runner nativo Chromium correcto y conservar las limitaciones declaradas de los probes locales. El GREEN host no sustituye comprobar la nueva APK en el Galaxy. QEMU permanece deshabilitado por el usuario. Amazon continúa UNRESOLVED_GRAPHICS_BLOCKER.

## Compilación y alcance

No cambiar pin, GN args, toolchain, package ni flags gráficos. No clean build, purge ni borrado de checkpoints. La futura compilación será incremental desde el último checkpoint compatible y verificado; este diseño no despacha runs ni modifica el monitor. La integración y el build siguen después de la revisión del diseño, plan y pruebas pertinentes.
