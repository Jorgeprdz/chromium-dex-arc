# Archium: cuentas Google, contraseñas y diseño Arc para Mac

Estado: sustituida por `2026-10-06-archium-local-arc-design.md` tras la decisión
del usuario de continuar con contraseñas locales sin Google Sync. Se conserva
como historial de diseño; no ejecutar sus requisitos de Google Sync.

Revisión previa de viabilidad solicitada por el usuario:
`docs/google-sync-scope-2026-10-06.md`. Google Sync sigue como objetivo condicionado
a prueba, no como capacidad garantizada. Se identificó también una ruta experimental
microG para Chromium 147, sin validación en Archium 157 y con un backend de claves
incompleto; no se incorpora automáticamente al diseño ni se declara funcional.

## Requisitos del usuario

La nueva entrega debe implementar acceso con Google y sincronización real del
navegador; guardar y exportar contraseñas; importar el CSV que el usuario ya
tiene; y reproducir el diseño de Arc Browser para Mac. La apariencia Arc no
puede depender de Samsung DeX: debe funcionar también en tablets.

Estos requisitos sustituyen la entrega anterior basada en login web, evaluación
del proveedor Android y una referencia visual de Arc para Windows. Ninguno de
esos sustitutos constituye la aceptación de la nueva entrega.

## Hallazgos confirmados

- La APK instalada es `app.archium.android`, versión 157.0.8086.0.
- El run 37255997027 terminó correctamente en la etapa ocho. Existen checkpoints
  hasta la etapa siete, con fuentes y objetos compilados. El último ocupa
  aproximadamente 24 GB comprimidos. No se ha probado aún reconstruir nuevos
  cambios desde ese checkpoint.
- La referencia anterior era Arc para Windows, no Mac.
- La sidebar no apareció después de activar Android Vertical Tabs con
  enabled-by-default y reiniciar. Ese experimento no prueba por sí mismo la
  causa. El flag fue devuelto a Default.
- El parche exige `FEATURE_PC` o un display externo con el campo Samsung
  `semDesktopModeEnabled`. Esa condición no satisface el nuevo requisito tablet.
- La implementación upstream de `NullAccountManagerDelegate` no enumera cuentas
  y no implementa adquisición de tokens. El parche anterior solo elimina la
  excepción al pedir agregar cuenta. No implementa inicio de sesión.
- `PasswordManagerBackendSupportHelper.isBackendPresent()` devuelve false en la
  implementación abierta de la revisión fijada. Cambiarlo a true no aporta un
  backend. La UI instalada muestra que el administrador dejó de funcionar.
- Chrome Sync requiere tokens OAuth con acceso restringido por Google. El
  requisito se conserva; no se reemplaza por sesión Gmail, actividad web ni
  sincronización propia mediante Drive.

## 1. Acceso Google y sincronización

Implementar un delegado Android real que enumere cuentas autorizadas, observe
cambios, permita seleccionar/agregar cuenta, obtenga identidad y tokens mediante
APIs admitidas y gestione renovación, revocación y errores. No solicitar permisos
ni aceptar consentimientos en silencio.

Integrarlo con IdentityManager y los servicios de sincronización de Chromium.
La interfaz debe mostrar cuenta activa, estado de sincronización y errores reales,
y permitir cerrar sesión. El inicio de sesión web no cambia este estado.

Se requieren credenciales propias y acceso de prueba admitido por Google. La
documentación oficial menciona cuentas de prueba en
google-browser-signin-testaccounts@chromium.org. Esa excepción no garantiza que
nuestro cliente Android obtenga los tokens: debe verificarse antes de afirmar
viabilidad o iniciar la compilación completa.

Prueba de aceptación: cuenta de prueba, token válido para el servicio solicitado,
sincronización de marcador e historial entre Archium y Chrome, persistencia después
de reiniciar, cierre de sesión y recuperación ante token revocado. Las contraseñas
solo se anuncian sincronizadas si su backend está integrado y pasa su prueba.

Si Google deniega el acceso, registrar el error sin tokens ni datos personales y
comunicar el bloqueo. No entregar una alternativa bajo la etiqueta Chrome Sync.

## 2. Contraseñas locales

Crear o adaptar un backend funcional para la revisión fijada; investigar primero
la reutilización de PasswordStore y componentes existentes antes de crear un
almacén paralelo. Conservar los mecanismos de matching y rellenado de Chromium.

Funciones obligatorias:

- Ofrecer guardar credenciales después de un inicio de sesión correcto y actualizar
  una contraseña existente tras su cambio.
- Listar, buscar, editar y eliminar registros; revelar/copiar con autenticación
  del dispositivo donde esté disponible.
