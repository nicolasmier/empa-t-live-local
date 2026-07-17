import uuid

from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def test_evento_activo_no_requiere_autenticacion(cliente) -> None:
    respuesta = cliente.get("/eventos/activo")
    # 200 (hay un evento publicado en la BD de dev) o 404 (ninguno) — en
    # cualquier caso, nunca 401/403: la ausencia de token no puede bloquearlo.
    assert respuesta.status_code in (200, 404)


def test_evento_activo_devuelve_el_mas_reciente_no_borrador_ni_archivado(cliente) -> None:
    token = _login_admin(cliente)
    codigo = f"ACTIVO-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento activo", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    # Recién creado está en Borrador: todavía no debe salir como "activo".
    respuesta = cliente.get("/eventos/activo")
    if respuesta.status_code == 200:
        assert respuesta.json()["id"] != evento_id

    cliente.post(
        f"/eventos/{evento_id}/estado",
        json={"estado": "publicado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    respuesta = cliente.get("/eventos/activo")
    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == evento_id
    assert respuesta.json()["codigo_acceso"] == codigo


def test_evento_activo_ignora_los_archivados(cliente) -> None:
    token = _login_admin(cliente)
    codigo = f"ARCHIVAR-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento a archivar", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    for estado in ("publicado", "archivado"):
        cliente.post(
            f"/eventos/{evento_id}/estado",
            json={"estado": estado},
            headers={"Authorization": f"Bearer {token}"},
        )

    respuesta = cliente.get("/eventos/activo")
    if respuesta.status_code == 200:
        assert respuesta.json()["id"] != evento_id
