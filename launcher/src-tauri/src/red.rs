use local_ip_address::local_ip;

/// IP de la LAN del recinto, para el IP:puerto de panel y web pública (Anexo C).
pub fn ip_lan() -> Result<String, String> {
    local_ip()
        .map(|ip| ip.to_string())
        .map_err(|e| format!("No se pudo detectar la IP de la red local: {e}"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::IpAddr;

    #[test]
    fn ip_lan_devuelve_una_ip_valida() {
        let ip = ip_lan().unwrap();
        assert!(ip.parse::<IpAddr>().is_ok(), "no es una IP válida: {ip}");
    }
}
