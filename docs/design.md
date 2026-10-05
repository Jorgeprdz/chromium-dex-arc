# Chromium para DeX: diseño visual Arc

Estado: diseño aprobado por el usuario el 2026-10-04. No se ha modificado Chromium ni creado una APK propia.
Actualización visual del usuario el 2026-10-05: referencia exterior de Arc para
Windows en `docs/references/arc-windows-reference.jpg`; marco con color personalizable,
barra superior compacta y rail izquierdo con favoritos, carpetas y pestañas.
Este diseño se aplica únicamente en modo escritorio/DeX. En la pantalla del
teléfono se conserva el diseño tradicional, también en horizontal. Esta
precisión sustituye cualquier elegibilidad anterior basada solo en el ancho.
El usuario aclaró que el violeta es solo el color de la referencia: se conserva
su distribución y se permite elegir el color del marco y rail, con persistencia
y contraste en claro/oscuro. Esta precisión sustituye la paleta lavanda fija
propuesta originalmente.
La ampliación de integraciones Google se documenta por separado en
`docs/superpowers/specs/2026-10-05-arc-google-design.md` y sigue en revisión.
Objetivo del usuario: adaptar Chromium para Android Desktop al look de Arc/Zen,
con navegación real en DeX y el motor ejecutándose en Android.

## Diseño propuesto

Referencia elegida explícitamente por el usuario: Arc de escritorio.
La propuesta utiliza su distribución lateral y un color de marco personalizable.

- Barra lateral izquierda de 240 dp, ajustable, con navegación y búsqueda arriba.
- Favoritos como botones compactos con favicon; lista vertical de pestañas debajo.
- Selección, cierre, creación y reordenación conectados a las pestañas reales.
- Color personalizable para el marco y la barra lateral, conservado tras reinicio.
  Temas claro y oscuro que conservan el contraste de texto e iconos. El contenido
  web conserva sus colores originales.
- Contenido amplio con margen de 8 dp; esquinas suaves donde el compositor permita
  recortarlas correctamente, sin cubrir contenido de la página con máscaras.
- Botón para contraer la barra a una columna de iconos de 52 dp. Sin controles
  decorativos que no funcionen. La primera versión no añade workspaces, split view
  ni modifica extensiones, sincronización, red, almacenamiento o seguridad web.
- Ctrl+L conserva el acceso a la dirección/búsqueda. Mouse, menús contextuales y
  foco de teclado deben seguir funcionando. En ventanas estrechas, la barra se
  contrae para conservar espacio; en teléfono se conserva el flujo móvil.

## Requisitos confirmados: escritorio y extensiones

- Desktop ready: ventanas DeX redimensionables y maximizables, navegación con
  mouse y teclado, foco correcto y adaptación al tamaño actual de la ventana.
- Conservar el soporte real de extensiones de Chromium Android Desktop, incluyendo
  la página de administración y las rutas de instalación admitidas por la base.
- Verificar instalación, activación, persistencia tras reinicio y acceso a la UI
  de extensiones en la APK propia. No prometer compatibilidad universal: las
  extensiones que dependan de APIs no disponibles en Android pueden fallar.
- El diseño lateral no debe ocultar el acceso a las acciones de las extensiones.

## Arquitectura y alternativas

Recomendación: un fork del código fuente de Chromium Android Desktop. Una extensión
puede proporcionar una página o un panel propio, pero no garantiza sustituir toda
la interfaz nativa. Una app WebView sería otra base técnica y no cumple el objetivo
actual de adaptar Chromium Desktop con sus funciones existentes.

Puntos de integración a investigar en el checkout exacto:
- ChromeTabbedActivity / TabbedRootUiCoordinator: composición del navegador Android.
- TabModelSelector y modelos existentes: pestañas normales e incógnitas separadas.
- Modelos de marcadores y omnibox existentes: favoritos y navegación reales.
- Capa de layout adaptativa: depende del tamaño de la ventana actual; no hardcodea
  un ID de pantalla DeX ni cambia resolución o densidad del teléfono.

La UI C++ de las plataformas de escritorio no se debe asumir disponible en Android
solo por el nombre AndroidDesktop. Se verificará la ruta activa del APK antes de
implementar la barra y ocultar su tira horizontal.

El fork debe tener applicationId y firma propios para coexistir con Chrome y con
el Chromium instalado. No se desinstalarán navegadores ni se migrarán perfiles
existentes automáticamente. La estética Arc/Zen no implica portar sus funciones.

## Compilación: restricción comprobada

El entorno disponible es Linux ARM64 con aproximadamente 91 GB libres en el
almacenamiento compartido del teléfono. La documentación de Chromium exige para
su flujo Android una máquina Linux x86-64, al menos 8 GB de RAM y 100 GB libres;
recomienda más de 16 GB de RAM. No hay todavía un constructor compatible asignado.
No se iniciará un checkout completo ni una compilación que agote el teléfono.

Antes de implementación hace falta resolver un constructor x86-64 con espacio
suficiente, fijar la revisión, hacer una compilación limpia sin cambios y después
aplicar la interfaz. No se ha verificado que un runner estándar de GitHub Actions
sea suficiente, ni se ha autorizado gasto en servicios de compilación.

## Validación necesaria

- Build limpio de la revisión seleccionada y build del fork con firma propia.
- Pruebas de pestañas: seleccionar/cerrar/reordenar sin pérdida del estado.
- Incógnito separado; foco y atajos; favoritos vinculados a marcadores reales.
- Teléfono, ventana DeX maximizada, redimensionada y cambio entre displays.
- Revisión de renderizado y recorte del contenido, sin tapar páginas.
- Verificación de que las funciones disponibles en la base no se pierdan.
- Actualizaciones regulares de seguridad del motor, independientes del diseño.

Fuentes primarias consultadas:
- https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md
- https://chromium.googlesource.com/chromium/src/+/main/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java
- https://docs.zen-browser.app/user-manual/compact-mode
- https://docs.zen-browser.app/user-manual/workspaces
