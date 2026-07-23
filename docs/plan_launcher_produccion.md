# Plan: dejar el launcher listo para producción (despliegue llave en mano)

**Objetivo:** que en un **PC nuevo** una persona (no necesariamente técnica)
llegue a *"servidor activo + túnel conectado + arranca solo en cada encendido"*
con el launcher, sin comandos de terminal.

Estado de partida (verificado hoy, 2026-07-23): el stack de producción y el
**túnel real** (`api.observeweb.com`) funcionan, pero **montados a mano**, no por
el launcher. El launcher tiene huecos concretos que este plan cierra.

---

## Huecos actuales del launcher (código real)

| # | Hueco | Dónde |
|---|---|---|
| G1 | "Iniciar" **no arranca el túnel** (`docker compose up -d` sin `--profile tunel`) | `launcher/src-tauri/src/docker.rs::iniciar` |
| G2 | La **configuración del túnel** (login, create, route dns, `config.yml`, `credentials.json`) es 100% manual; el launcher no la guía ni la automatiza | `docs/guia_tunel_cloudflare.md` |
| G3 | No verifica que **Docker** esté instalado/en marcha antes de `up` | `docker.rs::ejecutar_compose` |
| G4 | La imagen de la API se **construye** en destino (`build: context: ./api`), lo que exige el código fuente y un build lento en el primer arranque | `docker-compose.prod.yml` |
| G5 | No garantiza **arranque en el boot** ni deja claro que dependa de Docker | — |
| G6 | La cuenta admin por defecto es **conocida** (`admin@cronoempate.com`/`123@cronoempate`); en producción hay que forzar el cambio | `api/scripts/bootstrap_admin.py` |
| G7 | El **instalador Windows (.exe/NSIS)** no se ha compilado ni probado | `docs/pendiente_instalador_windows.md` |

---

## Fase 1 — El launcher arranca el túnel (desbloqueo inmediato)

**Qué:** que "Iniciar" levante también `cloudflared` cuando el túnel esté
configurado.

- En `docker.rs::iniciar`, añadir `--profile tunel` **solo si** el túnel está
  configurado (ver detección en Fase 2). Si no lo está, arrancar sin él y dejar
  el semáforo en "no configurado" (ya existe esa lógica en `estado_tunel`).
- Añadir el **fix SELinux** (`:ro,Z`) al montaje de `cloudflared` en el compose
  empaquetado (ya aplicado en el repo; asegurar que viaja en `resources-build`).
- Test: con `config.yml` configurado, "Iniciar" deja el semáforo de túnel en
  verde ("conectado") contra un túnel real.

**Coste:** bajo. Es el cambio que más valor da de inmediato.

## Fase 2 — Asistente de configuración del túnel (primer arranque)

**Qué:** que el launcher **guíe y ejecute** la configuración del túnel, en vez
del proceso manual de hoy.

- **Empaquetar `cloudflared`** como binario externo de Tauri (`externalBin` en
  `tauri.conf.json`) para no depender de que esté en el PATH del PC.
- Detectar "túnel sin configurar" = `config.yml` con placeholders
  (`<TUNNEL_ID>`) **o** sin `credentials.json` en la carpeta del stack.
- Asistente en la UI (`launcher/src`), con comandos Tauri nuevos que ejecuten por
  debajo:
  1. `cloudflared tunnel login` (abre el navegador → el usuario elige su dominio).
  2. `cloudflared tunnel create empatelive` → captura `TUNNEL_ID` y copia
     `credentials.json` a la carpeta del stack.
  3. Pedir el **hostname** (p. ej. `api.midominio.com`) y `cloudflared tunnel
     route dns`.
  4. Rellenar los placeholders de `config.yml` (tunnel id + hostname) sobre la
     copia escribible del stack (`app_data_dir/stack`).
- Persistir todo en `app_data_dir/stack/cloudflared/` (escribible, ya existe el
  patrón de copia en `entorno.rs`).

**Coste:** medio. Es el corazón del "llave en mano".

## Fase 3 — Comprobación guiada de Docker (G3)

- Antes de `up`, un comando Tauri comprueba `docker version` / `docker compose
  version`.
