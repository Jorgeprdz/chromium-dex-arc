# Archium — revisión de paridad Arc y segunda ronda DeX

Base revisada: `cb408045086340b964ab000467d2575f944345b1`, rama `feat/arc-media-only`, mismo worktree. Se conserva `ARCHIUM_BUILD_SCOPE=arc-media`, passwords locales deshabilitados y el trabajo previo del monitor.

**Dictamen de fuentes: READY FOR COMMIT y compilación autorizada. Checks finales de publicación PASS.** La aceptación Android/DeX sigue PARTIAL: la pantalla está desconectada y la APK modificada aún no está validada visualmente. El usuario retiró LinkedIn del scope y autorizó explícitamente commit, run, monitor e instalación automática verificada. Un PASS host no constituye aceptación visual.

## Cambios y componentes

| Archivo o componente | Cambio y propósito |
|---|---|
| `ArcDesktopCoordinator.java` | Observer SideUi después del commit de animación; integra bookmarks y navegación; gradiente continuo de sidebar; preset cálido; controles propios 14sp/48dp; libera nuevos observers. |
| `ArcNativeBookmarksBridge.java` — nuevo | Proyecta el BookmarkModel real, incluidos marcadores locales/cuenta y carpetas; usa BookmarkOpener/BookmarkManagerOpener nativos; no mantiene almacenamiento propio. |
| `ArcFavoriteTiles.java` — nuevo | Distribuye favoritos en tres columnas, filas uniformes y RTL; conserva todos los elementos mediante scroll. |
| `ArcCollectionsView.java` | Integra la proyección nativa junto a las colecciones existentes; limita favoritos visibles a tres filas; conserva espacios, carpetas y sus acciones; controles legibles de 14sp/48dp. |
| `ArcNavigationState.java` — nuevo | Escucha la pestaña autoritativa de ActivityTabProvider; habilita atrás/adelante, muestra Reload/Stop y ejecuta acciones del Tab real; pausa en MOBILE y libera listeners. Reutiliza los tres botones existentes. |
| `ArcDesktopAppearance.java`, `ArcDesktopPolicy.java` | Tokens centralizados de gradiente, contraste, tamaño de texto, radio y New Tab. Drawable reutilizado cuando la paleta permanece igual. |
| `TabbedRootUiCoordinator.java` | Conecta el puente, el supplier de pestaña y la supresión nativa del caption; oculta BookmarkBar horizontal en ARC sin cambiar preferencias; inicializa la búsqueda nativa también al entrar en ARC desde MOBILE. |
| `ToolbarControlContainer.java` | Libera las exclusiones de gestos del toolbar oculto y su interceptación de entrada; restaura la geometría nativa y las últimas exclusiones del llamador en MOBILE; respeta attach/detach. |
| `VerticalTabListCoordinator.java` | En ARC utiliza el overlay de búsqueda existente; fuera de ARC conserva la decisión nativa del feature flag. Mantiene los arreglos previos de movimiento de grupos. |
| `LocationBarTablet.java`, `UrlBarMediator.java` | Usa la opción nativa de mostrar el origen cuando no se está editando. La URL real completa sigue disponible al editar, navegar y copiar. |
| `TabVerticalViewBinder.java`, `VerticalTabListViewBinder.java`, `VerticalTabRailLayout.java` | Ajustan pestañas normales, contraste, radio, texto y New Tab; conservan hover, multiselección, pinned/grupos y restauran valores nativos en MOBILE, incluido incógnito dedicado. |
| `arc_strings.xml`, `chrome_java_sources.gni` | Etiquetas de preset cálido/personalizado y registro de los tres nuevos adaptadores. |
| `scripts/check-arc-preparation.py` | Contratos SDK de los nuevos adaptadores; mantiene explícita la distinción entre compilación aislada y Chromium/JNI real. |
| Nuevas pruebas y fixtures fijadas | Resize del contenido, URL compacta, bookmarks, caption/input, apariencia, ancho, superficies de navegación y estado de navegación. |
| `patches/archium-desktop.patch`, `patches/upstream-files.json` | Patch completo regenerado contra Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; 101 archivos. |

## Geometría de referencia y política implementada

