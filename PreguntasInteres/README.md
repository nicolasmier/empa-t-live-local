# PreguntasInteres

Preguntas frecuentes sobre EmpateLive, una por fichero, respondidas contra el
código y la spec v10 (`docs/spec-v10.md`, que es la fuente de verdad). Si algo
aquí discrepa del código, revísalo: manda la spec.

## Índice

### Cuentas, corredores e inscripciones
- [ComoSeEnlaza](ComoSeEnlaza.md) — cuenta vs inscripción; cómo se enlaza al corredor por email/teléfono.
- [ImportarCorredoresExcel](ImportarCorredoresExcel.md) — formato del Excel y reglas de importación.
- [AltaIndividualDeCorredores](AltaIndividualDeCorredores.md) — dar de alta corredores uno a uno desde el panel.

### Evento y operación
- [EstadosDelEvento](EstadosDelEvento.md) — máquina de estados y transiciones válidas.
- [SalidaProgramadaYRestablecer](SalidaProgramadaYRestablecer.md) — programar la hora de salida y restablecerla.
- [EstadoTransmitiendoVsSinSenal](EstadoTransmitiendoVsSinSenal.md) — cómo se detecta el estado de cada corredor.
- [RolesAdminYOperador](RolesAdminYOperador.md) — qué puede hacer cada rol del panel.

### App y transmisión GPS
- [TransmisionGpsYSinConexion](TransmisionGpsYSinConexion.md) — foreground service, cola offline, batería, cerrar la app.
- [IngestaDePosiciones](IngestaDePosiciones.md) — cómo procesa el servidor los puntos GPS.
- [CompilarEInstalarApk](CompilarEInstalarApk.md) — generar el APK y qué hacer si cambia la IP.
- [PersistenciaLoginApp](PersistenciaLoginApp.md) — dónde persisten las credenciales y la sesión de un corredor.

### Arquitectura, red y seguridad
- [ComoLleganLosDatosDelMovil](ComoLleganLosDatosDelMovil.md) — el túnel de Cloudflare (corredores fuera de la LAN).
- [QueSeExponePorInternet](QueSeExponePorInternet.md) — superficies expuestas vs LAN-only.
- [TiposDeToken](TiposDeToken.md) — los tres tokens y para qué sirve cada uno.
- [BackupsYSeguridad](BackupsYSeguridad.md) — contraseñas, tokens, rate limiting, copias de seguridad.

### Alcance
- [PorQueNoHaySos](PorQueNoHaySos.md) — por qué el SOS está pospuesto a la v1.1.
- [WebPublicaComoSeVe](WebPublicaComoSeVe.md) — cómo se ve la carrera en la pantalla del recinto.