- Importar CSV mediante el selector Android, validar columnas y filas, mostrar un
  resumen y gestionar duplicados sin sobrescrituras silenciosas.
- Exportar CSV mediante el selector Android, con acción explícita del usuario.
- Rellenar formularios de login dentro de Archium y persistir tras reinicio.

Almacenamiento cifrado con claves protegidas por Android Keystore, sin secretos en
logs, artifacts de CI ni repositorio. CSV de prueba con credenciales ficticias; no
leer el CSV real para desarrollar. La exportación CSV es texto claro por definición
y debe indicarse en el flujo de exportación.

El proveedor Autofill Android puede seguir disponible como elección adicional;
no sustituye este backend ni la importación directa solicitada.

Aceptación: guardar, actualizar, importar CSV con comillas/comas/saltos de línea,
rechazar registros inválidos, gestionar duplicados, exportar y reimportar sin
pérdida, rellenar en formularios de prueba y comprobar persistencia. Sin guardar
datos de incógnito por defecto.

## 3. Apariencia Arc para Mac, tablet y escritorio

Usar referencias de Arc para Mac. Antes de modificar layouts, fijar capturas de
referencia con su versión, estado de sidebar y dimensiones. Comparar la distribución,
tipografía, iconos, espaciado, selección, marco, esquinas y estados interactivos.
La referencia de Windows anterior no es válida para esta revisión.

Reproducir dentro del navegador la dirección y navegación en sidebar, favoritos,
secciones de pestañas fijadas y abiertas, controles inferiores, marco temático,
contenido con margen y recorte real, y el acceso a dirección/búsqueda. Los controles
visibles deben operar sobre modelos reales; no añadir botones decorativos sin
función. Conservar extensiones, omnibox, foco, teclado y mouse.

La decoración de ventanas y los botones que impone Android pertenecen al gestor
de ventanas. Documentar esta diferencia frente a macOS; la equivalencia visual
objetivo se aplica al contenido y controles que Archium puede dibujar.

Elegibilidad propuesta:

- Preferencia persistente de apariencia: Automático, Arc o móvil.
- Automático usa interfaz Arc en tablets y ventanas de escritorio compatibles,
  incluyendo DeX, con información del contexto de la ventana actual.
- Arc permite activarla manualmente sin depender de fabricante o display ID.
- El tamaño disponible regula expansión/contracción de la sidebar; no identifica
  por sí solo a Samsung DeX. No hardcodear IDs, densidad ni resolución.
- En teléfonos Automático conserva la UI móvil; el usuario puede elegir Arc.

Probar tablet sin DeX, teléfono, escritorio DeX, ventana estrecha/maximizada y
cambio de display. Conservar pestañas y navegación en todas las transiciones.
La comparación visual exige capturas reales de la APK con datos de prueba.

## 4. Compilación y criterios de entrega

Investigar la reconstrucción incremental desde el checkpoint siete. El restaurador
actual exige el mismo commit y no admite por sí solo un nuevo parche: se necesita
un flujo que verifique la identidad del checkpoint y del parche anterior, aplique
la transición controlada, regenere GN y reutilice objetos válidos de Ninja.
Nunca ignorar sus comprobaciones de integridad. No prometer duración hasta medir.

Separar pruebas de contratos y compilación de los componentes modificados de la
compilación completa. Estas pruebas reducen errores tempranos, pero no reemplazan
GN, la compilación real ni la ejecución de la APK.

No lanzar una compilación completa hasta resolver la viabilidad de Google Sync,
disponer de backend de contraseñas verificable y validar el plan visual y sus
condiciones de activación. No llamar terminada a la entrega hasta probar los tres
requisitos. Si uno se bloquea externamente, comunicarlo antes del run largo.

Mantener applicationId y firma compatibles con la APK del usuario cuando sea
posible; inspeccionar la firma actual antes de planificar una actualización. No
desinstalar ni borrar perfiles como parte de estas pruebas.

## Decisiones pendientes

1. Credenciales propias y cuenta de prueba admitida para Google Sync. Pregunta
   enviada al usuario; no se han recibido secretos ni aprobado sustitutos.
2. Captura/versión de Arc para Mac que define la equivalencia visual exacta.
3. Revisión de esta especificación; después se redactará el plan por archivos y
   pruebas para la implementación.

## Fuentes

- https://www.chromium.org/developers/how-tos/api-keys/
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/signin/public/android/java/src/org/chromium/components/signin/NullAccountManagerDelegate.java
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/PasswordManagerBackendSupportHelper.java
- https://arc.net/
- https://resources.arc.net/hc/en-us/articles/19230755904151-Favorites-Top-Tabs-Across-Every-Space
- https://resources.arc.net/hc/en-us/articles/19231060187159-Pinned-Tabs-Tabs-you-want-to-stick-around
