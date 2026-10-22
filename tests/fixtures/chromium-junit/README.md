# Pinned Chromium JVM test helpers

Unmodified upstream sources at `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, verified by `pinned.json`.

- `TestListComputer.java`, `Allowlist.java`: `testing/android/junit/java/src/org/chromium/testing/local/`.
- `shadows-allowlist.txt`: `testing/android/junit/`.
- `ThemeColorProvider.java`: `chrome/browser/ui/android/theme/java/src/org/chromium/chrome/browser/theme/`.

The local phone runner executes the real discovery policy before JUnit. These files are host fixtures, not modifications to Chromium's runner or policy. Native resources/controllers still require integrated validation.
