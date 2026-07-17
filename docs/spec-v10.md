# Plataforma de Seguimiento GPS para Carreras — Especificación Consolidada v10
## Documento maestro (spec-driven). Sustituye a la v9 como fuente única de verdad.

> **Cambios en v10 (decisiones del producto):**
> A. **Flujo de datos app → servidor especificado para desarrollo**: la app envía dos tipos de datos por el túnel — puntos GPS y datos de perfil (nombre, apellidos, club y **foto**, con endpoint multipart propio). La foto se almacena en el servidor local y se sirve en la LAN a la web pública. Las fotos pasan de v1.1 a v1.0.
> B. **Ventana operativa definida**: como norma general, el servidor se enciende **una hora antes de la carrera** y en ese momento se avisa a los corredores para introducir el código general del evento, vinculando sus señales GPS al evento en marcha.
> C. **SOS pospuesto a v1.1**: se elimina de todos los flujos, modelo de datos, API y UI de la v1.0.
>
> **Registro de correcciones aplicadas en la consolidación v9 (histórico):**
> 1. **Alcance del túnel corregido**: no expone "solo la ingesta de posiciones" — la app Android también necesita internet para login del corredor, unirse al evento, editar perfil y consultar estado. El túnel expone el subconjunto de API del corredor; el panel de administración y la web pública quedan LAN-only.
> 2. **Ventana operativa previa**: los corredores necesitan que el servidor esté encendido *antes* del día de la carrera para registrarse y unirse; se define una ventana previa recomendada.
> 3. **Estados y API alineados**: unirse a un evento se permite en Publicado/Preparación/En directo; el envío de posiciones solo se acepta En directo.
> 4. **Puertos unificados**: panel `:8080`, web pública `:8081`.
> 5. **SOS definido a nivel de flujo**: envío inmediato, fuera del intervalo normal y exento del límite de frecuencia.
> 6. **Tokens de dispositivo**: se almacena el hash, nunca el token en claro (coherencia con el criterio de contraseñas).
> 7. **`estado_transmision` eliminado del modelo de datos**: el estado se calcula siempre a partir de timestamps (fuente única de verdad).
> 8. Umbral de licencia de Docker Desktop corregido a dólares (10M USD).

> **Revisión editorial SDD (2026-07-16)**: auditoría de calidad Spec-Driven Development — numeración estable de requisitos funcionales (RF-xxx, sección 6), criterios de éxito medibles (CE-xxx, sección 15 nueva), escenarios de aceptación Dado/Cuando/Entonces y casos límite (EA-xxx, sección 5), supuestos explícitos (sección 16 nueva) y marcadores `[NEEDS CLARIFICATION: …]` en las ambigüedades detectadas. **Sin cambios de decisión de producto** y sin renumerar secciones ni anexos existentes.

> **Clarify SDD (2026-07-16)**: resueltos los 16 marcadores `[NEEDS CLARIFICATION]` bloqueantes para el servidor (Plan 1) con decisiones del responsable — máquina de estados (ingesta fuera de En directo, retroceso Finalizado→En directo), intervalos GPS por defecto, importación (dorsal duplicado, formato del Excel, email existente), foto (5 MB, lado máx. 512 px), ingesta (umbrales `directo`/`sospechoso`, lote máximo, evento≠token), sesiones, login, tokens de dispositivo y hash de contraseñas (argon2id). Quedan abiertos los marcadores **no bloqueantes** (favoritos, NTP, objetivos de CE-005/006/007, retención, catálogo de `tipo` de incidencia, licencia de Docker Desktop, Electron vs. Tauri).

---

# PARTE I — ESPECIFICACIÓN DE REQUISITOS (SRS)

## 1. Visión del producto
Plataforma profesional de seguimiento GPS para carreras deportivas, dirigida a empresas de cronometraje. Infraestructura 100% propia y local (el PC del Administrador), con la única dependencia externa —asumida y documentada— del proveedor de túnel usado para que las apps de los corredores alcancen el servidor (Parte II, Anexo D).

## 2. Objetivos
- Seguimiento GPS en tiempo real de 300–800 corredores por evento.
- Visualización atractiva y legible a distancia en la pantalla del recinto.
- Administración sencilla desde navegador, usable sin internet.
- Máxima autonomía de batería en la app Android.
- Puesta en marcha por el Administrador sin conocimientos técnicos (launcher gráfico, sin terminal).

## 3. Alcance
**Incluye**: servidor local (API + PostgreSQL en Docker), panel web de administración (LAN), web pública / pantalla de espectadores (LAN), app Android para corredores, launcher gráfico de escritorio, túnel de salida para la API del corredor.

**Fuera del alcance inicial**: iOS, dispositivos GPS dedicados, clasificaciones oficiales, acceso remoto de espectadores por internet, multiorganización/SaaS.

## 4. Roles
- **Administrador**: crea y configura eventos, importa corredores, gestiona GPX e imágenes, supervisa incidencias, inicia/detiene el servidor. No existe soporte técnico externo durante la carrera: si algo falla, la resolución depende del propio Administrador (riesgo aceptado, sección 14).
- **Operador**: supervisión y consulta; sin permisos de configuración.
- **Corredor**: cuenta permanente; edita nombre, apellidos, club y foto; introduce el código de carrera; consulta su estado de transmisión.
- **Espectador**: presente físicamente en el recinto; ve la pantalla local y usa sus filtros.

## 5. Casos de uso

