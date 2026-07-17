import uuid

from app.models import Auditoria
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento(cliente, token: str) -> int:
    codigo = f"UPD-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento a actualizar", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return creado.json()["id"]


def test_actualizar_evento_con_fecha_no_rompe_la_auditoria(cliente, db_session) -> None:
    # Regresión: `EventoActualizar.fecha` es un `date` de Python; pasarlo tal
    # cual (sin mode="json") al `detalle` JSONB de auditoría hacía que
    # psycopg lanzara un 500 al serializar ("Object of type date is not
    # JSON serializable"), y el navegador lo mostraba como un falso error de
    # CORS porque la respuesta 500 sin manejar no llevaba cabeceras CORS.
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    respuesta = cliente.put(
        f"/eventos/{evento_id}",
        json={"nombre": "Nuevo nombre", "fecha": "2026-10-15"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Nuevo nombre"
    assert cuerpo["fecha"] == "2026-10-15"

    auditoria = (
        db_session.query(Auditoria)
        .filter_by(entidad_tipo="evento", entidad_id=str(evento_id), accion="evento_actualizado")
        .one()
    )
    assert auditoria.detalle == {"nombre": "Nuevo nombre", "fecha": "2026-10-15"}


def test_actualizar_evento_solo_fecha(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    respuesta = cliente.put(
        f"/eventos/{evento_id}",
        json={"fecha": "2027-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["fecha"] == "2027-01-01"
