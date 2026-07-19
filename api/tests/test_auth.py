import uuid

from app.security.rate_limit import limitador_login


def _email_unico(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8]}@example.com"


def test_registro_y_login_corredor(cliente) -> None:
    email = _email_unico("corredor")
    respuesta = cliente.post(
        "/auth/corredores/registro",
        json={"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"},
    )
    assert respuesta.status_code == 201
    assert "access_token" in respuesta.json()

    respuesta = cliente.post(
        "/auth/corredores/login", json={"email": email, "password": "clave12345"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["token_type"] == "bearer"


def test_registro_corredor_email_duplicado(cliente) -> None:
    email = _email_unico("corredor")
    datos = {"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"}
    cliente.post("/auth/corredores/registro", json=datos)

    respuesta = cliente.post("/auth/corredores/registro", json=datos)
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "email_duplicado"


def test_login_corredor_password_incorrecta(cliente) -> None:
    email = _email_unico("corredor")
    cliente.post(
        "/auth/corredores/registro",
        json={"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"},
    )
    limitador_login.registrar_exito(f"corredor:{email.lower()}")

    respuesta = cliente.post(
        "/auth/corredores/login", json={"email": email, "password": "incorrecta"}
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "credenciales_invalidas"


def test_bloqueo_tras_cinco_intentos_fallidos(cliente) -> None:
    email = _email_unico("corredor")
    cliente.post(
        "/auth/corredores/registro",
        json={"nombre": "Ana", "apellidos": "Gómez", "email": email, "password": "clave12345"},
    )
    clave = f"corredor:{email.lower()}"
    limitador_login.registrar_exito(clave)

    for _ in range(5):
        cliente.post("/auth/corredores/login", json={"email": email, "password": "mala"})

    respuesta = cliente.post(
        "/auth/corredores/login", json={"email": email, "password": "clave12345"}
    )
    assert respuesta.status_code == 429
    assert respuesta.json()["error"]["code"] == "demasiados_intentos"
    limitador_login.registrar_exito(clave)


def test_login_panel_admin_seed(cliente) -> None:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    assert respuesta.status_code == 200
    assert "access_token" in respuesta.json()


def test_login_panel_credenciales_invalidas(cliente) -> None:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401
    limitador_login.registrar_exito("panel:admin@example.com")


def test_registro_activa_cuenta_pre_importada_solo_con_telefono(cliente, db_session) -> None:
    from app.models import Corredor

    telefono = f"6{uuid.uuid4().int % 10**8:08d}"
    pre_importado = Corredor(nombre="Excel", apellidos="Excel", telefono=telefono)
    db_session.add(pre_importado)
    db_session.commit()

    email = _email_unico("activa")
    respuesta = cliente.post(
        "/auth/corredores/registro",
        json={
            "nombre": "Nombre real",
            "apellidos": "Apellido real",
            "email": email,
            "password": "clave12345",
            "telefono": telefono,
        },
    )
    assert respuesta.status_code == 201

    db_session.refresh(pre_importado)
    assert pre_importado.email == email
    assert pre_importado.password_hash is not None
    # RF-002: el registro no pisa nombre/apellidos ya cargados por el organizador.
    assert pre_importado.nombre == "Excel"


def test_registro_corredor_telefono_duplicado(cliente, db_session) -> None:
    from app.models import Corredor

    telefono = f"6{uuid.uuid4().int % 10**8:08d}"
    ya_activado = Corredor(
        nombre="Ya",
        apellidos="Activado",
        email=_email_unico("yaactivo"),
        telefono=telefono,
        password_hash="x",
    )
    db_session.add(ya_activado)
    db_session.commit()

    respuesta = cliente.post(
        "/auth/corredores/registro",
        json={
            "nombre": "Otro",
            "apellidos": "Corredor",
            "email": _email_unico("otro"),
            "password": "clave12345",
            "telefono": telefono,
        },
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "telefono_duplicado"
