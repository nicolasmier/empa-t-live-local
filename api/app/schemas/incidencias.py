from datetime import datetime

from pydantic import BaseModel


class IncidenciaSalida(BaseModel):
    id: int
    evento_id: int
    inscripcion_id: int | None
    dorsal: str | None
    tipo: str
    descripcion: str | None
    creado_en: datetime
    resuelto_en: datetime | None

    model_config = {"from_attributes": True}