### Evento
Un evento tiene un `codigo_acceso` único (alias legible, p. ej. `MADRID2026`) y puede tener múltiples distancias (10K, 22K…), cada una con su GPX, sus corredores y su mapa.

### Flujo del corredor
1. Instala la app una sola vez y crea su cuenta permanente.
2. Completa su perfil (nombre, apellidos, club, foto).
3. Introduce el código de carrera → la app recupera su inscripción (distancia y dorsal) y recibe un token de dispositivo.
4. El día de la carrera, la app transmite en segundo plano.
5. Si cierra la app, deja de transmitir hasta reabrirla.

**Ventana operativa (decisión v10)**: los pasos 1–3 requieren servidor y túnel activos. Como norma general, el Administrador enciende el servidor **una hora antes de la carrera**; en ese momento se avisa a los corredores (megafonía, cartelería con el código, mensajería) para que abran la app, completen registro y perfil si no lo tienen hecho e introduzcan el código general del evento — eso vincula su señal GPS al evento en marcha. Con 300–800 corredores uniéndose en esa hora la carga es mínima (<1 petición/s). El Administrador puede encenderlo antes si lo prefiere (p. ej. durante la recogida de dorsales).

**Escenarios de aceptación (Dado/Cuando/Entonces)**:
- **EA-001** — Dado un corredor con cuenta e inscripción importada en una distancia del evento, y el evento en Publicado, Preparación o En directo, cuando introduce el `codigo_acceso`, entonces la app recibe su distancia, su dorsal y un token de dispositivo.
- **EA-002** — Dado un corredor unido al evento y el evento En directo, cuando la app envía posiciones con su token de dispositivo, entonces la API responde `202` con el número de puntos procesados y la posición del corredor se actualiza en la web pública en el siguiente sondeo.
- **EA-003** — Dado un corredor transmitiendo, cuando cierra la app, entonces deja de transmitir hasta reabrirla; superado `umbral_sin_senal_seg`, la web pública lo muestra como `sin_senal` con la hora de su última posición.

### Sin cobertura (corredor o servidor)
- Si el corredor pierde cobertura **o** el servidor está caído, la app se comporta igual: almacena las posiciones localmente.
- Al recuperar conexión, sincroniza el lote acumulado.
- El servidor guarda todos los puntos en el histórico, pero solo el más reciente pasa a "posición actual" (el corredor no retrocede visualmente).
- La web muestra la última posición conocida y su hora; el panel registra la incidencia y muestra un aviso.

**Escenarios de aceptación (Dado/Cuando/Entonces)**:
- **EA-004** — Dado un corredor sin cobertura o un servidor caído, cuando la app genera posiciones, entonces las almacena localmente sin perder ninguna.
- **EA-005** — Dado un lote de posiciones acumulado sin conexión, cuando la app recupera conexión, entonces sincroniza el lote completo; el servidor guarda todos los puntos en `posiciones_historico` con `origen = sincronizado` y solo el más reciente actualiza `posiciones_actuales`.
- **EA-006** — Dado un corredor cuya última posición supera `umbral_sin_senal_seg`, entonces la web pública muestra su última posición conocida con su hora, y el panel registra la incidencia y muestra un aviso.

### Casos límite (escenarios de aceptación)
- **EA-007** — *Lote sincronizado desordenado*: dado un lote cuyos puntos llegan desordenados cronológicamente, cuando se procesa, entonces todos los puntos se guardan en el histórico y `posiciones_actuales` solo se actualiza con puntos más recientes que el almacenado (la posición nunca retrocede; Anexo A).
- **EA-008** — *Timestamps con desviación excesiva*: dado un punto cuya desviación `|timestamp_recepcion − timestamp_dispositivo|` supera 600 s (o cuyo `timestamp_dispositivo` está más de 120 s en el futuro), cuando se ingiere, entonces se guarda marcado como `sospechoso` sin descartarse (Anexo B §5).
- **EA-009** — *Unirse en estado incorrecto*: dado un evento en Borrador, Finalizado o Archivado, cuando un corredor intenta unirse con el código, entonces la petición se rechaza con error claro (sección 11).
- **EA-010** — *Ingesta fuera de En directo*: dado un evento que no está En directo, cuando llega un envío de posiciones, entonces se rechaza con error claro (HTTP `409`) sin almacenarse (sección 11).
- **EA-011** — *Dorsal duplicado en importación*: dado un Excel con un dorsal repetido dentro de la misma distancia, cuando se importa, entonces la restricción `UNIQUE (distancia_id, dorsal)` impide esa fila; se **importan las filas válidas y se devuelve un informe fila a fila** con los conflictos (decisión clarify 2026-07-16; coherente con el informe de importación por fila del plan W3). La importación es idempotente.
- **EA-012** — *Corredor sin inscripción*: dado un corredor autenticado sin inscripción en el evento, cuando introduce el código, entonces recibe el error claro "no se ha encontrado tu inscripción; contacta con el organizador" (Anexo B §5).
- **EA-013** — *Foto inválida*: dado un fichero que no es JPEG/PNG (validado por su tipo real, no por la extensión) o que excede el límite de tamaño, cuando se sube como foto de perfil, entonces el servidor lo rechaza con error claro (Anexo B §5).
- **EA-014** — *Pérdida del túnel En directo*: dado que el túnel cae durante la carrera, entonces las apps almacenan localmente y sincronizan al restablecerse; la web pública (LAN) sigue mostrando las últimas posiciones recibidas y el launcher refleja la caída en su semáforo de túnel (sección 13, Anexo C).

## 6. Requisitos funcionales

