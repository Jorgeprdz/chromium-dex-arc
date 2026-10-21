# R5 Desktop final + Mobile — checkpoint acotado

Base: a2ad646f4dabd96a1ba82dc246b8184a708d32b4, instalada por run 39562759522.
Rama: assistant/archium-r5-final-mobile, worktree /workspace/Archium-R5-final-mobile.
Chromium: cfd94726b7b5fb48aedcc32662f2f3fbdbadec35, sin cambios de motor, GN, toolchain, dependencias ni branding.

## Bloque A: implementación y límites

- D1: retirado el override transitorio de User-Agent de ArcSplitViewportPolicy. El hook se conserva sin efectos para no romper sus consumidores/gates. El tamaño físico continúa por CompositorViewHolder.updateWebContentsSize → WebContents.setSize y los ContentViews de cada panel. No se fuerza page scale, UA ni recarga; no se modifican ratios, identidad o selección de parejas. RED/GREEN del contrato UA y 140 pruebas del conjunto split pasan. **Esto no demuestra resuelto el zoom residual del renderer. D1 continúa abierto hasta evidencia 50→25→50 real.**
- D2: mosaicos GridLayout con slots de 64dp + márgenes de 4dp por lado; columnas según ancho útil. Nunca una columna: bajo dos slots, botón con menú de todos los favoritos en orden almacenado. Scroll sólo vertical para poblaciones grandes. Resize conserva las instancias de mosaicos/favicons y los datos. Se invalidan restricciones de columnas antes de reducirlas. El shell mantiene accesibles favoritos también en rail compacto, sin mostrar allí toda la UI de colecciones.
- D3: target invisible de 16dp en VerticalTabsSideUiCoordinator.getResizeHandleWidthPx, conservando límites, arrastre y persistencia nativos. Test upstream actualizado pero **suite nativa de este coordinador NOT RUN**. Cursor, hover, feedback y posibles interferencias requieren revisar el handler nativo y probar mouse/touch/stylus. `manual_resize` conserva su configuración previa; su default upstream es false. No afirmar que el agarre esté activo en toda configuración.
- D4: Fijar/Añadir favorito pasan a iconos con descripción y tooltip cuando sus mitades no admiten texto; la anchura elegida no cambia. El menú de favoritos compacto usa icono y descripción accesible.
- D10: matriz de vistas Android verificada para ancho amplio, dos columnas, menú y vuelta al ancho inicial, conservando objetos y almacenamiento. Menú abre todos los elementos en orden. **DeX/Galaxy reales y arrastre continuo NOT RUN. D10 no cerrado.**

## Pruebas

Evidencia privada: /workspace/archium-evidence/r5-final-mobile/.

- split.log: 140 PASS, Robolectric SDK30/36; adapters de Tab/WebContents/JNI explícitos, no aceptación de Blink/Viz.
- collections.log: 20 PASS, vistas/estado completos con R sintético y NativeTabs mock. Reflow, menú, identidad, foco y presupuestos. No prueba composición web.
- geometry.log: 18 PASS, vistas/drawables y expresiones reales del shell.
- grid-green.log: política real compilada; slots de distintas densidades, incluida fraccional, sin overflow ni columna única.
- projection.log: 17 regresiones PASS; drag.log: 3 PASS; gate-coverage.log: 2 PASS.
- patch.log: 24 PASS. preparation.log: parche de 159 archivos reproducible y compilación API SDK37.2 aislada PASS.
- Suite host completa, compilación nativa Chromium, APK nueva, rendimiento, memoria y pruebas físicas: NOT RUN.

El primer intento local con JDK17 no compiló jars Android para Java21; no se cuenta como RED del producto. Se usó el JDK21 ya instalado, sin descargas ni cambios al toolchain de producción. Dos expectativas anteriores del controlador que exigían cambiar UA fueron sustituidas por el contrato aprobado: resize no modifica el modo de sitio ni recarga. Se conservó RunWith/Config para descubrimiento nativo.

## Continuación exacta

1. D1: usar fixture local responsive con meta viewport y registrar innerWidth, clientWidth, visualViewport.width/scale, devicePixelRatio y eventos resize al alternar 50→25→50 varias veces. Comparar con geometría real de cada WebContents. No introducir reset de zoom ni reload sin demostrar causa. No tocar páginas externas.
2. D3: localizar el handler de resize que consume getResizeHandleWidthPx mediante SideUiCoordinator del pin, comprobar habilitación manual_resize en el dispositivo, cursor y hover, captura/cancelación del drag y persistencia. Conservar límites 92–500dp. Probar favoritos durante resize.
3. Cerrar D4/D10 con mouse/teclado/touch y ventana baja/estrecha antes de marcar aceptación. Revisar el presupuesto vertical con muchas filas de favoritos.
4. Bloque B D5–D9: revisar sólo deltas necesarios sobre la base instalada; no reabrir primer clic ni decoración ya implementados sin fallo reproducido.
5. Bloques C/D Mobile: **NO IMPLEMENTADOS en este checkpoint**. Mantener diseño aprobado (omnibox superior y cuatro acciones inferiores); reutilizar bottom sheet, thumbnails, NTP y Spaces nativos. Punto de entrada actual: TabbedRootUiCoordinator y prepareArcMobileNavigation. Este último cambia UA de pestañas al volver a ventana móvil: revisar su conflicto con M9 (solicitar sitio escritorio no debe cambiar interfaz ni perder preferencia). No añadir controles falsos de resumen/traducción ni un segundo store de Spaces.
6. Al tener conjunto listo y gates específicos verdes, regenerar parche y usar checkpoint compatible. Esta solicitud tiene **0/1 workflows remotos consumidos**. No se publicó ni instaló APK nueva. No reintentar automáticamente tras el único intento autorizado.

Comandos específicos (usar cwd de este worktree):

```sh
python3 scripts/test-robolectric-collections.py --classpath-file /workspace/macdesk-maintenance/archium-r53/classpath-with-mockito.txt --java-home /root/.gradle/jdks/amazon_com_inc_-21-aarch64-linux.2 --work /workspace/archium-evidence/r5-final-mobile/collections
python3 scripts/test-robolectric-split.py --classpath-file /workspace/macdesk-maintenance/archium-r53/classpath-with-mockito.txt --java-home /root/.gradle/jdks/amazon_com_inc_-21-aarch64-linux.2 --work /workspace/archium-evidence/r5-final-mobile/split --controller
python3 scripts/test-robolectric-sidebar-geometry.py --classpath-file /workspace/macdesk-maintenance/archium-r53/classpath-with-mockito.txt --java-home /root/.gradle/jdks/amazon_com_inc_-21-aarch64-linux.2 --work /workspace/archium-evidence/r5-final-mobile/geometry
python3 -m unittest discover -s tests -p test_favorites_grid.py
python3 scripts/generate-arc-patch.py
python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.2/android.jar
```

Las rutas históricas de classpath contienen herramientas host reutilizadas; no son el repositorio de implementación.
