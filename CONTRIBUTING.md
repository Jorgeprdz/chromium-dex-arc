# Contribuir a Archium

Gracias por ayudar a mejorar la experiencia de Android de escritorio. Puedes aportar pruebas en dispositivo, documentación, traducciones o cambios de código.

[← Portada](README.md) · [Guía del repositorio](docs/PROJECT_GUIDE.md) · [Problemas conocidos](README.md#known-bugs--problemas-conocidos)

## Antes de empezar

Consulta los bugs y pendientes de la portada. Para un cambio grande, abre primero un issue con el problema, el comportamiento esperado y un alcance pequeño. La preview actual está basada en el build 38322756782; la rama con fuentes y herramientas es `assistant/archium-r4-recovery`.

## Reportar un bug

Incluye versión de Archium, modelo, Android, modo de escritorio, pasos reproducibles y resultado esperado frente al observado. Una captura o log sin cuentas, conversaciones, tokens ni otros datos personales ayuda a comprobarlo. Indica si sucede con la sidebar abierta o colapsada.

## Proponer código

1. Trabaja desde la [rama de código actual](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery).
2. Mantén el diff centrado en una causa reproducible y añade una regresión apropiada cuando corresponda.
3. Si modificas fuentes del overlay o `.source-modified`, regenera el patch con `scripts/generate-arc-patch.py` y comprueba que sea reproducible.
4. Explica qué probaste, sus exit codes y qué quedó pendiente. Los mocks y tests host no acreditan ejecución nativa ni aceptación en dispositivo.
5. Envía el PR hacia `assistant/archium-r4-recovery`. No hagas cambios ni merges sobre `feat/arc-desktop`, que es el respaldo protegido.

Los builds de Chromium consumen recursos considerables. Coordina con el mantenedor el dispatch fijado a un SHA y el checkpoint compatible. Preserva los outputs y caches válidos; no conviertas una restauración fallida en un build limpio ni desactives gates para obtener PASS.

## Documentación y pruebas físicas

También son útiles guías de instalación, revisión de textos, traducciones y pruebas sobre DeX u otros entornos Android Desktop. Usa capturas reales, identifica el APK probado y distingue un resultado observado de una hipótesis. El contenido de ejemplo debe permitir compartir la imagen sin exponer datos privados.

## Prioridades actuales

Geometría inferior, iconos compactos, aceptación de la omnibox y cambios de foco, compatibilidad en dispositivos reales y mediciones del Desktop Engine R1. La función propia de contraseñas sigue deprecated; esta preview no la reactiva.
