# Pendiente: instalador Windows real (spec v10 Anexo D)

Este documento registra honestamente qué parte de la FASE S5 se construyó y
verificó en este entorno (Linux, sin cuenta Cloudflare real) y qué queda por
hacer en una máquina Windows / con cuenta Cloudflare real antes de considerar el
instalador terminado.

> **Nota (Linux ya resuelto)**: el punto 2 de más abajo ("empaquetar `/api`
> dentro del instalador") y la resolución de rutas del launcher ya están
> implementados y verificados de punta a punta para Linux, empaquetado como
> AppImage — ver `launcher/README.md` ("Empaquetado (AppImage, Fedora/Linux)").
> Se copian los recursos empaquetados (compose, `.env.prod.example`,
> `cloudflared/config.yml` y `/api` sin `.venv`/`storage`, vía rsync
> `--exclude-from` el `.dockerignore`) a un directorio de datos escribible del
> usuario (`app_data_dir()`) en el primer arranque — la opción que este mismo
> documento proponía. Lo que sigue pendiente abajo (NSIS, Docker Desktop,
> túnel real) es específico de Windows y no aplica a la ruta Linux.

## Hecho y verificado en este entorno

- **Launcher (Tauri)**: compila y corre en Linux; lógica de Rust (envoltura de
  `docker compose`, detección de IP LAN, llamada a `/operacion/resumen`, generación
  de `.env` con secretos aleatorios) probada con tests unitarios y de integración
  contra el stack Docker real.
- **Backups**: `pg_dump` cifrado real generado y **restaurado con éxito en un
  Postgres limpio** (recuentos de filas idénticos en todas las tablas), tanto por
  la transición a Finalizado como por el job periódico.
- **Restricción de superficie del túnel**: verificada con un proxy nginx local
  que aplica exactamente las mismas reglas que `cloudflared/config.yml` — las 8
  rutas de la API del corredor pasan, las 8 rutas de gestión/lectura pública se
  bloquean (`cloudflared/verificar_superficie.sh`).
- **`docker-compose.prod.yml`**: sin hot-reload, exige secretos vía `.env`,
  bootstrap del primer Administrador (`scripts/bootstrap_admin.py`, idempotente).

## Pendiente (requiere Windows real y/o cuenta Cloudflare real)

1. **Compilar el instalador `.exe` (NSIS) en Windows.** `tauri.conf.json` ya
   declara `"targets": "all"` y la configuración `bundle.windows.nsis`, pero
   generar y probar el instalador real requiere `cargo tauri build` en una
   máquina Windows (o un runner de CI con el toolchain de Windows). No se ha
   producido ni probado ningún `.exe` en esta sesión.
2. **Empaquetar el código de `/api` dentro del instalador.** Ahora mismo
   `docker-compose.prod.yml` construye la imagen con `build: context: ./api`, lo
   que asume que el código fuente de `/api` está presente junto al compose. El
   instalador todavía no copia ese directorio (se descartó bundlearlo tal cual
   por el riesgo de arrastrar `.venv`/`storage` si existieran en la máquina de
   build). Antes de la release hace falta decidir entre:
   - Publicar una imagen Docker ya construida en un registro y cambiar
     `docker-compose.prod.yml` a `image: ...` en vez de `build:`, o
   - Empaquetar `/api` con un `.dockerignore`-aware copy (p. ej. `rsync
     --exclude-from`) como recurso del instalador.
3. **Comprobación guiada de Docker Desktop.** No implementada: el launcher no
   detecta todavía si Docker Desktop está instalado/en marcha antes de intentar
   `docker compose up`. Anexo D pide una instalación guiada; por ahora el launcher
   simplemente falla con el mensaje de error de `docker` si no está disponible.
4. **Tunnel Cloudflare real.** Todo lo construido usa un proxy local que imita
   las reglas de `cloudflared/config.yml`. Falta seguir
   `docs/guia_tunel_cloudflare.md` con una cuenta y dominio reales, y confirmar
   que el semáforo de túnel del launcher se pone en verde contra un tunnel real
   (no solo contra el contenedor `cloudflared` local).
5. **Capturas de pantalla de la guía del túnel.** `docs/guia_tunel_cloudflare.md`
   se escribió sin capturas (el interfaz de Cloudflare cambia; no se pueden
   fabricar capturas reales sin una cuenta real). Añadirlas cuando alguien haga
   la configuración real por primera vez.
6. **Ensayo de "instalador único" de principio a fin en un Windows limpio**
   (spec: "en un Windows limpio, una persona no técnica llega a 'Servidor activo
   + túnel conectado' solo con la guía") — no se ha podido reproducir ese
   escenario desde este entorno.

## Cómo retomarlo

Con acceso a una máquina Windows: instalar Rust + Node, clonar el repo, resolver
el punto 2 de arriba, y correr `cd launcher && npm install && npm run tauri
build`. El instalador NSIS resultante queda en
`launcher/src-tauri/target/release/bundle/nsis/`.
