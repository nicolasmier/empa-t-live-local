mod docker;
mod entorno;
mod red;
mod resumen;

use docker::EstadoServicio;
use resumen::ResumenOperativo;
use serde::Serialize;

const BASE_URL_API: &str = "http://localhost:8000";

#[derive(Serialize, Clone)]
pub struct EstadoServidor {
    pub estado: String,
    pub tunel: String,
    pub servicios: Vec<EstadoServicio>,
}

#[derive(Serialize, Clone)]
pub struct DireccionesLan {
    pub ip: String,
    pub panel: String,
    pub web_publica: String,
}

#[tauri::command]
fn iniciar_servidor(app: tauri::AppHandle) -> Result<String, String> {
    docker::iniciar(&entorno::preparar_stack(&app)?)
}

#[tauri::command]
fn detener_servidor(app: tauri::AppHandle) -> Result<String, String> {
    docker::detener(&entorno::preparar_stack(&app)?)
}

#[tauri::command]
fn estado_servidor(app: tauri::AppHandle) -> Result<EstadoServidor, String> {
    let servicios = docker::estado_servicios(&entorno::preparar_stack(&app)?)?;
    Ok(EstadoServidor {
        estado: docker::estado_global(&servicios).to_string(),
        tunel: docker::estado_tunel(&servicios).to_string(),
        servicios,
    })
}

#[tauri::command]
async fn resumen_operativo() -> Result<ResumenOperativo, String> {
    resumen::obtener_resumen(BASE_URL_API).await
}

#[tauri::command]
fn direcciones_lan() -> Result<DireccionesLan, String> {
    let ip = red::ip_lan()?;
    Ok(DireccionesLan {
        panel: format!("http://{ip}:8080"),
        web_publica: format!("http://{ip}:8081"),
        ip,
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            iniciar_servidor,
            detener_servidor,
            estado_servidor,
            resumen_operativo,
            direcciones_lan,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
