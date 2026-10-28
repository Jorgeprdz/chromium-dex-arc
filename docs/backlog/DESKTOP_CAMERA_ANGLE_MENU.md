# Seguimiento opcional: selección directa del giro manual de cámara

Estado: BORRADOR / BAJA PRIORIDAD / SIN IMPLEMENTACIÓN.

## Decisión vigente del usuario

Conservar la versión que ya funciona y evitar regresiones. Este documento es un recordatorio, no una autorización para implementar cambios ni lanzar compilaciones. No cambiar etiquetas, retirar Automático, modificar captura o sustituir el override manual actual.

Referencia instalada: run40602752877, SHA71da56fd2530d9a48813c9f9165c8fd98f501b36.

## Comportamiento existente

- El menú nativo ofrece Automático, Manual, Girar90 y Restablecer automático.
- Girar90 ya recorre 0→90→180→270→0 mediante `(modo + 1) % 4`.
- El usuario confirma que el override manual le resulta suficiente y que el PiP cumple visualmente lo esperado.
- La orientación automática no funciona correctamente en su entorno DeX; se conserva como limitación conocida. No se declara corregida.

## Mejora opcional para revisar más adelante

Ofrecer selección directa de 0°,90°,180° y270°, con indicador del ángulo activo, reutilizando ArcCameraControls y el estado por WebContents existentes. No hace falta añadir nuevas capacidades de rotación: sería únicamente una mejora de acceso al control existente.

La propuesta de renombrar Automático a Original se discutió, pero queda SIN APROBAR PARA IMPLEMENTACIÓN. No es requisito de este seguimiento. Una futura investigación de orientación automática sería un trabajo separado, basado en evidencia; no bloquea el uso manual actual.

## Condiciones antes de retomar

- [ ] Confirmar con el usuario que desea retomar esta mejora opcional.
- [ ] Conservar exactamente el pipeline nativo y la composición de giro manual actuales.
- [ ] Mantener el aislamiento por pestaña y el manejo de pestañas cerradas.
- [ ] Comprobar selección directa, estado marcado y restablecimiento, sin reiniciar la cámara.
- [ ] Verificar cámara/micrófono/pantalla simultáneos y PiP en DeX; distinguir vista local de recepción remota.
- [ ] Preservar Desktop/Mobile, geometría, viewport normal, permisos y datos.
- [ ] Integrar en un futuro build autorizado junto con cambios pertinentes; no compilar sólo por este recordatorio.

Archivos orientativos: `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCameraControls.java` y `chromium/chrome/android/java/res/values/arc_strings.xml`.

Este PR sólo agrega documentación. No hay código de la mejora ni pruebas físicas de una implementación nueva.