Cada requisito tiene un identificador estable `RF-xxx` para trazabilidad desde planes de implementación y tests. El contenido es el ya consolidado; la revisión SDD solo añade la numeración.

### Panel de administración (LAN, `:8080`)
- **RF-001** — CRUD y duplicado de eventos; varias distancias por evento.
- **RF-002** — Importación de corredores desde Excel; carga de GPX por distancia.
- **RF-003** — Gestión de cartel, patrocinadores, noticias e imágenes.
- **RF-004** — Configuración por evento: intervalos GPS, umbral de "sin señal", información visible, colores.
  - Valores por defecto al crear un evento (decisión clarify 2026-07-16): `intervalo_gps_parado_seg = 90`, `intervalo_gps_movimiento_seg = 20`, `umbral_sin_senal_seg = 180` (el umbral supera dos ciclos en parado para no marcar "sin señal" a un corredor detenido). Editables por evento.
- **RF-005** — Usable 100% sin internet (solo la recepción de posiciones necesita el túnel).

### App Android
- **RF-006** — Transmisión en segundo plano; solicitud de exclusión de optimización de batería.
- **RF-007** — Pantalla de estado: GPS, batería, conexión, transmisión y dorsal.
- **RF-008** — **Datos que la app envía al servidor (v10)** — dos flujos por el túnel:
  1. *Posiciones GPS*: por punto, timestamp del dispositivo, latitud, longitud, precisión, velocidad y batería. La identidad (inscripción) se deriva del token, nunca del payload.
  2. *Perfil*: nombre, apellidos y club (`PUT /corredores/{id}`) y foto (`POST /corredores/{id}/foto`, multipart). El servidor guarda la foto en almacenamiento local y la sirve en la LAN para la web pública (Anexo B §5).
- **RF-009** — Frecuencia orientativa: parado 60–120 s; caminando/corriendo 15–20 s.

### Web pública — pantalla local del recinto (LAN, `:8081`)
- **RF-010** — Cabecera: logo Cronoempate, nombre de la prueba, tiempo transcurrido.
- **RF-011** — Filtros: dorsal(es), todos, favoritos — resueltos en el cliente.
  - [NEEDS CLARIFICATION: los favoritos figuran aquí y en el Anexo C como filtro de v1.0, pero el roadmap (sección 14) sitúa "favoritos" en v1.1 — ¿en qué versión entran?]
- **RF-012** — Por distancia: mapa independiente, GPX en rojo, corredores como bolitas con dorsal, movimiento suave (interpolación en cliente).
- **RF-013** — Ficha al pulsar un corredor: foto, nombre, apellidos, club.
- **RF-014** — Debajo: cartel, información, patrocinadores, listado de corredores.
- **RF-015** — Actualización por sondeo (polling) cada 3–5 s (Anexo B, sección 5).

## 7. Requisitos no funcionales
- API-first; Docker; PostgreSQL; seguridad mediante tokens (Anexo E).
- Volumen: 300–800 corredores/evento (pico ~50 peticiones/s de ingesta).
- Despliegue: 100% local; a internet solo sale el subconjunto de API del corredor, vía Cloudflare Tunnel (Anexo D).
- Preparado para GPS dedicados (v2.0).
- Cumplimiento RGPD/LOPDGDD (sección 8 y Anexo F).

## 8. Protección de datos (resumen; detalle en Anexo F)
La plataforma trata datos personales y de geolocalización de personas identificadas: aplica el RGPD (UE 2016/679) y la LOPDGDD (LO 3/2018), bajo supervisión de la AEPD. Base jurídica recomendada: consentimiento explícito + ejecución del contrato de inscripción. Es muy probable que el tratamiento requiera una EIPD (art. 35 RGPD) antes del lanzamiento. **Bloqueante legal: validar con un asesor de protección de datos antes de lanzar.**

## 9. Arquitectura de despliegue

### Modelo
Todo el sistema (API + PostgreSQL en Docker, panel, web pública) corre en el PC del Administrador. No hay nube.

### Qué sale a internet y qué no (corrección v9)
| Superficie | Acceso | Motivo |
|---|---|---|
| API del corredor: login, unirse, perfil, estado, **ingesta de posiciones** | Internet, vía Cloudflare Tunnel | Los corredores no están en la LAN del recinto |
| Panel de administración (`:8080`) | Solo LAN | Lo usa el Administrador junto al PC |
| Web pública (`:8081`) | Solo LAN | Pantalla del recinto, conectada por cable |

### Componentes
- **Launcher gráfico**: Iniciar/Detener sin terminal; estado del servidor, del túnel, corredores transmitiendo e incidencias; IP:puerto y QR de las webs locales.
- **Stack Docker**: API + PostgreSQL.
- **Cloudflare Tunnel** (tunnel nombrado con dominio propio, no "quick tunnel"): gratuito y sobrado para este volumen; configuración una sola vez (Anexo D).

### Pantalla de espectadores
Conectada por cable (HDMI) al PC. Si se usa un dispositivo aparte, con router propio del evento, nunca la wifi pública del recinto.

## 10. Flujo de datos de posición GPS
1. La app envía puntos (individuales o en lote) a `POST /eventos/{id}/posiciones` a través del túnel.
2. La API valida (evento En directo, token válido, coherencia de timestamps) y guarda en `posiciones_historico` (append-only) y `posiciones_actuales` (UPSERT, solo si el punto es más reciente que el almacenado).
3. La web pública sondea `GET /eventos/{id}/distancias/{did}/posiciones` cada 3–5 s y anima los marcadores por interpolación.

