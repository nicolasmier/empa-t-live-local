#!/usr/bin/env bash
# Demo visual: 10 corredores sobre la ruta real de Villacabra (11K), repartidos
# en la salida con huecos aleatorios de 2-100 m (no todos apilados en el mismo
# punto) para comprobar cómo se ve el recorrido en el mapa. Tiempo acelerado:
# la carrera completa (~10.1 km, ~70 min al ritmo más lento simulado) se ve en
# unos 4 minutos reales — margen deliberado para poder abrir la web pública y
# ponerse a mirar sin perderse el arranque (con 1 minuto exacto el tiempo de
# cambiar de pestaña ya se comía la simulación entera).
#
# Requisito: el servidor tiene que estar levantado y accesible en
# http://localhost:8000 (docker-compose.dev.yml o docker-compose.prod.yml,
# cualquiera de los dos vale — ambos publican la API en el mismo puerto).
#
# Uso:
#   ./Simulaciones/demo_villacabra_10_corredores.sh
#
# Para verla: abre la web pública ANTES de lanzar el script (web-publica,
# :8081 en producción o `npm run dev --workspace web-publica` en desarrollo).
# No hay ningún código que escribir: la web pública muestra sola el evento
# activo (ver README.md de esta carpeta) — si ya la tenías abierta con una
# demo anterior, recarga la página una vez lanzado el script para que recoja
# el evento nuevo.
set -euo pipefail
cd "$(dirname "$0")/../simulador"

if [ -d .venv ]; then
  source .venv/bin/activate
fi

python -m simulador \
  --gpx "../api/seed/rutas/villacabra-11k.gpx" \
  --corredores 10 \
  --duracion-min 70 \
  --factor-aceleracion 17.5 \
  --espaciado-min-m 2 \
  --espaciado-max-m 100 \
  --perdida-cobertura 0 \
  --reloj-desviado 0 \
  --codigo-evento "${CODIGO_EVENTO:-DEMO-VILLACABRA}" \
  --admin-email "${ADMIN_EMAIL:-admincronoempate@cronoempate.com}" \
  --admin-password "${ADMIN_PASSWORD:-cronoempate123}" \
  --api-url "${API_URL:-http://localhost:8000}"
