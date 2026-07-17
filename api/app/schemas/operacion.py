from pydantic import BaseModel


class EventoActivoResumen(BaseModel):
    id: int
    nombre: str
    codigo_acceso: str
    estado: str


class ResumenOperativo(BaseModel):
    evento_activo: EventoActivoResumen | None
    corredores_transmitiendo: int
    corredores_sin_senal: int
    incidencias_abiertas: int
