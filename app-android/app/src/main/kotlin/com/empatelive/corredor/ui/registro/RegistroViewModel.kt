package com.empatelive.corredor.ui.registro

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.RegistroCorredorEntrada
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.extraerCorredorIdDeToken
import com.empatelive.corredor.red.llamarApi
import kotlinx.coroutines.launch

class RegistroViewModel(
    private val api: ApiService,
    private val sesion: SesionSeguraStorage,
) : ViewModel() {
    var nombre by mutableStateOf("")
    var apellidos by mutableStateOf("")
    var email by mutableStateOf("")
    var password by mutableStateOf("")
    var cargando by mutableStateOf(false)
    var error by mutableStateOf<String?>(null)
        private set

    fun registrar(alExito: () -> Unit) {
        if (nombre.isBlank() || apellidos.isBlank() || email.isBlank()) {
            error = "Rellena nombre, apellidos y email."
            return
        }
        if (password.length < 8) {
            error = "La contraseña debe tener al menos 8 caracteres."
            return
        }
        viewModelScope.launch {
            cargando = true
            error = null
            val resultado = llamarApi {
                api.registrarCorredor(
                    RegistroCorredorEntrada(
                        nombre = nombre.trim(),
                        apellidos = apellidos.trim(),
                        email = email.trim(),
                        password = password,
                    ),
                )
            }
            cargando = false
            when (resultado) {
                is ResultadoApi.Ok -> {
                    val corredorId = extraerCorredorIdDeToken(resultado.datos.accessToken)
                    if (corredorId == null) {
                        error = "Sesión inválida recibida del servidor."
                        return@launch
                    }
                    sesion.guardarSesion(corredorId, resultado.datos.accessToken)
                    alExito()
                }
                is ResultadoApi.Error -> error = resultado.mensaje
            }
        }
    }
}
