package com.empatelive.corredor.ubicacion

import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.BatteryManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.empatelive.corredor.datos.PosicionDao
import com.empatelive.corredor.datos.PosicionEntity
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.sincronizacion.SincronizadorPosiciones
import java.time.Instant
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** El corazón de la app (A2, spec §5/§6/RF-009). Foreground service con
 * notificación persistente — sin él Android mata la transmisión a los
 * minutos — que pide ubicación a frecuencia adaptativa según la velocidad
 * y encola cada punto en Room (esquema de A1). Enviar los puntos por lotes
 * a la API respetando el rate limit es A3, no este fichero.
 *
 * GPS crudo (`LocationManager`/`GPS_PROVIDER`), no `FusedLocationProviderClient`:
 * decisión tomada tras probarlo de verdad en el emulador — Fused depende de
 * Google Play Services, que en este AVD (imagen `google_apis`, no
 * `google_apis_playstore`) no entregaba las posiciones simuladas aunque el
 * HAL de GNSS sí las recibía. Más allá del emulador, esto es la opción más
 * robusta para el caso real: un corredor puede llevar un teléfono sin Play
 * Services (algunos mercados/fabricantes AOSP) y el caso de uso —GPS al
 * aire libre durante una carrera— no necesita fusión con wifi/red, solo
 * satélite de verdad.
 *
 * `START_NOT_STICKY` y `stopWithTask="true"` (manifest) a propósito: si el
 * sistema mata el proceso o el corredor cierra la app, el servicio NO se
 * reinicia solo — "no intentar resucitar el servicio a escondidas" (spec).
 */
class LocationTrackingService : LifecycleService() {
    private lateinit var gestorUbicacion: LocationManager
    private lateinit var dao: PosicionDao
    private lateinit var sincronizador: SincronizadorPosiciones
    private var intervaloActualMs: Long = -1
    private var bucleSincronizacionIniciado = false

    private val listenerUbicacion = LocationListener { ubicacion ->
        lifecycleScope.launch {
            guardarPosicion(ubicacion)
            ajustarFrecuenciaSegun(ubicacion)
        }
    }

    override fun onCreate() {
        super.onCreate()
        gestorUbicacion = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val contenedor = AppContainer(this)
        dao = contenedor.posicionDao
        sincronizador = SincronizadorPosiciones(contenedor.api, dao, contenedor.sesion)
        EstadoServicioUbicacion.marcarActivo(true)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        iniciarEnPrimerPlano()
        empezarActualizaciones(INTERVALO_INICIAL_MS)
        iniciarBucleDeSincronizacion()
        return START_NOT_STICKY
    }

    // A3: se relanza sola cada `INTERVALO_SINCRONIZACION_MS` mientras el
    // servicio viva — `lifecycleScope` se cancela solo en `onDestroy`
    // (LifecycleService), así que no hace falta parar este bucle a mano.
    // El intervalo (6 s) respeta el límite del servidor de 1 petición/5 s
    // por dispositivo (mismo margen que usa `simulador/`).
    private fun iniciarBucleDeSincronizacion() {
        if (bucleSincronizacionIniciado) return
        bucleSincronizacionIniciado = true
        lifecycleScope.launch {
            while (true) {
                sincronizador.sincronizarUnaVez()
                delay(INTERVALO_SINCRONIZACION_MS)
            }
        }
    }

    private fun iniciarEnPrimerPlano() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val gestor = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            gestor.createNotificationChannel(
                NotificationChannel(
                    CANAL_ID,
                    "Transmisión de posición",
                    NotificationManager.IMPORTANCE_LOW,
                ),
            )
        }
        val notificacion = NotificationCompat.Builder(this, CANAL_ID)
            .setContentTitle("EmpateLive")
            .setContentText("Transmitiendo tu posición")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setOngoing(true)
            .build()
        startForeground(NOTIFICACION_ID, notificacion)
    }

    // El permiso de ubicación ya se comprueba antes de arrancar este
    // servicio (ver TransmisionSeccion) — nunca se llega aquí sin él.
    @SuppressLint("MissingPermission")
    private fun empezarActualizaciones(intervaloMs: Long) {
        if (intervaloActualMs == intervaloMs) return
        intervaloActualMs = intervaloMs
        gestorUbicacion.removeUpdates(listenerUbicacion)
        gestorUbicacion.requestLocationUpdates(
            LocationManager.GPS_PROVIDER,
            intervaloMs,
            0f, // sin distancia mínima: la frecuencia ya la marca el intervalo
            listenerUbicacion,
            mainLooper,
        )
    }

    private fun ajustarFrecuenciaSegun(ubicacion: Location) {
        val velocidadKmh = if (ubicacion.hasSpeed()) metrosPorSegundoAKmh(ubicacion.speed) else null
        empezarActualizaciones(calcularIntervaloMs(velocidadKmh))
    }

    private suspend fun guardarPosicion(ubicacion: Location) {
        dao.insertar(
            PosicionEntity(
                // Hora de la lectura GPS en el dispositivo (spec §5), no la
                // del guardado en Room ni la del envío posterior (A3).
                timestampDispositivo = Instant.ofEpochMilli(ubicacion.time).toString(),
                latitud = ubicacion.latitude,
                longitud = ubicacion.longitude,
                precisionM = if (ubicacion.hasAccuracy()) ubicacion.accuracy else null,
                velocidadKmh = if (ubicacion.hasSpeed()) metrosPorSegundoAKmh(ubicacion.speed) else null,
                bateriaPct = leerPorcentajeBateria(),
            ),
        )
    }

    private fun leerPorcentajeBateria(): Int? {
        val gestor = getSystemService(Context.BATTERY_SERVICE) as? BatteryManager ?: return null
        return gestor.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    override fun onDestroy() {
        gestorUbicacion.removeUpdates(listenerUbicacion)
        EstadoServicioUbicacion.marcarActivo(false)
        super.onDestroy()
    }

    companion object {
        private const val CANAL_ID = "transmision_posicion"
        private const val NOTIFICACION_ID = 1
        private const val INTERVALO_INICIAL_MS = 17_500L
        private const val INTERVALO_SINCRONIZACION_MS = 6_000L

        fun intentPara(context: Context): Intent = Intent(context, LocationTrackingService::class.java)
    }
}
