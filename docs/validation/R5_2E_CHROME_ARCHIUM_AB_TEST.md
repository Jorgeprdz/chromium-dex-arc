# R5.2E — Chrome vs Archium: INCONCLUSIVE

Dispositivo real SM-S931B / Galaxy S25, ADB autorizado `emulator-5554`; 2026-10-19.
Worktree forense HEAD `1315f5b` (posterior al `20da9cd` indicado); código sin cambios.
Archium: 157.0.8086.0, versionCode 808600074; APK documentada del run 39296066030.
Chrome estable instalado: 149.0.7827.102, versionCode 782710233.
Captura Chrome: 2026-10-19T20:27:01.952Z–2026-10-19T20:27:08.942Z; Archium: 2026-10-19T20:27:08.945Z–2026-10-19T20:27:15.096Z.
URL exacta en ambos: https://www.amazon.com.mx/; ventanas DeX, UA de escritorio.
No se cambió modo, zoom, flags, cookies, configuración, perfiles ni datos personales.
Inicio scrollY=0; gesto mouse de 600 CSS px a 600 px/s; espera posterior 1.2 s.
Chrome: viewport 2000×962, DPR 1.20000005, visualViewport.scale=1; scroll final 0.
Archium: viewport 2256×1330, DPR 0.96068305, visualViewport.scale=1; scroll final 599.5734.
**Chrome: INCONCLUSIVE.** Amazon mostró «Continuar a Compras», no el catálogo; no se pulsó.
**Archium: FAIL.** Imágenes negras, texto repetido/superpuesto y residuos tras scroll.
Archium: 32 imágenes totalmente visibles, las 32 complete/naturalWidth>0; no implica píxeles correctos.
Bloqueo principal: documentos distintos; Chrome no alcanzó contenido de catálogo ni scroll equivalente.
Diferencias adicionales: versión Chromium, UA Linux/CrOS, viewport/DPR y backend; orientación horizontal.
GPU Chrome: Adreno 830, ANGLE OpenGL ES 3.2, Skia GaneshGL.
GPU Archium: Adreno 830, ANGLE Vulkan 1.3.284, Skia GraphiteDawnVulkan.
Composición GPU y rasterización: enabled/enabled en Chrome; enabled/enabled en Archium.
Browser.getBrowserCommandLine no disponible en ambos; no se afirman argumentos efectivos no observados.
Raster opcional: OMITIDO; no hay mecanismo previamente verificado de argumentos temporales y reversión.
No se desactivó raster GPU ni composición GPU. Sin tests host, nueva fixture, auditoría Surface, patch o build.
Capturas privadas CDP antes/después: `/workspace/macdesk-maintenance/archium-r52e-ab/{chrome,archium}-{before,after}.PRIVATE.png`.
Capturas físicas adicionales: mismo directorio, `{chrome,archium}-physical.PRIVATE.png`; no se equiparan a CDP.
Chrome después SHA-256: `9b0286947bdea1059512db4375ff01fe3f686dc1ae78ec572666e8ccd0e89080`.
Archium después SHA-256: `fd41e6a554a42a49c1b910978d7d2d77f28b3e096c4a3e91937a6fe4706d16ff`.
Hipótesis Graphite/Dawn/texturas vs Viz/buffers: ninguna gana o pierde apoyo causal con este A/B bloqueado.
No procede clasificar ARCHIUM_SPECIFIC_DIFFERENCE ni SHARED_GRAPHICS_FAILURE_CANDIDATE.
Única recomendación: resolver manualmente la pantalla previa de Amazon en Chrome antes de autorizar otro A/B.
**Decisión final: INCONCLUSIVE.** Se detiene la prueba, sin otra campaña ni modificación recomendada.
Fix de diálogos 5184755, checkpoints y supervisor intactos; forwards propios retirados. Sin commit de producción.
