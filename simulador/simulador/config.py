from dataclasses import dataclass


@dataclass
class ConfiguracionSimulacion:
    api_url: str
    gpx: str
    corredores: int
    duracion_min: float
    perdida_cobertura: float
    reloj_desviado: float
    admin_email: str
    admin_password: str
    codigo_evento: str
    factor_aceleracion: float
    espaciado_min_m: float
    espaciado_max_m: float