Esta tabla compara la política ejecutada por los tests con la referencia de imagen. No representa una captura posterior del APK nuevo. La densidad de prueba es 1; en Android se usan píxeles medidos del layout y los límites táctiles se convierten desde dp.

| Medida | Referencia Arc | Política implementada |
|---|---:|---:|
| Ventana de referencia | 1382 × 863 px | 1382 × 863 px |
| Sidebar expandido automático | 334 px, 24.17 % | 334 px, 24.17 % |
| Viewport X/Y de referencia | 334 / 12 px | 334 / 12 px |
| Viewport ancho/alto | 1037 × 840 px | 1037 × 840 px |
| Insets arriba/derecha/abajo | 12 / 11 / 11 px | 12 / 11 / 11 px |
| Radios exterior/interior | ~13 / ~11 px | 13 / 11 px |
| Omnibox, altura | 49 px | 49 px; mínimo táctil 48dp |
| Márgenes laterales de controles | 9 px | 9 px |
| Mosaicos, altura y huecos | 57 px; 9 / 8 px | 57 px; 9 / 8 px |
| Pestaña normal, radio | ~12–15 px | 14 px a escala de referencia |
| Texto principal | ~13–14 px de imagen | 14sp, con escalado de fuente Android |
| Sidebar colapsado | Contrato Android | 52dp, sin aplicar el porcentaje expandido |
| Footer | Centro ~833 px | Anclaje inferior; centro 833 px en el fixture 863 px |

La captura DeX usada para diagnosticar tiene ventana de **1628 × 875 px**, configuración **160dpi**, fontScale **0.9** y sidebar observado de aproximadamente **206 px (12.65 %)**. El allocator nativo ejecutado con W=1628, densidad=1 y ancho disponible=1216 produce **393 px** si no existe un resize manual guardado. En una ventana W=1303, el objetivo automático de referencia es aproximadamente **315 px**.

No se verificó el valor privado guardado de resize ni el ancho de WindowMetrics usado en el momento original de la captura. La opción explícita «Ancho automático de barra lateral», en el menú de apariencia, usa el setter nativo y fuerza el recálculo SideUi: la regresión comprueba 206→393 px. Conserva el ancho manual hasta que el usuario elige esa acción. La regla automática ya era proporcional en la base instalada; la causa de aquel 206 px no se declara resuelta.

El caption de Android se obtiene del contrato AppHeader/TopControlsStacker, no de la captura macOS. Su altura se reserva una vez y se transforma a coordenadas del holder/surface para clipping e input. Las coordenadas de imagen sin caption no deben convertirse directamente en posiciones absolutas sobre los controles DeX.

Tokens: referencia `1382/863/334`, colapsado `52dp`, navegación `48dp`, texto `14sp`, radio de pestaña `14 × referenceScale`, glyph New Tab `18dp` con hit mínimo `48dp`, alpha `204`, hueco de sección `8dp`, cálido `#EDAE9F`. El color personalizado/default previo se conserva; el preset cálido es una elección disponible en el menú de apariencia.

## Responsive y diagnóstico de los reportes

- **Contenido al colapsar:** la captura conserva el recorte del ancho expandido después de que Chromium ya redimensionó WebContents. El callback final de SideUi ahora actualiza el clip después de publicar las nuevas specs. Hover sigue reservando el ancho colapsado y los cambios manuales usan la ruta nativa.
- **Franja blanca:** se retira la superficie horizontal redundante de bookmarks en ARC y se libera la propiedad visual/input del toolbar oculto. Falta comprobar en el APK nuevo cuánto de la franja fotografiada procedía de esas superficies.
- **Dirección incompleta:** origen nativo compacto fuera de edición; texto completo durante la sesión de input y al copiar. No se emplea un servicio externo ni se cambia la URL navegada.
- **Favoritos:** mosaicos de tres columnas conectados al BookmarkModel real. Carpetas abren el manager nativo. Edición/movimiento/persistencia usan los modelos existentes; el scroll conserva accesibles las filas adicionales.
- **Búsqueda de pestañas:** la ruta anterior con feature flag apagado abría HubSearchActivity. ARC ahora inicializa y usa el overlay nativo dentro de la misma ventana, también tras MOBILE→ARC. Esto explica un cambio de foco de búsqueda; no prueba la causa de todos los clics que hacen desaparecer la ventana.
- **Arrastrar ventana:** el toolbar oculto retenía exclusiones sobre casi todo el caption. Se liberan cuando ARC lo suprime y se restauran en MOBILE. No se alteran los botones o decoraciones del sistema. Arrastre real corregido pendiente de validación DeX.
- **Clic en sidebar/minimización:** proceso principal continuó vivo en los muestreos; las capturas posteriores muestran otras ventanas en primer plano. No se consiguió distinguir de forma concluyente minimización, ocultación por otra actividad y cambio de foco. Sigue BLOCKED el diagnóstico causal.

