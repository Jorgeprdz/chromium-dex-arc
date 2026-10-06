# Alcance de Google Sync en Archium Android

Investigación: 2026-10-06. Base auditada: Chromium
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, versión 157.0.8086.0.
No se ha modificado ni recompilado el navegador durante esta investigación.
No se han solicitado tokens ni leído contraseñas o datos de cuenta del usuario.

## Conclusión

No existe una integración Google Sync verificada para Archium. No es correcto
afirmar que es imposible en todos los escenarios: Chromium documenta una excepción
para cuentas de prueba y existe un fork experimental con integración microG.
Tampoco es correcto prometer Sync completo después de añadir claves o recompilar.

Hay tres obstáculos independientes: autenticación Android, autorización del
servicio Google y acceso/almacenamiento de datos, incluidas claves de cifrado y
backend de contraseñas. La apariencia AndroidDesktop no cambia la plataforma
Android en estos componentes.

## Fuentes oficiales: acceso y autorización

La [documentación de claves de Chromium](https://www.chromium.org/developers/how-tos/api-keys/)
explica que la emisión del token necesario para iniciar sesión está restringida.
Documenta una excepción para cuentas de prueba incluidas en
`google-browser-signin-testaccounts@chromium.org`. El documento es general para
Chromium; no demuestra por sí mismo compatibilidad del paquete/firma de una APK
Android propia. La página del grupo no muestra su contenido sin iniciar sesión;
no se ha confirmado la admisión de la cuenta del usuario.

Esta excepción no debe confundirse con la lista de usuarios de prueba de la
pantalla OAuth de un proyecto Google Cloud. Son condiciones diferentes.

El código exacto define el scope
`https://www.googleapis.com/auth/chromesync` en
[gaia_constants.h](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/google_apis/gaia/gaia_constants.h).
No aparece en el [catálogo público de scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
consultado. La ausencia del catálogo no es una prueba autónoma de imposibilidad;
coincide con la restricción explícita descrita por Chromium.

[Sign in with Google](https://developer.android.com/identity/sign-in/credential-manager-siwg)
permite identificar al usuario de una aplicación. Ese resultado no sustituye el
access token con los scopes que pide Sync. Un token de identidad o consentimientos
para servicios distintos no conceden automáticamente acceso a Chrome Sync.

No se encontró documentación oficial que garantice aprobación para un fork Android
simplemente por pagar, publicarlo en Play Store o pasar verificación OAuth general.

## Qué falta en nuestra revisión exacta

1. [AccountManagerFacadeProvider](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/signin/public/android/java/src/org/chromium/components/signin/AccountManagerFacadeProvider.java)
   carga un delegado por ServiceLoader y usa NullAccountManagerDelegate si no existe.
   Nuestro parche anterior no registra un delegado funcional.
2. [NullAccountManagerDelegate](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/signin/public/android/java/src/org/chromium/components/signin/NullAccountManagerDelegate.java)
   no enumera cuentas ni obtiene tokens. Evitar la excepción de agregar cuenta
   no altera esas funciones.
3. [AccountManagerFacadeImpl](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/signin/public/android/java/src/org/chromium/components/signin/AccountManagerFacadeImpl.java)
   llama al delegado para los tokens. La revisión incluye una migración de
   AccountManagerDelegate y una ruta de PlatformAccount, por lo que un delegado
   antiguo no se puede asumir compatible sin adaptación.
4. [SyncServiceFactory](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/sync/sync_service_factory.cc)
   conserva el servicio de Sync y conexiones a modelos de marcadores, historial,
   sesiones y otros tipos. No hace falta inventar un protocolo de sincronización;
   sí completar autenticación, autorización y las dependencias de cada modelo.
5. [PasswordStoreBackendFactory](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/browser/password_manager/factories/password_store_backend_factory.cc)
   retorna PasswordStoreEmptyBackend en Android cuando no está disponible el
   backend interno. La rama que utiliza LoginDatabase y PasswordStoreBuiltInBackend
   es no-Android. Necesitará adaptación, no un simple cambio de disponibilidad.

## Evidencia de otros forks Android

Los mantenedores de [Thorium Android](https://github.com/Alex313031/Thorium-Android/discussions/4)
reportaron el mismo error de cuenta existente y restricciones Google en 2023/2024.
Su [FAQ](https://thorium.rocks/faq) señala que las claves incorporadas no bastan
en Android. Esto respalda la existencia de restricciones adicionales, pero su
explicación sobre whitelist/Play Store/coste no se ha verificado con una fuente
oficial de Google y no se toma como un procedimiento garantizado.

Se encontró [chromium_android_sync](https://github.com/bearinmindcat/chromium_android_sync),
un fork experimental con parches para Chromium 147.0.7699.1, no nuestra revisión
157. Se inspeccionaron sus commits iniciales y correctivos y los archivos relevantes
de la revisión `645017d0204a75a687525094a15a51cf3893c56e`.

La [documentación histórica de sus parches](https://github.com/bearinmindcat/chromium_android_sync/blob/645017d0204a75a687525094a15a51cf3893c56e/MICROG_PATCHES.md)
describe cuentas de tipo app.revanced, un ContentProvider propio, un delegado de
cuentas y redirección de GoogleAuthUtil a ReVanced GmsCore. Su lista de pruebas no
aporta resultados reproducibles de sincronización completa. También describe
problemas de identidad, cierre de sesión y CAPTCHA. Es evidencia de una ruta de
implementación, no evidencia de funcionamiento en nuestro Samsung.

[ReVanced GmsCore](https://github.com/ReVanced/GmsCore) documenta operación sin root
y coexistencia con Play Services bajo otro paquete. Por eso esta variante puede
investigarse sin sustituir GMS del teléfono. No se instaló ni configuró durante
la investigación y no se ha verificado que el delegado, su provider ni sus tokens
sean compatibles con Archium 157.

Limitación importante en el código inspeccionado:
[MicroGTrustedVaultBackend](https://github.com/bearinmindcat/chromium_android_sync/blob/645017d0204a75a687525094a15a51cf3893c56e/chrome/android/java/src/org/chromium/chrome/browser/sync/MicroGTrustedVaultBackend.java)
devuelve claves vacías y resultados que suprimen errores de recuperación.
Esto no recupera las claves de una cuenta ni prueba acceso a datos cifrados.
No se adopta su comentario de que Sync funciona sin cifrado como un hecho comprobado.
No copiar ese comportamiento para presentar estados de seguridad falsos.

## Alcance por función

| Función | Qué se puede afirmar hoy |
| --- | --- |
| Sesión web Gmail/Meet/Drive | Funciona de manera independiente; no es Sync del perfil. |
| Identidad Google de Archium | Implementable con APIs de identidad admitidas; no confiere acceso a Sync. |
| Marcadores, historial y pestañas con Chrome | Modelos disponibles, pendientes de token autorizado y prueba real entre clientes. |
| Contraseñas de Google dentro de Archium | Pendientes de autenticación, backend, claves y sincronización; el éxito de marcadores no prueba esta función. |
| Guardar/importar/exportar contraseñas locales | Independiente de Google Sync; requiere backend funcional en Android. |
| Passkeys, Google Pay y Wallet | Integraciones separadas; fuera de cualquier garantía derivada de Sync. |
| Extensiones y sus datos | Dependen de buildflags, controladores y APIs de cada extensión; no garantizados por iniciar sesión. |
| Sesiones de varios perfiles | Requieren aislamiento, cierre de sesión y políticas de borrado probados; no equivalen a sumar cuentas de Android. |

## Prueba mínima antes de otra compilación completa

Conservar dos rutas candidatas y probar una a la vez:

1. Oficial experimental: credenciales propias y cuenta de prueba admitida para el
   scope Sync; verificar que nuestro cliente Android obtiene un token y que el
   servidor lo acepta. Falta la configuración externa para ejecutar esa prueba.
2. Experimental microG: comprobar el contrato de ReVanced GmsCore y adaptar un
   delegado mínimo a la revisión 157, con cuenta de prueba distinta de la cuenta
   personal. Falta una prueba funcional; el código 147 no se aplica directamente.

La identidad de paquete/firma del cliente importa. Un resultado en una APK de
prueba con otro package no prueba automáticamente el acceso de Archium.
No copiar credenciales de Chrome ni cambiar la identidad del fork a Chrome.

Puertas de aceptación:

- Emitir, renovar e invalidar el token necesario sin guardar secretos en logs.
- Intercambiar un marcador ficticio e historial/pestañas de prueba con Chrome.
- Reiniciar y recuperar sesión, manejar revocación y cerrar sesión correctamente.
- Comprobar el caso de cuenta con claves/cifrado. Obtener claves realmente o mostrar
  el bloqueo; no devolver éxito vacío.
- Para contraseñas: backend funcional y una credencial ficticia sincronizada,
  rellenada y actualizada, sin necesidad de desactivar protecciones de la cuenta.

Se puede reducir el coste de autenticación inicial con un cliente de prueba
pequeño. Este no sustituye la integración final con SyncService y la APK real.
No prometer una duración de la implementación hasta superar estas pruebas.

## Decisión que permite la investigación

Google Sync completo no es un requisito actualmente garantizable de la próxima
APK. Puede mantenerse como objetivo condicionado a una prueba de viabilidad
separada y económica. La investigación justifica explorar esa prueba, pero no
iniciar otra compilación larga para averiguar únicamente si Google admite el
cliente. No se solicita aprobación del diseño con Sync etiquetado como resuelto.
