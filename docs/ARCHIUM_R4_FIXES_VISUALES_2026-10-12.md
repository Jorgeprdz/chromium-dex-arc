# Reparación autorizada tras APK 38285899318

Base: `assistant/archium-r4-recovery`, `7da34209c78510ae13e128765c6eb21bde955c88`.
Pin Chromium: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
El usuario autorizó «esos puntos + lo que ya habíamos señalado. procede a fix y siguiente build».
`feat/arc-desktop` y `main` permanecen protegidas y sin cambios.

## Hallazgos observados

- Run 38285899318 SUCCESS, APK instalada coincide con SHA256
  `bdf31fe1c860b06821951d5c2f633248b02f6c46797e3e4e18f64fab0fc6c9ff`.
- Arranque móvil COLD PASS. En DeX display 18 abre y muestra sidebar; al tocar
  la omnibox el proceso 14178 crashea a las 13:15:53 del teléfono. Stack:
  `LocationBarTablet` → `ViewUtils.getRelativeLayoutPosition`, cast de
  `ViewRootImpl` a `View`. La referencia al toolbar sigue siendo anterior al reparent.
- Capturas reales muestran las líneas blancas del padding del rail, el hueco
  reservado de la colección y el favicon descentrado en compacto.
- Las carpetas/espacios carecen de eliminación; el tinte del header sobrescribe
  fondo y colores de los favicons. La mezcla de color conserva solo 12% del seed
  en modo claro; preview del coordinator y binders leen estados diferentes.

## Plan de ejecución y aceptación

1. Corregir los dos cálculos de foco/expansión y el ancho efectivo de
   LocationBarTablet. Mantener sus rutas de descendiente y ventana móvil.
   RED/GREEN en Robolectric real y test completo bloqueante en ChromeJUnit.
2. Dar altura según contenido al scroll; añadir eliminar espacio/carpeta con
   confirmación. Transferir pestañas/pins/carpetas al espacio restante y promover
   hijos al eliminar carpeta; conservar favoritos e IDs. Probar persistencia,
   último espacio y fallos de escritura sin comandos nativos posteriores.
3. Favoritos como mosaicos cuadrados con favicon sin filtro monocromo. Conservar
   el gestor Chromium de marcadores y evitar migraciones implícitas de datos.
4. Aplicar una única paleta a marco, rail y pestañas; preview reversible por
   ventana, aplicar persistente y cancelar sin escritura. Mantener contraste,
   cápsula activa clara y tonos tenues derivados del color elegido.
5. Sustituir el punto por esfera multicolor nativa; retirar Autofill de la
   composición de la sidebar conservando el menú Chromium y extensiones.
6. Centrar el favicon nativo al colapsar y restaurar la edición real al enfocar,
   expandir o salir de Arc. Evitar reinstalar estilos y texto en cada frame para
   acompañar la animación nativa existente sin alterar viewport/TabModel.
7. Suite host integral, probes Android/JVM y Robolectric acotados sin skips
   críticos; regeneración oficial doble idéntica y aplicación del patch. Verificar
   SHA remoto, checkpoint compatible, disco del runner y ausencia de otro build.
8. Push temático y un workflow_dispatch incremental con SHA fijo. Gates reales
   ChromeJUnit/JNI/recursos antes de APK. Monitor en nueva sesión Termux y detener
   trabajo automático después del handoff solicitado. Runtime de APK nueva queda
   pendiente hasta probar esa APK en el dispositivo.

Se conserva el grosor del marco, la expansión del visor y la forma de la cápsula
activa. Contraseñas propias continúan DEPRECATED. No clean build ni borrado de
fuentes, outputs, logs Ninja o checkpoints remotos.
