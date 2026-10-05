# Chromium DeX Arc: interfaz, cuentas y autocompletado

Estado: propuesta ampliada para revisión. El diseño visual de `docs/design.md`
ya está aprobado; esta propuesta incorpora el pedido del 2026-10-05 de login con
Google, autocompletado y complementos de Google. No representa funciones implementadas.

## Objetivo

Un navegador de uso diario en DeX con distribución tipo Arc, pestañas y favoritos
reales, extensiones conservadas y acceso a servicios de Google. El usuario
condicionó usarlo como predeterminado a disponer de sus contraseñas de Google.
La integración de contraseñas es un criterio de aceptación, no una función
que se pueda sustituir por un simple botón a passwords.google.com.

## Base y preparación mientras corre el baseline

Revisión: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, snapshot AndroidDesktop_arm64
1710899, versión instalada 157.0.8086.0. El repositorio contiene scripts y
documentación, no el checkout completo de Chromium.

Preparar parches contra archivos de esa revisión descargados individualmente,
conservando originales para comprobar contextos y generar diffs reproducibles.
No descargar todo Chromium al teléfono. El run baseline permanece independiente;
los cambios preparados aquí no se incorporan a un run ya iniciado.
Un parche que aplica correctamente todavía necesita compilación y pruebas.

## Interfaz Arc

Referencia visual inspeccionada el 2026-10-05:
`docs/references/arc-windows-reference.jpg`, copiada de
`/sdcard/Download/The-Arc-Browser-in-Windows.jpg` (2026-10-04 19:41), la imagen
más reciente en Download del teléfono. Referencia: ventana exterior de Arc
para Windows, no el navegador coral mostrado dentro del contenido de la web.

El usuario precisa que este diseño se aplica solo al modo escritorio/DeX.
En la pantalla del teléfono se mantiene la interfaz tradicional, incluso en
horizontal o con ancho suficiente. La elegibilidad no puede depender solo
del ancho ni de `is_desktop_android`, que es una condición de compilación.
Usar el contexto de la ventana/display para identificar escritorio; verificar
la API exacta antes de implementar. Dentro de escritorio, el ancho determina
la contracción del rail. Volver al display del teléfono restaura la UI móvil
sin perder pestañas ni el estado de navegación.

Extender las pestañas verticales nativas, manteniendo TabModel, lifecycle,
incógnito, foco, menús y arrastre de Chromium. Puntos de integración comprobados:
`TabbedRootUiCoordinator`, `VerticalTabsSideUiCoordinator` y `VerticalTabUtils`.

- Barra izquierda expandida de 240 dp y contraída de 52 dp. Revisar los layouts
  y áreas táctiles antes de cambiar el ancho colapsado actual de 76 dp.
- Distribución del marco y rail izquierdo siguiendo la ventana exterior de la
  referencia. El violeta de la captura es un ejemplo, no un color obligatorio.
  El usuario puede elegir el color del marco y rail en ajustes de apariencia;
  guardar la elección y conservarla tras reiniciar. Derivar superficies y colores
  de texto/iconos con contraste legible en claro y oscuro. La elección no cambia
  la distribución ni tiñe el contenido web; el azul brillante de la referencia
  pertenece a la página. Esta personalización aplica a la interfaz de escritorio,
  conservando la interfaz tradicional del teléfono.
- Barra superior compacta con atrás, adelante, recargar, dirección y acceso a
  extensiones. Favoritos como botones compactos con favicon al inicio del rail,
  vinculados al modelo real de marcadores; carpetas/marcadores debajo y pestañas
  abiertas en una sección distinta con selección, creación, cierre y reordenación.
  No interpretar los puntos inferiores de la referencia como workspaces ya
  implementados ni añadir controles decorativos sin función.
- Conservar Ctrl+L y el omnibox nativo. Integrar su acceso en el rail sin recrear
  la lógica de navegación ni dejar controles que solo simulen funcionar.
- Margen de contenido de 8 dp. Esquinas únicamente con recorte real compatible
  con el compositor; nunca cubrir el contenido con máscaras.
- Adaptación al ancho de la ventana de escritorio/DeX; mantener el flujo móvil
  tradicional en la pantalla del teléfono, cualquiera que sea su ancho.
- Acceso a administración, instalación admitida y acciones de extensiones.

## Cuentas y servicios de Google: límites comprobados

Hay tres integraciones diferentes:

1. Login en páginas web: abrir las páginas oficiales en pestañas normales para
   Gmail, Drive, Calendar, Docs y YouTube. Las cookies pertenecen al perfil web.
   No presentar esa sesión como sincronización del navegador.
2. Login del navegador y Chrome Sync: Chromium documenta restricciones para
   emitir los tokens necesarios. Las claves de API no garantizan acceso.
   La excepción documentada para cuentas de prueba tampoco proporciona por sí
   misma el componente Android ausente en esta APK. Su viabilidad se evalúa por
   separado; no se anuncia como terminada por configurar OAuth.
