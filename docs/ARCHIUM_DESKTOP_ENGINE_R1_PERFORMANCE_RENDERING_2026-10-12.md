# Archium Desktop Engine R1 — Performance & Rendering

**Fecha:** 2026-10-12  
**Estado:** especificación y roadmap; **no implementado ni validado**  
**Proyecto:** [Archium / chromium-dex-arc](../README.md)  
**Rama de integración propuesta:** `assistant/archium-r4-recovery`  
**Ramas de preservación:** no modificar `feat/arc-desktop` ni `main`  
**Motor de referencia del fork:** Chromium Android Desktop arm64, revisión `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0)

> Objetivo de producto: que Archium conserve su identidad visual Arc, pero abra,
> represente y controle sitios web como un **navegador real de escritorio** sobre
> Android, con velocidad, estabilidad y eficiencia comparables a Samsung Internet.
> La comparación es una referencia de calidad, **no** una afirmación de paridad ni
> una intención de reutilizar código propietario de Samsung.

## 1. Visión y plataformas

Archium no está diseñado exclusivamente para Samsung DeX. El producto apunta a
entornos de escritorio basados en Android:

| Entorno objetivo | Política prevista | Validación |
| --- | --- | --- |
| **Googlebook OS** | Desktop-first cuando el sistema/ventana proporcione capacidades de escritorio; sin APIs privadas de fabricante | **PENDIENTE**, requiere dispositivo o entorno representativo real |
| **Samsung DeX** | Ventanas libres, monitor externo, mouse/teclado y UI Archium escritorio | **PENDIENTE R1**, existe evidencia de fallos runtime en la rama R4 |
| **Motorola Smart Connect / Ready For** | Misma arquitectura desktop adaptable, con pruebas específicas del gestor de ventanas | **PENDIENTE**, requiere equipo real |
| **Teléfono Android** | Preservar UI móvil, especialmente en el teléfono y en horizontal; opción de sitio desktop manual | Regresión obligatoria, **PENDIENTE R1** |
| **Ventana estrecha en un desktop** | Reflow de UI y página según espacio disponible; conservar estado | **PENDIENTE R1** |

**Principio:** detección por capacidades reales, tipo de ventana, tamaño efectivo,
configuración y cambios de pantalla. **No** hardcodear fabricante, identificadores
de display, resolución, DPI ni una simple orientación landscape. El cambio de
modo de página y el de apariencia Arc son políticas relacionadas pero diferentes.

La compatibilidad real entre dispositivos solo se acredita en hardware/runtime
representativo. La presencia de clases o flags en el código no demuestra soporte
funcional en otro fabricante.

## 2. Alcance prioritario

### P0 — Estabilidad antes de optimización

Antes de medir un motor de renderizado, Archium debe abrir, navegar y permanecer
estable. La documentación de R4 identifica un crash real de `LocationBarTablet`
al interactuar con la omnibox reubicada en DeX, pese a contar con una APK que
compiló. **No se considera cerrado por compilar.**

- Verificar en la nueva APK que no hay crash en arranque, omnibox, sugerencias,
  back/forward, navegación ni cambio móvil ↔ desktop.
- Preservar `TabModel`, estado de pestañas, perfil normal/incógnito,
  autocompletado nativo y ajustes existentes.
- Resolver problemas de viewport/recortes antes de atribuirlos a la GPU.
- Marcar `ANDROID_RUNTIME=PASS` solo con pruebas reales de la APK objetivo.
- Mantener como referencia el estado de
  [verificación R3](ARCHIUM_R3_VERIFICACION_2026-10-12.md) y
  [fixes R4](ARCHIUM_R4_FIXES_VISUALES_2026-10-12.md).

### P1 — Sitios desktop auténticos

Objetivo: una página recibe una representación coherente de navegador desktop,
no una versión móvil estirada a un monitor.

1. Integrar la decisión **Request Desktop Site (RDS)** con el tamaño y la clase
   efectiva de la ventana actual, capacidades de desktop y preferencias del usuario.
2. Auditar juntos **User-Agent, User-Agent Client Hints, viewport CSS, device
   metrics, device scale, viewport meta, text autosizing y zoom**. Evitar que
   un servidor reciba señales inconsistentes sobre el mismo cliente.
3. Conservar el soporte upstream para configuraciones de sitio y elecciones
   explícitas de "sitio móvil" / "sitio de escritorio"; nunca reescribirlas
   silenciosamente al redimensionar una ventana.
4. Usar los componentes nativos Chromium ya estudiados:
   `DesktopSiteUtils`, `REQUEST_DESKTOP_SITE`, `NavigationController`,
   `ZoomController`, `HostZoomMap` y preferencias del perfil.
5. No ejecutar recargas compulsivas por cada pixel de resize; aplicar la
   política cuando corresponda a la navegación y cambiar/reload solo si
   realmente cambia una propiedad que lo exige.
6. Preservar accesibilidad, tamaño de fuente/zoom elegido, persistencia por
   sitio y separación de incógnito.
7. Mantener el flujo móvil en el teléfono, incluso en horizontal; ofrecer
   override manual explícito.

**Nota:** la web puede optar por diseños responsive aunque declare RDS.
No se promete identidad píxel a píxel con Chrome, Samsung Internet o PC en
todos los sitios.

Referencia de código:
[investigación desktop/input de Chromium 157](investigacion-desktop-input-2026-10-06.md).
El umbral upstream tablet de 600 dp y la clasificación de UI compacta/tablet/
desktop (840 dp para desktop) son **puntos de partida**, no sustitutos de la
detección de capacidades, contexto de ventana y preferencias.

### P2 — Renderizado, GPU y latencia visual

Auditar primero la ruta real de Chromium **Blink → compositor/Viz → Skia →
GPU/Surface** de la APK, antes de alterar flags o scheduling:

- Inspeccionar en el dispositivo `chrome://gpu` cuando esté disponible,
  trazas Chromium/Perfetto, timestamps de frames, rasterización, overdraw,
  scroll jank, cambios de superficie, presión térmica y uso de memoria GPU.
