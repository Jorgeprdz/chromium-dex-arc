# R5.3 — omnibox, historial y vista dividida

Rama de implementación: `assistant/archium-r5-3-omnibox-split`, base `5b8694a`.
Chromium `157.0.8086.0`, pin `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
Estado: implementación conectada; revisión y gates finales en curso. Sin APK nueva ni run despachado.

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
Si la ventana completa baja de 480 dp se suspende la presentación y se conserva la pareja.

## RED/GREEN y alcance

- Estado puro: 6 JUnit PASS.
- Omnibox: baseline 10/16 FAIL; tests posteriores 18/18 PASS; auxiliares anidados cubiertos.
- Helpers R5/historial: 44 PASS.
- Policy móvil: RED clase ausente → 6 PASS. Integración: RED desktop no cambiado → GREEN SDK30/36.
- Superficie: RED NPE al perder ContentView durante suspensión → GREEN no adjunta pareja obsoleta/parcial.
- Split completo: 50 PASS (controles, animator, ContentHost, controller, viewport policy y cuerpos Java/JNI). Incluye selectores, cancelación, selección, perfiles, cierre, rollback, background, restauración, IDs faltantes y no persistir incógnito.
- Probe C++ compila el `.cc/.h` entregado, verifica geometría/IDs/límites en adaptadores explícitos de Layer/Tab/JNI. Probe de menú ejecuta AnchorInfo real. No son GPU, enlace Chromium ni capturas Android.
- Preparación aplica/parchea originales y compila Arc contra contratos sintéticos tipados; no sustituye build real GN/JNI/Chromium. Suite completa y revisión final se registrarán al concluir.

## Riesgos y aceptación pendiente

QEMU_ABI_BLOCKED; ningún PASS de Android gráfico. Dos páginas visibles, hit testing/IME, permisos/diálogos por panel, TalkBack, restauración tras muerte del proceso, pérdida de superficie y consumo de memoria/rendimiento requieren APK nueva y ejecución real. Fuente y host no acreditan píxeles, GPU ni estos resultados funcionales.
El fix de diálogos `5184755` y el arreglo de identidad/reordenamiento se preservan. El usuario confirmó diálogos visibles en la APK `5b8694a`; no implica validación de split.
Amazon permanece `UNRESOLVED_GRAPHICS_BLOCKER`, fuera de este lote. No flags gráficos, limpieza de outputs, alteración de pin/GN args/toolchain ni borrado de checkpoints.

## Compilación posterior

Sólo candidato completo y revisado → checkpoint compatible verificado → una compilación incremental autorizada. Fuente prevista `archium-checkpoint-38511423805-1`, commit `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`, run `38511423805`; restauración/hash y configuración se vuelven a verificar antes de compilar. Presupuesto y límites del supervisor se preservan.