**Timestamps**: cada punto guarda `timestamp_dispositivo` (hora del móvil; ordena, calcula ritmo y alimenta "última posición conocida") y `timestamp_recepcion` (hora del servidor; auditoría y clasificación `directo`/`sincronizado`). Puntos con desviación excesiva entre ambos se marcan como sospechosos sin descartarse.

**WebSocket**: descartado en v1.0 (un único cliente local hace innecesaria esa complejidad); candidato para v1.2.

## 11. Estados del evento
Borrador → Publicado → Preparación → En directo → Finalizado → Archivado.
- Avance en orden; retroceso de un paso permitido, salvo desde Archivado (terminal).
- **Unirse al evento** (corredor con código): permitido en Publicado, Preparación y En directo.
- **Ingesta de posiciones**: solo En directo; fuera de ese estado se **rechazan con error claro (HTTP `409`)**, sin almacenarse (decisión clarify 2026-07-16: se descartó la opción de guardar aparte como prueba para no añadir estado ni riesgo de mezcla con datos reales).
- Al pasar a Finalizado se revocan los tokens de dispositivo y se dispara el backup automático.
- Si se retrocede de Finalizado a En directo, los tokens de dispositivo revocados **no se reactivan**: los corredores deben volver a unirse con el código para obtener un token nuevo (decisión clarify 2026-07-16; no se reabren credenciales ya invalidadas).

## 12. Auditoría
Registrar: creación/modificación de eventos, importaciones, cambios de configuración, transiciones de estado, inicio/fin, incidencias (incluidas reconciliaciones tras pérdida de cobertura) y acciones de seguridad (revocación de tokens).

## 13. Riesgos aceptados y mitigaciones
- **Punto único de fallo** (PC, internet del recinto, túnel): sin soporte externo durante la carrera; mitigación: checklist pre-carrera (Anexo D) y conexión redundante 4G/5G recomendada.
- **Conectividad del recinto**: eslabón más frágil; la web local sigue funcionando sin internet mostrando las últimas posiciones recibidas.
- **Backups críticos**: todo el histórico vive en un único PC; backup automático obligatorio (Anexo D).
- **Eventos simultáneos**: requieren un PC independiente por evento.
- **RGPD**: bloqueante legal pendiente de asesor (Anexo F).
- **Proveedor de túnel**: revisar condiciones periódicamente.

## 14. Roadmap
- **v1.0**: panel, app Android (perfil con foto incluida), seguimiento GPS, múltiples distancias, GPX, importación Excel, launcher, túnel.
- **v1.1**: botón SOS, favoritos, clasificaciones orientativas, mejoras visuales.
- **v1.2**: configuración avanzada, estadísticas, API documentada, WebSocket si procede.
- **v2.0**: dispositivos GPS dedicados.
- **v3.0**: multiorganización/SaaS (requeriría arquitectura cloud paralela; fuera de esta fase).

## 15. Criterios de éxito (v1.0)
Resultados medibles y agnósticos de tecnología, derivados de las secciones 2, 5, 6 y 7 y de los Anexos C y D. Sirven de base a los tests de aceptación y de carga; ningún criterio introduce decisiones nuevas.

- **CE-001** — Un evento con 300–800 corredores transmitiendo simultáneamente funciona de principio a fin sin pérdida de puntos aceptados por la API.
- **CE-002** — La ingesta sostiene el pico de ~50 peticiones/s (sección 7) sin rechazar peticiones válidas ni degradar el sondeo de la web pública.
- **CE-003** — La web pública se actualiza por sondeo cada 3–5 s y el movimiento de los corredores se percibe fluido (interpolación en cliente) durante toda la carrera.
- **CE-004** — Los 300–800 corredores pueden unirse al evento dentro de la ventana operativa de una hora (carga <1 petición/s, sección 5) sin errores.
- **CE-005** — Un Administrador sin conocimientos técnicos pone en marcha servidor y túnel desde el launcher, sin usar la terminal. [NEEDS CLARIFICATION: tiempo máximo aceptable desde pulsar "Iniciar" hasta "servidor activo + túnel conectado".]
- **CE-006** — La app transmite en segundo plano durante toda la carrera con consumo de batería acotado. [NEEDS CLARIFICATION: objetivo cuantificado de autonomía (horas de transmisión continua o % de batería por hora) — la sección 2 solo pide "máxima autonomía".]
- **CE-007** — La latencia de punta a punta (punto generado en el móvil → visible en la pantalla) se mantiene dentro del objetivo. [NEEDS CLARIFICATION: latencia máxima aceptable de punta a punta; con envío cada 15–20 s y sondeo cada 3–5 s el mínimo estructural ronda los 20–25 s, pero no hay cifra objetivo.]
- **CE-008** — Tras una pérdida de cobertura, el 100% de los puntos acumulados llega a `posiciones_historico` al sincronizar y la posición mostrada nunca retrocede.
- **CE-009** — Si cae internet en el recinto, la web pública sigue operativa mostrando las últimas posiciones recibidas y su hora.
- **CE-010** — El backup se genera automáticamente al pasar a Finalizado y cada 30 min durante En directo (Anexo D), y es restaurable en un PC limpio.
- **CE-011** — La pantalla del recinto es legible a distancia: dorsales ≥ 24 px, cabecera ≥ 32 px y alto contraste marcador/fondo (Anexo C).

## 16. Supuestos
Supuestos hoy implícitos en el documento; si alguno deja de cumplirse, deben revisarse las secciones citadas.