- Identificar si una pérdida de fluidez proviene de la página, main thread,
  JavaScript, raster, compositing, SurfaceView, sidebar/blur u OEM compositor.
- Evitar invalidaciones y redibujados del marco/rail cuando cambia contenido
  web; el material visual de la UI **no** debe añadir repintados constantes
  ni capturas por frame.
- Preservar video hardware decode y la vía de composición del contenido,
  sin forzar Vulkan/ANGLE, decodificadores ni flags experimentales a todos
  los dispositivos. Solo habilitar variantes validadas por hardware/driver.
- Mantener hover y scrolling precisos con mouse; respetar refresh rate real
  de pantalla y comportamiento energético/thermal del dispositivo.
- Validar recortes, insets, esquinas y redimensionamiento sin franjas negras,
  superficies obsoletas ni superposición de controles sobre la página.

### P3 — Carga, memoria y pestañas

- Perfilar carga fría y caliente, navegación entre pestañas y coste de
  reanudar la aplicación.
- Reutilizar políticas upstream Chromium de scheduler, memory pressure,
  cachés y tab discarding. No hacer una segunda gestión de pestañas que
  compita con `TabModel` o con el sistema.
- Afinar solo después de identificar cuellos de botella en trazas reproducibles.
- Al liberar pestañas inactivas, conservar historia, identidad, URL canónica,
  sesiones, scroll y formularios según garantías existentes del motor.
- Controlar RAM/CPU/energía con 1, 5, 10 y 20 pestañas representativas.
- No intercambiar menor RAM por cierres de pestañas activas, pérdida de datos,
  recarga excesiva o procesos muertos en segundo plano.

### P4 — Input desktop y UX

Reutilizar dispatchers nativos (`KeyboardShortcuts`, `EventForwarder`,
`WebContents`, `MultiWindowUtils`) y validar:

