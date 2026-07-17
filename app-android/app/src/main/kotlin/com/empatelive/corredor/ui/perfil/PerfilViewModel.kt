package com.empatelive.corredor.ui.perfil

import android.content.Context
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.CorredorActualizar
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.llamarApi
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

class PerfilViewModel(
    private val api: ApiService,
    private val sesion: SesionSeguraStorage,
) : ViewModel() {
    var nombre by mutableStateOf("")
    var apellidos by mutableStateOf("")
    var club by mutableStateOf("")
    var fotoUrlServidor by mutableStateOf<String?>(null)
        private set
    var fotoLocalUri by mutableStateOf<Uri?>(null)
    var cargando by mutableStateOf(true)
        private set
    var guardando by mutableStateOf(false)
        private set
    var error by mutableStateOf<String?>(null)
        private set

    init {
        cargarPerfil()
    }

    private fun cargarPerfil() {
        val corredorId = sesion.obtenerCorredorId() ?: return
        viewModelScope.launch {
            cargando = true
            when (val resultado = llamarApi { api.obtenerPerfil(corredorId) }) {
                is ResultadoApi.Ok -> {
                    nombre = resultado.datos.nombre
                    apellidos = resultado.datos.apellidos
                    club = resultado.datos.club ?: ""
                    fotoUrlServidor = resultado.datos.fotoUrl
                }
                is ResultadoApi.Error -> error = resultado.mensaje
            }
            cargando = false
        }
    }

    fun guardar(contexto: Context, alContinuar: () -> Unit) {
        val corredorId = sesion.obtenerCorredorId() ?: return
        if (nombre.isBlank() || apellidos.isBlank()) {
            error = "Nombre y apellidos son obligatorios."
            return
        }

        viewModelScope.launch {
            guardando = true
            error = null

            val actualizar = llamarApi {
                api.actualizarPerfil(
                    corredorId,
                    CorredorActualizar(
                        nombre = nombre.trim(),
                        apellidos = apellidos.trim(),
                        club = club.trim().ifBlank { null },
                    ),
                )
            }
            if (actualizar is ResultadoApi.Error) {
                error = actualizar.mensaje
                guardando = false
                return@launch
            }

            val uriFoto = fotoLocalUri
            if (uriFoto != null) {
                val bytes = runCatching { comprimirImagenParaSubir(contexto, uriFoto) }.getOrNull()
                if (bytes == null) {
                    error = "No se pudo procesar la foto seleccionada."
                    guardando = false
                    return@launch
                }
                val cuerpo = bytes.toRequestBody("image/jpeg".toMediaType())
                val parte = MultipartBody.Part.createFormData("archivo", "perfil.jpg", cuerpo)
                val resultadoFoto = llamarApi { api.subirFoto(corredorId, parte) }
                if (resultadoFoto is ResultadoApi.Error) {
                    error = resultadoFoto.mensaje
                    guardando = false
                    return@launch
                }
            }

            guardando = false
            alContinuar()
        }
    }
}
