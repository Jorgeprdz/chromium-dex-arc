# R5.3 — omnibox, historial y vista dividida

Rama de implementación: `assistant/archium-r5-3-omnibox-split`, base `5b8694a`.
Chromium `157.0.8086.0`, pin `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
Estado: implementación conectada y correcciones de revisión verificadas; suite host final en curso. Sin APK nueva ni run despachado.

## Presentación y autoridad

- `StaticTabSceneLayer` conserva dos ContentLayer con IDs/bounds independientes y capas vivas del TabContentManager. JNI transmite ambas geometrías; la ruta de una pestaña se conserva.
- `StaticLayout.onShown` no sustituye el activo al mostrar la secundaria; ambas IDs quedan visibles mientras la escena es una pareja válida.
- `ArcSplitContentHost` adjunta ContentViews existentes y conserva/restaura sus LayoutParams y offsets. No crea WebContents, snapshots, WebView ni iframe.
- `CompositorViewHolder` dimensiona ambos WebContents y selecciona por identidad antes de dispatch de DOWN/rueda. TabModel sigue siendo autoridad de omnibox, historial y navegación.
- El controlador valida modelo, perfil, ventana y tipo de contenido. Observar cierre/movimiento y background/foreground permite suspender/recuperar sin reconstrucción global.
- Persistencia: IDs y ratio normales por task; espera restauración nativa, descarta IDs inexistentes y no escribe parejas incógnito.

## Funciones conectadas

Menú nativo de pestaña → Pantalla dividida → pestaña existente/nueva (`about:blank`) o salida. Entrada por menú existente de clic derecho/long press, sin modificar drag/reordenamiento.
Cápsula blanca con flechas oscuras apiladas, separador ajustable .2–.8 y objetivo táctil ampliado.
Swap anima posiciones de capas nativas durante 180 ms, conserva identidad activa y no navega. Resize/destroy/segundo swap terminan la animación; animaciones desactivadas aplican final inmediato. Durante transición bloquea input.
Clic omnibox reutiliza pop-up Ctrl+T con URL seleccionada; Ctrl+T vacío. Mantener Atrás/Adelante abre historial nativo del Tab activo.

## Panel estrecho — solicitud adicional

Cada WebContents recibe el ancho de su panel: CSS responsive no usa el ancho de toda la ventana.
`ArcSplitViewportPolicy` pide UA móvil por NavigationController por debajo de 600 dp; restaura preferencia escritorio al llegar a 640 dp (histéresis), salir o retirar controlador. No cambia DSF, zoom ni preferencias globales/de sitio; no fuerza escritorio a quien ya usa móvil. Respeta restauración explícita de escritorio detectada mientras controla el panel.
No recarga automáticamente: `setUseDesktopUserAgent(..., false, false)` está verificado en el NavigationController del pin. Una variante móvil servida por el servidor puede necesitar navegación/recarga explícita del usuario; no se promete adaptación automática de páginas no responsive.
Se garantiza un mínimo de 240 dp por panel ajustando únicamente la proporción presentada; se conserva la proporción solicitada para recuperar al ampliar. Si la ventana completa no admite dos mínimos se suspende la presentación y se conserva la pareja.

## RED/GREEN y alcance

- Estado puro: 6 JUnit PASS.
- Omnibox: baseline 10/16 FAIL; tests posteriores 18/18 PASS; auxiliares anidados cubiertos.
- Helpers R5/historial: 44 PASS.
- Policy móvil: RED clase ausente → 6 PASS. Integración: RED desktop no cambiado → GREEN SDK30/36.
- Superficie: RED NPE al perder ContentView durante suspensión → GREEN no adjunta pareja obsoleta/parcial.
- Split completo tras revisión: 68 PASS (controles, animator, ContentHost, controller, viewport policy y cuerpos Java/JNI). Incluye selectores, cancelación, selección, perfiles, cierre, rollback, background, restauración, IDs faltantes y no persistir incógnito.
- Probe C++ compila el `.cc/.h` entregado, verifica geometría/IDs/límites en adaptadores explícitos de Layer/Tab/JNI. Probe de menú ejecuta AnchorInfo real. No son GPU, enlace Chromium ni capturas Android.
- Preparación aplica/parchea originales y compila Arc contra contratos sintéticos tipados; no sustituye build real GN/JNI/Chromium. Suite host completa se registra al concluir; revisión independiente realizada y hallazgos importantes cubiertos con regresiones.

## Riesgos y aceptación pendiente

QEMU_ABI_BLOCKED; ningún PASS de Android gráfico. Dos páginas visibles, hit testing/IME, permisos/diálogos por panel, TalkBack, restauración tras muerte del proceso, pérdida de superficie y consumo de memoria/rendimiento requieren APK nueva y ejecución real. Fuente y host no acreditan píxeles, GPU ni estos resultados funcionales.
El fix de diálogos `5184755` y el arreglo de identidad/reordenamiento se preservan. El usuario confirmó diálogos visibles en la APK `5b8694a`; no implica validación de split.
Amazon permanece `UNRESOLVED_GRAPHICS_BLOCKER`, fuera de este lote. No flags gráficos, limpieza de outputs, alteración de pin/GN args/toolchain ni borrado de checkpoints.

## Compilación posterior

Sólo candidato completo y revisado → checkpoint compatible verificado → una compilación incremental autorizada. Fuente prevista `archium-checkpoint-38511423805-1`, commit `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`, run `38511423805`; restauración/hash y configuración se vuelven a verificar antes de compilar. Presupuesto y límites del supervisor se preservan.

## Revisión independiente y correcciones finales

Una revisión de rama completa identificó cinco hallazgos Important, sin Critical. Una sola pasada de corrección, sin segundo revisor:

1. Recuperación: invalidar caché ante ContentView cambiado/Activity oculta; foreground vuelve a mostrar ambos. Si rebind falla, retirar presentación y conservar tabs. RED de mismo viewport/IDs → GREEN.
2. Foco: `ArcSplitContentHost.focus` y helper nativo del holder, llamados en selección y presentación, restaurados al recuperar foco de ventana. No desplazar omnibox, editor Android ni modal; RED API ausente → GREEN de vistas Android y cuerpo real del helper. TabModel sigue siendo autoridad antes del input.
3. Teclado: inicializar activo antes que peer y aplicar modo global sólo desde Tab actual. RED derecha sobrescribía modo de izquierda → GREEN con modos diferentes y activo invertido. Ambos paneles comparten la política IME de la ventana activa; medición del teclado y entrada real siguen PENDING_DEVICE_VALIDATION.
4. Restauración: distinguir estado inválido de arranque incompleto. No consumir intento por Tab actual null, modo móvil o holder no preparado; observer de disponibilidad por frame reintenta sólo en transición, sin loop por frame. RED borrado/pérdida de intento → GREEN preservación y recuperación sin crear tabs.
5. Mínimos: proporción efectiva limitada por 240 dp en ambos lados, conservando preferencia. RED .2 en 500 dp → GREEN .48; densidades 1/1.5/2.625 y RTL cubiertas.

Adicionalmente se reprodujo y corrigió rollback de entrada fallida: vuelve a selección previa, recupera pareja anterior y oculta peer no adjuntado sin cerrar pestañas (RED 4 fallos → GREEN).
La suite host inicial falló sólo por el inventario cerrado de filtros de CI, que no incluía los cinco suites split añadidos. Se actualizó el inventario para exigirlos, sin retirar gates existentes.

### Decisiones y alcance del revisor

- Ruling: viabilidad de fuente admite preparar APK; pruebas host no certifican composición/píxeles/input Android. Coste si falla: revisión de diagnóstico sobre APK, nunca declarar aceptación visual previa.
- Ruling: ratio lógico .2–.8, mínimo físico efectivo 240 dp y suspensión sin cerrar tabs; coste: proporción temporal ajustada en ventanas pequeñas.
- Ruling: móvil 600/640 dp sin recarga ni cambio de zoom/global; coste: variantes de servidor requieren navegación explícita.
- Ruling: insets de ventana siguen al panel activo, no al situado a la derecha; coste: comportamiento de IME mixto debe validarse en APK.
- Diferidos Minor: UpdateVisibleIds de dos tabs por frame conserva preparación de fallback pero requiere medir coste; métodos compactos dificultan auditoría y pueden reformatearse posteriormente. Sin correcciones de polish en esta pasada.
- Apartados por requerir ejecución real: GPU, Surface, TalkBack, permisos/diálogos y memoria/rendimiento. Permanecen pendientes de APK compatible; no se descartan como requisitos.
- Compilación Chromium, GN y JNI generado: gates obligatorios del build incremental, no sustituidos por adaptadores.
- Wrapper NavigationController destruido: autoridad adicional del mismo pin inspeccionada (`NavigationControllerImpl.java`, SHA256 `db926a125b4ea60565d00a0e4447e95b591e6331c341e833d7f61d4c7c9cfd5d`); getter retorna false y setter no hace JNI si el puntero es cero. No se inventa crash ni se añade parche para uno no demostrado.
- Atribución completa de permisos desde panel inactivo: pendiente de prueba Android, ninguna afirmación de validación por corregir sólo foco.
- Amazon permanece fuera de alcance y bloqueado.
