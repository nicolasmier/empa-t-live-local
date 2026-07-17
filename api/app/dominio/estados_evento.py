"""Máquina de estados del evento (spec v10 §11).

Módulo puro y aislado: sin dependencias de infraestructura (BD, HTTP...).

Regla: avance en orden (a cualquier estado posterior); retroceso permitido
solo de un paso; salvo desde `archivado`, que es terminal (ninguna
transición posible, ni siquiera el retroceso de un paso).
"""

ORDEN_ESTADOS = ("borrador", "publicado", "preparacion", "en_directo", "finalizado", "archivado")
ESTADO_TERMINAL = "archivado"

_indice = {estado: i for i, estado in enumerate(ORDEN_ESTADOS)}


def transicion_valida(origen: str, destino: str) -> bool:
    if origen not in _indice or destino not in _indice:
        return False
    if origen == destino:
        return False
    if origen == ESTADO_TERMINAL:
        return False
    i, j = _indice[origen], _indice[destino]
    if j > i:
        return True
    return j == i - 1
