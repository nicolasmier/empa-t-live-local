from pydantic import BaseModel


class UnirseSalida(BaseModel):
    distancia_id: int
    distancia_nombre: str
    dorsal: str
    token_dispositivo: str
    evento_estado: str