- Si falta o no corre: mensaje claro + enlace de instalación (Docker Desktop en
  Windows), en vez del error crudo actual.

**Coste:** bajo.

## Fase 4 — Imagen de la API pre-construida (G4)

**Decisión de release** (el doc pendiente ya la plantea):

- **Opción A (recomendada):** publicar una imagen Docker ya construida en un
  registro y cambiar `docker-compose.prod.yml` de `build: context: ./api` a
  `image: <registro>/empatelive-api:<versión>`. El PC nuevo **no** necesita el
  código fuente ni construir nada → primer arranque rápido y fiable.
- **Opción B:** empaquetar `/api` con copia consciente de `.dockerignore` y
  construir en destino (más lento, requiere toolchain de build de Docker).

**Coste:** medio (A implica un pipeline de publicación de imagen).

## Fase 5 — Arranque en el boot (G5)

- **Mecanismo base (ya funciona):** contenedores con `restart: unless-stopped`
  + Docker habilitado en el arranque del sistema → el stack (incl. túnel) vuelve
  solo en cada encendido, sin abrir el launcher.
- **Lo que añade el launcher:**
  - Asegurar/documentar que Docker arranca al inicio (Windows: Docker Desktop
    "Start on login"; Linux: `systemctl enable docker`).
  - Opcional: registrar el propio launcher en el autostart del sistema para que
    la ventana de estado esté a mano, pero **el servidor no depende de abrir el
    launcher**.
- **Regla operativa (documentar bien):** el launcher es la **única** fuente de
  verdad del stack. No mezclar con arranques manuales (evita el choque de
  puertos 8000/8080/8081 que vimos hoy).

**Coste:** bajo (sobre todo documentación + un check).

## Fase 6 — Seguridad de la cuenta por defecto (G6)

- En el primer arranque en producción, **forzar el cambio** de la contraseña del
  admin genérico (`123@cronoempate` es conocida). Opciones: paso obligatorio en
  el launcher, o en el primer login del panel.
- Recordatorio: el panel es LAN-only (no sale por el túnel), lo que ya limita el
  riesgo, pero no se deja una credencial conocida en un evento real.

**Coste:** bajo.

## Fase 7 — Verificación de superficie automática (defensa en profundidad)

- Tras conectar el túnel, el launcher corre `cloudflared/verificar_superficie.sh`
  (o su equivalente) contra el hostname real: confirma que la lectura pública
  pasa y que **gestión + `/media/backups`** dan 404. Semáforo "superficie OK"
  antes de dar el evento por listo.

**Coste:** bajo-medio.

## Fase 8 — Instalador Windows y ensayo en limpio (G7)

- Compilar el `.exe` (NSIS) en Windows/CI (`cargo tauri build`; `tauri.conf.json`
  ya declara `targets: all`).
- Bundle: launcher + stack (compose, imagen/‑fuente de API, `dist` de panel y
  web, plantilla `cloudflared/config.yml`) + binario `cloudflared`.
- **Ensayo end-to-end en un Windows limpio**: de instalador a "servidor activo +
  túnel conectado", solo con el asistente. Es el criterio de aceptación del
  Anexo D.

**Coste:** alto (requiere máquina/CI Windows y una cuenta Cloudflare real).

---

## Orden sugerido

1. **Fase 1** (arrancar túnel) + **Fase 3** (check Docker) — desbloqueo rápido.
2. **Fase 2** (asistente de túnel) — el grueso del "llave en mano".
3. **Fase 5** (boot) + **Fase 6** (contraseña) + **Fase 7** (verificación).
4. **Fase 4** (imagen pre-construida) — decisión de release.
5. **Fase 8** (instalador Windows + ensayo) — último, necesita Windows/CI.

## Fuera de alcance (recordatorio de reglas)

- El **panel/gestión sigue LAN-only**: el asistente del túnel solo configura la
  superficie del corredor + lectura pública. Nunca abrir gestión por el túnel
  (regla del proyecto). El "admin desde internet" seguro sería vía Cloudflare
  Access (decisión aparte, no en este plan).
