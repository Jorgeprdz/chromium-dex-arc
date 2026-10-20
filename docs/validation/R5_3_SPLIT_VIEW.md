# R5.3 — vista dividida: estado de integración

Diseño y plan aprobados el 20-oct-2026. Trabajo aislado de la rama de compilación.
No se ha despachado otro run ni se ha tocado el supervisor/checkpoint.

## Contratos comprobados en Chromium fijado

Revision `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, versión 157.0.8086.0.

- `CompositorViewHolder.setTab()` conserva un solo `mTabVisible`, `mContentView`
  y `OnscreenContentProvider`; actualiza foco y listeners al cambiar la pestaña.
- `updateContentOverlayVisibility()` agrega/quita una sola vista. Las ContentView
  web no se posicionan como las páginas nativas en `repositionTabViewForSideUi()`.
- `StaticLayout.onShown()` cambia `LayoutTab.TAB_ID` al de cualquier pestaña
  que se muestra. Mostrar una segunda sin adaptar ese contrato cambia la escena.
- `TabImpl.show()/hide()` cambian visibilidad/interactabilidad y emiten observers;
  hide se usa tanto al cambiar de tab como al ocultarse la ventana.
- `StaticTabSceneLayer.UpdateTabLayer()` posee una sola ContentLayer; el offset
  X se refleja en ViewAndroid. ContentLayer reparenta la capa viva durante update.
- `ContextualSearchSceneLayer` muestra que un árbol puede contener otro WebContents
  vivo; no demuestra por sí solo dos Tabs con input, lifecycle y accesibilidad correctos.
- `ContentView.setContentOffsetXPix()` altera getLocationInWindow. EventOffsetHandler
  del holder obtiene el EventForwarder exclusivamente de `mTabVisible`.

La primera integración pendiente es conservar dos attachments y su visibilidad
sin que onShown de la secundaria sustituya la pestaña de la escena, y hacer
coincidir los offsets de input con bounds de composición independientes.
No se han modificado estos contratos nativos durante la investigación.
Dos columnas Android o animar View.translationX no demuestra que dos superficies
web estén presentadas; tampoco demostraría una transición nativa correcta.

## Implementación independiente comprobada

`ArcSplitState` conserva IDs, activo y proporción; TabModel sigue siendo propietario.
Seis casos JUnit PASS: inicio, rechazo sin perder pareja, swap reversible sin
cambiar activo/proporción, cierre de cualquiera, salida idempotente y ratio finito.
La fase RED detectó ausencia de la clase; no es reproducción de un bug gráfico.
Este componente aún no está conectado a un menú ni presenta WebContents.
Ruling: preparar estado independiente mientras continúa el gate de contrato nativo;
no habilitar una función incompleta en la interfaz.

## Cápsula y movimiento aprobados

Cápsula blanca pequeña y redondeada sobre el separador; flechas oscuras → / ←
apiladas. Intercambio propuesto de 180 ms, suave y rápido, sin navegación/reload.
Respetar animaciones desactivadas; resize/destroy deben cancelar dejando bounds
finales válidos e input coherente. Especificado, no presentado como animación ejecutada.

## Gate y siguiente paso

INTEGRATION_PENDING: falta adaptar y probar juntos escena, attachments, viewport,
foco, lifecycle e input antes de conectar el menú existente/nueva y el divisor.
La prueba crítica es dos WebContents vivos, cada uno con coordenadas y navegación
correctas, no dos snapshots. Los tests de estado no satisfacen ese gate.
QEMU_ABI_BLOCKED. No hay APK nueva para comprobar esta integración en Galaxy.
No se declara PASS visual ni se marca la vista dividida terminada.
Cambios actuales de omnibox/historial conservan pin, GN args, toolchain y package;
el último checkpoint debe verificarse de nuevo antes de cualquier build futuro.
