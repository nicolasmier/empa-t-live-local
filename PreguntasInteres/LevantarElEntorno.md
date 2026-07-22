# LevantarElEntorno

**Pregunta:** ¿Cómo se levanta el entorno (servidor, web, panel)? ¿Qué puertos?

## Desarrollo (docker compose)

```bash
docker compose -f docker-compose.dev.yml up -d
```

Levanta:

- **db**: Postgres 16 (puerto host **5433** → 5432 del contenedor).
- **api**: FastAPI/uvicorn en **:8000**. Al arrancar corre `alembic upgrade
  head` + `python -m seed.seed` y queda con `--reload`.

Las webs se levantan aparte (Vite), y resuelven la API por el **host del
navegador** hacia `:8000` (`web-shared/src/url.ts`):

```bash
npm run dev --workspace panel          # panel admin  → :8080
npm run dev --workspace web-publica    # web pública  → :8081
```

Para que un móvil u otro equipo de la LAN las vea, añade `-- --host 0.0.0.0`.

## Puertos (spec v10 §9)

| Servicio | Puerto | Alcance |
|---|---|---|
| API | 8000 | Corredor (túnel) + LAN |
| Panel admin | 8080 | **LAN-only** |
| Web pública | 8081 | **LAN-only** |
| Postgres (dev) | 5433 | Local |

## Producción / campo (launcher)

En un evento real se usa el **launcher** (Tauri) del escritorio, que orquesta
`docker-compose.prod.yml` (API + db + web + panel) y, con perfil, el
`cloudflared` del túnel. Semáforos de "Servidor" y "Túnel" en su interfaz.

## Gotchas conocidos (Fedora/SELinux)

- Montajes con `:Z` por SELinux.
- Un `docker restart` **no reengancha la red**: recrear con `up -d
  --force-recreate <servicio>` si la API no resuelve el host `db`.
- Si el volumen de la BD quedó con una revisión de Alembic vieja: `down -v` y
  volver a `up` (recrea y re-semilla).

Ver también: [ComoLleganLosDatosDelMovil](ComoLleganLosDatosDelMovil.md).
