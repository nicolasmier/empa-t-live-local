from pydantic import BaseModel


class CorredorActualizar(BaseModel):
    nombre: str | None = None
    apellidos: str | None = None
    club: str | None = None


class CorredorSalida(BaseModel):
    id: int
    nombre: str
    apellidos: str
    club: str | None
    foto_url: str | None
    email: str

    model_config = {"from_attributes": True}
