package com.empatelive.corredor.ui.perfil

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import com.empatelive.corredor.BuildConfig
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory

@Composable
fun PerfilScreen(
    contenedor: AppContainer,
    alContinuar: () -> Unit,
) {
    val vm: PerfilViewModel = viewModel(
        factory = ViewModelFactory { PerfilViewModel(contenedor.api, contenedor.sesion) },
    )
    val contexto = LocalContext.current

    val selectorFoto = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia(),
    ) { uri -> if (uri != null) vm.fotoLocalUri = uri }

    if (vm.cargando) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Text("Tu perfil", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Nombre, apellidos, club y una foto — se verán en la web pública junto a tu dorsal.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 4.dp, bottom = 16.dp),
        )

        // La API sirve la foto en una ruta relativa (`/media/fotos/...`, LAN);
        // hay que anteponerle la base para que Coil pueda cargarla.
        val fotoAMostrar: Any? = vm.fotoLocalUri ?: vm.fotoUrlServidor?.let { ruta ->
            if (ruta.startsWith("http")) ruta else BuildConfig.BASE_URL + ruta
        }
        Box(
            modifier = Modifier
                .size(120.dp)
                .align(Alignment.CenterHorizontally)
                .clip(CircleShape),
        ) {
            if (fotoAMostrar != null) {
                AsyncImage(
                    model = fotoAMostrar,
                    contentDescription = "Foto de perfil",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize(),
                )
            }
        }
        OutlinedButton(
            onClick = {
                selectorFoto.launch(
                    PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                )
            },
            modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 8.dp),
        ) {
            Text(if (fotoAMostrar != null) "Cambiar foto" else "Elegir foto")
        }

        OutlinedTextField(
            value = vm.nombre,
            onValueChange = { vm.nombre = it },
            label = { Text("Nombre") },
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
        )
        OutlinedTextField(
            value = vm.apellidos,
            onValueChange = { vm.apellidos = it },
            label = { Text("Apellidos") },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )
        OutlinedTextField(
            value = vm.club,
            onValueChange = { vm.club = it },
            label = { Text("Club (opcional)") },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )

        vm.error?.let {
            Text(
                it,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 8.dp),
            )
        }

        Button(
            onClick = { vm.guardar(contexto, alContinuar) },
            enabled = !vm.guardando,
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
        ) {
            if (vm.guardando) {
                CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
            }
            Text(if (vm.guardando) "Guardando…" else "Continuar")
        }
    }
}
