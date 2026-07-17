use serde::Serialize;
use std::path::Path;
use std::process::Command;

#[derive(Serialize, Clone)]
pub struct EstadoServicio {
    pub nombre: String,
    pub estado: String,
    pub salud: Option<String>,
}

fn ejecutar_compose(ruta_compose: &Path, args: &[&str]) -> Result<String, String> {
    let salida = Command::new("docker")
        .arg("compose")
        .arg("-f")
        .arg(ruta_compose)
        .args(args)
        .output()
        .map_err(|e| format!("No se pudo ejecutar Docker: {e}. ¿Está Docker Desktop en marcha?"))?;

    if salida.status.success() {
        Ok(String::from_utf8_lossy(&salida.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&salida.stderr).to_string())
    }
}

/// `docker compose up -d` (spec v10 Anexo C: botón principal Iniciar).
pub fn iniciar(ruta_compose: &Path) -> Result<String, String> {
    ejecutar_compose(ruta_compose, &["up", "-d"])
}

/// `docker compose down` (spec v10 Anexo C: botón principal Detener).
pub fn detener(ruta_compose: &Path) -> Result<String, String> {
    ejecutar_compose(ruta_compose, &["down"])
}

/// Estado de cada servicio (`docker compose ps` emite JSON Lines: una línea por contenedor).
pub fn estado_servicios(ruta_compose: &Path) -> Result<Vec<EstadoServicio>, String> {
    let salida = ejecutar_compose(ruta_compose, &["ps", "--format", "json", "--all"])?;
    let mut servicios = Vec::new();
    for linea in salida.lines() {
        let linea = linea.trim();
        if linea.is_empty() {
            continue;
        }
        let valor: serde_json::Value = serde_json::from_str(linea)
            .map_err(|e| format!("No se pudo interpretar la salida de Docker: {e}"))?;
        servicios.push(EstadoServicio {
            nombre: valor
                .get("Service")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string(),
            estado: valor
                .get("State")
                .and_then(|v| v.as_str())
                .unwrap_or("desconocido")
                .to_string(),
            salud: valor
                .get("Health")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string())
                .filter(|s| !s.is_empty()),
        });
    }
    Ok(servicios)
}

/// "Servidor detenido / iniciando / activo" (spec v10 Anexo C): calculado a partir
/// de los contenedores de base de datos y API, los dos imprescindibles.
pub fn estado_global(servicios: &[EstadoServicio]) -> &'static str {
    let core: Vec<&EstadoServicio> = servicios
        .iter()
        .filter(|s| s.nombre == "db" || s.nombre == "api")
        .collect();
    if core.is_empty() {
        return "detenido";
    }
    if core.iter().all(|s| s.estado == "running") {
        "activo"
    } else {
        "iniciando"
    }
}

/// Semáforo del túnel (spec v10 Anexo C): distingue "aún no configurado" de
/// "configurado pero caído", en vez de tratarlos igual.
pub fn estado_tunel(servicios: &[EstadoServicio]) -> &'static str {
    match servicios.iter().find(|s| s.nombre == "cloudflared") {
        None => "no_configurado",
        Some(s) if s.estado == "running" => "conectado",
        Some(_) => "caido",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn servicio(nombre: &str, estado: &str) -> EstadoServicio {
        EstadoServicio {
            nombre: nombre.to_string(),
            estado: estado.to_string(),
            salud: None,
        }
    }

    #[test]
    fn estado_global_detenido_sin_servicios() {
        assert_eq!(estado_global(&[]), "detenido");
    }

    #[test]
    fn estado_global_activo_si_db_y_api_corren() {
        let servicios = vec![servicio("db", "running"), servicio("api", "running")];
        assert_eq!(estado_global(&servicios), "activo");
    }

    #[test]
    fn estado_global_iniciando_si_falta_alguno() {
        let servicios = vec![servicio("db", "running"), servicio("api", "created")];
        assert_eq!(estado_global(&servicios), "iniciando");
    }

    #[test]
    fn estado_tunel_no_configurado_si_no_hay_servicio() {
        assert_eq!(estado_tunel(&[]), "no_configurado");
    }

    #[test]
    fn estado_tunel_conectado_si_corre() {
        let servicios = vec![servicio("cloudflared", "running")];
        assert_eq!(estado_tunel(&servicios), "conectado");
    }

    #[test]
    fn estado_tunel_caido_si_existe_pero_no_corre() {
        let servicios = vec![servicio("cloudflared", "exited")];
        assert_eq!(estado_tunel(&servicios), "caido");
    }

    /// Requiere `docker-compose.dev.yml` levantado; correr con:
    /// `EMPATELIVE_COMPOSE_FILE=../docker-compose.dev.yml cargo test -- --ignored`
    #[test]
    #[ignore]
    fn estado_servicios_contra_el_stack_real() {
        let ruta = std::env::var("EMPATELIVE_COMPOSE_FILE")
            .expect("define EMPATELIVE_COMPOSE_FILE apuntando al compose real");
        let servicios = estado_servicios(std::path::Path::new(&ruta)).unwrap();
        assert!(servicios.iter().any(|s| s.nombre == "db" && s.estado == "running"));
        assert!(servicios.iter().any(|s| s.nombre == "api" && s.estado == "running"));
        assert_eq!(estado_global(&servicios), "activo");
    }
}
