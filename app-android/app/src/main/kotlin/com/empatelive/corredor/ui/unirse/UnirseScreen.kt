package com.empatelive.corredor.ui.unirse

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory
import com.empatelive.corredor.ui.estado.PanelEstado

@Composable
fun UnirseScreen(contenedor: AppContainer) {
    val vm: UnirseViewModel = viewModel(
        factory = ViewModelFactory { UnirseViewModel(contenedor.api, contenedor.sesion) },
    )

    val dorsal = vm.dorsal
    if (dorsal != null) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                "Ya estás unido",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.align(Alignment.CenterHorizontally),
            )
            Text(
                vm.distanciaNombre ?: "",
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 4.dp),
            )
            Text(
                dorsal,
                fontSize = 72.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
            )
            Text(
                "Tu dorsal",
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.fillMaxWidth(),
            )

            PanelEstado(contenedor)

            TransmisionSeccion()

            OutlinedButton(
                onClick = vm::unirseAOtroEvento,
                modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 32.dp),
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
