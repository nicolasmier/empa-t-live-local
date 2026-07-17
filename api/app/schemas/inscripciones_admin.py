from pydantic import BaseModel


class InscripcionActualizar(BaseModel):
    dorsal: str | None = None
    nombre: str | None = None
    apellidos: str | None = None
    club: str | None = None


class EliminarInscripcionesEntrada(BaseModel):
    inscripcion_ids: list[int]


class EliminarInscripcionesSalida(BaseModel):
    eliminadas: int
