# Ensayo general — estado actual (FASE S6)

FASE S6 del plan de Servidor (`docs/Plan_Implementacion_1_Servidor_v2.md`) pide
un ensayo conjunto: "PC objetivo + launcher + simulador a 800 + 3-5 móviles
reales, 2-3 h, con fallos provocados". A fecha de este documento, **no existen
todavía ni el Web (panel/web pública) ni la App Android** — ningún agente ha
empezado esos dos planes — y este entorno de desarrollo no tiene un PC Windows
objetivo ni teléfonos físicos. El ensayo conjunto completo no se puede hacer
todavía.

Lo que sí depende solo del Servidor (ya construido en S1-S5) se ha ejecutado de
verdad, contra el stack Docker real, con resultados abajo.

## Ensayo parcial ejecutado

**Configuración**: `simulador --gpx rutas_ejemplo/5k_ejemplo.gpx --corredores 800
--duracion-min 30 --perdida-cobertura 0.10 --reloj-desviado 0.02
--factor-aceleracion 8`, contra `docker-compose.dev.yml` reconstruido desde cero.

**Fallo provocado**: reinicio (`docker restart`) del contenedor `api` ~100 s
después de que el evento pasara a En directo (≈ 19 s de caída real, mientras los
800 corredores virtuales seguían enviando posiciones) — simula la pérdida del
túnel/servidor que describe EA-014.

### Resultado

| Métrica | Valor |
|---|---|
| Corredores importados | 800 (0 errores) |
| Corredores unidos al evento | 800 |
| Puntos enviados con éxito | 37 587 |
| Lotes enviados con éxito | 13 176 |
| Errores 5xx | **0** |
| Otros errores (429/timeouts durante el corte, reintentados) | 181 (~1,4 %) |
| Duración real | 175,6 s (30 min simulados, factor ×8) |

Verificación directa en BD tras el ensayo:

- `posiciones_actuales`: **800/800** inscripciones con posición — ninguna se
  quedó sin actualizar pese al corte de 19 s.
- `posiciones_historico`: **37 587** filas, coincide exactamente con "puntos
  enviados" del resumen del simulador (cero pérdida).
- `incidencias` tipo `sin_senal`: 588 generadas al consultar la lectura pública
  tras el ensayo, sin errores ni degradación de la consulta a esa escala.
- Logs del contenedor `api`: sin excepciones ni tracebacks en toda la ventana
  del ensayo (incluida la del reinicio).
- Recursos tras el ensayo: ~125 MB RAM (api), ~36 MB RAM (db), CPU en reposo —
  no se capturó el pico de uso *durante* la carga (solo el estado post-ensayo).

### Criterios de la spec verificados por este ensayo

- **CE-001** (sin pérdida de puntos aceptados): ✅ — histórico = puntos
  reportados como enviados, sin discrepancia.
- **CE-002** (sostiene el pico de ingesta): ✅ — 0 errores 5xx a 800 corredores
  concurrentes; los únicos fallos fueron 429/timeout durante el corte inducido,
  reintentados automáticamente sin pérdida.
- **CE-008** (posición nunca retrocede tras pérdida de cobertura): ✅ por
  diseño (UPSERT condicionado, ya probado en S4) y confirmado aquí a escala.
- **CE-009** (la web pública sigue mostrando últimas posiciones si cae
  internet): **parcialmente verificable** — el servidor conserva y sirve
  correctamente las últimas posiciones durante y después del corte (lo que
  consultaría la web pública), pero no hay web pública construida todavía para
  probar el comportamiento del frontend en sí.

## Pendiente tras el ensayo S6 (histórico — ver ensayo FASE W4 más abajo)

1. ~~**Web** (panel + web pública) — plan 2, no empezado.~~ Hecho: ver
   "Ensayo FASE W4" más abajo.
2. **App Android** — plan 3, no empezada; sin ella no hay "3-5 móviles reales".
3. **PC objetivo real** (Windows, especificaciones del Anexo D) — este ensayo
   corrió en el entorno de desarrollo Linux del asistente, no en el hardware
   final.
4. **Túnel Cloudflare real** — ver `docs/pendiente_instalador_windows.md`.
5. Repetir el ensayo completo (2-3 h, con los fallos del Anexo D: corte de
   internet del recinto además del reinicio del túnel) una vez existan 1-4.

## Ensayo FASE W4 (Web ya construida) — 2026-07-17

Con el Panel y la Web pública ya construidos (planes W1-W3), se repite el
ensayo con ambos abiertos en un navegador real mientras corre el simulador,
completando lo que en la ronda anterior quedaba marcado como "no
verificable todavía" (CE-009) y añadiendo dos fallos provocados nuevos que
no se habían podido probar sin frontend: latencia de lectura a escala real y
la resiliencia visual de la web pública ante dos tipos de corte distintos.

