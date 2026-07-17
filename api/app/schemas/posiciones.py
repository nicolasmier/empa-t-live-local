from datetime import datetime

from pydantic import BaseModel


class PuntoPosicionEntrada(BaseModel):
    timestamp_dispositivo: datetime
    latitud: float
    longitud: float
    precision_m: float | None = None
    velocidad_kmh: float | None = None
    bateria_pct: int | None = None


class IngestaSalida(BaseModel):
    procesados: int


class PosicionPublica(BaseModel):
    inscripcion_id: int
    dorsal: str
    nombre: str
    apellidos: str
    club: str | None
    foto_url: str | None
    latitud: float | None
    longitud: float | None
    timestamp_dispositivo: datetime | None
    estado: str


class InscripcionEstadoSalida(BaseModel):
    dorsal: str
    distancia_nombre: str
    estado_transmision: str
    latitud: float | None
    longitud: float | None
    timestamp_dispositivo: datetime | None
    timestamp_recepcion: datetime | None
    bateria_pct: int | None
    estado_evento: str
