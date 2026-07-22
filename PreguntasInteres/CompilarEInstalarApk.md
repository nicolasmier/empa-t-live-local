# CompilarEInstalarApk

**Pregunta:** ¿Cómo se genera el APK para un móvil real y qué pasa si cambia la
IP del PC?

## A qué servidor apunta la app

La URL del servidor se fija **en tiempo de compilación** con la propiedad
`urlServidor` (`app-android/app/build.gradle.kts` → `BuildConfig.BASE_URL`):

- Por defecto `http://10.0.2.2:8000` (alias del `localhost` del host **en el
  emulador**).
- Para un móvil real, se sobreescribe con la **IP LAN del PC** (o el hostname del
  túnel en producción).

## Generar el APK (móvil real)

```bash
cd app-android
./gradlew assembleDebug -PurlServidor=http://<IP-LAN-DEL-PC>:8000
```

Se usa **`assembleDebug`** (no `assembleRelease`): el build de `release` **no
tiene configuración de firma**, así que saldría **sin firmar** y no se podría
instalar. El de debug va firmado con la clave de depuración → instalable.

El APK queda en `app-android/app/build/outputs/apk/debug/app-debug.apk`. Para el
kit de campo se copia a `instalableApp/EmpateLive-Corredor.apk`.

> `usesCleartextTraffic="true"` en el manifest permite `http://` en LAN mientras
> se prueba. En producción el túnel es **HTTPS** — revisar antes de un release.

## Instalar en el teléfono

Pasar el `.apk` al móvil (cable/Drive/WhatsApp) y abrirlo; aceptar "fuente
desconocida". Si Android da **conflicto de firma**, desinstalar la versión
anterior antes de reinstalar.

## Si cambia la IP del PC (otra WiFi, reinicio del router)

El APK deja de encontrar el servidor. Comprobar la IP nueva:

```bash
ip -4 addr show | grep -oP '(?<=inet )\d+(\.\d+){3}' | grep -v '^127\.'
```

y **regenerar** el APK con esa IP. En producción con túnel esto no pasa: la app
apunta a un hostname fijo, no a una IP.

Ver también: [ComoLleganLosDatosDelMovil](ComoLleganLosDatosDelMovil.md),
`instalableApp/README.md`.
