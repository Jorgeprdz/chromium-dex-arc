# R5.2C — Amazon directo y estado del fix nativo

Fecha: 2026-10-19. Investigación ejecutada en el worktree forense, sobre f0c696c.
[Prompt de continuación aplicado](../prompts/ARCHIUM_R5_2C_AMAZON_NATIVE_DIALOGS.md).
El usuario confirmó que los diálogos sólo oscurecen la pantalla y autorizó abrir
Amazon directamente. **Amazon FAIL reproducido; causa raíz gráfica NOT_PROVEN.**
No se cambió código GPU ni se despachó una compilación.

## APK realmente instalada

ADB autorizado identifica app.archium.android, versionCode 808600074,
versionName 157.0.8086.0. Hash medido del base.apk instalado:
`08da74aa96c34d414d9f96324f65a8be1df69067288f4079531c6de73a802b31`.
Coincide con la APK del run 39296066030, SHA
`3db367adff50d423b8c4475d10165d2790f6065a`.
Esto acredita el binario instalado, no que el supervisor lo instalara: su registro
sigue INSTALL_PENDING_DEVICE por QEMU_ABI_BLOCKED. No se modifica ese registro ni
se declara INSTALL_SUCCESS automático.

La APK no incluye el fix posterior `5184755`. Por eso no se repitieron los doce
mosaicos esperando un GREEN de un código que todavía no está instalado. Se
preserva ese fix, con 18 PASS Robolectric registrados en R5.2B; la aceptación
física del presenter corregido sigue pendiente.

Consulta DevTools nueva: Adreno 830, ANGLE Vulkan 1.3.284, GraphiteDawnVulkan,
gpu_compositing/rasterization/SurfaceControl habilitados. No se cambiaron flags,
Finch, configuraciones GPU ni la aceleración del navegador.

## Amazon observado directamente

Se abrió `https://www.amazon.com.mx/` en Archium, display lógico 35, y se realizó
una recarga normal sin borrar caché y un scroll. No se tocaron compras,
formularios, credenciales ni configuración de la cuenta. Se guardaron capturas
web y físicas del display externo correcto, metadata de imágenes y respuestas
Image del protocolo. No se publican las capturas completas por privacidad.

- Inicio: 129 imágenes DOM; 53 visibles de tamaño significativo, las 53 con
  complete=true y naturalWidth>0.
- Tras scroll: 162 imágenes DOM; 48 visibles, las 48 decodificadas según DOM.
- 168 registros de respuestas Image, sin fallos de transporte ni HTTP >=400 en
  esa ventana. Esto no es una auditoría de toda la red de Amazon.
- Las capturas muestran productos anormalmente negros/alterados y texto
  repetido/superpuesto. **DOM complete y HTTP correcto no equivalen a píxeles correctos.**

Se recuperaron seis archivos de imagen ya recibidos por esa página mediante
Page.getResourceContent, exclusivamente del CDN de imágenes. No se extrajeron
cookies ni headers de autorización. Los seis son AVIF y se decodificaron también
con FFmpeg/CPU. Los archivos y sus previews quedan privados. No se copiaron
recomendaciones personalizadas a fixtures públicas del repositorio.

No se aceptan como oracle cuantitativo los recortes rápidos de Amazon: algunos
bounds estaban parcialmente fuera del viewport y la colocación CSS/dinamismo no
se normalizó completamente. Se conserva la observación visual y los originales,
no una falsa métrica de corrupción basada en coordenadas incorrectas.

## Diferenciales ejecutados

1. Fixture R5.2 ya existente, sin modificar: 80 imágenes PNG generadas, dos fases
   y dos ciclos de scroll. Todas reportaron decodificación. En 32 ROIs de imágenes
   visibles, 1,002,320 píxeles comparados por estado: **cero diferencias** después
   del scroll dentro de cada fase. El cambio A→B sí modificó 539,139 píxeles.
2. Mapeo captura web→pantalla física derivado de píxeles de la fixture: offset
   (224,8), error RGB cero en 100 puntos. Los cuatro estados coincidieron también
   en sus ROIs de pantalla física. Se usó DPR medido, no PNG-width/innerWidth.
