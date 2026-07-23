package com.empatelive.corredor.ui.unirse

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import com.empatelive.corredor.BuildConfig
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory
import com.empatelive.corredor.ui.estado.PanelEstado

/** Desenvuelve el Context de Compose hasta la Activity, para poder minimizar
 * la app (`moveTaskToBack`) sin parar el servicio de transmisión. */
private fun Context.buscarActivity(): Activity? {
    var contexto: Context? = this
    while (contexto is ContextWrapper) {
        if (contexto is Activity) return contexto
        contexto = contexto.baseContext
    }
    return null
}

@Composable
fun UnirseScreen(contenedor: AppContainer) {
    val vm: UnirseViewModel = viewModel(
        factory = ViewModelFactory { UnirseViewModel(contenedor.api, contenedor.sesion) },
    )

    val dorsal = vm.dorsal
    if (dorsal != null) {
        val contexto = LocalContext.current

        // Recarga el perfil cada vez que la pantalla vuelve a primer plano (p. ej.
        // tras cambiar la foto en Perfil y volver): así toma la nueva `foto_url`
        // con `?v=` y Coil descarga la imagen nueva.
        val lifecycleOwner = LocalLifecycleOwner.current
        DisposableEffect(lifecycleOwner) {
            val observador = LifecycleEventObserver { _, evento ->
                if (evento == Lifecycle.Event.ON_RESUME) vm.refrescarPerfil()
            }
            lifecycleOwner.lifecycle.addObserver(observador)
            onDispose { lifecycleOwner.lifecycle.removeObserver(observador) }
        }

        val fotoAMostrar: Any? = vm.fotoUrl?.let { ruta ->
            if (ruta.startsWith("http")) ruta else BuildConfig.BASE_URL + ruta
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            // Cabecera "hero": la foto grande como CAPA INFERIOR, con el texto
            // (En carrera, nombre y dorsal) encima. Si no hay foto, el mismo
            // bloque sin imagen de fondo.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(320.dp)
                    .clip(RoundedCornerShape(20.dp)),
                contentAlignment = Alignment.Center,
            ) {
                if (fotoAMostrar != null) {
                    AsyncImage(
                        model = fotoAMostrar,
                        contentDescription = "Tu foto",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize(),
                    )
                    // Velo oscuro para que el texto se lea sobre la foto.
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(
                                Brush.verticalGradient(
                                    listOf(
                                        Color(0x66000000),
                                        Color(0x22000000),
                                        Color(0xAA000000),
                                    ),
                                ),
                            ),
                    )
                }

                Column(
                    modifier = Modifier.fillMaxWidth().padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        "En carrera",
                        style = MaterialTheme.typography.headlineSmall,
                        color = Color.White,
                    )
                    vm.nombreCorredor?.let { nombre ->
                        Text(
                            nombre,
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth().padding(top = 2.dp),
                        )
                    }
                    Text(
                        vm.distanciaNombre ?: "",
                        style = MaterialTheme.typography.bodyLarge,
                        color = Color.White,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                    Text(
                        dorsal,
                        fontSize = 72.sp,
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    )
                    Text(
                        "Tu dorsal",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }

            PanelEstado(contenedor)

            TransmisionSeccion()

            // Minimizar de forma segura: manda la app al fondo (como el botón
            // Inicio) SIN parar el servicio de ubicación. El foreground service
            // sigue transmitiendo con la pantalla apagada y la UI sin dibujarse,
            // que es el menor consumo posible. NO es cerrar la app (deslizarla en
            // recientes sí la para, stopWithTask): por eso "de manera segura".
            Button(
                onClick = { contexto.buscarActivity()?.moveTaskToBack(true) },
                modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
            ) {
                Text("Minimizar y ahorrar batería")
            }
            Text(
                "Sigue transmitiendo con la pantalla apagada. No cierres la app " +
                    "deslizándola: eso sí detiene la transmisión.",
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(top = 6.dp),
            )

            OutlinedButton(
                onClick = vm::unirseAOtroEvento,
                modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 24.dp),
            ) {
                Text("Unirme a otro evento")
            }
        }
        return
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("Unirte a la carrera", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Introduce el código de acceso del evento (te lo da el organizador).",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 4.dp, bottom = 16.dp),
        )

        OutlinedTextField(
            value = vm.codigo,
            onValueChange = { vm.codigo = it },
            label = { Text("Código de la carrera") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = vm.dorsalIntroducido,
            onValueChange = { vm.dorsalIntroducido = it },
            label = { Text("Tu dorsal") },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )
        Text(
            "El dorsal que te dio el organizador — confirma que la carrera te " +
                "reconoce a ti y no a otro corredor.",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(top = 2.dp),
        )

        vm.error?.let {
            Text(
                it,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 8.dp),
            )
        }

        Button(
            onClick = vm::unirse,
            enabled = !vm.cargando,
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
        ) {
            if (vm.cargando) {
                CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
            }
            Text(if (vm.cargando) "Uniendo…" else "Unirme")
        }
    }
}
