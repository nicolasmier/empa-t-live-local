package com.empatelive.corredor.ui.registro

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory

@Composable
fun RegistroScreen(
    contenedor: AppContainer,
    alRegistrarse: () -> Unit,
    irALogin: () -> Unit,
    // Si llega con email (viene del login al detectar una cuenta pre-cargada sin
    // activar), se rellena y se muestra el aviso de "primera vez".
    emailInicial: String = "",
) {
    val vm: RegistroViewModel = viewModel(
        factory = ViewModelFactory { RegistroViewModel(contenedor.api, contenedor.sesion) },
    )

    val vieneDeInscripcion = emailInicial.isNotBlank()
    LaunchedEffect(emailInicial) {
        if (vieneDeInscripcion && vm.email.isBlank()) vm.email = emailInicial
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Text(
            if (vieneDeInscripcion) "Activa tu cuenta" else "Crear cuenta",
            style = MaterialTheme.typography.headlineSmall,
        )
        if (vieneDeInscripcion) {
            Text(
                "Tu inscripción ya está cargada. Crea una contraseña para activar tu " +
                    "cuenta y poder entrar a la carrera.",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
            )
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
            value = vm.email,
            onValueChange = { vm.email = it },
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )
        OutlinedTextField(
            value = vm.telefono,
            onValueChange = { vm.telefono = it },
            label = { Text("Teléfono (opcional)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )
        Text(
            "Ponlo si el organizador te cargó con un email distinto (o sin email) " +
                "en el Excel de inscripciones — así enlazamos igualmente tu dorsal.",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.fillMaxWidth().padding(top = 2.dp),
        )
        OutlinedTextField(
            value = vm.password,
            onValueChange = { vm.password = it },
            label = { Text("Contraseña (mínimo 8 caracteres)") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
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
            onClick = { vm.registrar(alRegistrarse) },
            enabled = !vm.cargando,
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
        ) {
            if (vm.cargando) {
                CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
            }
            Text(if (vm.cargando) "Creando cuenta…" else "Crear cuenta")
        }

        TextButton(
            onClick = irALogin,
            modifier = Modifier.align(Alignment.CenterHorizontally),
        ) {
            Text("¿Ya tienes cuenta? Inicia sesión")
        }
    }
}
