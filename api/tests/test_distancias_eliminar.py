import uuid

from app.models import (
    Corredor,
    Distancia,
    Incidencia,
    Inscripcion,
    PosicionActual,
    TokenDispositivo,
)
from app.security.passwords import hash_password
from app.security.rate_limit import limitador_login
from app.security.tokens import generar_token_dispositivo, hash_token_dispositivo


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento(cliente, token: str) -> int:
    codigo = f"DEL-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento borrar distancia", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return creado.json()["id"]


def test_eliminar_distancia_vacia(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    creada = cliente.post(
        f"/eventos/{evento_id}/distancias", json={"nombre": "10K"}, headers=headers
    )
    distancia_id = creada.json()["id"]

    respuesta = cliente.delete(f"/distancias/{distancia_id}", headers=headers)
    assert respuesta.status_code == 204

    listado = cliente.get(f"/eventos/{evento_id}/distancias")
    assert listado.json() == []


def test_eliminar_distancia_con_corredores_borra_en_cascada(cliente, db_session) -> None:
    # Poder deshacer un error tras publicar (p. ej. distancia o importación
    # equivocadas) es más importante que proteger datos que el propio
    # Administrador ha decidido borrar: se borra la distancia con todo lo
    # que cuelga de sus inscripciones, no se bloquea con un 409.
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    creada = cliente.post(
        f"/eventos/{evento_id}/distancias", json={"nombre": "10K"}, headers=headers
    )
    distancia_id = creada.json()["id"]

    corredor = Corredor(
        nombre="Runner",
        apellidos="Test",
        email=f"del-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("clave12345"),
    )
    db_session.add(corredor)
    db_session.flush()
    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia_id, dorsal="1")
    db_session.add(inscripcion)
    db_session.flush()
    inscripcion_id = inscripcion.id

    db_session.add(
        PosicionActual(
            inscripcion_id=inscripcion_id,
            timestamp_dispositivo="2026-09-01T10:00:00+00:00",
            timestamp_recepcion="2026-09-01T10:00:00+00:00",
            latitud=40.0,
            longitud=-3.5,
        )
    )
    db_session.add(
        TokenDispositivo(
            inscripcion_id=inscripcion_id,
            token_hash=hash_token_dispositivo(generar_token_dispositivo()),
        )
    )
    db_session.add(
        Incidencia(evento_id=evento_id, inscripcion_id=inscripcion_id, tipo="sin_senal")
    )
    db_session.commit()

    respuesta = cliente.delete(f"/distancias/{distancia_id}", headers=headers)
    assert respuesta.status_code == 204

    assert db_session.get(Distancia, distancia_id) is None
    assert db_session.get(Inscripcion, inscripcion_id) is None
    assert db_session.get(PosicionActual, inscripcion_id) is None
    assert db_session.query(TokenDispositivo).filter_by(inscripcion_id=inscripcion_id).count() == 0
    assert db_session.query(Incidencia).filter_by(inscripcion_id=inscripcion_id).count() == 0
    # El corredor (cuenta permanente, independiente del evento) no se toca.
    assert db_session.get(Corredor, corredor.id) is not None
