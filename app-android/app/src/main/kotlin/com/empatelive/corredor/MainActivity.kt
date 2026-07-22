package com.empatelive.corredor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ubicacion.LocationTrackingService
import com.empatelive.corredor.ui.login.LoginScreen
import com.empatelive.corredor.ui.perfil.PerfilScreen
import com.empatelive.corredor.ui.registro.RegistroScreen
import com.empatelive.corredor.ui.theme.EmpateLiveTheme
import com.empatelive.corredor.ui.unirse.UnirseScreen

private object Rutas {
    const val LOGIN = "login"
    const val REGISTRO = "registro"
    const val PERFIL = "perfil"
    const val UNIRSE = "unirse"
}

class MainActivity : ComponentActivity() {
    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Tema siempre oscuro (EmpateLiveTheme): forzar iconos claros en las
        // barras de sistema, si no `enableEdgeToEdge()` decide según el modo
        // claro/oscuro del SISTEMA, que puede no coincidir con el de la app.
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
        )

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
            EmpateLiveTheme {
                val contexto = LocalContext.current
                val navController = rememberNavController()
                val entradaActual by navController.currentBackStackEntryAsState()
                val rutaActual = entradaActual?.destination?.route

                // Se puede volver atrás salvo que estemos en la raíz de la pila
                // (la primera pantalla mostrada). El logout solo tras autenticar.
                val puedeVolver = navController.previousBackStackEntry != null
                val esAutenticada = rutaActual == Rutas.PERFIL || rutaActual == Rutas.UNIRSE
                val mostrarBarra = puedeVolver || esAutenticada

                var confirmarCierre by remember { mutableStateOf(false) }

                // Logout: para la transmisión (si estuviera activa), limpia la
                // sesión y el token de dispositivo (SesionSeguraStorage.cerrarSesion)
                // y vuelve a login vaciando toda la pila de navegación.
                fun cerrarSesion() {
                    contexto.stopService(LocationTrackingService.intentPara(contexto))
                    contenedor.sesion.cerrarSesion()
                    navController.navigate(Rutas.LOGIN) {
                        popUpTo(0) { inclusive = true }
                        launchSingleTop = true
                    }
                }

                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(MaterialTheme.colorScheme.background),
                ) {
                    // Fondo: el logo de la cabecera de la web (blanco) como marca
                    // de agua tenue sobre el azul — misma identidad que la web.
                    Image(
                        painter = painterResource(R.drawable.logo_cabecera),
                        contentDescription = null,
                        modifier = Modifier
                            .align(Alignment.Center)
                            .fillMaxWidth()
                            .padding(horizontal = 32.dp),
                        alpha = 0.08f,
                        contentScale = ContentScale.FillWidth,
                    )

                    Scaffold(
                        containerColor = Color.Transparent,
                        // Sin esto, al no haber un Surface que fije LocalContentColor,
                        // el texto por defecto caía a negro sobre el fondo azul.
                        contentColor = MaterialTheme.colorScheme.onBackground,
                        topBar = {
                            if (mostrarBarra) {
                                TopAppBar(
                                    title = { Text("EmpateLive") },
                                    navigationIcon = {
                                        if (puedeVolver) {
                                            IconButton(onClick = { navController.popBackStack() }) {
                                                Icon(
                                                    Icons.AutoMirrored.Filled.ArrowBack,
                                                    contentDescription = "Atrás",
                                                )
                                            }
                                        }
                                    },
                                    actions = {
                                        if (esAutenticada) {
                                            TextButton(onClick = { confirmarCierre = true }) {
                                                Text("Cerrar sesión")
                                            }
                                        }
                                    },
                                    colors = TopAppBarDefaults.topAppBarColors(
                                        containerColor = Color.Transparent,
                                    ),
                                )
                            }
                        },
                    ) { innerPadding ->
                        NavHost(
                            navController = navController,
                            startDestination = destinoInicial,
                            modifier = Modifier.padding(innerPadding),
                        ) {
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
                                    // Sin popUpTo: se conserva Perfil en la pila para
                                    // poder volver desde Unirse a corregir el perfil.
                                    alContinuar = { navController.navigate(Rutas.UNIRSE) },
                                )
                            }
                            composable(Rutas.UNIRSE) {
                                UnirseScreen(contenedor = contenedor)
                            }
                        }
                    }
                }

                if (confirmarCierre) {
                    AlertDialog(
                        onDismissRequest = { confirmarCierre = false },
                        title = { Text("Cerrar sesión") },
                        text = {
                            Text(
                                "Se detendrá la transmisión de tu posición y volverás a la " +
                                    "pantalla de inicio. Tendrás que volver a entrar y unirte " +
                                    "a la carrera.",
                            )
                        },
                        confirmButton = {
                            TextButton(onClick = {
                                confirmarCierre = false
                                cerrarSesion()
                            }) { Text("Cerrar sesión") }
                        },
                        dismissButton = {
                            TextButton(onClick = { confirmarCierre = false }) { Text("Cancelar") }
                        },
                    )
                }
            }
        }
    }
}
