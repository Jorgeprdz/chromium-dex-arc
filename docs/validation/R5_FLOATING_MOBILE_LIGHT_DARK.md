# Archium R5 — Floating Mobile y auditoría Light/Dark

Fecha: 2026-10-22. Rama: `assistant/archium-r5-desktop-native-mobile`.
Base: `92c24dfff85ccb79d2fc5eeffbf4b9111c53988a`, APK del run39781720300 instalada y verificada previamente. Este documento describe un candidato posterior, todavía sin APK.

## Referencias inspeccionadas

- `/sdcard/Pictures/file_00000000fc7c81f999925f0eac1f5289.png` — SHA256 `785afbd0c4102e245b558638d9e90f5383bfbded4c4c1bf3531ae7ec513ce2ec`; secundaria: cápsulas translúcidas.
- `/sdcard/Pictures/file_000000002478820da1ff28ba0d091877.png` — SHA256 `a51144c1a33074017787165677a6608ff97101425b359558f52ffe40ed0e5d67`; principal: blanco y ambas cápsulas.

Copias y logs: `/workspace/archium-evidence/mobile-floating-approved/`. La segunda imagen es la referencia principal de fondo blanco y ambas cápsulas. La primera muestra la variante translúcida. Los PNG fueron abiertos visualmente antes de implementar. El hallazgo inicial de Download correspondía a otro logotipo y no se usó como referencia.

La instrucción posterior del usuario manda: **conservar ancho y altura actuales de la omnibar**. Se conserva también su layout, editor, controles de seguridad y navegación nativos. La nueva separación de gestos del diseño Floating sustituye la aprobación anterior de superposición de las etiquetas.

## Implementación acotada

- `ArcPhoneNavigation`: misma vista/delegate en el slot inferior Chromium. Cápsula con margen lateral18dp, altura56dp y reserva nativa76dp (10dp arriba y abajo, más los insets que gestiona Chromium), radio pill, superficie alfa249/255 y elevación Android6dp. Cuatro acciones existentes, contador real y selección azul; tonalidad accesible en oscuro. Sin blur ni capturas nuevas.
- `ToolbarPhone`: nueva opción de superficie habilitada sólo desde el modo teléfono. Fondo blanco en claro o202124 en oscuro; superficie de omnibar ligeramente translúcida, radio pill y elevación3dp. No se cambian XML, LayoutParams, padding, fuentes, anchos ni alturas de la omnibar. En foco y NTP se conservan los caminos de presentación/animación nativos.
- `ToolbarThemeColorProvider`: opción desactivada por defecto; coordina superficie con tintes nativos APP_DEFAULT/INCOGNITO. Conserva atenuación por foco de Activity y restablece el proveedor original al salir. El camino sin opción mantiene la lógica nativa.
- `StatusBarColorController`: transparencia mediante el helper edge-to-edge existente y contraste de iconos según la superficie real elegida. Excepciones de foco, NTP, indicadores, scrims y overrides siguen con Chromium. No se alteran flags de cutout, fullscreen ni el reparto de WindowInsets.
- `EdgeToEdgeSystemBarColorHelper`: override de contraste opcional, desactivado por defecto. Conserva el color de respaldo de iconos al actualizar insets/delegate; no cambia el color dibujado, la navegación ni el reparto de insets. Se limpia al volver a foco/NTP/overlays o salir del estilo teléfono.
- `ToolbarManager`: activa el estilo sólo para ToolbarPhone, usa la misma reserva inferior en delegate y coordinador, actualiza selección por URL y retira estilo al cambiar de modo/configuración. Observer de UI_MODE eliminado al destruir. Al salir de teléfono se cierra el menú y se libera la visibilidad/reserva de controles mediante el owner nativo.
- `ChromeTabbedActivity`: sólo añade consulta de NTP/homepage para la selección Inicio. No modifica navegación ni WebContents.

Reutilizados: LocationBar/ToolbarPhone, BottomControlsCoordinator, BottomBarHostManager/Hub, BottomSheetController y las acciones Chromium ya conectadas. No hay nuevo editor, segunda barra, sistema de pestañas, NTP, preferencia de tema o dependencia. Los cuatro originales nativos nuevos se guardan en `.source-reference`; patch/manifest contienen166 archivos.

## Auditoría: defectos demostrados y corregidos

El ensayo RED `theme-audit-red-v2.log` ejecutó56 pruebas y falló10 ejecuciones (cinco defectos, SDK30/36); no se trata de un fallo físico registrado en el dispositivo.

1. Tint de incógnito podía llegar después del color primario, dejando el fondo blanco. Ahora el cambio de tint sincroniza la superficie. Un refresco de configuración también recalcula paleta si el contexto DayNight cambió aunque el sitio no cambie su color.
2. Sheet abierto retenía textos, iconos y superficies de la paleta anterior. Se recolorean las mismas vistas sin recrear contenido ni perder scroll/foco; se notifica `onSheetBackgroundColorOverrideChanged()` al owner nativo. Se preserva favicon real y estado del switch.
3. Antes de enlazar Host se usaba blanco. Ahora el estado inicial resuelve `android:colorBackground` y usa uiMode nocturno como fallback. No se afirma que se haya observado/corregido un flash físico.
4. Zoom deshabilitado conservaba apariencia activa. Se aplica la misma atenuación0.4 de los otros controles deshabilitados, sin cambiar acciones ni geometría.
5. El ripple anterior podía reducir el contraste del texto azul a4.12:1. Se mantiene el mismo azul y se reduce sólo la opacidad máxima del ripple, alcanzando al menos4.60:1 en el cálculo de color declarado. Los textos habilitados se verifican contra4.5:1 y los iconos contra3:1, según [WCAG1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) y [WCAG1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). Controles inactivos están excluidos de esos umbrales; se revisa su diferenciación visual por separado.

