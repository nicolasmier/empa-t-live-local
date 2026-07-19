import uuid

from app.models import Corredor, Distancia, Inscripcion
from app.security.passwords import hash_password
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento_publicado(cliente, db_session, token: str) -> tuple[int, str]:
    codigo = f"UNIRSE-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento unirse", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    cliente.post(
        f"/eventos/{evento_id}/estado",
        json={"estado": "publicado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return evento_id, codigo


def _crear_corredor_inscrito(db_session, evento_id: int, password: str = "clave12345") -> str:
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.flush()

    email = f"runner-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(
        nombre="Runner",
        apellidos="Test",
        email=email,
        password_hash=hash_password(password),
    )
    db_session.add(corredor)
    db_session.flush()

    db_session.add(Inscripcion(corredor_id=corredor.id, distancia_id=distancia.id, dorsal="42"))
    db_session.commit()
    return email


def _login_corredor(cliente, email: str, password: str = "clave12345") -> str:
    respuesta = cliente.post("/auth/corredores/login", json={"email": email, "password": password})
    assert respuesta.status_code == 200
    return respuesta.json()["access_token"]


def test_unirse_devuelve_distancia_dorsal_y_token(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, codigo = _crear_evento_publicado(cliente, db_session, admin_token)
    email = _crear_corredor_inscrito(db_session, evento_id)
    token_corredor = _login_corredor(cliente, email)

    respuesta = cliente.post(
        f"/eventos/codigo/{codigo}/unirse",
        json={"dorsal": "42"},
        headers={"Authorization": f"Bearer {token_corredor}"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["evento_id"] == evento_id
    assert isinstance(cuerpo["inscripcion_id"], int)
    assert cuerpo["dorsal"] == "42"
    assert cuerpo["distancia_nombre"] == "10K"
    assert cuerpo["evento_estado"] == "publicado"
    assert len(cuerpo["token_dispositivo"]) > 20


def test_unirse_dos_veces_revoca_token_anterior(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, codigo = _crear_evento_publicado(cliente, db_session, admin_token)
    email = _crear_corredor_inscrito(db_session, evento_id)
    token_corredor = _login_corredor(cliente, email)
    cabeceras = {"Authorization": f"Bearer {token_corredor}"}

    primera = cliente.post(
        f"/eventos/codigo/{codigo}/unirse", json={"dorsal": "42"}, headers=cabeceras
    )
    segunda = cliente.post(
        f"/eventos/codigo/{codigo}/unirse", json={"dorsal": "42"}, headers=cabeceras
    )
    assert primera.json()["token_dispositivo"] != segunda.json()["token_dispositivo"]

    from app.models import TokenDispositivo

    inscripcion = db_session.query(Inscripcion).filter_by(dorsal="42").one()
    tokens = (
        db_session.query(TokenDispositivo).filter_by(inscripcion_id=inscripcion.id).all()
    )
    assert len(tokens) == 2
    activos = [t for t in tokens if t.revocado_en is None]
    assert len(activos) == 1


def test_unirse_evento_en_borrador_devuelve_409(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    codigo = f"BORRADOR-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento borrador", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    evento_id = creado.json()["id"]
    email = _crear_corredor_inscrito(db_session, evento_id)
    token_corredor = _login_corredor(cliente, email)

    respuesta = cliente.post(
        f"/eventos/codigo/{codigo}/unirse",
        json={"dorsal": "42"},
        headers={"Authorization": f"Bearer {token_corredor}"},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "estado_no_permite_union"


def test_unirse_sin_inscripcion_devuelve_404(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, codigo = _crear_evento_publicado(cliente, db_session, admin_token)

    email = f"sininscripcion-{uuid.uuid4().hex[:8]}@example.com"
    registro = cliente.post(
        "/auth/corredores/registro",
        json={
            "nombre": "Sin",
            "apellidos": "Inscripcion",
            "email": email,
            "password": "clave12345",
        },
    )
    token_corredor = registro.json()["access_token"]

    respuesta = cliente.post(
        f"/eventos/codigo/{codigo}/unirse",
        json={"dorsal": "999"},
        headers={"Authorization": f"Bearer {token_corredor}"},
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "sin_inscripcion"


def test_unirse_con_dorsal_incorrecto_devuelve_409(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, codigo = _crear_evento_publicado(cliente, db_session, admin_token)
    email = _crear_corredor_inscrito(db_session, evento_id)
    token_corredor = _login_corredor(cliente, email)

    respuesta = cliente.post(
        f"/eventos/codigo/{codigo}/unirse",
        json={"dorsal": "999"},
        headers={"Authorization": f"Bearer {token_corredor}"},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "dorsal_no_coincide"
