# Parejas, omnibox y sidebar — Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans or superpowers:subagent-driven-development; execute task-by-task with RED/GREEN.

**Goal:** conservar múltiples parejas, resolver el primer clic de omnibox y aplicar los siete refinamientos GO de sidebar.
**Architecture:** registro de asociaciones por TabModel/ventana independiente de la presentación; proyección de filas sobre TabModel nativo. Reutilizar candidato omnibox y estilos nativos.
**Tech Stack:** Chromium Android Java, PropertyModel, RecyclerView, Robolectric y probes host existentes.
**Spec:** ../specs/2026-10-21-persistent-split-pairs-design.md; ../../validation/R4_VISUAL_LINK_HOVER_FEASIBILITY.md; TODO.md próxima tanda.

## Global Constraints
- Pin Chromium 157.0.8086.0, package, GN args y toolchain intactos.
- No Amazon, Link Hover Preview, QEMU, cambios de compositor ni builds limpios.
- No despacho de Actions ni modificación del monitor en esta implementación.
- Colores, ancho, radios, botones, identidad y pestañas nativas conservados.
- Estado local/host no acredita aceptación Galaxy de una APK nueva.

## Review Focus
- Selección externa no disuelve asociaciones ni roba foco.
- Cerrar/mover miembro inactivo no selecciona superviviente ni afecta otras parejas.
- Callbacks de favicon y modelos reciclados no mezclan parejas/perfiles.
- Proyección y reorder resuelven IDs actuales, sin índices viejos ni filas duplicadas.
- Incógnito/modelo restaurado no filtran asociaciones ni fuerzan selección obsoleta.

### Task 1: registro y presentación
Files: ArcSplitPairStore.java (nuevo), ArcSplitViewCoordinator.java, ArcSplitViewCoordinatorTest.java, scripts/test-robolectric-split.py.
Interfaces: getPairSnapshot() devuelve asociaciones; setPairsChangedCallback(Runnable); setPairCompatibility(BiPredicate<Tab,Tab>); selectPair(int memberId) restaura último panel activo; isPairMember(int id).
- [ ] RED: A/B→C→A/B y A/B+D/E conservan ratio/activo; cierres inactivos y migración no roban selección.
- [ ] Implementar store, suspensión/presentación, serialización/migración, observación y limpieza.
- [ ] GREEN: probe controller; documentar límites del runner local.

### Task 2: proyección nativa de parejas
Files: TabListMediator.java, VerticalTabListCoordinator.java, TabProperties.java, TabVerticalViewBinder.java; conexión ArcDesktopCoordinator.
Interfaces: proveedor por ventana/TabModel, fila estable por pareja; selección/contexto/cierre usan miembro activo y ambos IDs disponibles.
- [ ] RED: una fila por pareja, títulos/logos y selección de segundo miembro; compatibilidad Space/pinned/grupo y drag.
- [ ] Implementar propiedades/proyección y actualización de filas sin propiedad de Tabs paralela.
- [ ] GREEN: probes relevantes, regresiones y preparación SDK37.

### Task 3: refinamiento visual
Files: ArcDesktopAppearance.java, TabVerticalViewBinder.java y ArcDesktopCoordinator.java según necesidad; pruebas de estado/sidebar existentes.
- [ ] RED: activo+hover/foco, seleccionado sin foco, fallback/título reciclado, microanimación cancelada.
- [ ] Implementar selección, separadores, tooltip nativo, normalización favicon, borde interior, Space actual y microanimación acotada.
- [ ] GREEN: pruebas UI de vistas reales; sin cambios de geometría/paleta.

### Task 4: candidato omnibox, gates y entrega
Files: candidato LocationBarLayout/UnitTest ya presente, parche/upstream-files, TODO e informe.
- [ ] Revisar candidato y ejecutar regresiones address popup, split, helpers, host, preparación SDK37/parche reproducible.
- [ ] Revisión completa y correcciones justificadas RED/GREEN.
- [ ] Actualizar TODO: tachar sólo implementación demostrada; Galaxy y build quedan pendientes.