6. El helper edge-to-edge recalculaba iconos usando TRANSPARENT tras una actualización de insets/delegate, perdiendo el contraste aplicado por el controlador. `status-owner-red.log` reproduce el fallo (blanco esperado, transparente recibido). El helper ahora conserva un override de contraste y lo elimina al devolver el control a Chromium; `status-owner-green.log` comprueba ambos temas, refresh por insets/delegate, prioridad de iconos forzados nativos y restablecimiento del camino original.

Los colores blancos/azules fijos restantes pertenecen a roles condicionados por tema. La rama oscura usa fondos oscuros, texto claro y azul claro; no fuerza blanco como fondo. Sombra e iconografía mantienen geometría. No se introducen recursos values-night propios: se consume el Context DayNight y los helpers de tema Chromium existentes.

## Validación local y límites

- Robolectric:56 PASS en SDK30/36. Vistas Android reales y clase entregada ToolbarThemeColorProvider; interfaces Chromium, proveedor activo y resolución de colores/recursos están simulados explícitamente. Shadows de recursos, sin mockStatic dependiente de Mockito inline. No es aceptación gráfica Chromium/dispositivo.
- Cobertura: cuatro acciones, contador, sheet sin editor, acciones/stale callbacks, Host/Hub/cleanup, áreas táctiles>=48dp, anchos240/320/800dp, márgenes/sombra/radio, paletas claro/oscuro/incógnito, cambios de paleta con sheet abierto, scroll conservado, llamada al owner de background, misma geometría al cambiar tema, estado inicial oscuro, controles deshabilitados y contraste de colores declarados normal/presionado.
- Owner de status bar:1 PASS; compila la clase entregada completa con fronteras OS/suppliers simuladas y comprueba contraste persistente. No prueba iconos físicos ni comportamiento real de WindowInsets.
- Contratos de superficie nativa:3 PASS. Ownership/compilación de campos TYPE_USE:5 PASS. Legacy Mobile retirado:5 PASS. Split5 PASS (sólo contratos/validador). Gates2 PASS; aplicación7 PASS y transición17 PASS. No se repite la suite host completa en esta tanda.
- Parche:166 archivos; regeneración repetida idéntica, SHA256 `e92ff6e522c1096635073dc877e435576f352f5952af0374092c0dd62c1e0046`; aplicación7 y transición17 PASS tras añadir el helper.
- Preparación SDK37.2: compilación aislada de adapters y aplicación/hash/XML del parche. La clase de paleta se compila en el runner Robolectric. ToolbarPhone/StatusBarColorController completos y la integración del helper aún requieren compilación integrada contra Chromium; no se atribuye ese resultado al SDK aislado.
- Desktop: sus coordinadores, sidebar, Spaces, Split View, compositor y política WebContents no tienen diff respecto92c24df. La comparación de los hashes del manifest confirma exactamente siete clases de producción y un test entregado distintos de la base; el resto conserva sus bytes (`scope-and-reproducibility.json`). Se comprueba también que los paths de Tablet y LocationBarLayout no se modificaron. Defaults/opción desactivada y retorno de la paleta nativa tienen prueba local. Aceptación Desktop/DeX física: PENDIENTE.

## Matriz de aceptación real solicitada

Todos los resultados visuales de la APK nueva siguen pendientes: no existe una APK de este candidato. Los PASS locales anteriores no cierran esta matriz.

| Componente | Claro | Oscuro |
| --- | --- | --- |
| Status bar | PENDIENTE APK | PENDIENTE APK |
| Omnibar | PENDIENTE APK | PENDIENTE APK |
| Floating Pill inferior | PENDIENTE APK | PENDIENTE APK |
| Menús y bottom sheets | PENDIENTE APK | PENDIENTE APK |
| Selector de pestañas | PENDIENTE APK | PENDIENTE APK |
| Cambios dinámicos | PENDIENTE APK | PENDIENTE APK |

Pendiente en dispositivo: transparencia/sombra/cutouts y contraste reales, ausencia de franjas, iconos de status/navigation bars OEM, gesto inferior y teclado, foco/edición/sugerencias/Enter/Back, Native More/AppMenu, permisos/diálogos/popups, Hub/previews y retorno de cápsula, fullscreen/media, claro→oscuro→claro con pestañas/menú/IME, seguir sistema, reinicio con tema persistido, adaptación de tablet/ventana y Desktop↔Phone. No se simulan esas pruebas para declararlas PASS.

## Fidelidad y continuación

La comprobación local compara formas, paleta y medidas del render con las propiedades Android entregadas; no existe todavía comparación de píxeles de la APK nueva. Se conserva el tamaño actual de omnibar por petición expresa, aunque difiera en píxeles del PNG. Se usan transparencias estables y elevaciones nativas en lugar del efecto de cristal/blur del render. El contenido de Google y otras webs no se estiliza; no se reproducen sus sombras/gradientes dibujados en la referencia. NTP, editor enfocado, sugerencias, Hub y diálogos mantienen comportamiento nativo.

Estado: **IMPLEMENTADO LOCALMENTE; VALIDACIÓN INTEGRADA/FÍSICA PENDIENTE. No se declara READY FOR BUILD ni coincidencia visual completa.** No se lanzó Actions, no se generó una APK y no se crearon checkpoints pesados en esta tanda. Conservar el run39781720300 y su APK como respaldo. Continuar desde el commit de este documento: primero compilar targets afectados/validar UI cuando el usuario autorice el siguiente paso; no disparar automáticamente un build completo ni reintentar workflows.
