# Archium for Android: código preparado

Trabajo aislado en la rama `feat/arc-desktop`. La APK instalada y el workflow
baseline permanecen intactos. El baseline no incorpora cambios escritos después
de su inicio.

## Código disponible

- `chromium/`: nuevas clases Java nativas, no una maqueta HTML ni un WebView.
- `patches/archium-desktop.patch`: cambios contra la revisión fijada de Chromium.
- `patches/upstream-files.json`: revisión y hashes de entradas/salidas del parche.
- `config/archium-args.gn`: paquete propio `app.archium.android`.
- Nombre visible y widgets: Archium for Android / Archium.

La política de ventana usa la configuración DeX de la Activity y el display de
esa ventana; no la anchura, un servicio global DeX ni el flag de compilación.
En el display principal de un teléfono se conserva la interfaz móvil. Un
dispositivo que declara FEATURE_PC puede usar Arc en su display principal.
Cambiar entre móvil y DeX reconstruye la Activity por el mecanismo nativo de
guardar/restaurar; falta comprobarlo con la APK y las pestañas reales.

Se extiende la rail nativa de pestañas (240/52 dp), con recursos para controles
de 44 dp más 4 dp de margen a cada lado. El encabezado incorpora los primeros
cuatro marcadores URL de la carpeta de escritorio como favoritos con favicon
local, navegación por carpetas reales, acceso al administrador completo y color
personalizable `#RRGGBB` persistente con superficies claras/oscuras legibles.
El navegador conserva sus modelos, menús y mecanismos de arrastre/incógnito.
El inset nativo del caption se sitúa antes de todo el encabezado y sigue las
notificaciones del gestor nativo. El color del encabezado observa explícitamente
los cambios de incógnito y retira el observador al destruirse.

Google se abre en pestañas reales del perfil actualmente seleccionado.
La sesión web no se presenta como Chrome Sync. La acción Autocompletado abre
la pantalla nativa de selección del proveedor; no habilita el servicio en
silencio. El fork permite evaluar Google como proveedor Android porque su
compilación pública carece del backend interno Google. El cambio de enrutamiento
está limitado al paquete `app.archium.android`, conserva los bloqueos de política
y las condiciones de disponibilidad, y recuerda la selección del usuario.

La operación Agregar cuenta del delegado vacío notifica `null` mediante el
contrato existente en vez de lanzar UnsupportedOperationException. Esto permite
la ruta de error del llamador; no añade autenticación OAuth ni acceso a Sync.

## Cómo verificar

```
python3 scripts/check-arc-preparation.py --fetch-sources
python3 -m unittest discover -s tests -p 'test_*.py'
```

`--fetch-sources` descarga solo los archivos originales tocados, con hashes
verificados de la revisión fijada. No realiza un checkout completo de Chromium.
Para otro SDK, pasar `--android-jar /ruta/android.jar`.

El comprobador aplica el diff en un checkout temporal pequeño y verifica todas
las salidas. Compila/ejecuta la política de display y contraste, comprueba la
ruta de proveedores y compila los adaptadores nuevos contra Android SDK 36
con contratos Chromium sustituidos por stubs. Esta última comprobación detecta
errores de APIs Android/sintaxis; NO verifica el grafo completo de GN, todas las
APIs reales de Chromium, NullAway ni la ejecución en Android.

La prueba del delegado vacío ejecuta el código original y reproduce su excepción
con `--test-original-account-delegate`; con el código parcheado comprueba una
única devolución de callback sin excepción. Las siete pruebas del aplicador
verifican aplicación real, dry-run, revisión incorrecta, cambios del usuario,
archivo nuevo ya existente, hunk incompatible y symlink, sin escritura parcial.

## Aplicar en un constructor completo

```
python3 /ruta/Archium/scripts/apply-arc-patches.py /ruta/chromium/src --check
python3 /ruta/Archium/scripts/apply-arc-patches.py /ruta/chromium/src
```

El aplicador requiere el HEAD exacto
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`. Rechaza archivos tocados que
difieran de los originales, rutas inseguras y conflictos antes de mutar.
No es idempotente: una segunda aplicación se rechaza porque los originales
ya cambiaron. El generador de diffs requiere `.source-reference` y
`.source-modified`; regenerar tras editar nuevos archivos de `chromium/`.

El constructor debe usar `config/archium-args.gn` y el target `chrome_public_apk`.
La APK resultante aún necesita firma propia persistente de Archium. No usar la
clave de prueba de Chromium como identidad de distribución; configurar la
firma del constructor o volver a firmar la APK antes de instalarla.

## Validación y funciones pendientes

No se ha compilado la APK del fork ni probado visualmente en DeX. Permanecen
pendientes: aplicar el margen de contenido de 8 dp mediante el compositor,
recorte real de esquinas, revisión completa de tints de toolbar/extensiones,
restauración de pestañas al cambiar de display y prueba de extensiones.
Estos puntos impiden describir la implementación como la interfaz final lista.

La entrega de credenciales Google al paquete propio debe comprobarse con una
cuenta/formulario de prueba. Permitir el framework no garantiza que Google
entregue datos a Archium. La importación CSV local sigue sin almacén funcional;
Chrome Sync, Google Pay, passkeys y extensiones que usen APIs privadas no se
declaran compatibles. Se conserva la condición del usuario: no recomendarlo
como predeterminado antes de comprobar el acceso a sus contraseñas.

## Referencias

Distribución exterior: `docs/references/arc-windows-reference.jpg`.
El enlace compartido `https://share.google/qF6snxFRmig6oc6t9` redirige a
`https://github.com/Arc-Mac/`. Se consultó como referencia adicional; no se
descargaron ejecutables ni se adoptaron como capacidades del fork las funciones
que esa página enumera. Referencia oficial visual: https://arc.net/.
Detección DeX de ventana documentada por Samsung:
https://developer.samsung.com/samsung-dex/modify-optional.html.

## Resultado del baseline vigilado

Run `37231453817`: cancelado el 2026-10-05 a las 02:07:42 UTC.
La anotación del job confirma que superó el timeout de 5 h 50 min;
la publicación de prerelease se omitió y no produjo una APK distribuible.
https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/37231453817

## Run de Archium

El workflow `baseline-build.yml` ahora aplica los parches y usa
`config/archium-args.gn`; conserva la APK de prueba como artifact durante siete
días. Timeout: 360 minutos, máximo del runner hospedado. No promete finalizar
en esa ventana; para superar seis horas se requiere otro constructor.
