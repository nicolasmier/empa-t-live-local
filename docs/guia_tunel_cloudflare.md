# Guía: configuración inicial del túnel Cloudflare

Configuración **única**, antes del primer evento (spec v10 Anexo D, SUP-006). El
Administrador necesita una cuenta de Cloudflare (gratuita) y un dominio propio (o
subdominio de uno que ya tenga). Esta guía no incluye capturas de pantalla — el
interfaz de Cloudflare cambia con cierta frecuencia; sigue los nombres de menú
indicados y confirma contra la documentación oficial de Cloudflare Tunnel si algo
no coincide exactamente.

## 1. Cuenta y dominio

1. Crea una cuenta gratuita en <https://dash.cloudflare.com/sign-up> si no tienes una.
2. Añade tu dominio a Cloudflare ("Add a site") y sigue el asistente para apuntar
   los servidores de nombres (nameservers) del dominio a Cloudflare. Si no tienes
   dominio propio, regístralo primero en cualquier proveedor (no hace falta que
   sea el propio Cloudflare Registrar).

## 2. Crear el tunnel nombrado

En el PC del Administrador, con `cloudflared` instalado (lo instala el instalador
del launcher):

```bash
cloudflared tunnel login
```

Esto abre el navegador para autorizar el tunnel contra tu cuenta. A continuación:

```bash
cloudflared tunnel create empatelive
```

Esto crea el tunnel y genera un fichero `credentials.json` (guárdalo; lo necesitas
en el paso 4). Anota el `<TUNNEL_ID>` que imprime el comando.

## 3. Apuntar un hostname al tunnel

```bash
cloudflared tunnel route dns empatelive api.tu-dominio.com
```

Sustituye `api.tu-dominio.com` por el hostname que prefieras dentro de tu dominio
(por ejemplo `carrera.tu-club.org`). Esto crea el registro DNS necesario en
Cloudflare automáticamente.

## 4. Completar `cloudflared/config.yml`

Edita `cloudflared/config.yml` (en la carpeta de instalación del launcher) y
sustituye los dos placeholders:

- `<TUNNEL_ID>` → el UUID del paso 2.
- `<TUNNEL_HOSTNAME>` → el hostname del paso 3 (`api.tu-dominio.com`).

Copia el `credentials.json` del paso 2 a la misma carpeta `cloudflared/` (el
`config.yml` ya espera encontrarlo en `/etc/cloudflared/credentials.json` dentro
del contenedor, que se corresponde con `cloudflared/credentials.json` en el host).

**No toques la línea `path:`** — esa expresión regular es la que garantiza que
solo la API del corredor (login, unirse, perfil, foto, posiciones) es alcanzable
desde internet; el panel, la web pública y el resto de la API de gestión quedan
fuera aunque se filtre un token (Anexo B §2, Anexo E).

## 5. Activar el túnel

Desde el launcher, o manualmente:

```bash
docker compose -f docker-compose.prod.yml --profile tunel up -d cloudflared
```

El semáforo de "Túnel" del launcher debe pasar a "Conectado" en unos segundos.

## 6. Verificar la restricción de superficie

Antes de dar el evento por listo, confirma que las rutas de gestión NO responden
desde el hostname público:

```bash
curl -i https://api.tu-dominio.com/eventos
# Debe dar 404, nunca la respuesta normal de la API.

curl -i https://api.tu-dominio.com/auth/corredores/login -X POST
# Debe llegar a la API (401/422, no 404): confirma que el túnel sí enruta esto.
```

Este mismo par de comprobaciones (contra las 15 rutas relevantes) se puede correr
en local sin cuenta real de Cloudflare con `cloudflared/verificar_superficie.sh`
— ver ese script para la lista completa.

## Revisión periódica

Revisa las condiciones del plan gratuito de Cloudflare Tunnel de vez en cuando
(spec v10 §13: "Proveedor de túnel: revisar condiciones periódicamente") — no
hay compromiso de continuidad de un producto gratuito de terceros.
