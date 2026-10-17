# Archium — TODO pendiente para Codex (2026-10-17)

**Estado:** PENDIENTE / BACKLOG. Documento de seguimiento, no equivale a reparación implementada ni a prueba superada.

**Repositorio:** `Jorgeprdz/chromium-dex-arc`  
**Rama de trabajo de este TODO:** `assistant/archium-r5-arc-experience`  
**Entorno observado:** Samsung Galaxy S25, Android, Archium; validar tanto modo teléfono como Samsung DeX.  
**Motor de referencia documentado:** Chromium 157.0.8086.0 (confirmar pin y HEAD efectivos antes de trabajar).  

> **Orden:** estabilidad/renderizado primero; después pulido estético. Evitar un build pesado antes de aislar causas y probar cambios pequeños. No modificar `main` ni `feat/arc-desktop` durante el diagnóstico sin autorización.

## P0 — R5.1: estabilidad del contenido, compositor y ventanas

### [ ] P0-01 — Scroll corrupto / imágenes y texto «barridos»

**Reproducción reportada (17-oct-2026):** al desplazarse en `amazon.com.mx`, tarjetas de productos, fotografías y tipografías aparecen arrastradas/deformadas, superpuestas o como bloques negros. Hay captura aportada en la conversación del reporte; **no está anexada a este repositorio**.

**Investigar:** ruta Blink → Viz → Skia → GPU/Surface, invalidación/rasterización de tiles, buffers, overlays, `SurfaceView`, clipping y transformaciones del contenedor web; evaluar interacciones con `ArcDesktopCoordinator`. No atribuirlo de entrada al CSS de Amazon.

**Aceptación:** scroll repetido sin artefactos, imágenes ni glifos negros/duplicados; sin regresiones de FPS, foco o consumo en teléfono/DeX. Comparar en el mismo equipo con Chrome Android y, de ser posible, Samsung Internet.

### [ ] P0-02 — Fondo oscurecido sin diálogo visible

**Reproducción reportada:** un mensaje emergente activa el oscurecimiento del fondo (`scrim`), pero el cuadro con el mensaje no aparece.

**Investigar:** distinguir `alert/confirm/prompt` JavaScript, `<dialog>` web y diálogos nativos Chromium/Android; revisar jerarquía de ventanas, tokens, elevación/z-order, overlay, coordenadas, insets, reparenting y foco (también con DeX).

**Aceptación:** mensaje y acciones visibles y operables, restauración del foco y retiro del oscurecimiento tras cerrar. Verificar móvil y escritorio, con teclado/mouse y toque.

### [ ] P0-03 — Desaparece el contenido web y solo queda la title bar

**Reproducción reportada:** ocasionalmente desaparece toda la zona del sitio y permanece únicamente la barra superior/título de Archium.

**Investigar:** pérdida/recreación de Surface, `surfaceCreated/surfaceDestroyed`, `WebContents` detach/attach, tamaño 0, recortes, occlusion, pestaña/renderer suspendido, cierre de renderer, GPU process loss, resize, minimizar/restaurar y cambios teléfono↔DeX. No confundir la UI nativa que permanece visible con un motor web sano.

**Aceptación:** superficie y pestaña recuperables en transiciones, resize y cambios de foco sin perder navegación/estado/formularios. Capturar logs del proceso y del compositor; no afirmar causa sin evidencia.

### [ ] P0-04 — Causa raíz, pruebas y entrega segura

- [ ] Registrar HEAD, APK/build instalado, versiones de Android, forma de ventana y condiciones de reproducción.
- [ ] Montar una página determinista con imágenes, tipografías, scroll, transform/sticky/fixed, canvas, `alert/confirm/prompt` y `<dialog>`.
- [ ] Comparar teléfono / DeX, ventanas estrechas / maximizadas, pestañas normal / incógnito; realizar scroll, abrir/cerrar popup, resize, minimizar/restaurar y volver a foco.
- [ ] Recolectar logs/trazas (GPU, renderer, compositor y Android WindowManager) eliminando tokens, cuentas y contenido privado.
- [ ] Mostrar RED antes del fix y GREEN después con pruebas relevantes; tests host no sustituyen validación visual de APK real.
- [ ] Arreglar mínimamente el componente responsable, sin workarounds globales ni cambios visuales ajenos.
- [ ] Usar build incremental **solo después** de diagnóstico, preflight, SHA exacto, gates y checkpoint compatible; solicitar aprobación antes de despachar el workflow.

**Prohibido como «solución» rápida:** desactivar GPU/aceleración global, forzar ANGLE/Vulkan indiscriminadamente, reemplazar Chromium por WebView, inyectar CSS/JS global para parchear sitios, ignorar crasheos o borrar cachés/checkpoints sin prueba.

## P1 — R5.2: pulido visual acordado el 16-oct-2026

- [ ] **Sidebar comprimida:** revisar ancho útil, aire entre pestañas, iconos y controles, especialmente en modo compacto y ventanas estrechas.
- [ ] **Jerarquía y consistencia visual:** homologar radios, espaciados, hover, foco, contraste y estado de pestaña seleccionada; evitar densidad excesiva.
- [ ] **Contenido web aparentemente pequeño:** medir viewport CSS, device scale, zoom, RDS/UA Client Hints y `text autosizing` antes de cambiar escalas; respetar elección del usuario y evitar zoom forzado.
- [ ] **Controles de ventana:** mejorar visibilidad, contraste, hit targets y alineación sin tapar contenido ni interferir con controles nativos de Android/DeX.
- [ ] **Expandir/contraer sidebar:** pulir animación, reflow, controles y persistencia, sin saltos de viewport ni recreación de pestañas.
- [ ] **Zona inferior/footer:** alinear iconos/acciones, espacios, clipping y remanentes visuales del borde inferior (incluida la cuña previamente reportada cuando corresponda).

**Decisiones visuales a preservar:** color durazno aprobado, identidad Arc/Archium Portal, pestañas verticales, estética ligera. No añadir sombras pesadas, bordes excesivos ni cristal/blur costoso sin soporte comprobado. Conservar navegación real de Chromium, bookmarks, perfiles y extensiones.

## Orden de ejecución cuando Codex esté disponible

1. **Auditar estado real del repo**, HEAD y de la APK que muestra el bug; no asumir que la rama de documentación coincide con los binarios instalados.
2. Reproducir, medir y aislar individualmente P0-01 / P0-02 / P0-03; determinar si comparten causa o requieren arreglos independientes.
3. Tests RED → fix mínimo → GREEN; revisión de diffs, memoria, energía y regresiones de interfaz móvil.
4. Hacer una sola solicitud de build incremental cuando haya evidencia suficiente y autorización explícita; validar APK en Galaxy S25 y DeX.
5. Cerrar P0; **solo entonces** trabajar P1 por lotes pequeños verificables.

**Documentos relacionados:** `docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md` y verificaciones R3/R4 en `docs/` cuando existan en la rama. Sus planes no constituyen pruebas de que P0 ya esté arreglado.
