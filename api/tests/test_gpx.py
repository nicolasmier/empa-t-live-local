import uuid

from app.models import Distancia
from app.security.rate_limit import limitador_login

_GPX_VALIDO = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="40.000000" lon="-3.500000"></trkpt>
      <trkpt lat="40.100000" lon="-3.400000"></trkpt>
      <trkpt lat="39.950000" lon="-3.600000"></trkpt>
    </trkseg>
  </trk>
</gpx>
"""


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_distancia(cliente, db_session, token: str) -> int:
    codigo = f"GPX-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento gpx", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    distancia = Distancia(evento_id=creado.json()["id"], nombre="10K")
    db_session.add(distancia)
    db_session.commit()
    return distancia.id


def test_subir_gpx_valido_extrae_bbox(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_distancia(cliente, db_session, token)

    respuesta = cliente.post(
        f"/distancias/{distancia_id}/gpx",
        files={"archivo": ("recorrido.gpx", _GPX_VALIDO, "application/gpx+xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["gpx_url"] == f"/media/gpx/{distancia_id}.gpx"
    bbox = cuerpo["mapa_config"]["bbox"]
    assert bbox["norte"] == 40.1
    assert bbox["sur"] == 39.95
    assert bbox["este"] == -3.4
    assert bbox["oeste"] == -3.6


def test_subir_gpx_corrupto_devuelve_400(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_distancia(cliente, db_session, token)

    respuesta = cliente.post(
        f"/distancias/{distancia_id}/gpx",
        files={"archivo": ("malo.gpx", b"esto no es xml valido", "application/gpx+xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "gpx_invalido"


def test_gpx_sin_puntos_devuelve_400(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_distancia(cliente, db_session, token)

    gpx_vacio = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg></trkseg></trk>
</gpx>
"""
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/gpx",
        files={"archivo": ("vacio.gpx", gpx_vacio, "application/gpx+xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "gpx_invalido"