Ventanas cortas mantienen la lista nativa flexible; la cabecera usa scroll y el presupuesto centralizado. Ceden elementos secundarios antes de consumir toda la lista. El footer sigue anclado; si no cabe, el menú nativo permanece accesible en la cabecera. RTL/LTR y fullscreen conservan el contrato previo. No se añadieron polling ni callbacks por frame.

## Scope actualizado

El usuario pidió no diagnosticar LinkedIn. No se realizan más investigaciones ni cambios por ese error; deja de condicionar el commit o el run.

## Regresiones encontradas y corregidas

1. **NPE potencial nuevo al cargar bookmarks:** el constructor del puente publica una respuesta síncrona incluso con modelo no cargado. La vista se adjunta al header antes del puente, para que el callback tenga LayoutParams reales. Regresión RED→GREEN con el orden de fuente y parámetros inicialmente nulos.
2. **Favicon tardío tras cambiar modelo:** callbacks comprueban tanto identidad de sesión como modelo actual; no pintan una vista anterior ni solicitan iconos del perfil regular para incógnito.
3. **MOBILE al inicio, búsqueda ARC después:** inicialización perezosa del overlay emparejada con la ruta del botón; evita una acción sin efecto por coordinator nulo.
4. **Paleta incógnito dedicada al volver a MOBILE:** se restauran los valores originales antes de la salida temprana del binder nativo.
5. **Verificación antigua de superficie plana:** el test previo exigía una llamada literal a `surface(...)`. Conserva su nombre y ahora ejecuta la propagación real de paleta regular→privada→regular; se comprueba el comportamiento al sustituir la superficie por el gradiente.

## Pruebas y aceptación

**Verificación final host: PASS.** `check-archium-repository.sh`: **257/257**, sin skips, `ARCHIUM_REPOSITORY_PREFLIGHT=PASS`, 167.583 s. `check-arc-preparation.py`: **101 archivos** aplicados con hashes coincidentes; política/geometry y adaptadores Android SDK 37 PASS. Ambas ejecuciones finales retornaron 0 después de integrar los callbacks de navegación definitivos.

Se mantienen las regresiones originales de R2; 137/137 fue el punto de partida histórico, 197/197 era el workspace anterior y se añadieron 60 verificaciones. El total 257 incluye las 12 pruebas del monitor que ya estaban sin commit; no implica que ese trabajo previo se haya incorporado al scope de producción de esta ronda.

Resultados aislados nuevos: resize de contenido **12/12**, URL compacta **6/6**, apariencia **6/6**, caption/input **7/7**, bookmarks **6/6**, ancho **9/9**, superficies de navegación/lifetime **8/8**, estado de navegación **6/6**. Las verificaciones de referencia coinciden por redondeo entero; no se ampliaron tolerancias para ocultar diferencias.

La primera integración completa detectó el test textual de superficie plana y una ejecución iniciada antes de terminar el nuevo fixture de NavigationHandle. Ambos se investigaron y la suite completa se volvió a ejecutar desde un proceso nuevo sobre los archivos finales; no se eliminaron ni saltaron pruebas. `git diff --check` también PASS.

SHA-256 de `patches/archium-desktop.patch`: `a47aabeea43b2fbbb9a2b06850e0490b68c45860873ee7b19beb1bcbc3cb68c5`. Revisión independiente de fuentes: sin Critical/Important pendientes tras reparar el montaje de bookmarks y revisar navegación. Compilación Chromium/NullAway completa pendiente.