- Click derecho y menús contextuales; botón central para abrir/cerrar
  según región; hover y focus correcto.
- `Ctrl+L`, `Ctrl+T`, `Ctrl+W`, `Ctrl+Tab`, hard reload cuando exista;
  no interceptar globalmente combinaciones que pertenecen a Android/OEM.
- `Ctrl+rueda` para zoom real de página cuando esté soportado, persistido
  correctamente; rueda/trackpad para scroll sin gestos ficticios.
- Selección de texto, arrastrar/soltar cuando la plataforma lo permita,
  ventanas redimensionables/múltiples y cambios de display sin pérdida de
  perfil ni foco.
- Sidebar expandida/compacta sin cambiar el layout de la página de modo
  sorpresivo ni modificar `WebContents` por estética.
- Extensiones y acciones del navegador permanecen disponibles; las APIs
  de extensión no implementadas en Android no se presumen compatibles.

## 3. Arquitectura

```text
Android system / window-manager capabilities
                  │
       Window + input capability observer
                  │
         Archium Desktop Policy
          ├── UI mode: AUTO / ARC / MOBILE
          ├── per-navigation RDS + site override
          ├── viewport, scale, autosizing, zoom
          └── shortcuts / input compatibility
                  │
          Chromium native stack
   TabModel ── WebContents ── Blink/Viz/Skia
                  │
        Android graphics / GPU / display
```

**Invariantes de diseño:**

- Un solo motor Chromium; **no** crear una alternativa WebView.
- Una sola fuente de verdad para preferencias, estado de sitio y dimensión
  efectiva de ventana. No duplicar lógica Java/C++ que diverja.
- Aislar adaptaciones OEM detrás de detección de capacidades, con fallback.
- No interferir con el contenido web mediante inyección global CSS/JS para
  simular escritorio.
- Conservar sandbox, site isolation, navegación segura, permisos y actualizaciones
  de seguridad; optimizar nunca justifica desactivar mitigaciones.
- La interfaz Arc y sus animaciones tienen presupuesto propio y no pueden
  degradar de forma sistemática el render del contenido.

## 4. Benchmark reproducible y criterio de aceptación

**No hay cifras de mejora verificadas a 2026-10-12.** Crear el baseline antes
de establecer umbrales numéricos definitivos. Comparar **Archium actual,
Archium candidato, Chrome para Android y Samsung Internet**, en el **mismo
dispositivo, red, versión de SO, temperatura y modo de pantalla**, documentando
versiones, energía, caché y fecha. Samsung Internet es la referencia de UX,
no un sustituto de un benchmark del mismo motor.

| Métrica / escenario | Cómo medir | Gate inicial de R1 |
| --- | --- | --- |
| Arranque frío/caliente | Instrumentación startup + trazas | Sin crash; no regresión sostenida vs baseline Archium |
| Carga desktop | LCP, INP, CLS cuando aplique; Navigation Timing; trazas | Sin regresión sostenida; señales desktop y layout correctos |
| Scroll de páginas densas | Frame pacing, janky frames, input-to-frame, Perfetto | Investigar cualquier regresión significativa |
| 1/5/10/20 pestañas | PSS/RSS y memoria de procesos, descartes, switch latency | Sin pérdida de sesión ni descarte espurio de foreground |
| Animación sidebar + página | Tracing GPU/UI, overdraw y repintados | Sidebar no provoca repintado permanente de página |
| Resize/maximizar/mover display | Video/capturas, bounds CSS y prueba funcional | Sin crash, franjas ni controles tapando contenido |
| Video/WebGL/canvas | Decodificación, CPU/GPU, frames perdidos | Sin fallback forzado evitable; reproducción correcta |
| Teclado/mouse/extensiones | Matriz manual + automatización | Comandos existentes no regresan |

**Protocolo mínimo:**

1. Conjunto fijo de páginas: sitio de lectura, página responsiva, hoja de
   cálculo o editor web, web app compleja, video, canvas/WebGL y formulario.
   No publicar datos privados o cookies del usuario.
