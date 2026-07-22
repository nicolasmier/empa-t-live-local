package com.empatelive.corredor.ui.theme

import androidx.compose.ui.graphics.Color

// Paleta azul de EmpateLive/CronoEmpate, unificada con la web pública y el panel
// (web-publica/src/index.css: --azul-oscuro / --azul-superficie / --azul-acento…).
// La app comparte identidad con la cabecera de la web (fondo azul + logo blanco).
// El semáforo verde/ámbar/gris de PanelEstado es independiente de este tema
// (colores fijos, spec Anexo E), así que el acento azul no choca con ese
// significado.
val FondoOscuro = Color(0xFF171F6E) // --azul-oscuro
val SuperficieOscura = Color(0xFF1F2C86) // --azul-superficie
val SuperficieVariante = Color(0xFF283A9C) // --azul-superficie-clara
val ContornoOscuro = Color(0xFF364AA8) // --azul-borde
val ContornoVarianteOscuro = Color(0xFF2A3A8F)

// Texto en gris claro (no blanco puro): se pide "gris claro" y una fuente más
// gruesa (ver Typography en Theme.kt) para que se lea bien sobre el azul.
val TextoPrincipalOscuro = Color(0xFFCBD2E8) // gris claro azulado
val TextoSecundarioOscuro = Color(0xFFAAB3D6) // --texto-suave, algo más apagado

val AcentoPrimario = Color(0xFF3D6BF0) // --azul-acento
val SobrePrimario = Color(0xFFFFFFFF)
val ContenedorPrimario = Color(0xFF283A9C)
val SobreContenedorPrimario = Color(0xFFDDE4FF)

val AcentoSecundario = Color(0xFF9FB4F0)
val SobreSecundario = Color(0xFF10205E)
val ContenedorSecundario = Color(0xFF2C3E96)
val SobreContenedorSecundario = Color(0xFFDDE4FF)

val ErrorOscuro = Color(0xFFFFB4AB)
val SobreErrorOscuro = Color(0xFF690005)
val ContenedorErrorOscuro = Color(0xFF93000A)
val SobreContenedorErrorOscuro = Color(0xFFFFDAD6)
