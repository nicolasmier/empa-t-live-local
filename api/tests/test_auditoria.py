import uuid

from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def test_auditoria_requiere_admin(cliente) -> None:
    respuesta = cliente.get("/auditoria")
    assert respuesta.status_code == 401


def test_auditoria_filtra_por_evento_y_accion(cliente) -> None:
    token = _login_admin(cliente)
    headers = {"Authorization": f"Bearer {token}"}
    codigo = f"AUD-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento auditoría", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers=headers,
    )
    evento_id = creado.json()["id"]
    cliente.post(f"/eventos/{evento_id}/estado", json={"estado": "publicado"}, headers=headers)

    respuesta = cliente.get("/auditoria", params={"evento_id": evento_id}, headers=headers)
    assert respuesta.status_code == 200
    acciones = {fila["accion"] for fila in respuesta.json()}
    assert acciones == {"evento_creado", "evento_cambio_estado"}

    respuesta = cliente.get(
        "/auditoria",
        params={"evento_id": evento_id, "accion": "evento_cambio_estado"},
        headers=headers,
    )
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["accion"] == "evento_cambio_estado"
    assert cuerpo[0]["detalle"] == {"desde": "borrador", "hasta": "publicado"}


def test_auditoria_filtra_por_usuario(cliente) -> None:
    token = _login_admin(cliente)
    headers = {"Authorization": f"Bearer {token}"}
    codigo = f"AUD-{uuid.uuid4().hex[:6]}"
    cliente.post(
        "/eventos",
        json={"nombre": "Evento auditoría 2", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers=headers,
    )

    respuesta = cliente.get("/auditoria", params={"usuario_id": 999999}, headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.json() == []
