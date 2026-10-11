# Archium R4: recuperación y reescritura

Base elegida y autorizada: 51e5ed429661727156ab2534caac99a82ee9264b.
Implementación exclusiva: assistant/archium-r4-recovery. Chromium pin:
cfd94726b7b5fb48aedcc32662f2f3fbdbadec35. main y feat/arc-desktop intactos.

La petición es rehacer los cambios Archium posteriores al respaldo, conservando
las funciones de la base. No es una reconstrucción limpia de Chromium ni un
merge/cherry-pick masivo desde la rama fallida. Los archivos de identidad Portal
aprobados son inputs inmutables; las herramientas de checkpoint/transición y
verificación que ya tienen pruebas reales se pueden reutilizar individualmente,
registrando su procedencia. Las pruebas existentes son oráculos, no evidencia
anticipada de que la nueva implementación pase.

Conservar: sidebar redimensionable, geometría y viewport/esquinas, translucidez,
pestaña activa en cápsula, nueva pestaña nativa en sidebar, favoritos/espacios,
omnibox funcional, navegación, foco/hover/accesibilidad, colores con 8 presets,
RGB/HEX, previsualización/apply/cancel/reset y preferencias persistentes,
Android Desktop y DeX. Blur/vibrancy real y dispositivo siguen UNVERIFIED;
no agregar nuevas funciones ni prometer soporte no probado.

Reescribir el orquestador con fases aisladas y errores fatales. SOLO dispatch
manual fijado a SHA, checkpoint explícito, mismo checkout/output, ARM64, dos
slices de hasta 75 minutos y reserva para checkpoint/upload. No clean fallback,
no flags que ignoren warnings/símbolos, no tests omitidos como PASS. Entorno JVM
con assertions exclusivamente en los runners, nunca en javac/D8/Ninja. Verificar
recursos fusionados y enlaces JNI antes del fanout y APK. Guardar checkpoint
quiescente cuando sea seguro conservando el primer exit code fallido.

No lanzar otra corrida pesada automáticamente después de 38165289963 FAILED.
Publicar código probado y estado exacto; una nueva corrida requiere autorización
posterior a la revisión de esta recuperación. Monitor: refresco 600 s, log final
sin caché parcial, tres líneas de primer error real, solo instalar APK verificada
si el run entero es SUCCESS. La APK histórica no reemplaza la entrega R4.
