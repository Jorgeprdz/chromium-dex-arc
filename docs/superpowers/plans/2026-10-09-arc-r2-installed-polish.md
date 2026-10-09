# Arc Desktop visual parity R2 — corrección del APK instalado

Base `bacd31c8286c677f24e55e3a46b12d9161664abc`, repositorio real `Jorgeprdz/chromium-dex-arc`, rama `feat/arc-media-only`, mismo worktree. El anexo del usuario define el diseño y ordena implementación, commit y run. Esa autorización prevalece sobre su exclusión genérica de Actions automáticos; no se hará merge. Scope `arc-media`, passwords locales deshabilitados. Ancho manual de sidebar preservado.

Diseño: refinar controles existentes, sin segundo omnibox ni modelo de tabs. Mantener navegación, favoritos/bookmarks reales, espacios, gradiente configurable, footer y panel redondeado. Tema activo claramente iluminado, controles secundarios discretos con hover/pressed/focus, tipografía Android escalable. No cambiar sitio, zoom, UA ni decoraciones DeX.

## Trabajo y propiedad

1. **Chrome nativo y foco:** conectar ARC al supplier de supresión de la capa gráfica del toolbar; mantener caption-only mediante stacker. Limitar clipping de expansión del LocationBar a su host lateral para que la cabecera no desborde sobre pestañas. Regresiones con restores MOBILE, null state, fullscreen y motivos nativos de supresión. Responsable `r2_native_chrome`, archivos nativos Toolbar/Root/LocationBar; integración con coordinator por root.
2. **Colecciones:** identificar mosaicos reales, reemplazar ojo genérico por favicon/fallback coherente con Chromium, conservar privacidad y acciones; reducir bloques permanentes del selector de espacio y acciones, equilibrar secciones. Responsable `r2_collections`, `ArcCollectionsView` y pruebas; callbacks del coordinator integrados por root.
3. **Pestañas y material:** tokens de texto/contraste/estados, selected capsule iluminada, inactive hover/focus, cierre contextual de mouse manteniendo acceso táctil, footer/navigation coherentes. Responsable `r2_tab_style`, política/apariencia y binders nativos; llamadas header/footer integradas por root.
4. **Transición:** actualizar recorte visible e input junto con animación nativa SideUi, manteniendo sizing real, collapsed52dp y hover overlay; cero polling permanente. Root modifica solo geometría/coordinator y regresiones de contenido. No reescribir allocator ni resetear ancho del usuario.

Cada unidad usa diagnóstico ya capturado, RED contra fuente real, patch mínimo y GREEN. Conservar tests anteriores; corregir fallos nuevos y repetir suite completa tras último cambio. Integrar helpers de apariencia/callbacks secuencialmente cuando estén disponibles para evitar ediciones simultáneas del mismo archivo.

## Validación y entrega

- Patch contra Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, hashes y registro GN coherentes; probes SDK37/JDK17 con declaraciones/anotaciones reales.
- Checks obligatorios Python3.12: `ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh` y `ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar`, configurando intérprete/JDK recuperados.
- Revisión independiente del delta integral, ajustes y retest si hay blockers. Matriz R2-01..14 con evidencia y BLOCKED/PARTIAL para funciones que no puedan probarse en el APK aún no construido.
- Capturas previas y grabación: `.sync-audit/arc-next-polish-20261009/`. Referencias de archivos92061/91725 no localizadas; no inventar comparación con imágenes no recibidas.
- Dictamen de fuentes antes de commit; commit/push y un run explícito usando checkpoint verificado con productor exacto. Activar monitor600s y worker independiente autorizado de instalación/hash; después pausa por instrucción previa. No declarar validación visual posterior hasta nuevo APK.

LinkedIn sigue excluido. Los márgenes azules del sitio no se modifican. La captura y prueba mantienen las pestañas existentes, incluidas las dos del mismo portal.
