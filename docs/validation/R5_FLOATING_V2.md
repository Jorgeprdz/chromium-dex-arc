# Floating V2 — candidato de implementación, 22-oct-2026 CDMX

Rama: `assistant/archium-r5-desktop-native-mobile`. Base: `c2e3773a604204676e4cec2296b650481e5b9632`, Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0). Este documento sustituye la dirección visual anterior: el usuario aprobó los dos renders V2 con contenido detrás de ambas cápsulas. No se considera aceptada una APK del candidato.

Referencias inspeccionadas: `Archium_Floating_V2_01_Instagram.png` y `Archium_Floating_V2_02_LinkedIn.png`, también entregadas en Download del teléfono. Copia y evidencia local: `/workspace/archium-evidence/floating-glass-over-content-v2/`. No se modifica el contenido de Instagram, LinkedIn ni otras webs.

## Cambios y componentes reutilizados

- `BrowserControlsManager`: opt-in de reserva/offsets cero para contenido web durante navegación Mobile. Mantiene los campos nativos de altura y restaura la política nativa al desactivarse. `CompositorViewHolder` actualiza tamaño y viewport mediante su flujo existente. No cambia Blink, GPU, UA, escalas, proporciones ni algoritmos de Split View.
- `ToolbarPhone`: fondo de cristal dentro de la cápsula existente, tanto en dibujo legacy como en la ruta refactorizada. **No cambia ancho, alto, padding, editor, acciones de seguridad ni hit targets de la omnibar.** Reutiliza elevación y foco existentes.
- `ArcPhoneNavigation`: misma cápsula y mismo slot nativo inferior, con cuatro acciones, contador y bottom sheet existentes. Fondo del slot/delegate transparente sólo cuando se activa el cristal; contraste de etiquetas neutras en ambos temas. No se agrega una segunda barra ni otra omnibar.
- `ArcPhoneGlass`: captura con PixelCopy sólo las regiones de las cápsulas del SurfaceView del compositor, reducidas a un máximo de 256×128 por imagen; una copia en vuelo, doble buffer por región. Blur de píxeles en un HandlerThread; controles/texto nativos permanecen nítidos. No captura la ventana ni persiste imágenes. El Drawable recorta la imagen desenfocada y aplica tinte translúcido claro/oscuro.
- `ToolbarManager`: activa sólo en teléfono y página web interactiva; vuelve a fondos/geometría nativos con editor, NTP, Hub o fullscreen. Restaura los Drawables originales de los contenedores. Invalida muestras en cambio de pestaña/URL; pausa/destroy detienen el muestreo y liberan buffers/worker; movimiento ajusta la frecuencia. Resultados tardíos o de geometría anterior se descartan.
- Registros GN y filtro de tests existentes ampliados; parche y manifest regenerados. Sin dependencias nuevas. Manifest comparado con la base: ningún archivo Desktop/Spaces/colecciones/Split específico cambia. La integración compartida se mantiene detrás del opt-in móvil.

## Evidencia local

| Verificación | Resultado | Alcance |
|---|---|---|
| Reserva viewport, cuerpos reales de getters compilados | PASS, 2 tests | Alturas/offsets cero, estado nativo preservado y restauración; wiring de integración |
| Navegación + cristal Robolectric SDK30/36 | PASS, 70 ejecuciones | Vistas Android reales; acciones/controller y captura GPU como fronteras explícitas |
| Política original de descubrimiento Chromium | PASS, 35 métodos | TestListComputer/Allowlist fijados e íntegros; sin application shadows |
| Host phone | PASS, 8 tests | Incluye duplicados hairline, dimensiones y guards de tema/política |
| Ownership del slot inferior y anotaciones TYPE_USE | PASS, 5 tests | Misma barra, sin nuevo root overlay; campos entregados compilados |
| Cobertura de gates | PASS, 2 tests | Suites entregadas registradas |
| Owner de contraste status bar | PASS, 1 test | Restauración nativa y actualizaciones de insets/delegate |
| Aplicación / transición del parche | PASS, 7 / 17 tests | Hashes fijados, transición incremental |
| Preparación SDK37.2/JDK21 | PASS | Parche de 169 archivos; adaptadores nuevos compilados con fronteras Chromium stubbed; regresiones sintéticas Desktop/sesión existentes |
| Regeneración de parche/manifest | PASS | Segunda generación idéntica byte a byte |
| Compilación integrada Chromium / APK V2 | NOT RUN | Sin Actions, publicación ni instalación nueva |
| Aceptación gráfica/dispositivo/rendimiento | PENDIENTE | Ninguna captura de la APK anterior valida este candidato |

Evidencia RED: `viewport-red.log`, `integration-red.log`, `glass-red.log`. GREEN: `viewport-green.log`, `glass-final.log`, `phone-host-final.log`, `preparation-final.log`, `patch-application.log`, `patch-transition.log`, `delivery-delta.txt`. Los fallos intermedios del harness gráfico/SQLite se corrigieron como limitaciones del entorno local; no se cuentan como bugs gráficos del producto.

## Diferencias y límites pendientes

El cristal usa muestreo limitado, no blur nativo continuo del compositor: cada región se actualiza aproximadamente a 8 fps durante movimiento y 2 fps en reposo. Falta medir fluidez, memoria y consumo reales. No se promete equivalencia de rendimiento ni coincidencia visual con los renders.

Cuando PixelCopy no dispone de un SurfaceView válido, la región sale de sus límites o la superficie protege su contenido, se conserva el tinte translúcido sin muestra; no se usa captura de ventana ni se eluden protecciones. Esta degradación y la ruta compositor/texturas requieren validación en Galaxy/DeX.

La NTP y edición utilizan sus superficies y geometría nativas deliberadamente; el trabajo pendiente de New Tab previamente aceptado no se reabre. El teclado y las reservas de sistema siguen con sus owners nativos; la barra inferior nativa se oculta ante IME. No se afirma validado ese comportamiento en la APK nueva.

Antes de aceptar visualmente: comprobar contenido detrás y fuera de ambas cápsulas, ausencia de bandejas grises, sombras, status/gesture bars y recortes; páginas claras/oscuras, cambio dinámico de tema, teclado y formularios inferiores, scroll hasta el final, rotación, fullscreen, Hub, incógnito, cambio/restauración de pestañas, y Desktop→Phone→Desktop. Verificar también controles compositados durante scroll y fuente de PixelCopy. La transparencia de status bar reutiliza el owner previo; no se ha demostrado en dispositivo que toda la franja superior muestre web.

**Estado:** implementación guardada con gates locales PASS; aceptación visual e integración nativa PENDIENTES. No declarar DONE ni coincidencia visual. No se lanzó una compilación; se necesita autorización nueva para un único build incremental y posterior validación física.
