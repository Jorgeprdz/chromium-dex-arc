### Task 1: Clasificación compartida y métricas actuales

**Files:** Create `chrome/browser/desktop_policy/android/BUILD.gn`, Java `ArchiumWindowClass.java`, `ArchiumWindowMetrics.java` en ese módulo. Modify `chrome/browser/ui/vertical_tabs/BUILD.gn`, `ArcDesktopPolicy.java`, `ArcDesktopAppearance.java`; tests de política y Android metrics.

**Interfaces:** Window class COMPACT/TABLET/DESKTOP; classify(widthDp) usa constantes WindowSizeClass reales. currentWidthDp(Context) utiliza contexto actual de Activity y Configuration/WindowMetrics; sin tamaño de panel. Arc AUTO consume la clasificación; ARC/MOBILE manual del plan visual conserva su contrato independiente de UA.

- [ ] RED: 580/599 compact;600/620/839 tablet;840/900 desktop;520->700 cambia clase. Marca/modelo/orientación no son argumentos de elegibilidad.
- [ ] Verificar API contra JAR real extraído del CIPD fijado; clases Android SDK no prueban GN completo.
- [ ] Implementar módulo y enlazar Arc sin referencias semDesktopMode/FEATURE_PC para elegibilidad.
- [ ] Android: Configuration contextual 580/620/900, rotación con ancho constante, metrics/insets coherentes en Activity real.
- [ ] GREEN política/metrics; verificar GN target público AndroidX y visibilidad en checkout completo; commit.
