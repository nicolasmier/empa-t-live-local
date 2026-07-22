package com.empatelive.corredor.ui.unirse

import android.Manifest
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.empatelive.corredor.ubicacion.EstadoServicioUbicacion
import com.empatelive.corredor.ubicacion.LocationTrackingService

private fun tienePermisoUbicacion(contexto: android.content.Context): Boolean =
    ContextCompat.checkSelfPermission(contexto, Manifest.permission.ACCESS_FINE_LOCATION) ==
        android.content.pm.PackageManager.PERMISSION_GRANTED

private fun ignoraOptimizacionBateria(contexto: android.content.Context): Boolean {
    val gestor = contexto.getSystemService(android.content.Context.POWER_SERVICE) as PowerManager
    return gestor.isIgnoringBatteryOptimizations(contexto.packageName)
}

/** A2: permisos de ubicación + exclusión de optimización de batería (con
 * pantalla explicativa ANTES de pedirla, spec) + arrancar/parar el
 * `LocationTrackingService`. Vive dentro de la pantalla "ya unido" de
 * Unirse: no tiene sentido pedir esto antes de tener dorsal.
 *
 * Un solo botón ("Activar GPS para el evento") pide el permiso si falta Y
 * arranca la transmisión en el mismo gesto — para el corredor es una sola
 * acción mental ("activa el GPS de la carrera"), no dos pasos separados.
 * Solo `ACCESS_FINE_LOCATION`/`ACCESS_COARSE_LOCATION` ("mientras se usa la
 * app"), nunca `ACCESS_BACKGROUND_LOCATION`: el foreground service con
 * notificación persistente (`FOREGROUND_SERVICE_LOCATION`, manifest) ya hace
 * que Android trate la app como "en uso" aunque la pantalla esté apagada, así
 * que el permiso "todo el tiempo" no aporta nada y sí un diálogo de sistema
 * más agresivo e innecesario. */
@Composable
fun TransmisionSeccion() {
    val contexto = LocalContext.current
    val transmitiendo by EstadoServicioUbicacion.activo.collectAsState()

    var tienePermiso by remember { mutableStateOf(tienePermisoUbicacion(contexto)) }
    var sinOptimizacionBateria by remember { mutableStateOf(ignoraOptimizacionBateria(contexto)) }

    fun iniciarTransmision() {
        ContextCompat.startForegroundService(contexto, LocationTrackingService.intentPara(contexto))
    }

    val lanzadorPermisos = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions(),
    ) { _ ->
        tienePermiso = tienePermisoUbicacion(contexto)
        if (tienePermiso) iniciarTransmision()
    }

    val lanzadorBateria = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult(),
    ) { _ -> sinOptimizacionBateria = ignoraOptimizacionBateria(contexto) }

    HorizontalDivider(modifier = Modifier.padding(vertical = 24.dp))
    Text("Transmisión GPS", style = MaterialTheme.typography.titleMedium)

    if (!tienePermiso) {
        Text(
            "La app necesita saber tu ubicación mientras corres para que se vea en la web pública.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
        )
    }

    if (!transmitiendo && tienePermiso && !sinOptimizacionBateria) {
        Column {
            Text(
                "Tu móvil puede intentar ahorrar batería cortando la app mientras " +
                    "corres. Para que la transmisión no se pare a mitad de carrera, " +
                    "desactiva la optimización de batería para EmpateLive.",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
            )
            OutlinedButton(
                onClick = {
                    lanzadorBateria.launch(
                        Intent(
                            Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                            Uri.parse("package:${contexto.packageName}"),
                        ),
                    )
                },
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
            ) {
                Text("Desactivar ahorro de batería para esta app")
            }
        }
    }

    Button(
        onClick = {
            when {
                transmitiendo -> contexto.stopService(LocationTrackingService.intentPara(contexto))
                tienePermiso -> iniciarTransmision()
                else -> {
                    val permisos = mutableListOf(
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION,
                    )
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        permisos.add(Manifest.permission.POST_NOTIFICATIONS)
                    }
                    lanzadorPermisos.launch(permisos.toTypedArray())
                }
            }
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(if (transmitiendo) "Detener transmisión" else "Activar GPS para el evento")
    }
}
