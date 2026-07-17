# Plan de Implementación — WEB (panel de administración + web pública)
## Basado en la Especificación Consolidada v10 (fuente única de verdad). Documento 2 de 3.

# 0. Coordinación entre agentes
- **Este agente consume, no define**: todo se desarrolla contra la OpenAPI publicada por el agente Servidor (cierre de su Fase S2) y contra el simulador de corredores (cierre de S4). Si un endpoint no se comporta como dice la spec v10, se reporta al agente Servidor — no se "adapta" el frontend a un comportamiento no especificado.
- **Prerrequisitos para arrancar**: `docker-compose.dev.yml` + seed + OpenAPI del agente Servidor. La Fase W2 (web pública) requiere además el simulador.
- Ambas webs viven solo en la LAN: panel en `:8080`, web pública en `:8081` (spec §9). No hay que implementar nada relativo al túnel.

# Alcance de este agente
Panel de administración (React + Vite sugerido) y web pública / pantalla del recinto (React + Leaflet + OpenStreetMap). **No incluye**: API, launcher, app Android.

---

# FASE W1 — Base común
1. Estructura: `/panel` y `/web-publica` en el monorepo; cliente HTTP generado desde la OpenAPI (tipado, evita divergencias silenciosas de contrato).
2. Sistema mínimo de componentes compartidos: colores semánticos (verde = transmitiendo, ámbar/gris = sin señal; el rojo queda reservado a futuro SOS v1.1), tipografías y tokens que respeten `colores_config` del evento.

**Aceptación**: ambos proyectos compilan, consumen el seed del entorno de desarrollo y pintan un "hola mundo" con datos reales de la API.

# FASE W2 — Web pública (pantalla del recinto) — prioridad, es el producto visible
Se desarrolla **con el simulador del agente Servidor corriendo** (800 corredores virtuales): nunca contra datos estáticos.

1. Estructura según spec Anexo C: cabecera (logo, nombre de la prueba, crono de tiempo transcurrido), filtros en cliente (dorsal(es), todos, ★ favoritos), pestañas por distancia, bloque inferior (cartel, info, patrocinadores, listado de corredores).
2. Mapa Leaflet por distancia: trazado GPX en rojo; marcadores-bolita con dorsal (≥24 px, alto contraste sobre el fondo del mapa; cabecera ≥32 px — se ve desde metros de distancia).
3. **Polling cada 3–5 s** a `GET /eventos/{id}/distancias/{did}/posiciones` + **interpolación de movimiento**: cada marcador anima de su posición previa a la nueva durante el intervalo (requestAnimationFrame). Casos límite obligatorios:
   - Corredor nuevo → aparece en su posición, sin animar desde (0,0).
   - Corredor `sin_senal` → se congela en gris mostrando la hora de su última posición.
   - Fallo de polling y reconexión → re-sincroniza sin saltos bruscos.
   - Salto grande legítimo (lote sincronizado tras pérdida de cobertura) → transición directa, sin recorrer el hueco a cámara lenta.
4. Ficha modal al pulsar un corredor: foto (servida por el servidor desde la LAN), nombre, apellidos, club — sin tapar el mapa.
5. **Tiles de mapa**: caché agresiva del navegador o servidor de tiles local opcional — el fondo del mapa es lo único de la web local que por defecto vendría de internet, y debe sobrevivir a un corte durante la carrera.

**Aceptación**: con el simulador a 800 corredores, render fluido (sin congelones) en el hardware objetivo; los estados visuales y los 4 casos límite de interpolación se comportan según spec; la web sigue operativa (últimas posiciones + mapa cacheado) con internet cortado.

# FASE W3 — Panel de administración
1. Login y layout por pestañas (spec Anexo C): General (nombre, fecha, código de acceso) · Distancias (+subida GPX) · Corredores · Contenido (cartel, patrocinadores, noticias) · Configuración (intervalos GPS, umbral sin señal, colores, info visible).
2. Importación Excel con **visualización del informe por fila** que devuelve la API (creados / actualizados / errores con motivo) — es la herramienta con la que el Administrador depura su fichero la víspera de la carrera; no basta un "importación completada".
3. Cambios de estado del evento con confirmación explícita en los pasos sensibles (a En directo; a Finalizado, que revoca tokens y dispara backup) y mensajes claros cuando la API devuelve 409 por transición inválida.
4. Vista de incidencias con aviso visual de nuevas (polling del panel) y filtro resuelta/no resuelta; vista de auditoría filtrable por fecha, usuario y acción.
5. Tabla de corredores por distancia con dorsal y estado de transmisión (mismo endpoint de posiciones que la web pública).

**Aceptación**: una persona sin conocimiento de la API monta un evento completo de principio a fin solo con el panel (crear → distancias+GPX → importar → configurar → Publicado → Preparación → En directo); los errores de importación y de transición se entienden sin ayuda técnica.

# FASE W4 — Integración y ensayo general
- Prueba conjunta con los otros agentes en el ensayo general (spec §13 y checklist del Anexo D): pantalla conectada por cable al PC objetivo, simulador a 800, corte de internet provocado de 10 min.
- Métrica a observar: fluidez del render y coherencia visual de reconexiones y lotes sincronizados.

# Riesgos que este agente neutraliza
| Riesgo | Dónde |
|---|---|
| Render se arrastra con 800 marcadores | W2 (desarrollo contra simulador a escala real) |
| Interpolación produce saltos o retrocesos visuales | W2 (casos límite obligatorios) |
| Mapa en blanco si cae internet en carrera | W2 (caché/servidor de tiles) |
| Administrador bloqueado por errores crípticos | W3 (informe por fila + mensajes de estado claros) |
