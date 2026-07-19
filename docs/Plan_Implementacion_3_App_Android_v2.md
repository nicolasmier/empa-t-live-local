# Plan de Implementación — APP ANDROID (corredores)
## Basado en la Especificación Consolidada v10 (fuente única de verdad). Documento 3 de 3.

# 0. Coordinación entre agentes
- **Este agente es el último en integrar**: desarrolla contra la API **congelada** del agente Servidor (su OpenAPI tras la Fase S4). La app es el cliente más caro de iterar (publicación, dispositivos físicos), así que no se construye contra endpoints en movimiento.
- **Prerrequisitos**: OpenAPI estable + entorno de desarrollo del servidor accesible (en local o por el túnel de pruebas) + un evento seedado En directo para probar.
- La app habla exclusivamente con la **API del corredor** expuesta por el túnel (spec Anexo B §2): auth, perfil, foto, unirse, estado e ingesta de posiciones. No existe para ella ninguna otra superficie.

# Alcance de este agente
App Android nativa (Kotlin sugerido). Sin SOS en v1.0 (pospuesto a v1.1 por decisión de producto — no implementar ni dejar restos de UI).

---

# FASE A1 — Cuenta, perfil y unión al evento
1. Registro/login de corredor contra `/auth/corredores/*`; sesión persistente (cuenta permanente, no se pide login en cada uso).
2. Perfil: nombre, apellidos, club (`PUT /corredores/{id}`) y **foto** (`POST /corredores/{id}/foto`): selección de galería o cámara, recorte/compresión en el dispositivo antes de subir (JPEG, respetando el límite de 5 MB de la API — no delegar en el servidor el rechazo de fotos de 40 MB de cámara moderna).
3. Unirse al evento: campo de código de carrera + confirmación del propio dorsal (decisión 2026-07-19, respaldo contra un email/teléfono mal enlazado) → `POST /eventos/codigo/{codigo}/unirse` → guardar distancia, dorsal y **token de dispositivo en almacenamiento seguro** (EncryptedSharedPreferences/Keystore). Manejar con mensaje claro tanto "no se ha encontrado tu inscripción" (404) como "el dorsal no coincide" (409).
4. Contexto de uso real a tener en cuenta en la UX de esta pantalla: la mayoría de corredores harán registro + código **en la hora previa a la salida** (spec §5), en la calle, con prisa y quizá mala cobertura — el flujo completo debe poder completarse en menos de 2 minutos y tolerar reintentos.

**Aceptación**: flujo completo registro → perfil con foto → código → dorsal en pantalla, en menos de 2 min contra el entorno de desarrollo; el token sobrevive a cerrar y reabrir la app.

# FASE A2 — Servicio de ubicación en segundo plano (el corazón de la app)
1. **Foreground service con notificación persistente** — patrón que Android exige para GPS continuo; sin él, el sistema mata la transmisión a los minutos.
2. Solicitud de exclusión de optimización de batería con pantalla explicativa previa (por qué se pide, qué pasa si no se concede).
3. Frecuencia adaptativa según velocidad (spec §6): parado 60–120 s; caminando/corriendo 15–20 s.
4. Comportamiento de ciclo de vida según spec §5: si el usuario cierra la app (swipe), se deja de transmitir hasta reabrir — no intentar resucitar el servicio a escondidas.

# FASE A3 — Cola local persistente y sincronización
1. **Toda posición se encola siempre** en Room/SQLite y solo se marca enviada al recibir el `202` de la API. Sin conexión —da igual si es el móvil sin cobertura o el servidor caído, indistinguibles a propósito (spec §5)— la cola crece.
2. Al recuperar conexión: envío en **lotes** (el endpoint acepta arrays) con orden por `timestamp_dispositivo`, respetando el rate limit de 1 petición/5 s (agrupar, no ametrallar).
3. La cola sobrevive a reinicios de la app y del teléfono; purga de puntos ya confirmados.
4. Timestamps: cada punto lleva la hora del dispositivo en el momento de la lectura GPS (no la del envío) — es lo que permite al servidor reconstruir el recorrido correctamente tras una sincronización tardía.

**Aceptación A2+A3 (banco de pruebas)**: sesión simulada con ubicaciones mock: 30 min transmitiendo, 15 min en modo avión, reconexión → el servidor recibe el lote completo ordenado, clasificado como `sincronizado`, sin duplicados ni huecos.

# FASE A4 — Pantalla de estado
Consulta pasiva (el corredor no mira el móvil corriendo): dorsal grande, y estado de GPS (activo/sin señal), batería, conexión y transmisión (enviando / encolando sin conexión), usando `GET /inscripciones/{id}/estado` y el estado local del servicio. Semántica de color de la spec (verde/ámbar-gris).

# FASE A5 — Pruebas de campo (obligatorias, no negociables)
El fallo nº 1 de este tipo de apps es el segundo plano según fabricante; no se cierra la fase sin:
1. Caminata real de 1 h con el móvil bloqueado en el bolsillo → recorrido completo en el histórico del servidor.
2. Modo avión 15 min a mitad de la caminata → lote sincronizado correcto al volver.
3. Repetido en **al menos 3 fabricantes** distintos, incluyendo los agresivos con batería (Xiaomi/Samsung/etc.), con la app instalada de cero y siguiendo solo las pantallas de la propia app (sin ajustes manuales ocultos).
4. Medición de batería: consumo < ~10%/h orientativo durante transmisión activa.

**Aceptación**: los 4 puntos superados y documentados (dispositivo, versión Android, resultado).

# FASE A6 — Integración y ensayo general
Participar en el ensayo general conjunto (spec §13): 3–5 móviles reales con la app junto al simulador a 800 corredores virtuales, incluyendo corte de internet del recinto de 10 min (verificar que las apps encolan y sincronizan al volver).

# Riesgos que este agente neutraliza
| Riesgo | Dónde |
|---|---|
| Android mata el GPS en segundo plano | A2 (foreground service) + A5 (multi-fabricante) |
| Pérdida de puntos sin cobertura o con servidor caído | A3 (cola persistente + lotes ordenados) |
| Corredor no logra unirse en la hora previa con prisa | A1 (flujo <2 min con reintentos) |
| Fotos enormes saturan la subida | A1 (compresión en dispositivo) |
| Batería agotada a mitad de carrera | A2 (frecuencia adaptativa) + A5 (medición real) |
