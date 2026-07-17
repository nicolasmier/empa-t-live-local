package com.empatelive.corredor.ui.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.empatelive.corredor.di.AppContainer
import com.empatelive.corredor.ui.ViewModelFactory

@Composable
fun LoginScreen(
    contenedor: AppContainer,
    alIniciarSesion: () -> Unit,
    irARegistro: () -> Unit,
) {
    val vm: LoginViewModel = viewModel(
        factory = ViewModelFactory { LoginViewModel(contenedor.api, contenedor.sesion) },
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("EmpateLive — Corredor", style = MaterialTheme.typography.headlineSmall)
        Text("Entra con tu cuenta", style = MaterialTheme.typography.bodyMedium)

        OutlinedTextField(
            value = vm.email,
            onValueChange = { vm.email = it },
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
        )
        OutlinedTextField(
            value = vm.password,
            onValueChange = { vm.password = it },
            label = { Text("Contraseña") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
        )

        vm.error?.let {
            Text(
                it,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 8.dp),
            )
        }

        Button(
            onClick = { vm.iniciarSesion(alIniciarSesion) },
            enabled = !vm.cargando,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
        ) {
            if (vm.cargando) {
                CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
            }
            Text(if (vm.cargando) "Entrando…" else "Entrar")
        }

        TextButton(
            onClick = irARegistro,
            modifier = Modifier.align(Alignment.CenterHorizontally),
        ) {
            Text("¿No tienes cuenta? Regístrate")
        }
    }
}
