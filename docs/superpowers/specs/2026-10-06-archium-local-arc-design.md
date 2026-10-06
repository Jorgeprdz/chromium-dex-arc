# Archium: contraseñas locales y Arc para Mac

Estado: alcance acordado en conversación; diseño escrito para revisión antes de
implementación. Sustituye la especificación con Google Sync.

## Resultado solicitado

El usuario decidió continuar sin Google Sync e implementar contraseñas locales:
importar su CSV, autocompletar, guardar y actualizar credenciales, consultar,
editar, eliminar y exportar, con almacenamiento cifrado y persistente. También
reafirmó expresamente Arc for Mac look and feel. La interfaz Arc debe funcionar
en una tablet y en escritorio, sin depender específicamente de Samsung DeX.

Base: Chromium 157.0.8086.0, revisión
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, paquete `app.archium.android`.
Preservar extensiones, navegación, perfiles, pestañas e incógnito de Chromium.
Trabajar sobre la rama aislada existente `feat/arc-desktop`.

## Contraseñas: arquitectura propuesta

Usar un backend local integrado con PasswordStore y PasswordManager de Chromium.
Adaptar primero PasswordStoreBuiltInBackend/LoginDatabase a la plataforma Android
de esta revisión. Incorporar un proveedor de cifrado respaldado por Android
Keystore; no usar una clave fija, el proveedor POSIX como sustituto de Keystore ni
almacenar el CSV como base de datos. Verificar las dependencias GN y la ruta de
OSCrypt antes de activar disponibilidad en la UI.

La build actual selecciona PasswordStoreEmptyBackend porque falta el backend
interno Google. El nuevo backend local y su interfaz deben ser una capacidad
propia de Archium. No simular que existe el backend Google, no registrar una
cuenta ficticia y no activar Sync para permitir guardado.

La disponibilidad solo se anuncia después de inicializar correctamente almacén
y cifrado. Si falta una clave o falla una migración, mostrar error recuperable;
no borrar registros ilegibles, guardar texto claro ni sustituir silenciosamente
el almacén por uno nuevo.

Las credenciales locales pertenecen al perfil original. Separar perfiles y
conservar la política de incógnito: no guardar nuevas credenciales de incógnito
ni crear rastros en el perfil normal por acceso implícito.

### Operaciones y experiencia

- Inicio de sesión correcto: ofrecer guardar o actualizar mediante el flujo real
  de PasswordManager, sin capturar valores arbitrariamente desde JavaScript.
- Formulario de login: sugerencias con matching de origen de Chromium y rellenado
  tras selección del usuario. No entregar contraseñas a un origen distinto.
- Pantalla nativa de contraseñas locales: listar/buscar, editar, eliminar y
  revelar/copiar con autenticación del dispositivo donde sea posible.
- Importar CSV: Android Storage Access Framework, lectura por URI, validación de
  encabezados `url`, `username`, `password`, soporte de columnas adicionales,
  UTF-8/BOM, comillas, comas y saltos de línea dentro de campos.
- Mostrar cantidades válidas, inválidas y duplicadas antes de confirmar. La clave
  de duplicado es origen/realm y usuario según el modelo de credenciales de
  Chromium. No sobrescribir contraseñas distintas sin una decisión del usuario.
- Importación cancelada: no escribir registros. Tras confirmar, usar una operación
  transaccional o una estrategia con rollback verificable; informar el resultado.
- Exportar CSV: autenticación, advertencia breve de que el archivo contiene
  contraseñas legibles, selector de destino y acción explícita del usuario.
  No exportar a una ruta compartida predeterminada ni dejar copias temporales.
- El roundtrip exportar/importar conserva los campos de credenciales compatibles
  con CSV, incluidas contraseñas con comillas y saltos de línea. Passkeys no se
  exportan como si fueran contraseñas.

No usar el CSV personal para las pruebas, ni registrar secretos o contenido de
formularios en logs, CI o repositorio. Las pruebas usan credenciales ficticias.

## Arc para Mac: apariencia e interacción

Referencia oficial guardada:
`docs/references/arc-mac-pinned-tabs.png`, captura de la sección macOS del artículo
de Arc sobre pestañas fijadas. El recorte muestra navegación y dirección en la
sidebar, favoritos, título de espacio, separador, Nueva pestaña y marco redondeado.
Sirve para esos elementos; antes de cerrar el diseño se completarán referencias
oficiales de los controles inferiores y estados que el recorte no muestra.

El objetivo es reproducir Arc para Mac dentro de la superficie dibujada por el
navegador, incluyendo proporciones, tipografía, iconos, colores, hover, selección,
espaciado, transiciones y foco. La decoración que imponga el gestor de ventanas
Android puede diferir de macOS; no sustituir sus botones por imitaciones sin función.

### Composición y comportamiento

- Sidebar a la izquierda con controles atrás, adelante, recargar, contraer y
  dirección/seguridad de sitio; conservar omnibox y mecanismos de permisos nativos.
- Favoritos como mosaicos con favicon que abren o seleccionan una pestaña real.
  A diferencia de la entrega anterior, no limitar el diseño a cuatro botones
  añadidos al encabezado de una rail de Chrome.
