# Plan de Implementación — SERVIDOR (backend + infraestructura)
## Basado en la Especificación Consolidada v10 (fuente única de verdad). Documento 1 de 3.

# 0. Coordinación entre agentes
- **Este agente es el proveedor de contratos**: los agentes de Web y App Android desarrollan contra la API de este servidor. Nada de lo que consuman puede cambiar sin actualizar primero la spec v10 y avisar.
- **Entregables hacia los otros agentes** (al cierre de la Fase S2): especificación OpenAPI generada desde el código, `docker-compose.dev.yml` funcional, seed de datos de desarrollo, y (al cierre de S4) el simulador de corredores.
- Regla de oro: si el código y la spec v10 discrepan, la spec manda; si la spec está mal, se corrige la spec en el mismo commit.

# Alcance de este agente
API REST + PostgreSQL + Docker + launcher gráfico + túnel + backups + simulador de corredores. **No incluye**: panel web, web pública (agente Web) ni app Android (agente Android).

---

# FASE S1 — Cimientos
1. Estructura de repo: `/api`, `/simulador`, `/launcher`, `/docs` (spec v10 dentro).
2. `docker-compose.dev.yml`: PostgreSQL + API con hot-reload. Stack sugerido: Python/FastAPI + SQLAlchemy o Node/NestJS + Prisma.
3. Migraciones versionadas implementando el Anexo A completo (sin `estado_sos`, pospuesto a v1.1), con las restricciones anti-error en BD:
   - `UNIQUE (distancia_id, dorsal)` y `UNIQUE (corredor_id, distancia_id)` en `inscripciones`.
   - `UNIQUE` en `eventos.codigo_acceso`, `usuarios.email`, `corredores.email`.
   - `CHECK` de `eventos.estado` contra la lista cerrada.
   - Índices: `inscripciones.distancia_id`; `(inscripcion_id, timestamp_dispositivo)` en histórico.
4. Seed: 1 evento, 2 distancias, 20 corredores inscritos, 1 admin, 1 operador.
5. CI: lint + tests + migraciones aplican en limpio.

**Aceptación**: `docker compose up` deja BD migrada y seedada; CI verde.

# FASE S2 — API núcleo (autenticación, eventos, estados, permisos)
1. Auth: registro/login de corredores y login de panel (argon2/bcrypt); tres tipos de token (Anexo B §3); tokens de dispositivo almacenados como hash; límite de intentos de login.
2. CRUD de eventos y distancias; duplicado de evento.
3. **Máquina de estados como módulo puro y aislado** (`estado_actual, destino → válido/inválido`) con tests de las 36 combinaciones; `POST /eventos/{id}/estado` la usa y devuelve 409 en transiciones inválidas. Al pasar a Finalizado: revocación masiva de tokens de dispositivo + disparo de backup.
4. Middleware de roles (matriz Anexo E) en todas las rutas desde el primer día.
5. Auditoría transversal: interceptor que registra toda escritura de gestión.
6. **Entregable a otros agentes**: OpenAPI publicada + seed + compose.

**Aceptación**: máquina de estados 100% testada; tests de permisos (Operador no escribe, corredor no accede a gestión); auditoría completa.

# FASE S3 — Importación, contenidos y flujo del corredor
1. Importación Excel → corredores + inscripciones (matching por email), **idempotente** (reimportar no duplica) y con informe por fila (creados/actualizados/errores con motivo).
2. Subida y validación de GPX (rechazo de corruptos con mensaje claro; extracción de bounding box a `mapa_config`).
3. CRUD de patrocinadores, noticias, cartel.
4. `POST /eventos/codigo/{codigo}/unirse`: busca inscripción del corredor autenticado; entrega token de dispositivo; permitido solo en Publicado/Preparación/En directo; error claro si no hay inscripción. Debe soportar sin degradarse el patrón real de uso: **300–800 corredores uniéndose en la hora previa a la salida** (spec §5, ventana operativa).
5. **Perfil y foto (v10)**: `PUT /corredores/{id}` (nombre, apellidos, club) y `POST /corredores/{id}/foto` — multipart, solo JPEG/PNG, límite 5 MB, validación del tipo real del fichero (no solo extensión), redimensionado a máx. 512×512, guardado en volumen local, actualización de `foto_url`. La imagen se sirve en la LAN (la consumirá la web pública).

