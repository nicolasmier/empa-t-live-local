#!/usr/bin/env bash
# Recompila el bundle de la web de SEGUIMIENTO PÚBLICA (el que va a Cloudflare
# Pages, apuntando al hostname del túnel) y opcionalmente lo despliega.
#
# No toca el bundle de la pantalla del recinto (LAN, :8081), que se construye
# aparte con `npm run build` y resuelve la API por hostname:8000.
#
# Uso:
#   ./redeploy-publica.sh            # solo compila a dist-publica/
#   ./redeploy-publica.sh --deploy   # compila y sube a Cloudflare Pages (wrangler)
set -euo pipefail

# Hostname del túnel que la API pública sirve (ver cloudflared/config.yml).
API_URL="${API_URL:-https://api.observeweb.com}"
# Nombre del proyecto de Cloudflare Pages (el que creaste en el dashboard).
PROYECTO_PAGES="${PROYECTO_PAGES:-empatelive}"

cd "$(dirname "$0")"

echo "→ Compilando bundle público con VITE_API_URL=$API_URL"
VITE_API_URL="$API_URL" npx vite build --outDir dist-publica --emptyOutDir

if [ "${1:-}" = "--deploy" ]; then
  echo "→ Desplegando dist-publica/ a Cloudflare Pages (proyecto: $PROYECTO_PAGES)"
  npx wrangler pages deploy dist-publica --project-name "$PROYECTO_PAGES"
else
  echo "→ Bundle listo en dist-publica/. Súbelo al dashboard de Pages,"
  echo "  o vuelve a lanzar con --deploy para hacerlo por CLI."
fi
