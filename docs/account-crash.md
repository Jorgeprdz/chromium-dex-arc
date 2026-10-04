# Crash al pulsar Agregar cuenta

Confirmado en logcat del teléfono el 2026-10-04 (dos cierres del proceso
org.chromium.chrome). No se capturaron credenciales ni contenido del perfil.

Excepción exacta:

```text
java.lang.UnsupportedOperationException: NullAccountManagerDelegate does not implement createAddAccountIntent
```

La APK snapshot instalada llega a un delegado que no implementa la operación
de agregar cuenta. Es un fallo de la ruta nativa de cuentas de esta base; no
demuestra un problema con la contraseña, extensiones o login en páginas web.

El fork debe evitar exponer una acción que termine en esta excepción y dar una
respuesta clara cuando la integración no esté disponible. Resolver el cierre no
equivale a habilitar sincronización con Google; investigar esa posibilidad por
separado sin prometerla.

No se modificó ni reinstaló la APK instalada. El build baseline permanece
in_progress en run37231453817, sin cambios visuales ni corrección de este crash.
