import io
import uuid

from PIL import Image


def _registrar_corredor(cliente) -> tuple[int, str]:
    email = f"perfil-{uuid.uuid4().hex[:8]}@example.com"
    respuesta = cliente.post(
        "/auth/corredores/registro",
        json={"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"},
    )
    token = respuesta.json()["access_token"]

    import jwt as pyjwt

    from app.config import settings

    payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
    return int(payload["sub"]), token


def _imagen_bytes(lado: int, formato: str = "JPEG") -> bytes:
    imagen = Image.new("RGB", (lado, lado), color="blue")
    buffer = io.BytesIO()
    imagen.save(buffer, format=formato)
    return buffer.getvalue()


def test_obtener_y_actualizar_perfil_propio(cliente) -> None:
    corredor_id, token = _registrar_corredor(cliente)
    cabeceras = {"Authorization": f"Bearer {token}"}

    perfil = cliente.get(f"/corredores/{corredor_id}", headers=cabeceras)
    assert perfil.status_code == 200
    assert perfil.json()["nombre"] == "Ana"

    actualizado = cliente.put(
        f"/corredores/{corredor_id}", json={"club": "Club Nuevo"}, headers=cabeceras
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["club"] == "Club Nuevo"


def test_no_se_puede_acceder_al_perfil_de_otro_corredor(cliente) -> None:
    _, token_a = _registrar_corredor(cliente)
    corredor_b_id, _ = _registrar_corredor(cliente)

    respuesta = cliente.get(
        f"/corredores/{corredor_b_id}", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert respuesta.status_code == 403


def test_subir_foto_redimensiona_y_actualiza_url(cliente) -> None:
    corredor_id, token = _registrar_corredor(cliente)
    cabeceras = {"Authorization": f"Bearer {token}"}

    respuesta = cliente.post(
        f"/corredores/{corredor_id}/foto",
        files={"archivo": ("foto.jpg", _imagen_bytes(1024), "image/jpeg")},
        headers=cabeceras,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["foto_url"] == f"/media/fotos/{corredor_id}.jpg"

    descarga = cliente.get(respuesta.json()["foto_url"])
    assert descarga.status_code == 200
    imagen_guardada = Image.open(io.BytesIO(descarga.content))
    assert max(imagen_guardada.size) <= 512


def test_subir_foto_demasiado_grande_devuelve_413(cliente) -> None:
    corredor_id, token = _registrar_corredor(cliente)
    contenido_enorme = b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024 + 1)

    respuesta = cliente.post(
        f"/corredores/{corredor_id}/foto",
        files={"archivo": ("foto.jpg", contenido_enorme, "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 413
    assert respuesta.json()["error"]["code"] == "imagen_demasiado_grande"


def test_subir_foto_formato_no_admitido_devuelve_400(cliente) -> None:
    corredor_id, token = _registrar_corredor(cliente)

    respuesta = cliente.post(
        f"/corredores/{corredor_id}/foto",
        files={"archivo": ("foto.gif", b"GIF89a" + b"0" * 100, "image/gif")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "formato_invalido"