3. Probe temporal con tres imágenes reales recuperadas, cada una como AVIF y como
   PNG decodificado por CPU, con blend normal y multiply: **12/12 decodificadas y
   visibles normalmente**. No reproduce el defecto de composición complejo de
   Amazon ni autoriza convertir todos sus AVIF a PNG.

Conclusión limitada: el backend puede presentar esas imágenes y multiply en un
contexto simple. No hay evidencia para culpar por sí solo a AVIF o aplicar un
workaround global de formato, GPU o Graphite. Siguen como hipótesis invalidación,
reutilización de recursos/tiles, render passes y composición del sitio durante
scroll. Tampoco se ha demostrado que Amazon comparta causa con el presenter nativo.

## Fix recomendado aplicado: desbloquear el recolector Perfetto

Se encontró un defecto concreto en el instrumento R5.2: escribía el output de
Perfetto bajo `/data/local/tmp`. El CLI del Galaxy devolvió exit 1 y «Failed to
open» para esa ruta. El instrumento ocultaba stderr del recibo público para no
filtrar información privada, por lo que antes sólo figuraba CAPTURE_BLOCKED.

La [documentación oficial de Android](https://developer.android.com/tools/perfetto)
y [Perfetto](https://perfetto.dev/docs/learning-more/android) indican la carpeta
`/data/misc/perfetto-traces` para el output. Se cambió únicamente ese prefijo,
con nombre UUID independiente; no se cambian permisos ni se usa root.

RED: 15 tests Python, 1 fallo que reproduce la política de escritura Android en
la frontera del subprocess. GREEN: 15 PASS tras el cambio; el archivo recuperado
se conserva con permisos 0600. El stub de permisos no se presenta como Android
real. La comprobación real separada con el mismo CONFIG y CLI produjo exit 0,
pull exit 0 y un archivo de 8,383,068 bytes, SHA-256:
`52bcd56670f4e917a9d59dd7f52c4f4fd6c78159ade3f94d8ae048a2a0b31694`.

**La traza no está correlacionada con el scroll.** Terminó a 19:35:16.998Z; la
primera captura de esa repetición fue a 19:35:22.763Z y el scroll ocurrió después.
No se usa como prueba causal de corrupción ni se afirman resource/fence IDs a
partir de ella. Se conserva el recibo original y un correlation-review.json que
corrige expresamente el alcance. La última captura física quedó además ocluida
por otra aplicación al cambiar el usuario de ventana: no se publica ni se usa
para comparaciones globales. Se detuvieron las interacciones del dispositivo;
no se cerró ni manipuló esa otra aplicación.

Se necesita otra captura correctamente sincronizada cuando el dispositivo esté
libre, o tracing de Chromium con frame/paint/resource IDs. El fix del recolector
permite obtenerla sin compilar Chromium. Capturar un archivo binario por sí solo
no demuestra que cada datasource contenga los eventos requeridos.

## Estado y siguiente integración

- Diálogos: fix de código 5184755 conservado; APK corregida/Green Galaxy pendientes.
- Amazon: FAIL real, archivos recibidos/decodificados; primera causa de composición
  todavía no demostrada. **No hay fix GPU de producto en esta entrega.**
- Cambios nuevos: un prefijo de output en scripts/r52_capture_trace.py, regresión
  Python, prompt y este informe. Sin modificaciones al patch de Chromium, args,
  toolchain, ARM64, identidad Portal, supervisor ni rama activa.
- QEMU Android: QEMU_ABI_BLOCKED conservado. FFmpeg CPU y estos ensayos físicos no
  se etiquetan como ejecución Android QEMU.
- La próxima compilación, si se autoriza, debe integrar 5184755 y reutilizar un
  checkpoint completo compatible. No hay motivo demostrado para agregar flags
  GPU especulativos a esa compilación.

[Recibo de evidencia depurado](r52c/evidence.json). Originales privados:
`/workspace/macdesk-maintenance/archium-r52c/`. Los servidores temporales tienen
caducidad; sus pestañas y los forwards ADB propios se cerraron. Amazon permanece
abierto; no se alteraron pestañas personales preexistentes ni otras aplicaciones.
