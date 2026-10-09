# ARCHIUM — Prompt maestro consolidado de fixes visuales R3

**Fecha:** 2026-10-09  
**Repositorio:** `Jorgeprdz/chromium-dex-arc`  
**Rama de trabajo:** `feat/arc-desktop`  
**Alcance:** refinamiento de interfaz Arc en Archium para Samsung DeX, sin reemplazar arquitectura ni funciones.  
**Modo de ejecución futura:** `INSPECT → COMPARE → PATCH → TEST → RE-AUDIT → FIX → RETEST → REPORT`.  
**Estado de este documento:** especificación para trabajo posterior; el commit de este documento **no autoriza ejecutar fixes ni iniciar builds**.

## 0. Contexto y fuentes de referencia

Referencias visuales suministradas en la conversación, que pueden no estar versionadas en el repositorio:

- `91725.webp`: Arc original en macOS, material translúcido y wallpaper de tonos anaranjados.
- `91962.jpg`: Archium anterior (gris), antes de los ajustes principales.
- `92061.jpg`: Archium intermedio, con nuevos controles.
- `92459.jpg`: Archium R3, versión más reciente usada para la auditoría.
- Recortes adicionales del **encuentro inferior** entre sidebar y visor, donde aparece una pequeña cuña triangular.

**Advertencia de comparación:** las capturas tienen tamaño de ventana, densidad visual, página web y sistema operativo distintos. Las medidas en píxeles de imagen **no son valores dp**. No convertirlas en dimensiones absolutas de Android ni tratar el CSS de los sitios visitados como parte de Archium.

**Corrección fundamental de interpretación:** el color naranja/coral que aparece en Arc original **se debe a la apariencia translúcida/vibrancy sobre el fondo de pantalla naranja de macOS**, no a que el tema del navegador necesariamente sea un gradiente naranja fijo. Replicar el **material** y su adaptación al backdrop, no pintar el resultado de una captura.

**Restricción fundamental de geometría:** el usuario ha ajustado manualmente el ancho de la sidebar. **NO** compararlo como defecto ni restablecerlo a 334 px, 240 dp u otro número tomado de las referencias. Conservar el resize, las preferencias y el ancho seleccionado.

## 1. Lo que ya está mejor y debe preservarse

La última captura R3 muestra:

- Back / Forward / Reload con iconos minimalistas, sin cuadrados sólidos permanentes.
- Omnibox integrada en sidebar, con dominio y acción de favorito.
- Pestaña activa como cápsula blanca, claramente diferenciada.
- Filas inactivas más limpias, sin botones de cierre permanentes.
- Tres mosaicos de acceso rápido visualmente más uniformes.
- Selector de espacio «Personal» simplificado a una etiqueta.
- Sidebar con gradación gris-lavanda actual y resize manual.
- Controles inferiores y web viewport con esquinas redondeadas.

**No reconstruir desde cero, no duplicar componentes, no volver al diseño del build anterior.** Antes de editar, inspeccionar la implementación y comprobar qué ya funciona.

## 2. P0 — Reparar el triángulo en la unión inferior sidebar ↔ visor web

**Fallo observado:** abajo, en la esquina **inferior izquierda del visor web** junto a la sidebar, queda una pequeña cuña/triangulito de otra superficie. Rompe la continuidad del encuentro entre ambos componentes.

**Hipótesis a verificar, no causa confirmada:** interacción entre `bottom-left border-radius`, clipping, paddings/insets, elevación, antialiasing o el color de la superficie raíz expuesto bajo la esquina.

**Pasos obligatorios:**

1. Inspeccionar la jerarquía real de la ventana, rail/sidebar, viewport, contenedor de Chromium y superficies raíz; identificar quién dibuja cada píxel de la unión.
2. Verificar si la esquina es interna o parte del redondeo externo que se quiere conservar.
3. Aplicar la corrección **en el origen de la geometría/composición**: alineación exacta, clip correcto, radios coherentes o fondo subyacente consistente.
4. Si se demuestra que el radio inferior izquierdo del visor es el responsable y no es necesario para la estética, eliminar **solo ese radio interno**; **no** hacerlo a ciegas.
5. Conservar los radios de las esquinas **exteriores** de la ventana y la esquina superior izquierda del visor cuando corresponda al diseño.
6. No agregar triangulitos pintados, overlays opacos ni parches de color que tapen el fallo de forma artificial.