2. Mínimo **5 repeticiones por combinación** cuando sea viable, distinguir
   cold/warm y caché habilitado/deshabilitado; registrar mediana, p95 cuando
   haya muestras suficientes y dispersión, sin presentar precisión ficticia.
3. Ejecución en ventana compacta, desktop parcial, desktop maximizada y
   cambio de display. Comparar únicamente condiciones equivalentes.
4. Registrar logs/trace con identificadores de build/commit/driver, evidencia
   visual y una tabla de `PASS / FAIL / BLOCKED / NOT RUN`.
5. Cualquier regresión de crash, seguridad, perfil o pérdida de datos
   **bloquea** R1, aunque los FPS promedio mejoren.
6. Googlebook OS y Motorola quedan **BLOCKED / NOT RUN** mientras no
   exista prueba real suficiente; no extender el PASS de DeX a otros OEM.

## 5. Ejecución por etapas (sin builds prematuros)

| Etapa | Alcance | Condición de salida |
| --- | --- | --- |
| **R1.0 — Runtime baseline** | Cerrar crash DeX de omnibox/toolbar, verificar APK instalable y flujos vitales; recopilar medidas actuales | APP_RUNTIME PASS + baseline archivado |
| **R1.1 — Desktop page policy** | RDS/UA/Client Hints/viewport/zoom/resizing consistentes y overrides de usuario | Pruebas sitio+ventana+perfil y UI móvil sin regresiones |
| **R1.2 — GPU & rendering** | Trazas de compositor y correcciones dirigidas por evidencia | Mejoras cuantificadas, sin flags GPU inseguros |
| **R1.3 — Resource management** | Tab lifecycle, memoria, caché y latencia de navegación | Métricas reproducibles y conservación de sesión |
| **R1.4 — Cross-OEM acceptance** | DeX, Googlebook OS, Motorola, mouse/teclado y multiwindow | Matriz con evidencia por plataforma; bloqueos explícitos |

**Reglas de implementación y CI:**

- Esta entrega es **solo documentación**: no modifica código, argumentos GN,
  motor, APK ni workflows y **no autoriza** lanzar un nuevo build.
- Antes de cada cambio: leer HEAD, preservar checkpoints reutilizables,
  identificar targets tocados, escribir prueba RED, reparar, validar GREEN y
  comprobar diff. No repetir compilaciones completas a ciegas.
- Conservar la revisión Chromium fijada para las reparaciones actuales;
  proponer actualización de motor por separado, con revisión de seguridad y
  coste de compatibilidad.
- Usar compilación incremental/checkpoint solo si hashes, SHA de fuente y
  procedencia coinciden; fallar cerrado si el checkpoint no es compatible.
- No marcar éxito sin artefacto verificable **y** runtime en dispositivo.
- Mantener las ramas `feat/arc-desktop` y `main` intactas salvo orden
  posterior explícita. Una futura integración debe revisarse antes del merge.

## 6. Fuentes y trazabilidad

- [Diseño Arc/desktop](design.md).
- [Investigación real de input, RDS y zoom en Chromium 157](investigacion-desktop-input-2026-10-06.md).
- [Estado de implementación / advertencias históricas](archium-current-handoff.md).
- [Verificación de runtime R3, 2026-10-12](ARCHIUM_R3_VERIFICACION_2026-10-12.md).
- [Plan y hallazgos R4, 2026-10-12](ARCHIUM_R4_FIXES_VISUALES_2026-10-12.md).
- [Instrucciones oficiales de compilación de Chromium Android](https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md).
- [Guía de rendimiento de Chrome / DevTools](https://developer.chrome.com/docs/devtools/performance/).

**Definición de terminado:** Archium ejecuta navegación desktop coherente,
con calidad medible de representación y respuesta, sin romper la UI móvil ni
las funciones nativas Chromium, con pruebas reales por plataforma y sin
presentar un build exitoso como aceptación de producto.
