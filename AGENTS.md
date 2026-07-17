# AGENTS.md

## Reglas absolutas

- La fuente de verdad es `docs/spec-v10.md`. Si el código y la spec discrepan, la spec manda.
- **Nunca implementar SOS** (pospuesto a v1.1).
- **Nunca exponer rutas de gestión por el túnel Cloudflare** — solo rutas de corredor (registro, login, perfil, foto, unirse, estado, ingesta de posiciones).

## Estructura del monorepo

| Directorio | Tecnología | Descripción |
|---|---|---|
| `api/` | FastAPI + SQLAlchemy + Alembic | Servidor principal. Entrypoint: `app/main.py` |
| `launcher/` | Tauri 2 (Rust + vanilla HTML/JS) | App de escritorio que gestiona Docker compose |
| `simulador/` | Python (httpx) | Genera corredores virtuales contra la API real |
| `cloudflared/` | nginx / cloudflared config | Configuración del túnel y verificación de superficie |
| `docs/` | Markdown | Spec v10 y planes de implementación |

## Convenciones

- **snake_case** en nombres de columnas/variables de BD.
- **Español** en documentación, nombres de variables internas, comentarios de spec, y mensajes de error orientados al usuario.
- Los routers de la API viven en `api/app/routers/`, los modelos en `api/app/models/`, los schemas en `api/app/schemas/`.
- `api/openapi.json` es un entregable coordinado para agentes Web y Android — debe mantenerse sincronizado.

## Dev: levantar el entorno

```bash
# Desarrollo (DB en port 5433, API en port 8000, hot-reload)
docker compose -f docker-compose.dev.yml up

# Producción (requiere .env con secretos — el launcher lo genera automáticamente)
docker compose -f docker-compose.prod.yml up

# Túnel simulado (perfil verificacion-tunel)
docker compose -f docker-compose.dev.yml --profile verificacion-tunel up -d
```

El compose de dev ejecuta automáticamente `alembic upgrade head` + seed + uvicorn.

## API: commands

```bash
cd api
pip install -e ".[dev]"

# Lint
ruff check .

# Tests (requiere PostgreSQL en port 5433)
alembic upgrade head
python -m seed.seed
pytest

# Regenerar openapi.json tras cambios de contrato
python -m scripts.exportar_openapi
```

**DB de tests**: usa la misma que dev (port 5433, user/pass/db: `empatelive`). Los tests usan transacciones con rollback — nada queda en la BD.

## Simulador

```bash
cd simulador
pip install -e ".[dev]"
python -m simulador --gpx rutas_ejemplo/5k_ejemplo.gpx --corredores 50 --duracion-min 5
```

Requiere el servidor levantado. Usa el usuario admin del seed (`admin@example.com`).

## Launcher (Tauri)

```bash
cd launcher
npm install
npm run tauri dev     # desarrollo
npm run tauri build   # empaquetar instalador
```

El launcher gestiona Docker compose directamente. Usa `EMPATELIVE_COMPOSE_FILE` para apuntar a un compose distinto en dev.

## CI (`.github/workflows/ci.yml`)

- **api**: lint → migrations → seed → pytest → openapi.json drift check (`git diff --exit-code openapi.json`).
- **simulador**: lint → pytest.

## Seed (`api/seed/seed.py`)

- Admin: `admin@example.com` / `admin1234`
- Operador: `operador@example.com` / `operador1234`
- Corredores: `corredor01@example.com` a `corredor20@example.com` / `corredor1234`
- Evento semilla: código `MADRID2026`, distancias 10K y 22K

## Túnel Cloudflare (Anexo B §2, Anexo D)

La superficie pública se restringe a nivel de reverse proxy, no de auth. El regex de rutas permitidas está en `cloudflared/config.yml` y `cloudflared/nginx-verificacion.conf`. Si cambias las rutas expuestas, actualiza ambos ficheros.

## Referencias clave

- Spec: `docs/spec-v10.md`
- Planes: `docs/Plan_Implementacion_1_Servidor_v2.md`, `docs/Plan_Implementacion_2_Web_v2.md`, `docs/Plan_Implementacion_3_App_Android_v2.md`
- Config de la API: `api/app/config.py` (pydantic-settings, lee `.env`)
- Migraciones: `api/migrations/versions/`
