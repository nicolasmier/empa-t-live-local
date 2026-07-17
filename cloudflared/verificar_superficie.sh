#!/usr/bin/env bash
# Test explícito del plan S5: "las rutas de gestión NO responden desde el
# hostname público". Corre contra tunel-simulado (nginx con las mismas reglas
# que cloudflared/config.yml) — no requiere una cuenta real de Cloudflare.
#
# Uso:
#   docker compose -f docker-compose.dev.yml --profile verificacion-tunel up -d
#   ./cloudflared/verificar_superficie.sh
set -uo pipefail

PROXY="http://localhost:8888"
FALLOS=0

es_json() {
    # Las respuestas de la API son JSON; el 404 por defecto de nginx es HTML.
    echo "$1" | head -c1 | grep -q '{'
}

verificar_permitida() {
    local metodo="$1" ruta="$2"
    local cuerpo
    cuerpo=$(curl -s -X "$metodo" "$PROXY$ruta")
    if es_json "$cuerpo"; then
        echo "OK   permitida  $metodo $ruta (llegó a la API)"
    else
        echo "FALLO permitida $metodo $ruta -> bloqueada por el túnel, no debería"
        FALLOS=$((FALLOS + 1))
    fi
}

verificar_bloqueada() {
    local metodo="$1" ruta="$2"
    local codigo cuerpo
    codigo=$(curl -s -o /tmp/cuerpo_verif -w "%{http_code}" -X "$metodo" "$PROXY$ruta")
    cuerpo=$(cat /tmp/cuerpo_verif)
    if [ "$codigo" = "404" ] && ! es_json "$cuerpo"; then
        echo "OK   bloqueada  $metodo $ruta (404 del túnel, no llegó a la API)"
    else
        echo "FALLO bloqueada $metodo $ruta -> código $codigo, cuerpo: ${cuerpo:0:80}"
        FALLOS=$((FALLOS + 1))
    fi
}

echo "=== Rutas de la API del corredor (deben pasar el túnel) ==="
verificar_permitida POST /auth/corredores/login
verificar_permitida POST /auth/corredores/registro
verificar_permitida GET /corredores/1
verificar_permitida POST /corredores/1/foto
verificar_permitida POST /eventos/codigo/ABC123/unirse
verificar_permitida GET /inscripciones/1/estado
verificar_permitida POST /eventos/1/posiciones

echo
echo "=== Rutas de gestión / lectura pública (NO deben pasar el túnel) ==="
verificar_bloqueada POST /auth/login
verificar_bloqueada GET /eventos
verificar_bloqueada GET /eventos/1/distancias/2/posiciones
verificar_bloqueada GET /auditoria
verificar_bloqueada GET /salud
verificar_bloqueada GET /media/fotos/1.jpg
verificar_bloqueada POST /distancias/1/gpx
verificar_bloqueada POST /distancias/1/corredores/importar
verificar_bloqueada GET /operacion/resumen
verificar_bloqueada GET /eventos/activo
verificar_bloqueada GET /eventos/1/distancias

echo
if [ "$FALLOS" -eq 0 ]; then
    echo "RESULTADO: OK — la superficie del túnel coincide con el Anexo B §2."
else
    echo "RESULTADO: FALLO — $FALLOS comprobación(es) incorrectas."
    exit 1
fi
