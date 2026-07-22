# TransmisionGpsYSinConexion

**Pregunta:** ¿Cómo transmite el GPS la app? ¿Qué pasa con la pantalla apagada,
sin cobertura o si se cierra la app?

## Cómo transmite

La app arranca un **foreground service** con notificación persistente
(`LocationTrackingService`, `foregroundServiceType="location"`). Ese servicio:

1. Lee la ubicación y la guarda **localmente** en Room (SQLite, WAL).
2. Un sincronizador (`SincronizadorPosiciones`) sube los puntos pendientes al
   servidor por lotes cada ~6 s.

Por eso solo pide permiso de ubicación **"mientras se usa la app"**
(`ACCESS_FINE/COARSE_LOCATION`), **no** "todo el tiempo"
(`ACCESS_BACKGROUND_LOCATION`): el foreground service ya hace que Android trate
la app como "en uso" aunque la pantalla esté apagada.

## Frecuencia adaptativa

El intervalo entre puntos se ajusta según el movimiento (`FrecuenciaAdaptativa`),
con los valores por defecto del evento (configurables en BD):

- Parado: `intervalo_gps_parado_seg` = **90 s**
- En movimiento: `intervalo_gps_movimiento_seg` = **20 s**

## Sin cobertura (modo avión, zona sin red)

Los puntos se **encolan localmente** y se envían solos al recuperar conexión. La
pantalla de estado muestra un contador **"Encolando sin conexión (N)"** que baja
a 0 al reconectar. No se pierden puntos por un corte temporal.

## Pantalla apagada / ahorro de batería

- Con la pantalla apagada sigue transmitiendo (gracias al foreground service).
- La app ofrece **desactivar la optimización de batería** para EmpateLive; si no,
  Android puede matar la app a mitad de carrera. Objetivo orientativo de la spec:
  **< ~10 %/hora** transmitiendo.

## Si el corredor cierra la app

Deslizarla desde "recientes" **detiene** la transmisión (`stopWithTask="true"`,
spec §5). Es el comportamiento esperado: **nunca** se resucita el servicio a
escondidas (nada de `START_STICKY` ni `WorkManager` de reinicio).

Ficheros: `app-android/.../ubicacion/` y `.../datos/` (Room).