**Configuración**: `simulador --gpx villacabra-11k.gpx --corredores 800
--duracion-min 20 --perdida-cobertura 0.10 --factor-aceleracion 4
--codigo-evento W4ENSAYO`, con `docker-compose.dev.yml` ya en marcha, Panel
(`:8080`) y Web pública (`:8081`) abiertos en Chrome real vía Playwright.

### Hallazgo 1 — Latencia de `GET .../posiciones` a 800 corredores (N+1)

Con el simulador escribiendo posiciones en paralelo, la lectura que sondea
la web pública cada 3-5 s tardaba **~2.3 s de media** (15 muestras directas,
2221-2495 ms) — dentro del intervalo de sondeo, pero con muy poco margen, y
un factor de riesgo para "fluidez del render" con corredores reales.

Causa: dos patrones N+1 en el camino de lectura —
1. `listar_posiciones_publicas` (`posiciones.py`) accedía a
   `inscripcion.posicion_actual` e `inscripcion.corredor` en un bucle sin
   carga adelantada → hasta ~1600 consultas extra por petición a 800
   corredores.
2. `sincronizar_incidencias_sin_senal` (`servicios/incidencias.py`) hacía
   **una consulta por inscripción** para comprobar si tenía una incidencia
   `sin_senal` abierta, en vez de una sola consulta por lote.

**Corrección aplicada**: `selectinload` en la consulta de inscripciones (1 y
2) y una única consulta `IN (...)` para las incidencias abiertas del lote,
en vez de una por inscripción. Resultado tras la corrección: **~1.5-1.6 s**
de media (mismo escenario, mismo simulador en marcha) — mejora de ~35 %.
Con el simulador parado (sin contención de escritura), la lectura baja a
milisegundos, así que el ~1.5 s restante es sobre todo contención de
escritura concurrente del propio entorno de desarrollo (pool de 60
conexiones/hilos compartido con las escrituras de 800 corredores
simultáneos), no coste de consulta. Se deja documentado por si conviene
revisar en un futuro (async, mayor pool, o cache corto) — no se ha tocado
más por ser un cambio de arquitectura mayor, no un bug puntual.

Mismo día: dos suites de test rotas por este ensayo resultaron ser
contaminación de datos (un evento de prueba en `en_directo` en la BD
compartida interfería con `test_operacion.py`, que asume un único evento en
directo) — no una regresión del cambio; confirmado archivando el evento y
repitiendo `pytest` (113/113 verdes).

### Hallazgo 2 — Corte del contenedor `api` (~10.6 s) con la web pública abierta

`docker restart empatelivelocal-api-1` a mitad de sondeo, con 800
marcadores ya renderizados. Un único sondeo cayó con
`net::ERR_CONNECTION_RESET` durante el reinicio; los marcadores
**se mantuvieron en su última posición conocida durante todo el corte**, sin
parpadeos, desapariciones ni saltos, y se retomó el sondeo normal al volver
la API, sin ningún salto visual incoherente al reconectar.

Se encontró y corrigió un bug real en el camino de manejo de errores: el
fallo de red (no un simple 404/500) hacía que `api.GET(...)` **rechazara la
promesa** en vez de resolver con `{ error }`, y como `sondear()` no tenía
`try/catch`, se escapaba como una excepción no capturada en vez de marcar
`conectado = false` — visible como `pageerror: TypeError: Failed to fetch`
en la consola durante el corte. El resultado visual había sido correcto por
casualidad (el estado simplemente no se tocaba), pero de forma frágil y sin
avisar a quien mira la pantalla de que la conexión se ha perdido.

**Corrección aplicada**: `try/catch` en `usePosicionesPolling` (trata el
fallo de red igual que un error HTTP) y un aviso visible en la cabecera
("Sin conexión con el servidor — mostrando la última posición conocida",
en ámbar, discreto, coherente con el resto del diseño) cuando
`conectado === false` — antes ese estado se calculaba pero no se mostraba
en ningún sitio. Repetido el mismo corte tras la corrección: cero errores de
consola, aviso visible durante el corte, desaparece solo al reconectar.

### Hallazgo 3 — Riesgo "mapa en blanco" si cae el internet del recinto (confirmado, sin corregir)

El plan (`Plan_Implementacion_2_Web_v2.md`) daba por hecho una "caché/servidor
de tiles" en la FASE W2 como mitigación de este riesgo, pero **nunca se
implementó**: el mapa usa tiles de OpenStreetMap en vivo
(`tile.openstreetmap.org`), un recurso externo que no sobrevive a un corte
del internet del recinto (a diferencia de la API/LAN, que no depende de él).

