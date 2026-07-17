# Launcher

FASE S5 del plan de Servidor (`docs/Plan_Implementacion_1_Servidor_v2.md`).
Aplicación de escritorio (Tauri: Rust + webview) que envuelve `docker compose`
para que el Administrador inicie/detenga el servidor sin usar la terminal
(spec v10 Anexo C).

## Qué hace

- Botón único Iniciar/Detener (`docker compose up -d` / `down`).
- Estado grande: detenido / iniciando / activo, calculado a partir de
  `docker compose ps`.
- Semáforos: túnel (no configurado / conectado / caído), corredores
  transmitiendo, incidencias abiertas — estos dos últimos vía
  `GET /operacion/resumen` de la API.
- IP:puerto de panel (`:8080`) y web pública (`:8081`) con botón de copiar y QR
  — servidos por los contenedores `panel`/`web-publica` de
  `docker-compose.prod.yml` (nginx sirviendo el `dist/` ya compilado).
- Genera `.env` con secretos aleatorios en el primer arranque, si no existe ya
  (ver "Dónde vive el stack instalado" más abajo).

## Dónde vive el stack instalado

En el paquete (AppImage) los recursos (`docker-compose.prod.yml`,
`.env.prod.example`, `cloudflared/config.yml`, una copia de `/api` sin
`.venv`/`storage`, y los `dist/` ya compilados de `panel` y `web-publica`)
viajan de solo lectura dentro del propio `.AppImage`. En el
primer arranque se copian a un directorio escribible del usuario —
`~/.local/share/com.empatelive.launcher/stack/` en Linux — porque ahí es
donde se genera el `.env` y donde Docker necesita poder construir la imagen
de `/api`. Arranques posteriores reutilizan esa copia (no se vuelve a copiar
ni se regenera el `.env`).

Con `EMPATELIVE_COMPOSE_FILE` definida (modo desarrollo) no se copia nada: se
usa esa ruta tal cual.

## Desarrollo

```bash
npm install
EMPATELIVE_COMPOSE_FILE=../docker-compose.dev.yml npm run tauri dev
```

`EMPATELIVE_COMPOSE_FILE` apunta a qué compose envuelve el launcher; en
desarrollo conviene usar `docker-compose.dev.yml` (no exige secretos en `.env`).
Sin esa variable, usa `docker-compose.prod.yml` por defecto (el real, para producción).

## Tests

```bash
cd src-tauri
cargo test                 # unitarios, sin dependencias externas
cargo test -- --ignored    # + integración contra el stack Docker real (debe estar levantado)
```

## Empaquetado (AppImage, Fedora/Linux)

```bash
cd launcher
NO_STRIP=1 APPIMAGE_EXTRACT_AND_RUN=1 npm run tauri build -- --bundles appimage
```

- `beforeBuildCommand` corre `scripts/preparar_recursos.sh`, que primero
  compila `panel` y `web-publica` (`npm run build --workspace`) y copia sus
  `dist/` a `resources-build/{panel,web-publica}/dist/`, y luego copia `/api`
  (excluyendo `.venv`/`storage`/etc. vía `api/.dockerignore`) a
  `resources-build/api/` — de ahí lo empaqueta `tauri.conf.json`
  (`bundle.resources`) como `stack/api`, `stack/panel/dist` y
  `stack/web-publica/dist`. `resources-build/` no se versiona (está en
  `.gitignore`).
- `APPIMAGE_EXTRACT_AND_RUN=1` evita que `linuxdeploy` necesite FUSE (no
  siempre disponible/instalado).
- `NO_STRIP=1` evita que `linuxdeploy` intente hacer `strip` de las librerías
  del sistema: en Fedora (binutils/glibc muy recientes, secciones `.relr.dyn`)
  el `strip` que trae empaquetado `linuxdeploy` no las reconoce y falla.
- El `.AppImage` resultante queda en
  `launcher/src-tauri/target/release/bundle/appimage/`.

### Icono de escritorio (para que el Administrador no escriba nada)

```bash
mkdir -p ~/.local/bin ~/.local/share/applications ~/.local/share/icons
cp "src-tauri/target/release/bundle/appimage/EmpateLive Launcher_0.1.0_amd64.AppImage" \
   ~/.local/bin/empatelive-launcher
chmod +x ~/.local/bin/empatelive-launcher
cp src-tauri/icons/128x128.png ~/.local/share/icons/empatelive-launcher.png
```

Y un `~/.local/share/applications/empatelive-launcher.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=EmpateLive Launcher
Comment=Iniciar/detener el servidor de EmpateLive
Exec=/home/USUARIO/.local/bin/empatelive-launcher
Icon=/home/USUARIO/.local/share/icons/empatelive-launcher.png
Terminal=false
Categories=Utility;
```

Con eso aparece en el menú de aplicaciones de GNOME: el Administrador solo
tiene que hacer clic en el icono.

## Pendiente

Ver `docs/pendiente_instalador_windows.md`: el instalador `.exe` real no se ha
compilado ni probado en Windows desde este entorno de desarrollo (Linux). La
ruta Linux/AppImage sí está construida y verificada de punta a punta (build
real de `/api`, migraciones, bootstrap del Administrador, API respondiendo).
