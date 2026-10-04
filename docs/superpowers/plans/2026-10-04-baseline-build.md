# Chromium Desktop baseline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compilar Chromium Android Desktop ARM64 sin cambios para validar el constructor gratuito.

**Architecture:** Workflow manual con revisión fija, dependencias Android descargadas por gclient y salida chrome_public_apk. Limpieza limitada a herramientas prescindibles de la VM efímera, seguida de guardia de 100 GB.

**Tech Stack:** GN, Ninja, depot_tools, GitHub Actions ubuntu-24.04.

**Spec:** ../../design.md

## Global Constraints

- Sin checkout completo en teléfono; sin servicios de pago.
- is_desktop_android=true; sin cambios al motor o soporte de extensiones.
- Esta base mantiene ID/firma originales y no se instala sobre perfiles existentes.
- Fork posterior con ID/firma propios antes de instalarlo.

## Review Focus

- Ejecución fuera de CI: abortar antes de cualquier borrado.
- Espacio insuficiente tras limpieza: abortar antes del checkout.
- Revisión equivocada: comprobar HEAD exacto antes de hooks.
- Build incompleto: no publicar prerelease sin APK no vacía.
- Base sin look Arc: identificarla explícitamente como baseline, no producto.

### Task 1: Construcción reproducible

**Files:** scripts/build-baseline.sh, .github/workflows/baseline-build.yml.
**Interfaces:** bash scripts/build-baseline.sh produce baseline-output únicamente tras build exitoso.

- [x] Fijar Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 y depot_tools 8a5434051036b32412a2ecb10c213a72e3f3ccb9.
- [x] Preparar guardias, gclient Android, GN sin símbolos y compile con 4 procesos.
- [x] Verificar sintaxis Bash y rechazo local (exit 2).
- [ ] Ejecutar workflow manual y verificar checkout, hooks, GN, Ninja y APK.
- [ ] Documentar resultado real: tiempos, espacio, errores y SHA256 si hay APK.
- [ ] Solo tras baseline exitosa, concretar integración UI con modelos reales, barra lateral, escritorio/extensiones y applicationId/firma propios.

Decisión: la autorización completa incluye publicación/ejecución, se continúa sin otra confirmación. El resultado del build es requisito para declarar viable el constructor.
