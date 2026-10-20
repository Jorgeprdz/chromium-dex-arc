# Chromium source used by the JVM probe

`ResourceRequestBody.java` is unchanged Chromium source at
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`:
`content/public/android/java/src/org/chromium/content_public/common/ResourceRequestBody.java`.
SHA-256: `f4fbbdceaa3e3ec44eeaca903782fc172090ce34112f8296acc7810cdcdeaaec`. Its original copyright/license header is retained.

The split probe compiles this real final class. Its generated JNI bridge is an
explicit test adapter; `BaseRobolectricTestRunner` and GURL are also adapters in
that probe. The actual native Chromium runner remains a mandatory CI gate.