- **SUP-001** — Cada corredor lleva su propio móvil Android con datos móviles activos, GPS y batería suficiente para la prueba; no se entregan dispositivos (los GPS dedicados quedan fuera de alcance hasta v2.0, sección 3).
- **SUP-002** — Hay un único evento activo por PC; los eventos simultáneos requieren un PC independiente por evento (sección 13).
- **SUP-003** — El Administrador tiene permisos de instalación en el PC Windows (instalador del launcher y de Docker Desktop, Anexo D).
- **SUP-004** — La LAN del recinto la controla el organizador (pantalla por cable HDMI o router propio del evento, nunca la wifi pública, sección 9); por eso el Anexo E acepta HTTP simple dentro de esa "LAN de confianza".
- **SUP-005** — El reloj del servidor es fiable. [NEEDS CLARIFICATION: ¿se exige sincronización NTP del PC del Administrador? La clasificación `directo`/`sincronizado` y la marca `sospechoso` dependen de que el reloj del servidor sea correcto.]
- **SUP-006** — El organizador dispone de un dominio propio en una cuenta gratuita de Cloudflare, configurado una sola vez antes del primer evento (Anexo D).
- **SUP-007** — Las inscripciones se importan desde Excel antes de que los corredores introduzcan el código; el matching corredor–inscripción se hace por email, que se asume único y correcto en el Excel (Anexo B §4).
- **SUP-008** — Un corredor transmite desde un único dispositivo durante la carrera: unirse desde un segundo dispositivo **revoca el token anterior** (un solo token de dispositivo activo por inscripción; decisión clarify 2026-07-16). Evita señales duplicadas o contradictorias.
- **SUP-009** — El corredor concede a la app el permiso de ubicación en segundo plano y la exclusión de optimización de batería cuando se le solicitan (RF-006).
- **SUP-010** — Los espectadores no necesitan acceso remoto: consumen la pantalla física del recinto u otros dispositivos de la LAN (sección 3).

---

# PARTE II — ANEXOS TÉCNICOS

## Anexo A — Modelo de datos (PostgreSQL)

```mermaid
erDiagram
  USUARIOS ||--o{ EVENTOS : crea
  USUARIOS ||--o{ AUDITORIA : genera
  EVENTOS ||--o{ DISTANCIAS : contiene
  EVENTOS ||--o{ PATROCINADORES : tiene
  EVENTOS ||--o{ NOTICIAS : tiene
  EVENTOS ||--o{ INCIDENCIAS : registra
  DISTANCIAS ||--o{ INSCRIPCIONES : recibe
  CORREDORES ||--o{ INSCRIPCIONES : participa
  INSCRIPCIONES ||--o| POSICIONES_ACTUALES : tiene
  INSCRIPCIONES ||--o{ POSICIONES_HISTORICO : genera
  INSCRIPCIONES ||--o{ TOKENS_DISPOSITIVO : autentica
  INSCRIPCIONES ||--o{ INCIDENCIAS : "puede generar"

  USUARIOS {
    bigserial id PK
    varchar nombre
    varchar email UK
    varchar password_hash
    varchar rol
    timestamptz creado_en
  }
  CORREDORES {
    bigserial id PK
    varchar nombre
    varchar apellidos
    varchar club
    varchar foto_url
    varchar email UK
    varchar password_hash
    timestamptz creado_en
  }
  EVENTOS {
    bigserial id PK
    varchar nombre
    varchar codigo_acceso UK
    date fecha
    varchar estado
    int intervalo_gps_parado_seg
    int intervalo_gps_movimiento_seg
    int umbral_sin_senal_seg
    jsonb colores_config
    jsonb info_visible_config
    varchar cartel_url
    bigint creado_por FK
    timestamptz creado_en
  }
  DISTANCIAS {
    bigserial id PK
    bigint evento_id FK
    varchar nombre
    varchar gpx_url
    jsonb mapa_config
  }
  INSCRIPCIONES {
    bigserial id PK
    bigint corredor_id FK
    bigint distancia_id FK
    varchar dorsal
    timestamptz creado_en
  }
  POSICIONES_ACTUALES {
    bigint inscripcion_id PK_FK
    timestamptz timestamp_dispositivo
    timestamptz timestamp_recepcion
    numeric latitud
    numeric longitud
    numeric precision_m
    numeric velocidad_kmh
    int bateria_pct
  }
  POSICIONES_HISTORICO {
    bigserial id PK
    bigint inscripcion_id FK
    timestamptz timestamp_dispositivo
    timestamptz timestamp_recepcion
    numeric latitud
    numeric longitud
    numeric precision_m
    numeric velocidad_kmh
    int bateria_pct
    varchar origen
    boolean sospechoso
  }
  PATROCINADORES {
    bigserial id PK
    bigint evento_id FK
    varchar nombre
    varchar logo_url
    varchar enlace_url
    int orden
  }
  NOTICIAS {
    bigserial id PK
    bigint evento_id FK
    varchar titulo
    text contenido
    timestamptz publicado_en
  }
  INCIDENCIAS {
    bigserial id PK
    bigint evento_id FK
    bigint inscripcion_id FK
    varchar tipo
    text descripcion
    timestamptz creado_en
    timestamptz resuelto_en
  }
  AUDITORIA {
    bigserial id PK
    bigint usuario_id FK
    varchar accion
    varchar entidad_tipo
    varchar entidad_id
    jsonb detalle
    timestamptz creado_en
  }
  TOKENS_DISPOSITIVO {
    bigserial id PK
    bigint inscripcion_id FK
    varchar token_hash
    timestamptz creado_en
    timestamptz revocado_en
  }
```