3. Gestor de contraseñas interno Android: el backend downstream no está presente
   en la implementación abierta. `PasswordManagerBackendSupportHelper` devuelve
   false y `IsPasswordManagerAvailable` lo exige. No forzar true: eso no implementa
   guardar, importar ni rellenar contraseñas.

La ruta Agregar cuenta de la APK instalada produce
`NullAccountManagerDelegate does not implement createAddAccountIntent`.
La primera implementación debe evitar ese cierre y explicar la disponibilidad
real, conservando la sesión web como ruta utilizable.

No incluir claves ajenas ni suplantar la identidad o firma de Chrome.
Una configuración de APIs públicas propias solo se añade cuando una función
concreta la necesite y existan credenciales y accesos válidos.

## Autocompletado y contraseñas

Evaluar primero la integración existente del framework Autofill de Android,
documentada en `components/android_autofill/README.md` y controlada por la
preferencia `autofill.using_virtual_view_structure`.

Conservar una selección explícita del usuario del proveedor de autocompletado.
Comprobar con el proveedor Google del teléfono si entrega credenciales en el
paquete propio del fork, y verificar sugerencias, autenticación, selección de
cuenta y rellenado efectivo en un formulario de prueba. La presencia del
framework no prueba compatibilidad con Google Password Manager.

Si el proveedor Google funciona, el usuario puede usar las contraseñas desde
su proveedor sin copiarlas al perfil del fork. Esto no satisface una exigencia
de importación local CSV si el usuario requiere específicamente esa modalidad.
La importación CSV local requiere un almacén de contraseñas funcional: se diseña
como un subsistema separado si la ruta Android no cumple el requisito.

Conservar el autocompletado local disponible de direcciones y formularios.
Tarjetas de Google Pay, passkeys y otros datos de cuenta se evalúan individualmente;
no inferir su funcionamiento a partir del éxito con contraseñas.

## Complementos

Conservar la infraestructura de extensiones Android Desktop. Cada extensión de
Google solicitada debe probarse por nombre. `chrome.identity.getAuthToken` usa
APIs restringidas fuera de Chrome; la instalación de una extensión no prueba
que su autenticación o todas sus funciones sean compatibles.

"Todos los complementos de Google" se trata como una intención de compatibilidad,
no como un alcance verificable. La primera comprobación abarca servicios web,
contraseñas, autocompletado y extensiones; otras funciones necesitan nombre y
criterio de aceptación antes de declararlas compatibles.

## Identidad del fork y errores

ApplicationId y firma propios, coexistiendo con la APK instalada y Chrome.
No migrar perfiles automáticamente. No almacenar credenciales en logs ni añadir
datos personales al repositorio. Mantener el soporte de seguridad de Chromium
y programar actualizaciones del motor independientemente de la estética.

## Entregas y aceptación

1. Parches UI contra la revisión fijada y validación de aplicación, recursos y
   estilo. Build propio después de confirmar la viabilidad del constructor.
2. APK con pestañas y favoritos reales: mouse, teclado, incógnito, ventana
   estrecha/maximizada, reinicio y cambio de display. Confirmar ausencia de
   superposición sobre el contenido web y acceso a extensiones.
   Comprobar teléfono vertical/horizontal con interfaz tradicional, DeX con
   interfaz Arc y traslado entre ambos displays sin pérdida de pestañas.
   Comprobar cambio de color desde apariencia, persistencia tras reinicio,
   contraste claro/oscuro y contenido web sin tinte.
3. Corrección de la ruta Agregar cuenta: sin excepción y sin atribuir Sync a
   una sesión web. Login web en Google probado manualmente por el usuario.
4. Prueba de Autofill Android con credenciales de prueba: primero Google,
   después un proveedor alternativo si hace falta. Resultado explícito de si
   cumple la condición del usuario para usarlo como predeterminado.
5. Integraciones Google de cuenta y extensiones: tabla por función con estado
   probado, bloqueado por acceso o pendiente; no una etiqueta global de éxito.

## Alternativas y decisión propuesta

Recomendado: fork nativo con interfaz Arc, sesión web Google y evaluación del
autocompletado Android. Conserva la base elegida y aprovecha código existente.

Alternativa: gestor local propio/importación CSV si el proveedor Android falla;
es un subsistema adicional que exige diseño de almacenamiento y pruebas.

Alternativa: conservar Chrome como navegador principal si se exige equivalencia
completa con sus integraciones privadas. Ese requisito no puede prometerse en
este fork con los componentes disponibles.

## Fuentes primarias comprobadas el 2026-10-05

- https://www.chromium.org/developers/how-tos/api-keys/
- https://blog.chromium.org/2021/01/limiting-private-api-availability-in.html
- https://developers.googleblog.com/en/chrome-3p-autofill-services/
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/android_autofill/README.md
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/PasswordManagerBackendSupportHelper.java
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java
