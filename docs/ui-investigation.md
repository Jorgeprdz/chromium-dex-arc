# Integración UI comprobada en Chromium 1710899

Revisión: cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.

La base ya incluye pestañas verticales nativas de Android. Conviene extender esa
implementación y sus modelos, antes que recrear la lista desde cero.

Archivos comprobados:

- chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java: crea VerticalTabsSideUiCoordinator, alterna la tira horizontal, ajusta márgenes del compositor y destruye observadores junto al lifecycle.
- chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java: ancho expandido 240 dp, colapsado 76 dp, máximo manual 500 dp y límite proporcional de 0.33 del ancho de ventana. Incluye preferencia de habilitación, redimensionamiento y hover.
- chrome/android/java/src/org/chromium/chrome/browser/app/ChromeActivity.java: integra ExtensionWindowControllerBridge y su fábrica en el perfil y ventana actuales.

Para el diseño aprobado, el ancho expandido coincide. El colapsado debe pasar a
52 dp después de revisar los layouts y áreas de interacción; cambiar la constante
sola no garantiza un render correcto. La elegibilidad actual requiere la feature
AndroidVerticalTabs y el form factor tablet calculado en el contexto de ventana.
Hay que probar esa elegibilidad en DeX; no asumir que is_desktop_android elimina
todas las condiciones.

Pendientes antes de parchear UI: revisar recursos de la rail, acceso a favoritos
y omnibox, separación móvil/escritorio y recorte real del compositor. Conservar
los mecanismos nativos de estado, foco, cierre, reordenación y separación incógnito.
No se ha aplicado ningún parche visual todavía.

Fuente primaria: https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/