**Aceptación:** cero triángulos/huecos/líneas de 1 px en el encuentro inferior; sin flashing al redimensionar, mover, maximizar o restaurar la ventana; con fondos claros, oscuros y variables; sin clipping de la página ni alteración del comportamiento de la sidebar.

## 3. P0 — Material de sidebar: translucidez real estilo Arc, no naranja fijo

**Problema:** Archium muestra una superficie gris-lavanda que puede percibirse plana; Arc macOS obtiene parte de su tono del wallpaper a través de su material translúcido.

**Investigar primero las capacidades reales en la implementación Chromium Android Desktop y compositor de Samsung DeX:**

- Alpha/translucidez real por píxel de la superficie/window cuando esté soportada.
- Blur-behind o background blur de Android/WindowManager y restricciones OEM.
- Composición y clipping de la sidebar sin hacer transparente el contenido web.
- Influencia de la parte **realmente visible** del wallpaper/escritorio detrás de la ventana.
- Legibilidad y contraste del texto sobre backdrops cambiantes.
- Interacción con material claro/oscuro y color personalizable ya previsto en `docs/design.md`.
- Consumo GPU, rendimiento, batería, overdraw y fluidez durante resize.

**Jerarquía de solución:**

A. Translucidez real + blur del escritorio **solo si** DeX/compositor realmente lo permiten.  
B. Translucidez real con una capa de contraste, sin blur cuando blur no esté soportado.  
C. Fallback opaco con tinte configurable/dinámico del wallpaper, cuando pueda obtenerse legítimamente, etiquetado como fallback y **no** como translucidez real.

**Restricciones:** no copiar naranja/coral de forma fija; no utilizar screenshots frecuentes, polling ni MediaProjection continua; no usar falsos fondos capturados; no aplicar blur a pantalla completa; no requerir root/Shizuku; no convertir el WebView/Chromium en una superficie translúcida que afecte la página; no modificar controles nativos de DeX.

**Aceptación:** probar wallpaper azul, naranja, claro y oscuro, además de mover la ventana por zonas distintas. Documentar si el material cambia **en tiempo real** con el backdrop o si se trata solamente de un color de tema/dynamic color. Si DeX no expone el efecto real, reportar la limitación y conservar el fallback seguro.

## 4. P0 — «Nueva pestaña» integrada en la lista

**Estado R3:** signo `+` aislado y centrado bajo las pestañas abiertas.

**Referencia Arc:** acción «New Tab» como fila con signo + y etiqueta antes de las pestañas.

- Reutilizar la acción nativa de creación, sin duplicar estado ni crear una segunda ruta funcional.
- Mostrar **«Nueva pestaña»** como fila alineada con las demás, idealmente al inicio de la sección de pestañas.
- Emplear padding, tipografía, radio y estados hover/focus/pressed consistentes.
- Si sidebar compacta no permite etiqueta, conservar al menos un control comprensible, accesible y con tooltip.
- Conservar shortcuts y foco existentes; no alterar TabModel ni la separación de perfiles.

**Aceptación:** acción visible y usable con mouse, teclado y touch, en tamaños compactos/intermedios/amplios.

## 5. P0 — Encabezado del espacio y jerarquía de secciones

**Estado R3:** «Personal» ya es discreto, pero la búsqueda a la derecha y la transición a la lista carecen de una jerarquía tan clara como la de Arc.

- Mantener el selector de espacio en texto, con su función real y affordance de desplegable.
- Refinar baseline, distancias verticales, separación entre pinned tiles, espacio y lista.
- Integrar búsqueda en una región de herramientas coherente, sin perder funcionalidad.
- Emplear separadores sutiles solo donde clarifiquen niveles de navegación.
- Preservar semántica de Spaces, favoritos, fijados, carpetas y tabs; no confundir un control con una carpeta.

