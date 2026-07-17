import io
import uuid

from PIL import Image

from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento(cliente, token: str) -> int:
    codigo = f"CONT-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento contenido", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return creado.json()["id"]


def _png_bytes(lado: int = 100) -> bytes:
    imagen = Image.new("RGB", (lado, lado), color="red")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


def test_patrocinadores_crud_y_lectura_publica(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    creado = cliente.post(
        f"/eventos/{evento_id}/patrocinadores",
        json={"nombre": "Sponsor A", "orden": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert creado.status_code == 201
    patrocinador_id = creado.json()["id"]

    lectura_sin_auth = cliente.get(f"/eventos/{evento_id}/patrocinadores")
    assert lectura_sin_auth.status_code == 200
    assert len(lectura_sin_auth.json()) == 1

    actualizado = cliente.put(
        f"/patrocinadores/{patrocinador_id}",
        json={"orden": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["orden"] == 5


def test_noticias_crud_y_lectura_publica(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    creada = cliente.post(
        f"/eventos/{evento_id}/noticias",
        json={"titulo": "Bienvenida", "contenido": "Texto de la noticia."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert creada.status_code == 201

    lectura_sin_auth = cliente.get(f"/eventos/{evento_id}/noticias")
    assert lectura_sin_auth.status_code == 200
    assert lectura_sin_auth.json()[0]["titulo"] == "Bienvenida"


def test_subir_cartel_actualiza_evento(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/cartel",
        files={"archivo": ("cartel.png", _png_bytes(), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["cartel_url"] == f"/media/carteles/{evento_id}.png"

    descarga = cliente.get(respuesta.json()["cartel_url"])
    assert descarga.status_code == 200


def test_subir_cartel_formato_invalido_devuelve_400(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/cartel",
        files={"archivo": ("no-imagen.txt", b"esto no es una imagen", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "formato_invalido"


def test_eliminar_patrocinador(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    creado = cliente.post(
        f"/eventos/{evento_id}/patrocinadores", json={"nombre": "Sponsor B"}, headers=headers
    )
    patrocinador_id = creado.json()["id"]

    respuesta = cliente.delete(f"/patrocinadores/{patrocinador_id}", headers=headers)
    assert respuesta.status_code == 204
    assert cliente.get(f"/eventos/{evento_id}/patrocinadores").json() == []


def test_eliminar_noticia(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    creada = cliente.post(
        f"/eventos/{evento_id}/noticias",
        json={"titulo": "A borrar", "contenido": "..."},
        headers=headers,
    )
    noticia_id = creada.json()["id"]

    respuesta = cliente.delete(f"/noticias/{noticia_id}", headers=headers)
    assert respuesta.status_code == 204
    assert cliente.get(f"/eventos/{evento_id}/noticias").json() == []


def test_eliminar_cartel_borra_el_fichero_y_limpia_cartel_url(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    headers = {"Authorization": f"Bearer {token}"}
    subida = cliente.post(
        f"/eventos/{evento_id}/cartel",
        files={"archivo": ("cartel.png", _png_bytes(), "image/png")},
        headers=headers,
    )
    cartel_url = subida.json()["cartel_url"]
    assert cliente.get(cartel_url).status_code == 200

    respuesta = cliente.delete(f"/eventos/{evento_id}/cartel", headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.json()["cartel_url"] is None
    assert cliente.get(cartel_url).status_code == 404


def test_eliminar_cartel_sin_cartel_no_falla(cliente) -> None:
    token = _login_admin(cliente)
    evento_id = _crear_evento(cliente, token)
    respuesta = cliente.delete(
        f"/eventos/{evento_id}/cartel", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["cartel_url"] is None
