# R5.4 — reparación del gate JVM (20-oct-2026)

El [run39486593880](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39486593880), SHA `0eabba10a1e81dbb653098bcdd2c02ac5da4e47a`, terminó FAILURE, sin APK publicada/verificada. El enlace ARM64 de `libchrome.so` sí terminó y produjo `JNI_LINK_PASS=PASS` a las20:48:23Z. La suite ArcSplitViewCoordinatorTest falló después, a las20:50Z.

## Causas demostradas

- `linkOpeningCreatesNativeTabOrNavigatesNeighborWithOriginalParams` y `staleOrBlockedSourceAndExternalSchemesCannotUseLinkRoute`: GURL → LibraryLoader → ContextUtils.getApplicationContext falla por falta de preparación de Chromium. La clase usaba el runner genérico de Robolectric.
- `nativeLinkPreservesHeadersBodyAndRendererFlag`: Mockito rechaza `mock(ResourceRequestBody.class)` porque la clase upstream es final. Cada caso falló en SDK30 y36: seis fallos.
- El guard host de descubrimiento exigía el runner genérico incluso al controlador; ahora exige BaseRobolectricTestRunner en ese controlador y conserva el genérico en las suites de vistas. RED1 fallo → GREEN1/1.

El probe local anterior usaba una clase de cuerpo no final y Mockito inline; su adaptador GURL tampoco exigía preparación. Ese PASS no cubría estas diferencias de CI.

## Corrección y comprobaciones

Sólo cambia `ArcSplitViewCoordinatorTest.java` en el árbol aplicado a Chromium: usa BaseRobolectricTestRunner, que configura contexto/proceso y bibliotecas, y crea ResourceRequestBody mediante la fábrica real con un mock acotado de su interfaz Natives, restablecida en finally. Se conservan las comprobaciones de headers, identidad POST y renderer flag.

El probe ahora fuerza Mockito subclass, compila ResourceRequestBody upstream intacto y comprueba su SHA256; exige inicialización del contexto en su adaptador GURL. BaseRunner y GURL locales siguen siendo adaptadores explícitos: no demuestran carga nativa ni equivalencia completa con CI.

- RED local con esos límites:54 casos del controlador,6 fallos correspondientes a las dos causas.
- GREEN local:124/124 split; repetición final del controlador54/54.
- Preparación SDK37, sintaxis, actionlint, patch generado reproducible y diff-check:PASS.
- Suite host completa:373 casos ejecutados;372 PASS y un fallo del guard antiguo que exigía el runner genérico. Tras ajustar ese guard, repetición pertinente1/1 PASS. No se presenta esta combinación como una nueva ejecución completa de373 sin fallos. Los controles de recursos Android sí pasaron con SDK/AAPT2 configurados.
- Revisión independiente:sin Important/Critical. CI ejecuta SDK30/36 en shards separados, compatible con la restricción de sandbox del runner Chromium.
- Runner nativo completo Chromium:pendiente del nuevo run. QEMU:DISABLED_BY_USER. Aceptación visual Galaxy:pendiente.

## Reutilización y entrega

Checkpoint de origen:`archium-checkpoint-39486593880-1`; source_run_id:`39486593880`; source_commit:`0eabba10a1e81dbb653098bcdd2c02ac5da4e47a`. Cuatro grupos,25 partes,26.530.775.894bytes de archivos ZIP. Manifiesto SHA256:`5564ce7fc2b5d3273ef58ca1a88f15accaf4be199480f9b8f103baa1bd67e240`.

Metadata, identidad, grupos consecutivos y hashes de manifiesto comprobados por lectura remota acotada. Todos los bytes, espacio/inodos y configuración real del checkout deben pasar las comprobaciones de CI antes de continuar. No hay fallback limpio. Chromium157.0.8086.0/pincfd94726, GN args, toolchain, package, workflows y código de producción permanecen idénticos al checkpoint; sólo se invalida la dependencia real del test modificado.

SHA de corrección:`e5cc6a32f1038aa87024f6d5863d7cfca7d813ed`. El RUN_ID nuevo y la primera consulta del monitor se conservarán en el estado persistente `.local/state/archium-r5-progressive/state.json` y su evidencia de handoff. Se mantienen una compilación activa,600s, sin QEMU ni reparación/continuación automática; no se reinician contadores ni presupuesto.

Amazon sigue `UNRESOLVED_GRAPHICS_BLOCKER`. Ningún resultado de este informe valida cambios gráficos en el dispositivo.