**Aceptación:** el usuario reconoce intuitivamente espacio activo, accesos fijados, nueva pestaña y pestañas abiertas, sin controles aislados ni separadores excesivos.

## 6. P1 — Filas de pestañas y selección R3

**Estado R3:** la cápsula blanca de pestaña activa es un avance. **NO REVERTIRLA.**

- Crear/ajustar tokens coherentes de altura, radio, padding, distancia favicon–texto y tipo de letra.
- Mantener alto contraste entre active e inactive; hover/focus visibles en DeX.
- Mostrar cierre contextualmente con mouse cuando sea adecuado, con alternativa accesible para touch/teclado.
- Truncar títulos con elipsis sin cortar favicons ni acciones; evitar diferencias bruscas de ancho entre estados.
- No deducir que pestañas del mismo sitio están duplicadas accidentalmente: pueden ser dos instancias legítimas.
- No obligar a ensanchar la sidebar para arreglar textos pequeños.

**Aceptación:** selección clara, títulos legibles, sin saltos, overlap ni botones inalcanzables.

## 7. P1 — Header, omnibox y navegación

**Estado R3:** Back/Forward/Reload ya usan un lenguaje limpio. Preservar.

- Inspeccionar alignment y tamaños ópticos.
- Revisar hover/disabled/focus y tooltips.
- Mantener la omnibox flexible, con URL truncada y acciones sin superposición.
- Preservar navegación real, favoritos, autocompletado y shortcuts nativos disponibles.
- No volver a dibujar botones cuadrados grandes ni insertar otra barra web redundante.
- No ampliar el alcance a cambio automático de user-agent, política de zoom o text autosizing, expresamente diferidos en la documentación del proyecto.

## 8. P1 — Mosaicos superiores y controles inferiores

- Identificar la **función real** de cada uno de los tres mosaicos superiores; no asumir que el engranaje es un bookmark.
- Ajustar tamaños ópticos, radios, gutters, padding, estados y comportamiento responsive.
- Normalizar **alineación** de controles del footer, manteniendo identificaciones de marca si son necesarias.
- Conservar accesos funcionales, menú, búsqueda y funciones de extensiones donde estén conectadas.
- No reemplazar acciones con iconos decorativos para imitar la captura de macOS.

## 9. P1 — Contenedor web e insets

- Revisar origen del margen/franja superior interna y su interacción con viewport.
- Conservar radios exteriores correctos y conexión inferior corregida.
- No tocar el CSS de Rappi, Seguros Monterrey u otras páginas; sus márgenes, banners y columnas no son «fallos del navegador».
- No inyectar CSS ni alterar zoom/User-Agent solo para igualar páginas distintas.
- Evitar WebView/viewport recargado innecesariamente durante resize, maximización o cambio de tema.

## 10. P0 — Preservación estricta de resize y estado

**El usuario decide la anchura de la sidebar**: no establecer valor fijo de la captura ni sobrescribir preferencias persistidas.

Validar anchos compacto, intermedio y amplio; resize por arrastre; maximizar/restaurar DeX; resolución/escala diferente; scroll de muchas pestañas; textos largos y menús cerca de bordes.

Durante resize **no debe haber** recargas, crash, pérdida de pestañas, clipping, controles solapados, reordenamientos inesperados ni saltos arbitrarios del ancho.

Preservar las funciones Chromium/Archium, extensiones, navegación, historial, bookmarks, perfiles normales/incógnito y almacenamiento. No modificar el gestor de contraseñas ni CSV por este prompt.

## 11. Exclusiones y seguridad del cambio

- No dibujar traffic lights de macOS; cerrar/minimizar/maximizar lo gestiona Android.
- No modificar taskbar, system bars ni WindowManager fuera del alcance imprescindible y demostrado.
- No recrear el navegador en un WebView separado; utilizar la estructura real del fork.
- No borrar/reescribir cambios que Codex u otro agente haya dejado en el workspace.
- No usar acciones GitHub, publicar APK, instalar en dispositivo, cambiar permisos, hacer merge o lanzar compilaciones costosas **sin autorización posterior**.
- No fingir paridad completa con Arc ni confundir screenshots con validación runtime.

