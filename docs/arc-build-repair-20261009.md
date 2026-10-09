# Reparación del run 37905612954

Base: `38326ef19f1e82548bf32ff412c0350374cdf3a6`, misma rama y worktree. Se conserva la implementación de paridad Arc, el scope `arc-media` y passwords locales deshabilitados. LinkedIn permanece fuera del alcance.

## Causa y corrección

El log real del job `113738228422` identifica un error de compilación Java en `VerticalTabRailLayout.java`: `@Nullable ImageView.ScaleType` coloca una anotación TYPE_USE sobre el calificador del tipo anidado. La declaración correcta es `ImageView.@Nullable ScaleType`. Se modifica esa única declaración y se regenera el patch de 101 archivos.

La prueba API anterior compilaba los métodos con campos sintéticos sin anotaciones y no detectaba este error. Ahora extrae las declaraciones Arc reales, preserva sus anotaciones y las compila contra Android37/JDK17 con Nullable restringido a TYPE_USE. El ciclo RED reprodujo el error del run; GREEN pasó las seis pruebas de apariencia.

El monitor calculaba la duración contra la hora de cada consulta incluso después de finalizar. Ahora los runs terminados usan la última fecha de finalización de sus jobs; si no hay fechas de jobs, utilizan `updated_at` del run. Los runs activos siguen contando hasta la consulta. Tres regresiones cubren fallo/éxito/cancelación, último job de cleanup, timestamps ausentes y etapa terminada dentro de un run aún activo. RED reprodujo el tiempo incorrecto; GREEN pasó las 19 pruebas de monitor/instalación.

El run se creó a las 08:32:46 UTC y terminó a las 09:40:42 UTC: **1 h 07 min 56 s**. El panel a las 13:00 mostraba incorrectamente 4 h 27 min. El worker rechazó la instalación del build fallido; no se instaló un artefacto de ese run.

## Recuperación de compilación

Checkpoint `archium-checkpoint-37905612954-1`: manifest descargado y validado contra el producer `38326ef19f1e82548bf32ff412c0350374cdf3a6` y Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`. Las 23 partes remotas están uploaded y coinciden en tamaño y digest SHA-256 con el manifest. El nuevo run reutilizará ese checkpoint mediante los inputs explícitos. La restauración en CI vuelve a verificar el hash de cada parte descargada.

## Validación y entrega

Checks completos con Python3.12/JDK17: **265/265 PASS**, sin skips, 175.665 s; preflight exit0. Preparación: **101 archivos aplicados y hashes coincidentes**, geometría y adaptadores SDK37 PASS, exit0. Revisión independiente: sin blockers, apariencia6/6 y monitor19/19 repetidos PASS. Consulta real del run con el monitor reparado: tiempo1h7min. Evidencia en `.sync-audit/arc-next-polish-20261009/{repository-build-repair,preparation-build-repair,appearance-compile-red,appearance-compile-green,monitor-clock-red,monitor-clock-green}.log`.

**READY FOR COMMIT** para esta reparación. La compilación integral y la aceptación visual del APK nuevo permanecen pendientes; las pruebas host no acreditan aceptación DeX.

Cambios: declaración del rail, patch/manifest regenerados, probe de apariencia, reloj del monitor y tres regresiones. No se cambian controles del sistema, geometría, persistencia ni navegación. El monitor mantiene intervalo de 600 segundos y el worker independiente instala únicamente tras éxito del run/commit esperado, verificación del artefacto y comparación del SHA-256 del APK instalado. Tras iniciar ambos, el agente se pone en pausa por instrucción del usuario.