- Pestañas fijadas/carpetas y pestañas abiertas en secciones separadas por una línea;
  selección, cierre, creación, arrastre y menús conectados a modelos persistentes.
- Al cerrar una pestaña fijada, conservar su entrada y URL fijada para volver a
  abrirla. Cerrar una pestaña abierta conserva el mecanismo de restauración.
- Controles inferiores que aparecen en la referencia deben operar realmente.
  Espacios, si se muestran, deben seleccionar colecciones locales persistentes de
  pestañas/fijados; no puntos decorativos ni cuentas Google simuladas.
- Dirección/búsqueda desde la sidebar y command bar: Ctrl+L conserva edición de
  dirección; Ctrl+T abre búsqueda/nueva pestaña, con selección de pestañas existentes
  y navegación. Conservar atajos de pestañas, navegación y acceso a extensiones.
- Contenido web con margen y recorte real de esquinas compatible con el compositor;
  no cubrir el contenido con máscaras. El tema del marco no tiñe las páginas.
- Sidebar contraíble, redimensionable y visible temporalmente en ventanas estrechas,
  conservando foco y acceso a los controles. No dejar una tira horizontal de Chrome
  junto a la sidebar Arc.
- Marco personalizable persistente y estados claro/oscuro legibles. Usar referencias
  Mac para colores y estados; la paleta naranja de la captura es una posibilidad,
  no un color obligatorio para todos los usuarios.
- Si se ofrece limpiar/archivar pestañas, debe ser una acción explícita con
  recuperación. No activar autoarchivado destructivo de pestañas existentes.

### Activación y adaptación

Preferencia persistente: Automático / Arc / móvil.

- Automático activa Arc en tablets y ventanas de escritorio compatibles, incluido
  DeX, usando el contexto de la ventana. La condición actual que exige campos
  exclusivos Samsung se reemplaza.
- Arc permite elegir el diseño manualmente sin depender de marca ni display ID.
- Automático conserva la interfaz móvil en teléfonos; Arc sigue disponible manualmente.
- La geometría de la ventana regula el layout y colapso, no elimina el acceso a Arc.
- Cambiar modo, orientación o pantalla preserva modelos de pestañas, formularios,
  historial de navegación y preferencias de apariencia.

## Compilación y actualización

Separar validación de contraseñas, validación visual/funcional Arc y build completo.
El backend debe pasar pruebas nativas con cifrado; los parsers deben pasar pruebas
con CSV ficticios; la activación de UI debe pasar pruebas de política tablet,
escritorio y override manual. Los stubs de APIs no sustituyen GN y compilación real.

Investigar reconstrucción incremental desde
`archium-checkpoint-37255997027-7`. La restauración actual fija commit y parches;
para reutilizarla con cambios se necesita una transición verificable desde el
parche anterior al nuevo y regenerar GN. No saltarse controles de integridad ni
prometer que el nuevo run será corto sin medirlo.

Mantener checkpoints del nuevo build. Comprobar firma de actualización antes de
instalar: no desinstalar la APK ni borrar el perfil del usuario para superar un
conflicto de firma. No incorporar el CSV personal a la compilación.

## Aceptación de la entrega

1. Importar CSV ficticio, guardar/actualizar desde login, rellenar en el origen
   correcto y exportar/reimportar sin pérdida; comprobar persistencia tras reinicio.
2. Cancelación, duplicados, CSV malformado, falta de clave y errores de escritura
   no producen pérdida ni exposición de contraseñas.
3. Arc visible y operable en tablet sin DeX, escritorio, móvil con override manual,
   ventana estrecha y maximizada. Comparación visual con referencias Mac.
4. Favoritos, fijados, carpetas, pestañas, menús, arrastre, teclado y extensiones
   funcionan después de reiniciar y de cambiar display/orientación/modo.
5. APK compilada y probada en el teléfono. Enumerar resultados reales y pendientes;
   una compilación exitosa no equivale a aceptación funcional o visual.

## Fuera del alcance elegido

Google Sync, transferencia automática de datos con Chrome, backend Google de
contraseñas, passkeys y Wallet no son dependencias ni promesas de esta entrega.
Sesión web Google permanece disponible. La investigación previa de Sync se
conserva en `docs/google-sync-scope-2026-10-06.md` para trabajo futuro separado.

## Orden propuesto

Implementar y verificar primero el almacén local, después la interfaz e interacción
Arc con pruebas independientes, y finalmente compilar/instalar/verificar la APK
integrada. Preparar planes separados para cada subsistema y la reconstrucción;
mantener el método de ejecución inline utilizado por el usuario en esta sesión.

## Fuentes de referencia

- https://resources.arc.net/hc/en-us/articles/19231060187159-Pinned-Tabs-Tabs-you-want-to-stick-around
- https://resources.arc.net/hc/en-us/articles/19230755904151-Favorites-Top-Tabs-Across-Every-Space
- https://resources.arc.net/hc/article_attachments/20509285257111
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/password_manager/factories/password_store_backend_factory.cc
- https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/password_manager/core/browser/password_store/password_store_built_in_backend.h
