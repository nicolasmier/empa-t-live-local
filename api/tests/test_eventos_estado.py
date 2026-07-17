import uuid

from app.models import Corredor, Distancia, Inscripcion, TokenDispositivo
from app.security.rate_limit import limitador_login
from app.security.tokens import hash_token_dispositivo


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def test_transicion_invalida_devuelve_409(cliente) -> None:
    token = _login_admin(cliente)
    cabeceras = {"Authorization": f"Bearer {token}"}

    creado = cliente.post(
        "/eventos",
        json={
            "nombre": "Evento 409",
            "codigo_acceso": f"E409-{uuid.uuid4().hex[:6]}",
            "fecha": "2026-09-01",
        },
        headers=cabeceras,
    )
    evento_id = creado.json()["id"]

    respuesta = cliente.post(
        f"/eventos/{evento_id}/estado", json={"estado": "en_directo_typo"}, headers=cabeceras
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "transicion_invalida"


def test_ciclo_completo_estados_y_revocacion_tokens(cliente, db_session) -> None:
    token = _login_admin(cliente)
    cabeceras = {"Authorization": f"Bearer {token}"}

    codigo = f"CICLO-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos", json={"nombre": "Evento ciclo", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers=cabeceras,
    )
    assert creado.status_code == 201
    evento_id = creado.json()["id"]
    assert creado.json()["estado"] == "borrador"

    for destino in ("publicado", "preparacion", "en_directo"):
        respuesta = cliente.post(
            f"/eventos/{evento_id}/estado", json={"estado": destino}, headers=cabeceras
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == destino

    # Inscripción con token de dispositivo activo, para comprobar la revocación masiva.
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.flush()

    corredor = Corredor(
        nombre="Runner",
        apellidos="Test",
        email=f"runner-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
    )
    db_session.add(corredor)
    db_session.flush()

    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia.id, dorsal="1")
    db_session.add(inscripcion)
    db_session.flush()

    token_dispositivo = TokenDispositivo(
        inscripcion_id=inscripcion.id, token_hash=hash_token_dispositivo("secreto")
    )
    db_session.add(token_dispositivo)
    db_session.commit()

    finalizar = cliente.post(
        f"/eventos/{evento_id}/estado", json={"estado": "finalizado"}, headers=cabeceras
    )
    assert finalizar.status_code == 200

    db_session.refresh(token_dispositivo)
    assert token_dispositivo.revocado_en is not None

    auditoria = cliente.get(f"/auditoria?evento_id={evento_id}", headers=cabeceras)
    assert auditoria.status_code == 200
    acciones = {entrada["accion"] for entrada in auditoria.json()}
    assert "evento_creado" in acciones
    assert "evento_cambio_estado" in acciones
