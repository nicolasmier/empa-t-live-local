# App Android — Corredor

FASE A1 del plan de App Android (`docs/Plan_Implementacion_3_App_Android_v2.md`):
cuenta, perfil (con foto) y unión al evento. Kotlin + Jetpack Compose,
Retrofit/OkHttp/kotlinx.serialization, Room (solo esquema todavía, la
sincronización es de A3), EncryptedSharedPreferences para el token de
sesión y el de dispositivo.

## Entorno de desarrollo

Este proyecto no traía SDK de Android — se provisionó en
`~/Android/sdk` (cmdline-tools, `platform-tools`, `platforms;android-35`,
`build-tools;35.0.0`, `emulator`, `system-images;android-35;google_apis;x86_64`),
y un JDK 21 (Temurin) en `~/.jdks/temurin-21` porque el JDK del sistema
puede ser demasiado reciente para el AGP/Gradle estables en uso — configurado
en `~/.gradle/gradle.properties` (`org.gradle.java.home`), no en este
repo, porque es específico de esta máquina.

`local.properties` (con `sdk.dir`) tampoco se versiona — cada máquina debe
generarlo o apuntar a su propio SDK.

## Compilar y testear

```bash
cd app-android
./gradlew assembleDebug
./gradlew testDebugUnitTest
```

## Emulador

```bash
avdmanager create avd -n empatelive_test -k "system-images;android-35;google_apis;x86_64" -d pixel_6
emulator -avd empatelive_test
```

El emulador accede al `docker-compose.dev.yml` del host en
`http://10.0.2.2:8000` (alias fijo del emulador hacia el `localhost` del
host) — ya configurado como `BASE_URL` en `app/build.gradle.kts`.

## Probar el flujo A1 de verdad

```bash
docker compose -f ../docker-compose.dev.yml up -d --build
./gradlew installDebug
adb shell am start -n com.empatelive.corredor/.MainActivity
```

Con el seed de dev aplicado, únete con el código de un evento seedado
(`docs/...` o revisa `api/seed/seed.py`) tras completar registro + perfil.
Cierra y reabre la app: debe ir directa al dorsal, sin pedir login de nuevo.

## Qué falta (A2 en adelante)

Este scaffold cubre solo **FASE A1**. El servicio de ubicación en segundo
plano (A2, "el corazón de la app"), la sincronización real de la cola de
Room (A3), la pantalla de estado (A4) y las pruebas de campo
multi-fabricante (A5, obligatorias y no negociables) quedan para rondas
siguientes — ver `docs/Plan_Implementacion_3_App_Android_v2.md`.