Probado bloqueando en el navegador el dominio de tiles (mismo efecto que un
corte de internet real) manteniendo la API/LAN intactas:
- **Con la pantalla ya abierta y sin tocarla**, los tiles ya cargados
  siguen visibles durante todo el corte (el navegador los tiene en caché) —
  el caso más realista para una pantalla fija de recinto que nadie manipula.
- **En cualquier carga nueva de la página, o al hacer zoom/pan a una zona no
  vista antes**, los tiles nuevos fallan y esa zona del mapa queda gris/en
  blanco.
- En **ningún** caso se rompe la app: el trazado GPX (servido por la propia
  API, no por internet) y los marcadores de corredores con su dorsal siguen
  renderizándose con normalidad sobre el fondo en blanco — la información
  de "quién va por dónde" se conserva, solo se pierde el contexto visual de
  calles/terreno.

**Decisión (2026-07-17, responsable del producto)**: riesgo aceptado por
ahora, no se construye la caché/proxy de tiles local en esta sesión — es un
cambio de alcance mayor (pre-descarga del bbox de la ruta durante la hora de
margen antes de la carrera, almacenamiento en `storage/`, endpoint proxy,
cambio del `tileLayer` de Leaflet con fallback), no un bugfix puntual, y el
impacto real es acotado (los datos de corredores no se pierden, solo el
fondo de calles). Mitigación operativa mientras tanto: checklist Anexo D,
"Internet del recinto probado (ideal: respaldo 4G/5G)". Retomar si se decide
lo contrario.

### Resumen frente a los riesgos que W4 debía neutralizar

| Riesgo (tabla del plan) | Resultado |
|---|---|
| Render se arrastra con 800 marcadores | ✅ corregido (N+1, ~35 % menos latencia) y confirmado en navegador real |
| Interpolación produce saltos o retrocesos visuales | ✅ ya cubierto por los casos límite de W2; confirmado también en el corte de API de este ensayo (sin saltos al reconectar) |
| Mapa en blanco si cae internet en carrera | ⚠️ riesgo real confirmado y **aceptado** (impacto acotado: datos de corredores no se pierden, solo el fondo de calles) |
| Administrador bloqueado por errores crípticos | ✅ cubierto en W3 (informe de importación por fila, mensajes de transición claros) |

## Pendiente para el ensayo general completo

1. **App Android** — plan 3, no empezada; sin ella no hay "3-5 móviles reales"
   (el simulador cubre la carga, pero no la app real en un teléfono).
2. **PC objetivo real** (Windows, especificaciones del Anexo D) — todo lo de
   este documento corrió en el entorno de desarrollo Linux del asistente.
3. **Túnel Cloudflare real** — ver `docs/pendiente_instalador_windows.md`.
4. Repetir el ensayo completo (2-3 h, con los fallos del Anexo D) una vez
   existan 1-3.

(La caché/servidor de tiles del Hallazgo 3 se evaluó y el riesgo se aceptó
conscientemente — no queda pendiente salvo que se decida lo contrario.)

## Cómo repetir el ensayo S6 (histórico, solo Servidor)

```bash
docker compose -f docker-compose.dev.yml up -d --build
cd simulador && source .venv/bin/activate
python -m simulador --gpx rutas_ejemplo/5k_ejemplo.gpx --corredores 800 \
  --duracion-min 30 --perdida-cobertura 0.10 --reloj-desviado 0.02 \
  --factor-aceleracion 8
# En otra terminal, ~1-2 min después de "Comenzando la simulación":
docker restart empatelivelocal-api-1
```

## Cómo repetir el ensayo FASE W4 (con Web)

```bash
docker compose -f docker-compose.dev.yml up -d --build
npm run dev --workspace panel &          # :8080
npm run dev --workspace web-publica &    # :8081
cd simulador && source .venv/bin/activate
python -m simulador --gpx ../api/seed/rutas/villacabra-11k.gpx --corredores 800 \
  --duracion-min 20 --perdida-cobertura 0.10 --factor-aceleracion 4 \
  --codigo-evento W4ENSAYO
# En otra terminal, con la web pública abierta y marcadores visibles:
docker restart empatelivelocal-api-1     # Hallazgo 2
# Para el Hallazgo 3 (riesgo del mapa), bloquear en el navegador las
# peticiones a *.tile.openstreetmap.org (p. ej. con page.route en Playwright)
# y comprobar que el trazado GPX y los marcadores se mantienen.
```
