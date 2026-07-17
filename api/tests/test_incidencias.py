import uuid
from datetime import UTC, datetime, timedelta

from app.models import Corredor, Distancia, Incidencia, Inscripcion, PosicionActual
from app.security.passwords import hash_password
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _login_operador(cliente) -> str:
    limitador_login.registrar_exito("panel:operador@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "operador@example.com", "password": "operador1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento_en_directo(cliente, db_session, token: str) -> tuple[int, int]:
    codigo = f"INC-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento incidencias", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.commit()

    for estado in ("publicado", "preparacion", "en_directo"):
        cliente.post(
            f"/eventos/{evento_id}/estado",
            json={"estado": estado},
            headers={"Authorization": f"Bearer {token}"},
        )
    return evento_id, distancia.id


def _generar_incidencia_sin_senal(cliente, db_session, evento_id: int, distancia_id: int) -> int:
    email = f"inc-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(
        nombre="Runner", apellidos="Test", email=email, password_hash=hash_password("clave12345")
    )
    db_session.add(corredor)
    db_session.flush()
    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia_id, dorsal="9")
    db_session.add(inscripcion)
    db_session.flush()

    ahora = datetime.now(UTC)
    db_session.add(
        PosicionActual(
            inscripcion_id=inscripcion.id,
            timestamp_dispositivo=ahora - timedelta(seconds=600),
            timestamp_recepcion=ahora - timedelta(seconds=600),
            latitud=40.0,
            longitud=-3.5,
        )
    )
    db_session.commit()

    respuesta = cliente.get(f"/eventos/{evento_id}/distancias/{distancia_id}/posiciones")
    assert respuesta.status_code == 200

    return (
        db_session.query(Incidencia)
        .filter_by(inscripcion_id=inscripcion.id, tipo="sin_senal")
        .one()
        .id
    )


def test_listar_incidencias_requiere_autenticacion(cliente, db_session) -> None:
    token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, token)
    _generar_incidencia_sin_senal(cliente, db_session, evento_id, distancia_id)

    respuesta = cliente.get(f"/eventos/{evento_id}/incidencias")
    assert respuesta.status_code == 401


def test_operador_puede_listar_y_resolver_incidencias(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    incidencia_id = _generar_incidencia_sin_senal(cliente, db_session, evento_id, distancia_id)

    operador_token = _login_operador(cliente)
    headers = {"Authorization": f"Bearer {operador_token}"}

    respuesta = cliente.get(f"/eventos/{evento_id}/incidencias", headers=headers)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == incidencia_id
    assert cuerpo[0]["dorsal"] == "9"
    assert cuerpo[0]["resuelto_en"] is None

    respuesta = cliente.get(
        f"/eventos/{evento_id}/incidencias", params={"resuelta": "true"}, headers=headers
    )
    assert respuesta.json() == []

    respuesta = cliente.put(f"/incidencias/{incidencia_id}/resolver", headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.json()["resuelto_en"] is not None

    respuesta = cliente.get(
        f"/eventos/{evento_id}/incidencias", params={"resuelta": "false"}, headers=headers
    )
    assert respuesta.json() == []


def test_resolver_incidencia_inexistente_devuelve_404(cliente) -> None:
    token = _login_admin(cliente)
    respuesta = cliente.put(
        "/incidencias/999999/resolver", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 404
