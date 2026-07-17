package com.empatelive.corredor.ui.login

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.LoginCorredorEntrada
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.extraerCorredorIdDeToken
import com.empatelive.corredor.red.llamarApi
import kotlinx.coroutines.launch

class LoginViewModel(
    private val api: ApiService,
    private val sesion: SesionSeguraStorage,
) : ViewModel() {
    var email by mutableStateOf("")
    var password by mutableStateOf("")
    var cargando by mutableStateOf(false)
    var error by mutableStateOf<String?>(null)
        private set

    fun iniciarSesion(alExito: () -> Unit) {
        if (email.isBlank() || password.isBlank()) {
            error = "Introduce tu email y contraseña."
            return
        }
        viewModelScope.launch {
            cargando = true
            error = null
            val resultado = llamarApi {
                api.loginCorredor(LoginCorredorEntrada(email.trim(), password))
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