### Notas por entidad
- **usuarios**: cuentas de panel (Administrador/Operador); `rol` acota permisos.
- **corredores**: cuenta permanente, independiente del evento; incluye `password_hash` (argon2id, Anexo E) para el login de la app.
- **eventos**: `estado` según sección 11; `codigo_acceso` es el código de carrera; configuración GPS/visual por evento (JSON para lo visual, evita migraciones).
- **inscripciones**: une corredor + distancia y asigna `dorsal`. Restricción: `UNIQUE (distancia_id, dorsal)` — el dorsal es único por distancia, no globalmente. También `UNIQUE (corredor_id, distancia_id)`.
- **posiciones_actuales**: una fila por inscripción, UPSERT condicionado a que el nuevo `timestamp_dispositivo` sea posterior al almacenado (evita que un lote sincronizado desordenado retroceda la posición).
- **posiciones_historico**: append-only; `origen` ∈ {`directo`, `sincronizado`}; `sospechoso` marca desviación excesiva entre timestamps.
- **tokens_dispositivo** (corrección v9): guarda **hash** del token, no el token en claro; `revocado_en` para revocación individual o masiva al Finalizar.
- **incidencias**: con `inscripcion_id` (por corredor) o sin él (sistémicas, p. ej. caída del servidor). [NEEDS CLARIFICATION: catálogo cerrado de valores admitidos en `tipo` de incidencia.]

### Índices y rendimiento
- `posiciones_actuales`: acceso por distancia vía join con `inscripciones` (índice en `inscripciones.distancia_id`).
- `posiciones_historico`: índice compuesto `(inscripcion_id, timestamp_dispositivo)`.
- Volumen pequeño para PostgreSQL a esta escala; sin particionado en v1.

### Retención (ligado al Anexo F)
Job programado que, pasado el plazo definido en la política de privacidad [NEEDS CLARIFICATION: plazo de retención concreto de las posiciones — el Anexo F lo deja "a definir"], purga o anonimiza [NEEDS CLARIFICATION: ¿purgar o anonimizar? Elegir una política; condiciona el diseño del job] `posiciones_historico` de eventos antiguos.

## Anexo B — API REST

### 1. Principios
- REST + JSON; subidas de ficheros (GPX, imágenes, Excel) en multipart/form-data.
- Errores: `{ "error": { "code", "message" } }` + código HTTP estándar.
- `Authorization: Bearer <token>`.

### 2. Superficies de exposición (corrección v9)
| Superficie | Endpoints | Acceso |
|---|---|---|
| **API del corredor** | `/auth/corredores/*`, `/corredores/{id}` (propio), `/corredores/{id}/foto`, `/eventos/codigo/{codigo}/unirse`, `/inscripciones/{id}/estado`, `/eventos/{id}/posiciones` | Internet (túnel) |
| **API de gestión** | resto de endpoints (eventos, distancias, importación, contenido, incidencias, auditoría) | Solo LAN |
| **API de lectura pública** | `GET /eventos/{id}/distancias/{did}/posiciones` y contenido del evento | Solo LAN |

La separación se implementa a nivel de reverse proxy/túnel (el túnel solo enruta las rutas del corredor), no confiando únicamente en la autenticación.

### 3. Autenticación
| Token | Usuario | Vida | Alcance |
|---|---|---|---|
| Sesión de panel | Admin/Operador | 12 h, renovable | API de gestión |
| Sesión de corredor | Corredor | 30 días | Perfil propio, unirse |
| Token de dispositivo | App durante un evento | Hasta Finalizado (revocación automática) | Solo `POST /posiciones` y `GET /inscripciones/{id}/estado` |

- `POST /auth/login` y `POST /auth/corredores/login` → `{ email, password }`.
- El token de dispositivo se entrega al unirse con el código; separado de la sesión del corredor para revocarlo sin cerrar su cuenta.
- Duración de sesiones (decisión clarify 2026-07-16): sesión de panel **12 h renovable**; sesión de corredor **30 días**. El token de dispositivo es independiente y caduca al Finalizar el evento.

### 4. Endpoints de gestión (LAN)
| Método | Endpoint | Notas | Auth |
|---|---|---|---|
| GET/POST | `/eventos` | Alta en Borrador | Admin (lectura tb. Operador) |
| GET/PUT | `/eventos/{id}` | Configuración | Admin (lectura tb. Operador) |
| POST | `/eventos/{id}/duplicar` | Copia en Borrador | Admin |
| POST | `/eventos/{id}/estado` | Valida transición (sección 11); `409` si inválida | Admin |
| GET/POST | `/eventos/{id}/distancias` · PUT `/distancias/{id}` | | Admin |
| POST | `/distancias/{id}/gpx` | multipart | Admin |
| POST | `/distancias/{id}/corredores/importar` | Excel → corredores + inscripciones (matching por email) | Admin |
| GET/POST/PUT | `/eventos/{id}/patrocinadores` · `/noticias` | | Admin (lectura LAN abierta) |
| GET | `/eventos/{id}/incidencias` · PUT `/incidencias/{id}/resolver` | | Admin/Operador |
| GET | `/auditoria?evento_id=&desde=&hasta=` | | Admin |

