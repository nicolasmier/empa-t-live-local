import uuid

from app.models import Corredor
from app.security.rate_limit import limitador_login


def test_login_en_cuenta_preimportada_sin_password_es_rechazado(cliente, db_session) -> None:
    email = f"preimportado-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(nombre="Pre", apellidos="Importado", email=email, password_hash=None)
    db_session.add(corredor)
    db_session.commit()

    limitador_login.registrar_exito(f"corredor:{email.lower()}")
    respuesta = cliente.post(
        "/auth/corredores/login", json={"email": email, "password": "cualquiera"}
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "cuenta_no_activada"


def test_registro_activa_cuenta_preimportada_sin_tocar_perfil(cliente, db_session) -> None:
    email = f"activar-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(
        nombre="Nombre del Excel", apellidos="Apellido del Excel", email=email, password_hash=None
    )
    db_session.add(corredor)
    db_session.commit()
    corredor_id = corredor.id

    respuesta = cliente.post(
        "/auth/corredores/registro",
        json={
            "nombre": "Nombre distinto tecleado en la app",
            "apellidos": "Apellido distinto",
            "email": email,
            "password": "clave12345",
        },
    )
    assert respuesta.status_code == 201
    assert "access_token" in respuesta.json()

    db_session.refresh(corredor)
    assert corredor.password_hash is not None
    assert corredor.nombre == "Nombre del Excel"
    assert corredor.id == corredor_id

    login = cliente.post("/auth/corredores/login", json={"email": email, "password": "clave12345"})
    assert login.status_code == 200


def test_registro_sobre_cuenta_ya_activa_devuelve_409(cliente) -> None:
    email = f"activa-{uuid.uuid4().hex[:8]}@example.com"
    datos = {"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"}
    cliente.post("/auth/corredores/registro", json=datos)

    respuesta = cliente.post("/auth/corredores/registro", json=datos)
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "email_duplicado"
