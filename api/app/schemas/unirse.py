from pydantic import BaseModel


class UnirseSalida(BaseModel):
    evento_id: int
    inscripcion_id: int
    distancia_id: int
    distancia_nombre: str
    dorsal: str
    token_dispositivo: str
    evento_estado: str