**Formato del Excel de importación** (decisión clarify 2026-07-16): columnas obligatorias `email`, `nombre`, `apellidos`, `dorsal`; columna opcional `club`. La distancia se toma de la ruta (`/distancias/{id}/corredores/importar`), no de una columna. Si el `email` ya existe como cuenta de corredor registrada, **se vincula la inscripción a la cuenta existente sin modificar su perfil** (matching idempotente por email); si no existe, se crea la cuenta. La foto no se importa por Excel: la sube el corredor desde la app.

### 5. Endpoints del corredor (túnel)
- `POST /eventos/codigo/{codigo_acceso}/unirse` — busca la inscripción del corredor autenticado en ese evento; si existe, devuelve distancia, dorsal y **token de dispositivo**; si no, error claro ("no se ha encontrado tu inscripción; contacta con el organizador"). Permitido en Publicado/Preparación/En directo.
- `GET/PUT /corredores/{id}` — perfil propio (nombre, apellidos, club).
- `POST /corredores/{id}/foto` — subida de foto de perfil (multipart; solo JPEG/PNG, **límite normativo 5 MB**; foto mayor → error claro). El servidor valida el tipo real del fichero, la redimensiona escalando el **lado mayor a 512 px máx. preservando la relación de aspecto** (sin recorte), la guarda en un volumen local y actualiza `foto_url`; la web pública la sirve desde la LAN. (Valores fijados en clarify 2026-07-16.)
- `GET /inscripciones/{id}/estado` — para la pantalla de estado de la app. Devuelve (decisión clarify 2026-07-16): `dorsal`, nombre de la distancia, `estado_transmision` calculado (`transmitiendo`/`sin_senal`, comparando la última posición con `umbral_sin_senal_seg`), `latitud`/`longitud` y `timestamp_dispositivo` de la última posición conocida, `timestamp_recepcion`, `bateria_pct` del último punto y `estado` del evento.
- `POST /eventos/{id}/posiciones` — body: **array** de puntos `{ timestamp_dispositivo, latitud, longitud, precision_m, velocidad_kmh, bateria_pct }`. La inscripción se deriva del token (anti-suplantación). La API:
  - Rechaza si el evento no está En directo.
  - Sella `timestamp_recepcion`; clasifica `origen`: **`directo` si `timestamp_recepcion − timestamp_dispositivo ≤ 10 s`**, `sincronizado` en caso contrario (decisión clarify 2026-07-16).
  - Marca `sospechoso` (sin descartar) si `|timestamp_recepcion − timestamp_dispositivo| > 600 s`, o si el `timestamp_dispositivo` está más de **120 s en el futuro** respecto al reloj del servidor (decisión clarify 2026-07-16).
  - UPSERT en `posiciones_actuales` solo si el punto es más reciente que el almacenado.
  - Responde `202` con el nº de puntos procesados.
  - Tamaño máximo del lote: **500 puntos por petición**; si se excede, responde `413` con error claro y la app parte el lote (decisión clarify 2026-07-16).
  - Si el `{id}` de evento de la URL no corresponde al evento de la inscripción derivada del token, responde **`403`** con error claro (la identidad del token manda sobre la URL; decisión clarify 2026-07-16).

### 6. Endpoint de lectura pública (LAN)
- `GET /eventos/{id}/distancias/{did}/posiciones` — por inscripción activa: dorsal, nombre, apellidos, club, foto_url, lat, lon, `timestamp_dispositivo` y `estado` calculado (`transmitiendo` / `sin_senal`) comparando con `umbral_sin_senal_seg`. Es el endpoint que sondea la pantalla cada 3–5 s.

### 7. Reglas anti-abuso
- Ingesta: máx. 1 petición / 5 s por token de dispositivo.
- Login: **máx. 5 intentos fallidos por cuenta en una ventana de 15 min; superados, bloqueo de 15 min** (aplica a login de panel y de corredor; decisión clarify 2026-07-16).

## Anexo C — UI/UX

### Principios
Launcher sin jerga técnica; panel optimizado para tareas repetitivas; web pública legible a metros de distancia; app de consulta pasiva durante la carrera.

### Launcher (pantalla única)
Estado grande ("Servidor detenido / iniciando / activo"), un botón principal Iniciar/Detener, semáforos (túnel, corredores transmitiendo, incidencias), IP:puerto de panel (`:8080`) y web pública (`:8081`) con botón copiar y QR.

### Panel (`:8080`)
Login → listado de eventos → edición por pestañas: General (nombre, fecha, código de acceso) · Distancias (+GPX) · Corredores (importación Excel, tabla con dorsal y estado) · Contenido (cartel, patrocinadores, noticias) · Configuración (intervalos, umbral sin señal, colores, info visible). Vistas de Incidencias y Auditoría filtrables.

### Web pública (`:8081`)
Cabecera (logo, prueba, crono) → filtros (dorsal, todos, ★ favoritos) → mapa por distancia (pestañas si hay varias; GPX rojo, bolitas con dorsal, interpolación suave) → ficha modal al pulsar corredor (foto, nombre, apellidos, club, sin tapar el mapa) → cartel, info, patrocinadores, listado.

### App Android
Login/registro (una vez) → unirse con código → pantalla de estado (dorsal, GPS, batería, conexión) → perfil editable (nombre, apellidos, club y subida de foto).

### Semántica de color
Verde = transmitiendo · Ámbar/gris = sin señal (+hora de última posición). El rojo queda reservado para el futuro SOS (v1.1). `colores_config` personaliza la paleta, pero se conserva la asociación semántica.

### Legibilidad
Web pública: dorsales ≥ 24 px sobre el mapa, cabecera ≥ 32 px, alto contraste marcador/fondo. Launcher y panel: tipografía estándar de escritorio.

