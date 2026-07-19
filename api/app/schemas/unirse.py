from pydantic import BaseModel


class UnirseEntrada(BaseModel):
    # Confirmación de dorsal (decisión 2026-07-19): el código de evento por sí
    # solo identifica LA CARRERA, no al corredor — quien identifica al corredor
    # es su sesión ya autenticada (email/teléfono). Pedir también el dorsal que
    # el organizador le entregó es un respaldo barato contra cualquier mismatch
    # entre lo que cargó el admin y la cuenta con la que el corredor entró en la
    # app: si no coinciden, mejor que el corredor lo vea aquí y lo corrija antes
    # de la carrera que descubrir en directo que está viendo/enviando la señal
    # equivocada.
    dorsal: str


class UnirseSalida(BaseModel):
    evento_id: int
    inscripcion_id: int
    distancia_id: int
    distancia_nombre: str
    dorsal: str
    token_dispositivo: str
    evento_estado: str
