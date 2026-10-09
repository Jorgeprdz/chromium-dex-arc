# Archium — reparación de crash y pulido DeX

Revisión sobre `0a403f4cf72c74906aaf3a17eb7a8026f6d1dd38`, misma rama
`feat/arc-media-only` y mismo worktree. Chromium permanece en
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; scope `arc-media`, passwords locales
deshabilitados. La autorización posterior del usuario permite commit, push, run,
capturas ADB e instalación de la actualización al finalizar una compilación exitosa.

**READY FOR COMMIT y compilación. Aceptación visual: PARTIAL.** La captura del APK
anterior confirma filas duplicadas tras mover un grupo. También confirma el panel
dibujado bajo el caption, la banda vacía de favoritos y el shortcut Autofill. Las
capturas se conservan privadas por contener información del usuario. No se afirma
que los fixes se hayan observado en el dispositivo antes de compilar el nuevo APK.

## Correcciones y evidencia

| Componente | Causa y cambio | Resultado |
|---|---|---|
| Crash al enfocar URL | `LocationBarTablet` conservaba el toolbar como ancestro tras reparentar el holder. Ahora resuelve el contenedor vivo, su scroll/padding y los márgenes RTL, conservando el cálculo nativo en MOBILE. Callbacks detached se omiten. | PASS host; PARTIAL dispositivo |
| Resize con URL expandida | El listener del header sobrescribía altura WRAP_CONTENT y márgenes de expansión. El layout Arc difiere el baseline mientras Chromium posee la expansión; unfocus aplica la geometría vigente. | PASS integración host |
| Arrastre de grupos | La actualización filtrada reconstruía todas las filas después del movimiento nativo, invalidando los holders aún usados por ItemTouchHelper. Los observers de reorder ahora podan filas ocultas sin reemplazar modelos visibles; merge/ungroup y cambios de membresía siguen reconciliándose. | PASS host; PARTIAL render de arrastre |
| Caption Android | El stacker real ya reserva 40 px y coloca BookmarkBar en Y=40. El fallo visible estaba en el outline del compositor. El borde inferior del spacer nativo se transforma a coordenadas del holder y de la superficie; hit testing usa el mismo rectángulo. No se suma otra altura al margen del compositor. | PASS contrato nativo/host; PARTIAL composición Android |
| Animación sidebar | Los listeners de rail/columna repetían applyAppearance y sus fondos por cada cambio de ancho. Ahora actualizan geometría/controles sin recorrer estilos ni rebind de colecciones; layout de igual tamaño no realiza trabajo. La transición nativa permanece intacta. | PASS trabajo de callbacks; fluidez real pendiente |
| Espacio entre secciones | Favoritos vacíos no reservan una fila. Spaces y colecciones se separan 8 dp; favoritos reales conservan las dimensiones de referencia. | PASS host/SDK |
| Footer | El scope sin passwords deja de crear un shortcut Autofill. Permanecen menú, extensiones y New Tab nativos. | PASS host/SDK |

No quedan bloqueantes confirmados de fuentes o checks locales de R2 en esta
revisión. El crash de foco y el reset durante drag son defectos encontrados en el
APK desplegado y corregidos en fuentes con regresiones RED→GREEN. Su aceptación
integral continúa pendiente de instalar y usar la nueva compilación en DeX.

## Geometría y responsive

| Medida | Referencia | Política final |
|---|---|---|
| Ventana de prueba | 1382 × 863 | 1382 × 863 a densidad 1 |
| Sidebar expandido | 334 px | 334 px objetivo, preservando ancho manual y límites Side UI |
| Sidebar colapsado | — | 52 dp nativos |
| Viewport sin caption | 1037 × 840, X=334, Y=12 | Sin cambios: 1037 × 840; insets 12/11/11 |
| Radios exterior/interior | 13/11 px estimados | Sin cambios: 13/11 normalizados por ancho/densidad |
| Omnibox no expandido | 316 × 49, márgenes 9 | Sin cambios; expansión/foco pertenecen a LocationBarTablet |
| Favoritos reales | 99/100/100 × 57; gaps 9/8 | Sin cambios; si no hay favoritos, la fila queda GONE |
| Spaces → colecciones | Sin medida exigida | Separación nueva 8 dp, 16 px a densidad 2 |
| Caption 40 y holder Y=16 | Zona reservada al SO | Clip local Y=24, borde visible en Y=40; no marginTop adicional |

La lista de pestañas conserva su presupuesto flexible y el footer anclado. Los
controles secundarios siguen cediendo espacio en ventanas cortas/estrechas. MOBILE
restaura la composición original; fullscreen elimina la decoración. El idioma RTL
no cambia el anclaje físico del Side UI nativo. No se añaden controles de ventana.

## Validación ejecutada

Python 3.12 y JDK 17, con Android jar 37:

```sh
ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar
ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh
```

Ambos checks PASS. Preparación: 96 archivos aplicados con hashes correctos y
compilación SDK aislada de adapters. Suite completa del worktree: **197/197 PASS**;
incluye 12 verificaciones de cambios anteriores del monitor conservados pendientes,
que no forman parte de este commit de fixes. Se mantienen las regresiones R2.

Las regresiones nuevas ejecutan cuerpos reales de Java contra límites Android
simulados. La prueba de caption utiliza fixtures upstream íntegros y comprobados
para TopControlsStacker/BookmarkBarCoordinator. Sus resultados no sustituyen el
renderizado SurfaceView, la entrada real ni mediciones de frames en DeX.

La revisión independiente encontró la interferencia del setter de geometría con el
omnibox expandido; se corrigió antes de repetir la suite completa. Los dos fallos
iniciales de la suite general eran un doble de favoritos desactualizado y una
aserción textual de New Tab; se actualizó el doble sin reducir las comprobaciones
de dimensiones y se conservó el comentario correcto de propiedad nativa.

## Archivos de esta entrega

- LocationBarTablet: original pinned nuevo y fuente modificada en `.source-reference` / `.source-modified`.
- VerticalTabListCoordinator: observers nativos de reorder en `.source-modified`.
- ArcDesktopCoordinator, ArcCollectionsView y ArcDesktopPolicy en `chromium/`.
- `patches/archium-desktop.patch` y `patches/upstream-files.json` regenerados.
- Tests nuevos de locationbar, group drag, sidebar animation/polish y caption stacker, con dos fixtures upstream.
- Tests existentes de geometry/runtime actualizados para los límites añadidos.
- Este informe. El diff completo está disponible en el commit de esta entrega.

Riesgos residuales: confirmar crash/foco/dropdown durante resize, reorder en grupos
expandidos y Spaces, caption combinado con bookmarks/superficie, fluidez de la
transición y restauración AUTO/ARC/MOBILE en el nuevo APK. Las copias del drag ya
atascadas en la instancia anterior desaparecen al recrear esa instancia; el fix
previene el reset que las provoca y no borra datos de navegación.
