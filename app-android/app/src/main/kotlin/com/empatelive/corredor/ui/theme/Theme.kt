package com.empatelive.corredor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontWeight

private val EsquemaOscuro = darkColorScheme(
    primary = AcentoPrimario,
    onPrimary = SobrePrimario,
    primaryContainer = ContenedorPrimario,
    onPrimaryContainer = SobreContenedorPrimario,
    secondary = AcentoSecundario,
    onSecondary = SobreSecundario,
    secondaryContainer = ContenedorSecundario,
    onSecondaryContainer = SobreContenedorSecundario,
    background = FondoOscuro,
    onBackground = TextoPrincipalOscuro,
    surface = SuperficieOscura,
    onSurface = TextoPrincipalOscuro,
    surfaceVariant = SuperficieVariante,
    onSurfaceVariant = TextoSecundarioOscuro,
    outline = ContornoOscuro,
    outlineVariant = ContornoVarianteOscuro,
    error = ErrorOscuro,
    onError = SobreErrorOscuro,
    errorContainer = ContenedorErrorOscuro,
    onErrorContainer = SobreContenedorErrorOscuro,
    inverseSurface = TextoPrincipalOscuro,
    inverseOnSurface = SuperficieOscura,
    inversePrimary = ContenedorPrimario,
    surfaceTint = AcentoPrimario,
)

// Tipografía más gruesa ("tipo negrita", petición 2026-07-22): se sube el peso
// de los estilos que usan las pantallas para que el texto se lea más marcado
// sobre el fondo azul. Se parte de los valores por defecto de Material3 y solo
// se cambia el `fontWeight`.
private val TipografiaBase = Typography()
private val TipografiaEmpateLive = Typography(
    headlineSmall = TipografiaBase.headlineSmall.copy(fontWeight = FontWeight.Bold),
    titleLarge = TipografiaBase.titleLarge.copy(fontWeight = FontWeight.Bold),
    titleMedium = TipografiaBase.titleMedium.copy(fontWeight = FontWeight.Bold),
    bodyLarge = TipografiaBase.bodyLarge.copy(fontWeight = FontWeight.SemiBold),
    bodyMedium = TipografiaBase.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
    bodySmall = TipografiaBase.bodySmall.copy(fontWeight = FontWeight.Medium),
    labelLarge = TipografiaBase.labelLarge.copy(fontWeight = FontWeight.Bold),
)

/** Tema único de la app — siempre oscuro/azul (identidad de CronoEmpate), sin
 * seguir el modo claro/oscuro del sistema. Texto en gris claro y tipografía
 * más gruesa (ver Color.kt y TipografiaEmpateLive). */
@Composable
fun EmpateLiveTheme(contenido: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = EsquemaOscuro,
        typography = TipografiaEmpateLive,
        content = contenido,
    )
}
