package com.empatelive.corredor.ui.estado

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory

private val VERDE = Color(0xFF2E7D32)
private val GRIS = Color(0xFF9E9E9E)
private val AMBAR = Color(0xFFF9A825)

/** A4: consulta pasiva del estado — pensada para un vistazo rápido, no
 * para leerla corriendo. Combina lo que el propio dispositivo sabe (¿sigue
 * vivo el `Service`? ¿cuántos puntos hay sin enviar en Room?) con lo que
 * confirma el servidor (`GET /inscripciones/{id}/estado`). */
@Composable
fun PanelEstado(contenedor: AppContainer) {
    val contexto = LocalContext.current
    val vm: EstadoViewModel = viewModel(
        factory = ViewModelFactory {
            EstadoViewModel(contenedor.api, contenedor.posicionDao, contenedor.sesion, contexto)
        },
    )

    Column(modifier = Modifier.fillMaxWidth().padding(top = 16.dp)) {
        FilaEstado(
            etiqueta = "GPS",
            valor = if (vm.transmisionActivaLocal) "Transmitiendo" else "Detenido",
            color = if (vm.transmisionActivaLocal) VERDE else GRIS,
        )
        FilaEstado(
            etiqueta = "Batería",
            valor = vm.bateriaPct?.let { "$it %" } ?: "—",
            color = null,
        )
        FilaEstado(
            etiqueta = "Conexión",
            valor = when {
                !vm.transmisionActivaLocal -> "—"
                vm.puntosPendientes == 0 -> "Enviando"
                else -> "Encolando sin conexión (${vm.puntosPendientes})"
            },
            color = if (vm.puntosPendientes > 0 && vm.transmisionActivaLocal) AMBAR else VERDE,
        )
        FilaEstado(
            etiqueta = "Servidor",
            valor = when {
                !vm.conectadoConServidor -> "Sin contacto"
                vm.estadoServidor == "transmitiendo" -> "Te ve transmitiendo"
                vm.estadoServidor == "sin_senal" -> "Te ve sin señal"
                else -> "—"
            },
            color = if (!vm.conectadoConServidor) null else AMBAR,
        )
    }
}

@Composable
private fun FilaEstado(etiqueta: String, valor: String, color: Color?) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(etiqueta, style = MaterialTheme.typography.bodyMedium)
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (color != null) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(color),
                )
                Spacer(modifier = Modifier.width(6.dp))
            }
            Text(valor, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
