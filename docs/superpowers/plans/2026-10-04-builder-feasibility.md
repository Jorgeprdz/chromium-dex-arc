# Chromium DeX Arc: comprobación del constructor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determinar con mediciones si existe una ruta gratuita de compilación sin otro equipo.

**Architecture:** Repositorio pequeño de preparación, separado de DEXCorners. Un workflow manual realiza un inventario de un runner Linux x86-64; no descarga el motor. El resultado determina si procede preparar el build de Chromium o si hace falta otra infraestructura.

**Tech Stack:** Bash, GitHub Actions ubuntu-24.04, Chromium Android Desktop ARM64.

**Spec:** ../../design.md

## Global Constraints

- Diseño Arc aprobado; no sustituir la base por WebView.
- Desktop ready y soporte de extensiones son requisitos explícitos del usuario.
- No contratar servicios de pago.
- No iniciar un checkout completo que agote el almacenamiento del teléfono.
- No alterar navegadores o perfiles existentes ni el proyecto DEXCorners.
- La futura aplicación tendrá applicationId y firma propios.
- La publicación de este nuevo repositorio público requiere autorización del usuario.

## Review Focus

- Espacio anunciado versus espacio real: registrar ambos sin prometer que el build cabe.
- Discos separados: no sumar espacio de montajes como si fuera un solo filesystem.
- Arquitectura ARM64 del teléfono: el inventario local no prueba compatibilidad del builder x86-64.
- Duración de compilación: un inventario exitoso no demuestra que se complete el build.
- Costos y privacidad: usar únicamente runner estándar público; no incluir datos personales ni secretos.

### Task 1: Inventario reproducible y revisión de publicación

**Files:** `.github/workflows/runner-probe.yml`, `scripts/probe-runner.sh`, `README.md`, `docs/design.md`.

**Interfaces:** `bash scripts/probe-runner.sh` imprime recursos medidos; no produce una APK.

- [x] Preparar script de inventario de solo lectura y workflow manual con timeout de 10 minutos.
- [x] Comprobar sintaxis Bash y YAML, y revisar que no contiene descargas del motor, borrados ni secretos.
- [x] Obtener autorización para publicar el repositorio nuevo `Jorgeprdz/chromium-dex-arc`.
- [x] Publicar únicamente los archivos de preparación revisados.
- [x] Ejecutar el workflow manual y guardar las medidas en `docs/builder-inventory.md`.
- [x] Comparar filesystem disponible, RAM y arquitectura con los requisitos oficiales; documentar si una limpieza controlada del runner podría acercarlo al mínimo. No ejecutarla en este inventario.

### Task 2: Decisión técnica a partir de las medidas

**Files:** `docs/builder-inventory.md`, `docs/superpowers/plans/2026-10-04-browser-implementation.md` (solo si hay constructor viable).

**Interfaces:** Las medidas de Task 1 determinan la infraestructura admitida. La revisión base es `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

- [ ] Si no existe ruta gratuita comprobable, informar la restricción concreta sin iniciar una descarga masiva ni cambiar de motor.
- [ ] Si existe una ruta, revisar las interfaces reales de UI y modelos en esa revisión y escribir el plan de implementación con los archivos exactos.
- [ ] Incluir en ese plan: baseline `chrome_public_apk` con `is_desktop_android=true`, applicationId/firma propios, barra lateral de 240 dp/52 dp, pestañas reales, favoritos, tema lavanda/oscuro, margen de 8 dp, adaptación móvil y pruebas de DeX, además de instalación/activación/persistencia y acceso a acciones de extensiones.
- [ ] Reservar instalación y afirmaciones de funcionamiento para una APK compilada, firmada y probada. No presentar este inventario como implementación del navegador.

Revisión del plan: cubre la limitación inmediata; la integración visual queda condicionada a disponer de un constructor. No hay métodos de UI inventados ni una promesa de compilación en runners estándar.
