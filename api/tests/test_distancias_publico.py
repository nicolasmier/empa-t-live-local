import uuid

from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def test_listar_distancias_no_requiere_autenticacion(cliente) -> None:
    token = _login_admin(cliente)
    codigo = f"DISTPUB-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento distancias", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    cliente.post(
        f"/eventos/{evento_id}/distancias",
        json={"nombre": "10K"},
        headers={"Authorization": f"Bearer {token}"},
    )

    respuesta = cliente.get(f"/eventos/{evento_id}/distancias")
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["nombre"] == "10K"


def test_crear_distancia_sigue_requiriendo_admin(cliente) -> None:
    respuesta = cliente.post("/eventos/1/distancias", json={"nombre": "10K"})
    assert respuesta.status_code == 401
