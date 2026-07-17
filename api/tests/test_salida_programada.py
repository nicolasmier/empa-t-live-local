import uuid
from datetime import UTC, datetime, timedelta

from app.models import Auditoria, Evento
from app.security.rate_limit import limitador_login
from app.servicios.salida_programada import activar_salidas_programadas


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento_en_preparacion(cliente, token: str) -> int:
    codigo = f"PROG-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento programado", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    for estado in ("publicado", "preparacion"):
        cliente.post(
            f"/eventos/{evento_id}/estado",
            json={"estado": estado},
            headers={"Authorization": f"Bearer {token}"},
        )
    return evento_id


def test_programar_y_cancelar_hora_de_salida(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento_en_preparacion(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    hora = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    respuesta = cliente.put(
        f"/eventos/{evento_id}", json={"hora_programada_directo": hora}, headers=headers
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["hora_programada_directo"] is not None

    cancelacion = cliente.put(
        f"/eventos/{evento_id}", json={"hora_programada_directo": None}, headers=headers
    )
    assert cancelacion.status_code == 200
    assert cancelacion.json()["hora_programada_directo"] is None


def test_activar_salidas_programadas_pasa_a_en_directo_si_ya_toca(cliente, db_session) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento_en_preparacion(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}

    hora_pasada = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    cliente.put(
        f"/eventos/{evento_id}",
        json={"hora_programada_directo": hora_pasada},
        headers=headers,
    )

    # Se le pasa `db_session` (la misma transacción de prueba) en vez de
    # dejar que abra su propia conexión: con una conexión aparte no vería el
    # evento, que solo existe dentro de la transacción de este test.
    activar_salidas_programadas(db_session)

    db_session.expire_all()
    evento = db_session.get(Evento, evento_id)
    assert evento.estado == "en_directo"
    assert evento.hora_programada_directo is None

    auditoria = (
        db_session.query(Auditoria)
        .filter_by(entidad_tipo="evento", entidad_id=str(evento_id), accion="evento_salida_automatica")
        .one()
    )
    assert auditoria.detalle["hora_programada"] is not None


def test_activar_salidas_programadas_no_toca_si_la_hora_no_ha_llegado(cliente, db_session) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento_en_preparacion(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}

    hora_futura = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
    cliente.put(
        f"/eventos/{evento_id}",
        json={"hora_programada_directo": hora_futura},
        headers=headers,
    )

    activar_salidas_programadas(db_session)

    db_session.expire_all()
    evento = db_session.get(Evento, evento_id)
    assert evento.estado == "preparacion"
    assert evento.hora_programada_directo is not None


def test_cambiar_estado_manualmente_limpia_la_hora_programada(cliente, db_session) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento_en_preparacion(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}

    hora_futura = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
    cliente.put(
        f"/eventos/{evento_id}",
        json={"hora_programada_directo": hora_futura},
        headers=headers,
    )

    respuesta = cliente.post(
        f"/eventos/{evento_id}/estado", json={"estado": "en_directo"}, headers=headers
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["hora_programada_directo"] is None
