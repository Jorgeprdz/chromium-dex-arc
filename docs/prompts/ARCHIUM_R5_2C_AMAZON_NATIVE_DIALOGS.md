# ARCHIUM R5.2C — Amazon y diálogos: continuación recomendada

Ejecutar en el worktree forense existente. Conservar los commits 5184755 y
f0c696c y la corrección de identidad de pestañas de 3db367a. No modificar main,
feat/arc-desktop, la rama activa ni el supervisor.

1. Confirmar por hash el APK realmente instalado y compararlo con el run
   39296066030. Distinguir actualización manual observada de instalación automática.
2. Diálogos: mantener el fix del presenter 5184755 y sus trazas optativas. La APK
   de 3db367a no lo contiene. No repetir los doce mosaicos en esa APK esperando
   un resultado distinto. Mantener DEVICE_ACCEPTANCE_PENDING.
3. Amazon: separar descarga/red/decodificación de raster/composición. Reutilizar
   la fixture local R5.2 y probar imágenes controladas, scroll y fases A/B en el
   backend real. Comparar captura de superficie web y captura física del display
   correcto, con DOM/decodificación y logs correlacionados. No interactuar con
   compras, formularios o ajustes de cuenta. El usuario autorizó después abrir
   directamente Amazon: se permite observar su homepage, recarga normal y scroll;
   no se automatizan otras acciones de cuenta. Conservar capturas sólo privadas.
4. Identificar la primera discrepancia demostrable. Sólo entonces escribir RED,
   corrección mínima y GREEN. No cambiar flags ANGLE/Graphite ni desactivar GPU
   como sustituto del diagnóstico. Si no hay reproducción causal, conservar la
   evidencia y el punto de bloqueo; no inventar un fix de Amazon.
5. Comprobar patch/manifest, compatibilidad estructural con el pin y cambios
   anteriores. Registrar pruebas reales y las pendientes de Galaxy/QEMU.
6. Preparar integración incremental revisable y un informe R5.2C. No construir,
   instalar, despachar Actions, alterar args/toolchain ni reiniciar el supervisor
   en esta investigación. Cualquier próximo build requiere autorización separada
   sobre el cambio concreto y checkpoint válido, sin fallback limpio.

Entregas: este prompt ejecutable, docs/validation/R5_2C_AMAZON_NATIVE_DIALOGS.md,
evidencias depuradas y SHA de la continuación local. Conservar originales privados,
no publicar datos de navegación y finalizar sin esperar trabajos de GitHub.

Recomendación tras ejecución: conservar el fix de diálogos 5184755 para la próxima
integración autorizada; incorporar la corrección demostrada del path de Perfetto.
Amazon sigue FAIL reproducido y sin fix causal demostrado. No cambiar Graphite
por tanteo: completar correlación de trazas/frames/layers antes de un parche GPU.
