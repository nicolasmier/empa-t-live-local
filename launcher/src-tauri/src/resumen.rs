use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize, Clone)]
pub struct EventoActivoResumen {
    pub id: i64,
    pub nombre: String,
    pub codigo_acceso: String,
    pub estado: String,
}

#[derive(Deserialize, Serialize, Clone)]
pub struct ResumenOperativo {
    pub evento_activo: Option<EventoActivoResumen>,
    pub corredores_transmitiendo: i64,
    pub corredores_sin_senal: i64,
    pub incidencias_abiertas: i64,
}

/// `GET /operacion/resumen` (LAN, sin auth): semáforos de corredores transmitiendo
/// e incidencias del launcher (spec v10 Anexo C).
pub async fn obtener_resumen(base_url: &str) -> Result<ResumenOperativo, String> {
    let url = format!("{base_url}/operacion/resumen");
    let cliente = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .map_err(|e| format!("No se pudo crear el cliente HTTP: {e}"))?;

    let respuesta = cliente
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("No se pudo contactar con el servidor: {e}"))?;

    respuesta
        .json::<ResumenOperativo>()
        .await
        .map_err(|e| format!("Respuesta inesperada del servidor: {e}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Requiere la API real en marcha (`docker compose -f docker-compose.dev.yml up`).
    #[tokio::test]
    #[ignore]
    async fn obtener_resumen_contra_la_api_real() {
        let resumen = obtener_resumen("http://localhost:8000").await.unwrap();
        assert!(resumen.corredores_transmitiendo >= 0);
        assert!(resumen.incidencias_abiertas >= 0);
    }
}
