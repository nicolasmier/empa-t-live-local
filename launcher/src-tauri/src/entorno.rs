use rand::Rng;
use std::fs;
use std::path::{Path, PathBuf};
use tauri::Manager;

/// Ruta al `docker-compose` que envuelve el launcher.
///
/// `EMPATELIVE_COMPOSE_FILE` permite apuntar a otro fichero durante el
/// desarrollo (p. ej. `docker-compose.dev.yml`, que no exige secretos en
/// `.env`) y se usa tal cual, sin copiar nada.
///
/// En el paquete instalado (AppImage) no hay esa variable: los ficheros del
/// stack (`docker-compose.prod.yml`, `.env.prod.example`, `cloudflared/` y
/// `/api`) viajan como recursos de solo lectura de Tauri. La primera vez que
/// se arranca, se copian a `app_data_dir()/stack` — un directorio escribible
/// del usuario — porque ahí es donde `asegurar_env` necesita crear el `.env`
/// y donde Docker necesita poder resolver `build: context: ./api`.
///
/// Genera también el `.env` aquí (no solo al pulsar "Iniciar"): el propio
/// `estado_servidor` corre `docker compose ps` nada más abrir la ventana, y
/// sin `.env` esa llamada falla por las variables `${...:?}` sin definir del
/// compose de producción — el Administrador vería un error crudo de Docker
/// antes incluso de tocar nada.
pub fn preparar_stack(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    if let Ok(ruta) = std::env::var("EMPATELIVE_COMPOSE_FILE") {
        asegurar_env(Path::new(&ruta))?;
        return Ok(PathBuf::from(ruta));
    }

    let destino = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("No se pudo localizar el directorio de datos: {e}"))?
        .join("stack");
    let compose_destino = destino.join("docker-compose.prod.yml");

    if !compose_destino.exists() {
        let origen = app
            .path()
            .resource_dir()
            .map_err(|e| format!("No se pudo localizar los recursos empaquetados: {e}"))?
            .join("stack");
        copiar_directorio(&origen, &destino)
            .map_err(|e| format!("No se pudo preparar los ficheros del servidor: {e}"))?;
    }

    asegurar_env(&compose_destino)?;
    Ok(compose_destino)
}

/// Copia recursiva simple (sin dependencias externas): usada una única vez,
/// en el primer arranque, para llevar los recursos empaquetados de solo
/// lectura a un directorio de datos escribible.
fn copiar_directorio(origen: &Path, destino: &Path) -> std::io::Result<()> {
    fs::create_dir_all(destino)?;
    for entrada in fs::read_dir(origen)? {
        let entrada = entrada?;
        let destino_hijo = destino.join(entrada.file_name());
        if entrada.file_type()?.is_dir() {
            copiar_directorio(&entrada.path(), &destino_hijo)?;
        } else {
            fs::copy(entrada.path(), &destino_hijo)?;
        }
    }
    Ok(())
}

fn generar_secreto(longitud: usize) -> String {
    const CARACTERES: &[u8] =
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let mut rng = rand::thread_rng();
    (0..longitud)
        .map(|_| {
            let indice = rng.gen_range(0..CARACTERES.len());
            CARACTERES[indice] as char
        })
        .collect()
}

/// Genera `.env` con secretos aleatorios si no existe todavía, junto al
/// `docker-compose.prod.yml` (spec v10 Anexo D: sin terminal, sin pedirle al
/// Administrador que invente contraseñas).
pub fn asegurar_env(ruta_compose: &Path) -> Result<bool, String> {
    let directorio = ruta_compose.parent().unwrap_or_else(|| Path::new("."));
    let ruta_env = directorio.join(".env");
    if ruta_env.exists() {
        return Ok(false);
    }

    let contenido = format!(
        "POSTGRES_PASSWORD={}\nSECRET_KEY={}\nBACKUP_PASSPHRASE={}\nBACKUP_DIR_SECUNDARIO=\nADMIN_BOOTSTRAP_EMAIL=admin@localhost\n",
        generar_secreto(32),
        generar_secreto(32),
        generar_secreto(32),
    );
    fs::write(&ruta_env, contenido).map_err(|e| format!("No se pudo crear .env: {e}"))?;
    Ok(true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn no_sobrescribe_un_env_existente() {
        let directorio = tempfile::tempdir().unwrap();
        let compose = directorio.path().join("docker-compose.prod.yml");
        fs::write(&compose, "services: {}").unwrap();
        let env = directorio.path().join(".env");
        fs::write(&env, "MARCA=original").unwrap();

        let creado = asegurar_env(&compose).unwrap();

        assert!(!creado);
        assert_eq!(fs::read_to_string(&env).unwrap(), "MARCA=original");
    }

    #[test]
    fn genera_un_env_con_los_cuatro_secretos_si_no_existe() {
        let directorio = tempfile::tempdir().unwrap();
        let compose = directorio.path().join("docker-compose.prod.yml");
        fs::write(&compose, "services: {}").unwrap();

        let creado = asegurar_env(&compose).unwrap();

        assert!(creado);
        let contenido = fs::read_to_string(directorio.path().join(".env")).unwrap();
        assert!(contenido.contains("POSTGRES_PASSWORD="));
        assert!(contenido.contains("SECRET_KEY="));
        assert!(contenido.contains("BACKUP_PASSPHRASE="));
    }

    #[test]
    fn copiar_directorio_reproduce_un_arbol_con_subdirectorios() {
        let origen = tempfile::tempdir().unwrap();
        fs::write(origen.path().join("docker-compose.prod.yml"), "services: {}").unwrap();
        fs::create_dir(origen.path().join("api")).unwrap();
        fs::write(origen.path().join("api").join("Dockerfile"), "FROM scratch").unwrap();
        fs::create_dir(origen.path().join("cloudflared")).unwrap();
        fs::write(
            origen.path().join("cloudflared").join("config.yml"),
            "tunnel: x",
        )
        .unwrap();

        let raiz_destino = tempfile::tempdir().unwrap();
        let destino = raiz_destino.path().join("stack");
        copiar_directorio(origen.path(), &destino).unwrap();

        assert_eq!(
            fs::read_to_string(destino.join("docker-compose.prod.yml")).unwrap(),
            "services: {}"
        );
        assert_eq!(
            fs::read_to_string(destino.join("api").join("Dockerfile")).unwrap(),
            "FROM scratch"
        );
        assert_eq!(
            fs::read_to_string(destino.join("cloudflared").join("config.yml")).unwrap(),
            "tunnel: x"
        );
    }
}
