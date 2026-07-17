import pytest

from app.dominio.estados_evento import ORDEN_ESTADOS, transicion_valida

# Tabla completa de las 6x6 = 36 combinaciones (spec v10 §11): avance en orden a
# cualquier estado posterior; retroceso permitido solo de un paso; `archivado` es
# terminal (ninguna transición posible, ni siquiera el retroceso de un paso).
_ESPERADO = {
    ("borrador", "borrador"): False,
    ("borrador", "publicado"): True,
    ("borrador", "preparacion"): True,
    ("borrador", "en_directo"): True,
    ("borrador", "finalizado"): True,
    ("borrador", "archivado"): True,
    ("publicado", "borrador"): True,
    ("publicado", "publicado"): False,
    ("publicado", "preparacion"): True,
    ("publicado", "en_directo"): True,
    ("publicado", "finalizado"): True,
    ("publicado", "archivado"): True,
    ("preparacion", "borrador"): False,
    ("preparacion", "publicado"): True,
    ("preparacion", "preparacion"): False,
    ("preparacion", "en_directo"): True,
    ("preparacion", "finalizado"): True,
    ("preparacion", "archivado"): True,
    ("en_directo", "borrador"): False,
    ("en_directo", "publicado"): False,
    ("en_directo", "preparacion"): True,
    ("en_directo", "en_directo"): False,
    ("en_directo", "finalizado"): True,
    ("en_directo", "archivado"): True,
    ("finalizado", "borrador"): False,
    ("finalizado", "publicado"): False,
    ("finalizado", "preparacion"): False,
    # Decisión clarify 2026-07-16: retroceso Finalizado -> En directo es válido
    # (los tokens de dispositivo revocados no se reactivan; ver servicios/tokens_dispositivo.py).
    ("finalizado", "en_directo"): True,
    ("finalizado", "finalizado"): False,
    ("finalizado", "archivado"): True,
    ("archivado", "borrador"): False,
    ("archivado", "publicado"): False,
    ("archivado", "preparacion"): False,
    ("archivado", "en_directo"): False,
    ("archivado", "finalizado"): False,
    ("archivado", "archivado"): False,
}


def test_tabla_cubre_las_36_combinaciones() -> None:
    assert len(_ESPERADO) == len(ORDEN_ESTADOS) ** 2 == 36


@pytest.mark.parametrize(("origen", "destino"), list(_ESPERADO.keys()))
def test_transicion(origen: str, destino: str) -> None:
    assert transicion_valida(origen, destino) is _ESPERADO[(origen, destino)]


def test_estado_desconocido_es_invalido() -> None:
    assert transicion_valida("borrador", "estado_inventado") is False
    assert transicion_valida("estado_inventado", "borrador") is False
