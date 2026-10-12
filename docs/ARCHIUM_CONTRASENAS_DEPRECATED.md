# Gestor propio de contraseñas — DEPRECATED

Decisión explícita del usuario, 2026-10-12: «solo contraseñas» y «ya queda deprecated».

El gestor propio de Archium queda fuera de la entrega R4: backend local,
clave Android Keystore, pantalla propia, puente del gestor e importación/exportación
CSV. No desarrollar ni volver a activar estas funciones sin una petición explícita.
Esta decisión sustituye el alcance de contraseñas de los planes anteriores.

La implementación y sus pruebas históricas se conservan como antecedente; no
constituyen componentes habilitados ni gates nativos de la entrega actual.
Los checks históricos host pueden seguir ejecutándose y deben identificarse como
validación histórica, sin acreditar funciones de la APK.

R4 usa `enable_archium_local_passwords = false`. El workflow debe validar el
argumento efectivo de GN y la ausencia de los componentes propios en las
dependencias de la APK. Conserva el gestor y autocompletado estándar de Chromium,
pagos, Arc/DeX, colores e identidad Portal. No modifica datos de usuario existentes.

Los enlaces JNI se verifican sobre `//chrome/android:libchrome`, el componente
nativo que usa `chrome_public_apk`, en lugar de los ejecutables propios retirados.
La ausencia de esos tests nativos se registra como `DEPRECATED / OUT_OF_SCOPE`,
nunca como tests ejecutados o PASS. Los gates reales de Robolectric, recursos,
enlace de Chromium y APK siguen siendo bloqueantes.

Cambiar el argumento GN obliga a regenerar el grafo y recompilar el delta
afectado. El checkpoint anterior se conserva; no autoriza una compilación limpia
ni garantiza que el build completo vaya a terminar sin errores.
