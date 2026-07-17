package com.empatelive.corredor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.login.LoginScreen
import com.empatelive.corredor.ui.perfil.PerfilScreen
import com.empatelive.corredor.ui.registro.RegistroScreen
import com.empatelive.corredor.ui.unirse.UnirseScreen

private object Rutas {
    const val LOGIN = "login"
    const val REGISTRO = "registro"
    const val PERFIL = "perfil"
    const val UNIRSE = "unirse"
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val contenedor = AppContainer(applicationContext)

        // FASE A1: registro/login → perfil → unirse (→ dorsal). Si ya hay
        // sesión guardada de un arranque anterior, se salta directo a donde
        // se quedó — "el token sobrevive a cerrar y reabrir la app".
        val destinoInicial = when {
            !contenedor.sesion.haySesion() -> Rutas.LOGIN
            !contenedor.sesion.hayInscripcion() -> Rutas.PERFIL
            else -> Rutas.UNIRSE
        }

        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val navController = rememberNavController()
                    NavHost(navController = navController, startDestination = destinoInicial) {
                        composable(Rutas.LOGIN) {
                            LoginScreen(
                                contenedor = contenedor,
                                alIniciarSesion = {
                                    navController.navigate(Rutas.PERFIL) {
                                        popUpTo(Rutas.LOGIN) { inclusive = true }
                                    }
                                },
                                irARegistro = { navController.navigate(Rutas.REGISTRO) },
                            )
                        }
                        composable(Rutas.REGISTRO) {
                            RegistroScreen(
                                contenedor = contenedor,
                                alRegistrarse = {
                                    navController.navigate(Rutas.PERFIL) {
                                        popUpTo(Rutas.LOGIN) { inclusive = true }
                                    }
                                },
                                irALogin = { navController.popBackStack() },
                            )
                        }
                        composable(Rutas.PERFIL) {
                            PerfilScreen(
                                contenedor = contenedor,
                                alContinuar = {
                                    navController.navigate(Rutas.UNIRSE) {
                                        popUpTo(Rutas.PERFIL) { inclusive = true }
                                    }
                                },
                            )
                        }
                        composable(Rutas.UNIRSE) {
                            UnirseScreen(contenedor = contenedor)
                        }
                    }
                }
            }
        }
    }
}
