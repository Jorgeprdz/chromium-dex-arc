# Archium — omnibox y vista dividida (propuesta para revisión)

Fecha: 20-oct-2026. Rama aislada: `assistant/archium-r5-3-omnibox-split`.
Base: `5b8694a07f328128e1267262780e6996b0ba4509`.
Estado: DRAFT — implementación de vista dividida pendiente de aprobación.

## Intención y alcance

El usuario reporta que ya no ve sugerencias al escribir en la omnibox lateral.
Se debe recuperar el desplegable de Chromium y conservar historial, búsqueda,
seguridad de navegación y comportamiento de teclado; no sustituirlo por resultados falsos.

El usuario solicita dos páginas reales en el mismo visor de Archium. La entrada
será el menú de una pestaña, mediante clic derecho o pulsación prolongada.
Confirmó «ambas» opciones para elegir el segundo panel: pestaña abierta o nueva.
No se modifica Amazon, el motor, flags gráficos, perfiles ni datos del teléfono.

## Interacción propuesta

1. Menú de pestaña: «Pantalla dividida».
2. Submenú: «Elegir pestaña abierta» / «Abrir pestaña nueva».
3. La pestaña del menú ocupa el panel izquierdo. La segunda ocupa el derecho.
4. Distribución inicial 50/50; un separador permite ajustar los tamaños.
5. Clic o toque en un panel lo activa. Omnibox, atrás/adelante, recarga y atajos
   actúan sobre ese panel; ambos contenidos permanecen visibles e interactivos.
6. «Salir de vista dividida» conserva las dos pestañas y muestra la activa.
7. Cerrar una pestaña usa el cierre nativo habitual; el panel restante vuelve
   al visor completo. Nunca se intercambian silenciosamente identidades de pestaña.

Supuestos de la propuesta: vista lado a lado; máximo dos paneles por ventana;
no mezclar pestañas normales con incógnito ni perfiles distintos. Si falta
ancho para dos paneles utilizables, mostrar temporalmente sólo el activo,
conservando la pareja para recuperar la división al ampliar la ventana.

## Opciones técnicas y recomendación

A. Ampliar el host compositor existente para dos contenidos nativos visibles.
Reutiliza integración de Chromium, pero afecta contratos hoy escritos para una
única pestaña activa, composición, tamaños y accesibilidad.

B. Añadir un segundo host compositor coordinado dentro de la misma Activity.
Separa los bounds y parte del lifecycle, pero duplica recursos de presentación
y requiere comprobar compatibilidad con WindowAndroid, foco y los delegates.

Se recomienda investigar primero A, manteniendo B como alternativa evaluada
antes de fijar la implementación. No se permite escoger una ruta sin demostrar
que presenta dos WebContents reales y que el renderizado/foco se conservan.
No se usan WebView, iframes, bitmaps de pestañas ni ventanas Android separadas.

## Límites del código comprobado

`VerticalTabListCoordinator` ya tiene rutas de clic contextual y long press.
Debe extenderse su menú de pestaña, sin reemplazar el drag existente.

`CompositorViewHolder.setTab()` mantiene `mTabVisible`, `mView`, un
`OnscreenContentProvider` y `mContentView` únicos. Dos columnas Android o un
segundo contenedor por sí solos no implementan dos páginas vivas.
No se ha demostrado todavía una API nativa lista para dividir esta versión.

## Contratos de estado e integración

- Un controlador de pareja conserva IDs nativos de ambas pestañas, panel activo
  y proporción. TabModel/TabModelSelector siguen siendo propietarios de las pestañas.
- Cada pestaña mantiene su WebContents; no se recrea al cambiar el foco.
- Navegación, permisos, descargas y diálogos deben asociarse a la pestaña real
  correspondiente. Se conserva el fix de presentación `5184755`.
- Redimensionar cambia sólo los bounds nativos de cada panel y los insets
  correspondientes; no se fuerza DSF ni zoom.
- Destruir la Activity libera observers/hosts y no destruye perfiles.
- Restauración de pareja exige reconciliar IDs con la restauración nativa;
  no se declara persistencia completa antes de probarla.
- Las páginas nativas/no compatibles no se convierten en otra URL ni se cargan
  de nuevo silenciosamente; el controlador debe rechazar la combinación sin
  modificar las pestañas existentes hasta definir soporte verificable.

## Verificación y aceptación

Omnibox: RED reproducible, sugerencias visibles al escribir, selección con
mouse/teclado, Enter/Escape, foco, sidebar expandida/compacta y modo móvil.

División: pareja A/B correcta, elegir existente/nueva, foco y navegación por
panel, drag de separador, cierre, salida, resize, recreación de Activity,
diálogos por pestaña, separación de incógnito y ausencia de fugas/overlap.

Tests host/Robolectric no equivalen a dos superficies funcionando en Android.
QEMU sigue `QEMU_ABI_BLOCKED`; aceptación visual y de superficies será pendiente
hasta ejecución real de la APK correspondiente.

## Build y documentación

No despachar un build por redactar esta propuesta. No compilar desde cero,
limpiar outputs ni modificar GN args/toolchain/pin para facilitar la división.
Un cambio nativo futuro sólo permite recompilar dependencias invalidadas por
el grafo de Ninja, después de verificar el checkpoint e integrar los gates.
Actualizar TODO con implementación, resultados reales y limitaciones por separado.

## Decisión solicitada

Aprobar el comportamiento propuesto y el alcance de integración nativa para
preparar el plan técnico. Esta propuesta no afirma viabilidad ni implementación
terminada y no autoriza presentar un botón inoperante como la función completa.
