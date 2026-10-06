# Anexo aprobado por instrucción del usuario — Desktop Policy + Keyboard/Mouse

Este anexo extiende `2026-10-06-archium-local-arc-design.md`. Mantiene contraseñas locales, importación/exportación CSV, navegador nativo y diseño Arc for Mac ya aprobados. El usuario entregó el alcance, reglas y validaciones y pidió integrarlo; no introduce otra propuesta de diseño visual.

## Adaptive Desktop Policy

La ventana actual es la autoridad. Compacta <600 dp: UI y sitios mobile salvo elección explícita. Tablet 600–839 dp: Archium tablet y desktop site automático. Desktop >=840 dp: Archium desktop y desktop site automático. Tablet y Desktop pueden compartir la UI Arc ahora, pero conservar clases distintas para ampliarla después. Reutilizar el umbral tablet de Chromium. Elegibilidad independiente de fabricante, DeX, orientación, panel físico, densidad como criterio o servicios propietarios.

Configuration/WindowMetrics deben representar el Activity/display actual. Recalcular en resize, split screen, maximizar/restaurar, freeform, rotación y cambio de display; preferir actualización dinámica sin recreation. Donde la construcción upstream de la UI exija recreation, usar save/restore nativo y verificar conservación de tabs, seleccionado, historial, navegación, incógnito, scroll y formularios cuando sea posible.

RDS se integra en los caminos actuales de carga/restauración/navegación de Chromium. Las preferencias persistentes por sitio tienen prioridad; no escribir preferencias por cada cambio de tamaño. Desktop UA debe provenir de Chromium y su versión real. Al volver a compacta, mobile salvo elección persistente explícita. Preparar adaptive enabled/always desktop como opciones futuras de Settings > Desktop, sin obligar a otra pantalla ahora.

Zoom: usar HostZoomMap/ChromeZoomLevelPrefs y PageZoom, con precedencia host -> global usuario ->100%. Exponer/reutilizar control real; admitir 80/90/100/110/125/150 y preservar en reload y reapertura. Preparar remember-per-site sin sustituir almacenamiento native. Desactivar inflación de texto móvil solo cuando elegible y renderizando desktop, conservando comportamiento/accessibilidad mobile.

## Keyboard

Reutilizar los comandos actuales, disponibles con teclado/mouse aunque la ventana sea compacta. Atajos: Ctrl+L (enfoca/selecciona omnibox), T, W, Shift+T, Tab, Shift+Tab, 1–8, 9, D, H, J, Shift+N; Alt+Left/Right; F5/Ctrl+R; Ctrl+Shift+R si ruta nativa; Ctrl+Shift+B muestra/oculta sidebar Arc donde disponible. Mantener acciones de bookmarks, extensiones, restauración y modelo incognito. F11 solo si hay soporte real estable; el código fijado lo marca no implementado, por lo que la entrega puede documentar esa limitación.

## Mouse

Middle link -> tab background, Ctrl+click -> nueva tab, Shift+click -> ruta real new window cuando soportada. Si el window manager no la permite, documentar sin ventana simulada. Middle tab -> cierre mediante modelo/controlador real si interceptar rail es seguro. Wheel normal conserva comportamiento web. Ctrl+wheel reutiliza zoom nativo si funcional. Back/Forward siguen despacho nativo posterior al renderer y no deben romper consumidores web.

Ninguna función de producción requiere root/Shizuku/ADB. No WebView, scraping, JavaScript/CSS zoom, eventos web artificiales ni cambios innecesarios al diseño Arc aprobado.

## Validación y entrega

Probar matriz 580/600/620/839/840/900 dp, tablet split 520 y expansión700, phone en landscape <600, tablet, DeX, display externo y freeform. Recalcular al cambiar de display, no perder tabs; zoom persiste al reload/reopen. Verificar los shortcuts mínimos solicitados, mouse/modificadores, side buttons y Ctrl+wheel, registrando cualquier captura por Android antes del app.

Changelog final: Adaptive Desktop Policy; Tablet Mode; Desktop Mode; Keyboard; Mouse; Existing Chromium functionality reused; Known limitations. Entregar lista de archivos, pruebas, APK conservada y resultado real de compilación. No declarar success antes de compilación terminada.

## Instrucción de pausa

Después de lanzar el run de compilación final, actualizar monitores con su ID, verificar consulta y pausar. La pausa no equivale a build terminado ni entrega verificada. No instalar ni continuar E2E automáticamente hasta que el usuario reanude.
