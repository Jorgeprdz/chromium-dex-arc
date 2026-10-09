# Archium R3.2 — Blur y selector de color (2026-10-09)

**Intención corregida:** el usuario busca **vidrio esmerilado con blur verdadero**, no un fondo transparente a través del cual se distingan los objetos del escritorio. El color naranja visto en Arc macOS procede del wallpaper y de su material, no de una paleta naranja obligatoria.

## Decisión técnica

- Preferir blur auténtico del **backdrop** solo cuando Android/DeX permita hacerlo en el área de sidebar, de forma estable y con alta legibilidad. No confundirlo con RenderEffect sobre el propio contenido.
- La compatibilidad real de ese desenfoque no se ha demostrado en el dispositivo. **No declarar que es imposible ni simularlo.**
- Hasta tener pruebas, mantener un **fallback opaco configurable**, sin capturas del wallpaper, polling, root, Shizuku ni cambios del contenido web.
- El control de color existente se amplía con **ocho colores predeterminados**, un selector arbitrario mediante deslizadores RGB y entrada HEX, y una vista previa del color efectivo. Cancelar no guarda. Restablecer recupera el color base.
- Mantener preferencias persistentes, contraste dinámico, tema claro/oscuro, pestañas, resize de sidebar, controles DeX y branding Archium Portal.

## Validación y builds

- El build que está en curso, run **37987348539**, pertenece al commit **25a065599887457cb5e716009ae4d80d9df44544**. **No incluye** los cambios R3.2 posteriores.
- No lanzar un segundo build de APK mientras siga ese run; este cambio de código requiere una compilación posterior para comprobarse en dispositivo.
- Los tests estáticos/host y los preflights verifican estructura y patch, **no** blur real ni apariencia final.
- Validar en la siguiente APK: swatches, RGB, HEX, preview exacto, Cancel/Restablecer, persistencia tras reinicio, accesibilidad y ausencia de regresión de resize.