### Dispositivos
Launcher: escritorio, tamaño fijo. Panel: navegador de escritorio (móvil no prioritario en v1). Web pública: pantalla/proyector por cable; accesible también desde otros dispositivos de la LAN. App: uso puntual, no en primer plano durante el recorrido.

## Anexo D — Despliegue

### Requisitos del PC
Windows 10/11 64 bits · 8 GB RAM (16 recomendado) · CPU 4 núcleos · 20 GB libres · internet en el recinto (banda ancha o 4G/5G) · Docker Desktop (gratuito bajo 250 empleados y 10M USD de facturación; confirmar umbral). [NEEDS CLARIFICATION: confirmar las condiciones vigentes de la licencia de Docker Desktop antes de empaquetar el instalador.]

### Empaquetado del launcher
Electron o Tauri [NEEDS CLARIFICATION: decidir Electron o Tauri antes de implementar el launcher] como instalador único de Windows que incluye: launcher, ficheros Docker Compose del stack y comprobación/instalación guiada de Docker Desktop. "Iniciar servidor" = `docker compose up -d` traducido a estados visuales; logs ocultos tras un "ver detalles". Actualizaciones con un botón, solo entre carreras (nunca con un evento En directo).

### Cloudflare Tunnel (configuración única inicial)
1. Dominio propio (o subdominio) en una cuenta gratuita de Cloudflare.
2. `cloudflared` empaquetado en el instalador.
3. Tunnel nombrado → hostname público (p. ej. `api.cronoempate.com`) → **enruta únicamente las rutas de la API del corredor** (Anexo B, sección 2).
4. Registrado como servicio del sistema (sobrevive a reinicios).

### Backups (crítico)
`pg_dump` completo: automático al pasar a Finalizado + periódico (30 min) durante En directo. Destino: carpeta local + destino externo (USB o nube). Cifrados (Anexo E). Retención ligada al Anexo F.

### Checklist pre-carrera
- [ ] Servidor encendido al menos una hora antes de la salida (norma general, sección 5) y corredores avisados para introducir el código del evento.
- [ ] PC a corriente; suspensión/hibernación desactivadas; actualizaciones de Windows pausadas.
- [ ] Internet del recinto probado (ideal: respaldo 4G/5G).
- [ ] Pantalla conectada por cable.
- [ ] Launcher: servidor activo + túnel conectado.
- [ ] Evento en Preparación; pasar a En directo al empezar.
- [ ] Destino de backup accesible.

## Anexo E — Seguridad
- Contraseñas (usuarios y corredores) con **argon2id** (parámetros mínimos recomendados por OWASP: memoria 19 MiB, 2 iteraciones, paralelismo 1; decisión clarify 2026-07-16). Tokens de dispositivo almacenados como hash (corrección v9).
- Identidad siempre derivada del token verificado en servidor; ningún endpoint de escritura confía en IDs del payload.
- Transporte: HTTPS/TLS extremo a extremo en todo lo que pasa por el túnel; HTTP simple aceptable dentro de la LAN de confianza en v1.
- Separación de superficies a nivel de túnel/proxy: las rutas de gestión no son alcanzables desde internet aunque se filtre un token.
- Rate limiting (Anexo B, sección 7).
- Revocación: automática de tokens de dispositivo al Finalizar; manual desde el panel para un token concreto (posiciones falsas). Todo queda en auditoría.
- Datos en reposo: cifrado de disco completo (BitLocker) recomendado en el PC; backups cifrados igual.
- Actualizaciones de seguridad de imágenes Docker por el mismo mecanismo del launcher (Anexo D).

### Matriz de permisos
| Acción | Admin | Operador | Corredor | LAN anónimo |
|---|---|---|---|---|
| Configurar eventos/distancias/GPX | ✓ | ✗ | ✗ | ✗ |
| Importar corredores | ✓ | ✗ | ✗ | ✗ |
| Cambiar estado del evento | ✓ | ✗ | ✗ | ✗ |
| Consultar estado / incidencias | ✓ | ✓ | — | ✗ |
| Editar perfil propio | — | — | ✓ | ✗ |
| Enviar posiciones | ✗ | ✗ | ✓ (token disp.) | ✗ |
| Ver web pública | ✓ | ✓ | ✓ | ✓ |

## Anexo F — Privacidad y EIPD
> **Punto de partida de trabajo, no documento final. Requiere validación por abogado/consultor de protección de datos antes del lanzamiento.**

- **Marco**: RGPD + LOPDGDD (AEPD).
- **Política de privacidad — contenido mínimo**: responsable y contacto; datos recogidos (identidad, foto, email, GPS durante el evento); finalidad (seguimiento en carrera y pantalla del recinto); base jurídica (consentimiento explícito + contrato de inscripción); audiencia (espectadores presentes; sin cesión a terceros); plazo de conservación (a definir, enlazado al job de purga del Anexo A); derechos ARCO-POL y cómo ejercerlos; derecho a reclamar ante la AEPD; referencia a medidas de seguridad (Anexo E).
- **EIPD — pasos**: descripción sistemática del tratamiento; necesidad y proporcionalidad (el tracking es el núcleo del servicio); riesgos (exposición de ubicación en tiempo real); mitigaciones — documentar explícitamente que la pantalla es local al recinto y no accesible por internet, lo que reduce la exposición frente a un modelo abierto; consulta al DPO si se nombra; aprobación formal previa al lanzamiento.
- **Pendientes**: encargar redacción final; fijar plazo de conservación; valorar DPO con el asesor.
