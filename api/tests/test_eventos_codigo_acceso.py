import uuid

from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento(cliente, token: str, codigo: str | None = None) -> int:
    codigo = codigo or f"COD-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento código", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return creado.json()["id"]


def test_editar_codigo_acceso(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    nuevo_codigo = f"NUEVO-{uuid.uuid4().hex[:6]}"

    respuesta = cliente.put(
        f"/eventos/{evento_id}",
        json={"codigo_acceso": nuevo_codigo},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["codigo_acceso"] == nuevo_codigo


def test_editar_codigo_acceso_duplicado_devuelve_409(cliente) -> None:
    token = _login_admin(cliente)
    codigo_existente = f"EXISTENTE-{uuid.uuid4().hex[:6]}"
    _crear_evento(cliente, token, codigo_existente)
    evento_id = _crear_evento(cliente, token)

    respuesta = cliente.put(
        f"/eventos/{evento_id}",
        json={"codigo_acceso": codigo_existente},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "codigo_duplicado"


def test_editar_codigo_acceso_igual_al_propio_no_da_error(cliente) -> None:
    token = _login_admin(cliente)
    codigo = f"PROPIO-{uuid.uuid4().hex[:6]}"
    evento_id = _crear_evento(cliente, token, codigo)

    respuesta = cliente.put(
        f"/eventos/{evento_id}",
        json={"codigo_acceso": codigo, "nombre": "Renombrado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["codigo_acceso"] == codigo
