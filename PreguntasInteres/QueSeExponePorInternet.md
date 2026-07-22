# QueSeExponePorInternet

**Pregunta:** ¿Qué queda accesible desde internet por el túnel y qué no? ¿Es
seguro?

## Respuesta

Por el túnel **solo** se expone el subconjunto de **API del corredor**. El
**panel de administración** y la **web pública** son **LAN-only**: nunca salen
por el túnel (spec v10 §9, Anexo B §2, Anexo E).

### Se expone por internet (túnel)

- `POST /auth/corredores/registro` y `POST /auth/corredores/login`
- `GET/PUT /corredores/{id}` (el propio) y `POST /corredores/{id}/foto`
- `POST /eventos/codigo/{codigo}/unirse`
- `GET /inscripciones/{id}/estado`
- `POST /eventos/{id}/posiciones` (ingesta GPS)

### Queda LAN-only (nunca por el túnel)

- Todo el panel de administración (`/eventos`, edición, importación, estados…).
- La web pública / pantalla del recinto.
- El resto de la API de gestión.

## Cómo se garantiza (no depende solo del token)

La separación se implementa **a nivel de proxy/túnel**, con una **expresión
regular de rutas** en `cloudflared/config.yml`. Aunque se filtrara un token, las
rutas de gestión devuelven **404** desde el hostname público.

- Espejo local para probarlo sin cuenta de Cloudflare:
  `cloudflared/nginx-verificacion.conf` (perfil `verificacion-tunel` del
  `docker-compose.dev.yml`).
- Script de comprobación de las 15 rutas: `cloudflared/verificar_superficie.sh`.

> Regla del proyecto (CLAUDE.md): **"Nunca exponer rutas de gestión por el
> túnel."**

Ver también: [ComoLleganLosDatosDelMovil](ComoLleganLosDatosDelMovil.md),
[TiposDeToken](TiposDeToken.md).
