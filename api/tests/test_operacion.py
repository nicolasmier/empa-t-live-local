import uuid
from datetime import UTC, datetime, timedelta

from app.models import Corredor, Distancia, Inscripcion, PosicionActual
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def test_sin_evento_en_directo_devuelve_ceros(cliente) -> None:
    respuesta = cliente.get("/operacion/resumen")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["evento_activo"] is None
    assert cuerpo["corredores_transmitiendo"] == 0
    assert cuerpo["corredores_sin_senal"] == 0
    assert cuerpo["incidencias_abiertas"] == 0


def test_resumen_no_requiere_autenticacion(cliente) -> None:
    respuesta = cliente.get("/operacion/resumen")
    assert respuesta.status_code == 200


def test_resumen_cuenta_transmitiendo_y_sin_senal(cliente, db_session) -> None:
    token = _login_admin(cliente)
    codigo = f"RESUMEN-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento resumen", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    for estado in ("publicado", "preparacion", "en_directo"):
        cliente.post(
            f"/eventos/{evento_id}/estado",
            json={"estado": estado},
            headers={"Authorization": f"Bearer {token}"},
        )

    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.flush()

    ahora = datetime.now(UTC)

    corredor_activo = Corredor(
        nombre="Activo", apellidos="Test", email=f"activo-{uuid.uuid4().hex[:8]}@example.com"
    )
    corredor_inactivo = Corredor(
        nombre="Inactivo", apellidos="Test", email=f"inactivo-{uuid.uuid4().hex[:8]}@example.com"
    )
    db_session.add_all([corredor_activo, corredor_inactivo])
    db_session.flush()

    inscripcion_activa = Inscripcion(
        corredor_id=corredor_activo.id, distancia_id=distancia.id, dorsal="1"
    )
    inscripcion_inactiva = Inscripcion(
        corredor_id=corredor_inactivo.id, distancia_id=distancia.id, dorsal="2"
    )
    db_session.add_all([inscripcion_activa, inscripcion_inactiva])
    db_session.flush()

    db_session.add(
        PosicionActual(
            inscripcion_id=inscripcion_activa.id,
            timestamp_dispositivo=ahora,
            timestamp_recepcion=ahora,
            latitud=40.0,
            longitud=-3.5,
        )
    )
    db_session.add(
        PosicionActual(
            inscripcion_id=inscripcion_inactiva.id,
            timestamp_dispositivo=ahora - timedelta(seconds=600),
            timestamp_recepcion=ahora - timedelta(seconds=600),
            latitud=40.0,
            longitud=-3.5,
        )
    )
    db_session.commit()

    respuesta = cliente.get("/operacion/resumen")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["evento_activo"]["codigo_acceso"] == codigo
    assert cuerpo["corredores_transmitiendo"] == 1
    assert cuerpo["corredores_sin_senal"] == 1
    assert cuerpo["incidencias_abiertas"] == 1
