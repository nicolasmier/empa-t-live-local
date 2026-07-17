import uuid

from app.security.rate_limit import limitador_login


def _login(cliente, email: str, password: str) -> str:
    limitador_login.registrar_exito(f"panel:{email}")
    respuesta = cliente.post("/auth/login", json={"email": email, "password": password})
    assert respuesta.status_code == 200
    return respuesta.json()["access_token"]


def test_sin_token_devuelve_401(cliente) -> None:
    respuesta = cliente.get("/eventos")
    assert respuesta.status_code == 401


def test_operador_no_puede_crear_eventos(cliente) -> None:
    token = _login(cliente, "operador@example.com", "operador1234")
    respuesta = cliente.post(
        "/eventos",
        json={
            "nombre": "Prueba",
            "codigo_acceso": f"TEST-{uuid.uuid4().hex[:6]}",
            "fecha": "2026-09-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "prohibido"


def test_operador_puede_listar_eventos(cliente) -> None:
    token = _login(cliente, "operador@example.com", "operador1234")
    respuesta = cliente.get("/eventos", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200


def test_corredor_no_accede_a_gestion(cliente) -> None:
    email = f"corredor-{uuid.uuid4().hex[:8]}@example.com"
    registro = cliente.post(
        "/auth/corredores/registro",
        json={"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"},
    )
    token = registro.json()["access_token"]

    respuesta = cliente.get("/eventos", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 401


def test_admin_puede_crear_evento(cliente) -> None:
    token = _login(cliente, "admin@example.com", "admin1234")
    respuesta = cliente.post(
        "/eventos",
        json={
            "nombre": "Prueba",
            "codigo_acceso": f"TEST-{uuid.uuid4().hex[:6]}",
            "fecha": "2026-09-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "borrador"
