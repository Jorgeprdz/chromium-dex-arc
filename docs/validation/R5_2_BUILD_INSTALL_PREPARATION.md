# R5.2 — preparación de build e instalación

Autorización explícita: «compila e instala». Integrar el candidato sobre
`assistant/archium-r5-arc-experience` y reutilizar el supervisor independiente.
No se modifica main, feat/arc-desktop, pin, GN args, toolchain ni checkpoints.

- Base preservada: `3db367adff50d423b8c4475d10165d2790f6065a` (pestañas).
- Diálogos: `51847556e761ca0600a4aa824531e40d200fdf17`.
- Sidebar/footer/hover: `0ab6204c9e785ef4d6ce1da456070f0a24f476fe`.
- Checkpoint: `archium-checkpoint-38511423805-1`; run `38511423805`.
- Fuente: `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`.
- Manifiesto SHA256: `50d9ad33ed84646d15368c696ff74fd103a7a9ef5e5829c152c399b95ccea56f`.
- Inventario remoto: cuatro grupos no expirados, 25 partes, 26 508 245 892 bytes de artefactos.
- Revisión Chromium: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0).
- Pin de depot_tools: `8a5434051036b32412a2ecb10c213a72e3f3ccb9`.

Se verificó metadata/manifiesto remoto; los bytes completos se verifican en CI
antes de restaurar y antes de compilar. El runner debe verificar espacio e inodos,
conservar outputs, comparar args.gn y revisiones, y aplicar la transición mínima.
No se permite fallback limpio. El workflow caller existente exige la rama base
y el SHA remoto exacto; preflight no se omite para este nuevo SHA.

Reverificación local: sidebar 18/18 y gate de diálogos 18/18 bajo Robolectric;
transición de checkpoint 17/17, identidad de pestañas 5/5 y supervisor 11/11.
Preparación de 128 archivos y compilación aislada de adaptadores: PASS.
Estos resultados no equivalen a una APK ni a validación GPU/Android física.
Suite host completa reverificada: **340/340 PASS**, salida 0 (760.363s).
AAPT2 real ejecutado mediante QEMU de usuario x86; no es Android/QEMU.
GN local del sistema; CI exige reconstruir GN en el pin DEPS de Chromium.
Los eventos de captura impresos por tests del recolector son controles con
subprocesos adaptados, no nueva evidencia gráfica del Galaxy.
Logs privados: `/workspace/macdesk-maintenance/archium-r52-ui/build-handoff/`.

El supervisor conserva su ventana original de 10h, límite acumulado de seis
runs y dos reparaciones por causa; no se reinician contadores ni presupuesto.
RUN_ID, SHA final, nonce, primera consulta y sesión Termux se guardarán en
`/workspace/.local/state/archium-r5-progressive/` al verificar el despacho.
Codex termina el turno al confirmar la transferencia, sin esperar la APK.

QEMU permanece `QEMU_ABI_BLOCKED`. El supervisor existente bloquea la instalación
si se repite ese resultado, aunque el job termine success. No se elimina ese
gate ni se promete instalación sin confirmación del sistema y verificación
de hash, paquete, versión y certificado. La instalación nueva sigue PENDING.
Amazon conserva `UNRESOLVED_GRAPHICS_BLOCKER`; congelamiento reportado, sin fix.