**Aceptación**: Excel de 800 filas con errores a propósito → informe correcto y sin duplicados al reimportar; corredor seedado se une, recibe token y sube foto que queda accesible por URL en la LAN.

# FASE S4 — Ingesta de posiciones + SIMULADOR (hito de riesgo técnico)
1. `POST /eventos/{id}/posiciones` (Anexo B §5): lotes, identidad por token, rechazo fuera de En directo, doble timestamp (`dispositivo`/`recepcion`), clasificación `directo`/`sincronizado`, marca `sospechoso` por desviación de relojes, **UPSERT en posición actual condicionado a timestamp más reciente**, rate limit 1 petición/5 s por token.
2. `GET /eventos/{id}/distancias/{did}/posiciones`: estado calculado `transmitiendo`/`sin_senal` contra `umbral_sin_senal_seg`; incluye dorsal, nombre, apellidos, club, foto_url, lat, lon, timestamp.
3. Incidencias automáticas: sin señal supera umbral → incidencia; recuperación → registro/resolución.
4. **Simulador** (`/simulador`, CLI): toma un GPX y genera N corredores virtuales a ritmos realistas enviando por la API real con tokens reales. Parámetros: `--corredores 800`, `--perdida-cobertura 10%` (paran y luego sincronizan lote), `--reloj-desviado 2%`. Es el entregable clave para que el agente Web desarrolle contra datos vivos.
5. Tests de integración con el simulador: lotes desordenados no retroceden posiciones; lote sincronizado entero en histórico pero solo el último punto en actuales.

**Aceptación**: simulación de 800 corredores 30 min con 10% de pérdida de cobertura → sin 5xx, `posiciones_actuales` coherente, incidencias generadas, consumo de recursos razonable en el PC objetivo.

# FASE S5 — Launcher, túnel, backups e instalador
1. Launcher (Tauri sugerido): Iniciar/Detener (`docker compose up/down` envuelto), semáforos (contenedores sanos, túnel conectado, corredores transmitiendo, incidencias), IP:puerto + QR de panel (`:8080`) y web pública (`:8081`).
2. `cloudflared` como servicio, tunnel nombrado con dominio propio, **enrutando únicamente las rutas de la API del corredor** (Anexo B §2). Test explícito: las rutas de gestión NO responden desde el hostname público.
3. Backups: `pg_dump` al Finalizar + cada 30 min En directo; destino secundario configurable; cifrados. **Probar la restauración en otro PC, no solo la copia.**
4. Instalador Windows único: launcher + compose + `cloudflared` + comprobación guiada de Docker Desktop.
5. Guía paso a paso (con capturas) de la configuración inicial única del dominio en Cloudflare.

**Aceptación**: en un Windows limpio, una persona no técnica llega a "Servidor activo + túnel conectado" solo con la guía; gestión inaccesible desde internet; backup restaurado con éxito.

# FASE S6 — Soporte a integración y ensayo general
- Disponibilidad para los agentes Web y Android durante sus integraciones (bugs de contrato tienen prioridad).
- Organizar el **ensayo general** conjunto: PC objetivo + launcher + simulador a 800 + 3–5 móviles reales, 2–3 h, con fallos provocados (corte de internet 10 min, reinicio del túnel) — criterios en la spec v10 §13 y checklist del Anexo D.

# Riesgos que este agente neutraliza
| Riesgo | Dónde |
|---|---|
| Lotes sincronizados corrompen la posición actual | S4 (UPSERT condicionado + tests) |
| Dorsales/estados inválidos en datos | S1 (restricciones en BD) |
| Rutas de gestión expuestas a internet | S5 (test de superficie del túnel) |
| Pérdida de datos del PC único | S5 (backups + restauración probada) |
| Avalancha de uniones 1h antes de la salida | S3 (test de carga del flujo unirse) |