Comandos obligatorios, con Python 3.12 y JDK 17:

```sh
ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar
ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh
```

| ID | Resultado integral | Evidencia y límite |
|---|---|---|
| UI-01 | PARTIAL | Ratio y acción explícita 206→393 PASS host; medición final del APK en DeX pendiente. |
| UI-02 | PARTIAL | Acciones/capacidades/Reload–Stop PASS en clase real con límites simulados; input DeX nuevo pendiente. |
| UI-03 | PARTIAL | Origen/edición/copia y geometría/dropdown PASS host; foco durante resize real pendiente. |
| UI-04 | PARTIAL | Gradiente, contraste, cache y restauración PASS host; screenshot nuevo pendiente. |
| UI-05 | PARTIAL | Radio/texto/selección en binder real PASS host; render Android pendiente. |
| UI-06 | PARTIAL | Hover y multiselección nativos PASS host; mouse DeX nuevo pendiente. |
| UI-07 | PARTIAL | BookmarkModel/commands/lifetime/grid PASS host; JNI y mosaicos reales pendientes. |
| UI-08 | PARTIAL | Spaces/carpetas/persistencia y controles previos conservados; interacción visual nueva pendiente. |
| UI-09 | PARTIAL | 14sp/48dp y escalado comprobados en límites host; lectura en pantalla pendiente. |
| UI-10 | PARTIAL | New Tab nativo compacto, hover, hit y footer/budget PASS host; disposición real pendiente. |
| UI-11 | PARTIAL | Recorte/input/surface swap y reservas PASS host; franja real y vídeo pendientes. |
| UI-12 | PARTIAL | Resize continuo y commit SideUi PASS host; frame timing/maximización DeX pendiente. |
| UI-13 | PARTIAL | Sin cambios a decoraciones OS; liberación/restauración de caption probada; arrastre real pendiente. |
| UI-14 | PARTIAL | Persistencia/identidad y perfiles PASS host con límites nativos simulados; reinicio real pendiente. |
| UI-15 | PARTIAL | Navegación y teardown PASS host; atajos Ctrl+L/T/W y Alt+Left/Right reales pendientes. |

Los PASS host anteriores no se elevan a PASS de aceptación integral. La ausencia de leaks de Activity y el rendimiento de animación no se acreditan con probes de objetos simulados.

La revisión independiente encontró el NPE de bookmarks y confirmó después su reparación. Su revisión final no encontró Critical/Important adicionales de fuente; la suite completa posterior confirmó PASS host. No equivale a la validación visual de los cambios en el dispositivo.

La instrucción posterior del usuario autoriza commit/push, lanzamiento del run, monitor e instalación de su APK final; sustituye la restricción de publicación anterior. No autoriza merge. Tras activar monitor e instalador, el agente se pondrá en pausa. El worker exige commit/run, checksum, firma, paquete y comparación del SHA-256 de base.apk instalada, y reintenta desconexiones sin convertirlas en éxito. El monitor muestra CONFIRMADA solo tras esa verificación, con intervalo de 600 s.

Evidencia privada: `.sync-audit/arc-next-polish-20261009/03-archium-restored.png`, `04-collapsed-settled.png`, dumps de activity/window y logs de checks. Capturas 01/02 y UIAutomator del display móvil no se presentan como evidencia de Chrome DeX. No existe screenshot posterior de este código.

## Cierre de publicación autorizado

Último delta: acción de ancho automático y pruebas10/10; monitor/instalador16/16 con reconexión, timeout y hash instalado. **Checks de publicación finales: 262/262 PASS, sin skips, 173.801 s; preparación101archivos/SDK37 PASS; ambos exit0.** Resultados en repository-publish.log y preparation-publish.log de la evidencia privada. Bashsyntax del nuevo launcher independiente Termux PASS. La integración ya se probó en el contenedor nativo independiente: GitHub y verificación hash de la APK instalada anterior operativos; el nuevo run usará su propio commit/artefacto. El run usará el checkpoint archium-checkpoint-37807259506-1, producer33db26aa6fad2e8a9ac9ccf26774605edb9db771, previamente verificado.