## 12. Protocolo de trabajo futuro para Codex u otro agente

1. Confirmar remoto `Jorgeprdz/chromium-dex-arc` y rama activa `feat/arc-desktop`; inspeccionar HEAD y `git status` antes de escribir. Si existen cambios locales, preservarlos.
2. Leer `docs/design.md`, `docs/archium-current-handoff.md`, `docs/Archium-PROMPT-RECUPERACION.md` y este documento. Si docs anteriores describen estados históricos, **verificar el código vivo** en lugar de asumir que siguen vigentes.
3. Ubicar los componentes reales de Chromium/Arc y sus tests; no inventar rutas o clases ni editar un checkout de Chromium inexistente.
4. Separar los fixes pequeños y reversibles. Orden recomendado: **triángulo inferior → preservar resize/estado → New Tab/jerarquía → pestañas/header/footer → material translúcido**, dejando el blur dependiente del compositor como investigación/prototipo aislado.
5. Para cada fix: anotar causa raíz, diff acotado, pruebas apropiadas, potenciales regresiones y evidencia visual si se dispone de ejecución gráfica.
6. Ejecutar las pruebas locales disponibles que no impliquen nuevos gastos/runs. No apagar tests ni maquillar errores para obtener verde.
7. Cuando las pruebas requieran APK, DeX, instrumentación nativa o runner no disponibles/autorizados, marcar **BLOCKED**, nunca PASS.
8. Re-auditar todo cambio contra R3 y la referencia Arc. Iterar hasta agotar defectos reproducibles y verificables del alcance, sin entrar en rediseños ilimitados.
9. Reportar antes/después, archivos modificados, SHA/estado git, PASS/PARTIAL/FAIL/BLOCKED, limitaciones OEM y cualquier riesgo de regresión. Dejar la auditoría final independiente para Codex si se quiere reservar su cuota.

## 13. Matriz de aceptación

| ID | Tema | Prioridad | Evidencia mínima |
|---|---|---|---|
| R3-01 | Cuña inferior izquierda eliminada | P0 | Captura ampliada en wallpaper claro/oscuro y durante resize |
| R3-02 | Resize y preferencia conservados | P0 | 3 anchos, mover/maximizar/restaurar, sin salto ni pérdida |
| R3-03 | Nueva pestaña como fila | P0 | UI + creación real con mouse/teclado |
| R3-04 | Jerarquía Espacio / secciones | P0 | Captura y comprobación funcional |
| R3-05 | Translucidez real o fallback honesto | P0 | Matriz wallpapers + limitación DeX documentada |
| R3-06 | Selección y densidad de tabs | P1 | Active/inactive/hover/focus, títulos largos |
| R3-07 | Header y omnibox | P1 | Foco, navegación y estado disabled |
| R3-08 | Pinned tiles | P1 | Funciones reales y responsive |
| R3-09 | Footer controls | P1 | Alineación, tooltips, acciones |
| R3-10 | Viewport/insets y clipping | P1 | Sin franjas redundantes ni recorte del sitio |
| R3-11 | Sin regresiones de estado | P0 | Pestañas, navegación, favoritos, perfiles |
| R3-12 | Controles nativos intocados | P0 | DeX resize y decoraciones sin duplicados |

Estados permitidos: **PASS / PARTIAL / FAIL / BLOCKED**, sustentados con evidencia.

## Definición de terminado

Archium debe ofrecer la jerarquía visual y sensación de material de Arc, respetando su funcionamiento nativo en Android/DeX. El resultado **no** exige copiar una paleta naranja ni equiparar el ancho de sidebar al screenshot de macOS. La unión inferior sidebar–visor debe ser geométricamente continua, sin «triangulito».

**REGLA FINAL:** NO RECONSTRUIR. REFINAR. PRESERVAR LOS AVANCES Y EL RESIZE. INVESTIGAR EL MATERIAL REAL. ARREGLAR LA CUÑA INFERIOR EN SU CAUSA. NO DECLARAR PASS SIN PRUEBAS.
