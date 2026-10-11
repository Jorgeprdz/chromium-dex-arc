# Archium R4 Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rehacer los cambios posteriores al respaldo en una nueva rama, preservando Archium y eliminando el flujo de CI acumulado.
**Architecture:** Base 51e5ed4 más componentes Java acotados y un orquestador de fases independiente. Reutilizar solo assets y utilidades verificadas con procedencia explícita.
**Tech Stack:** Java Android, Python/Bash, GN/Ninja/Siso, GitHub Actions, AAPT2.
**Spec:** docs/superpowers/specs/2026-10-11-archium-recovery.md

## Task 1: Base, inventario y trazabilidad
- [x] Crear rama nueva desde el respaldo y comprobar pin/ramas protegidas.
- [ ] Registrar los deltas posteriores, primer fallo real y qué se reescribe/reutiliza.
- [ ] Guardar el reporte forense sin modificar la rama anterior.
Expected: rama nueva contiene solo cambios revisables; ningún merge masivo.

## Task 2: Flujo de compilación nuevo
- [ ] Escribir pruebas negativas de fases, SHA/branch, clean fallback, fallo y scoped JVM.
- [ ] Observar RED; escribir orquestador nuevo con restore único y fases bloqueantes.
- [ ] Workflow manual nuevo, fuente explícita, global concurrency, dos slices y reservas.
- [ ] Eliminar ejecución automática/push pesado del flujo de recuperación.
- [ ] Ejecutar pruebas de routing y JVM real; lint y commits temáticos.
Expected: primer fallo conserva exit code; ninguna fase/APK posterior ejecutada.

## Task 3: Reescritura de cambios R3 de interfaz
- [ ] Reimplementar desde la base controles nueva pestaña/navegación/foco.
- [ ] Reimplementar editor de colores en componente aislado con draft/apply/cancel/reset.
- [ ] Conservar geometría/sidebar y probar correcciones de lifecycle/viewport.
- [ ] Tests negativos de observadores, colores, foco y stale callbacks antes del fix.
Expected: sin pérdida de funciones de la base; tests host honestos y Robolectric programado.

## Task 4: Portal y recursos
- [ ] Copiar individualmente assets aprobados sin modificar blobs.
- [ ] Reutilizar herramientas verificadas de integración/content/AAPT2 y pruebas negativas.
- [ ] Probar recursos acotados con SDK37 real; programar merge Chromium como gate CI.
Expected: iconos aprobados preservados; fixture no acredita merge/APK final.

## Task 5: P0, GN/JNI y reproducibilidad
- [ ] Reimplementar display independiente de decor attach y conservar assert de release.
- [ ] Registrar pruebas Robolectric/JVM; mantener owners reales de payments/JNI.
- [ ] Corregir fixture GN con stdout/stderr visibles y tres escenarios GN reales.
- [ ] Regenerar patch/manifest dos veces mediante generador oficial y comparar hashes.
Expected: JVM y GN reales PASS; JNI real PENDING hasta restore/link.

## Task 6: Validación, revisión y publicación
- [ ] Suite host completa con SDK/GN reales; bash/compileall/actionlint/diff-check.
- [ ] Revisión independiente del diff nuevo; reparar hallazgos críticos con regresión.
- [ ] Publicar commits nuevos sin force, confirmar ramas protegidas.
- [ ] Registrar FAILED histórico; después de gates y publicación lanzar UNA corrida manual sobre SHA final y abrir monitor.
Expected: resultados observados, riesgos pendientes y checkpoints preservados.
