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


def _crear_evento_y_distancia(cliente, db_session, token: str) -> tuple[int, int]:
    codigo = f"ADM-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento admin corredores", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.commit()
    return evento_id, distancia.id


def _crear_inscripcion(db_session, distancia_id: int, dorsal: str = "1") -> int:
    email = f"corr-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(
        nombre="Runner", apellidos="Test", email=email, password_hash=hash_password("clave12345")
    )
    db_session.add(corredor)
    db_session.flush()
    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia_id, dorsal=dorsal)
    db_session.add(inscripcion)
    db_session.commit()
    return inscripcion.id


def test_admin_edita_dorsal_y_datos_del_corredor(cliente, db_session) -> None:
    token = _login_admin(cliente)
    _, distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    inscripcion_id = _crear_inscripcion(db_session, distancia_id, dorsal="7")

    respuesta = cliente.put(
        f"/distancias/{distancia_id}/corredores/{inscripcion_id}",
        json={"dorsal": "99", "nombre": "Nuevo", "club": "Club X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["dorsal"] == "99"
    assert cuerpo["nombre"] == "Nuevo"
    assert cuerpo["club"] == "Club X"


def test_admin_no_puede_asignar_dorsal_duplicado(cliente, db_session) -> None:
    token = _login_admin(cliente)
    _, distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    _crear_inscripcion(db_session, distancia_id, dorsal="1")
    inscripcion_id_2 = _crear_inscripcion(db_session, distancia_id, dorsal="2")

    respuesta = cliente.put(
        f"/distancias/{distancia_id}/corredores/{inscripcion_id_2}",
        json={"dorsal": "1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "dorsal_duplicado"


def test_admin_elimina_un_corredor(cliente, db_session) -> None:
    token = _login_admin(cliente)
    _, distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    inscripcion_id = _crear_inscripcion(db_session, distancia_id)

    respuesta = cliente.delete(
        f"/distancias/{distancia_id}/corredores/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 204
    assert db_session.get(Inscripcion, inscripcion_id) is None


def test_admin_elimina_corredores_en_bloque(cliente, db_session) -> None:
    token = _login_admin(cliente)
    _, distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    id1 = _crear_inscripcion(db_session, distancia_id, dorsal="1")
    id2 = _crear_inscripcion(db_session, distancia_id, dorsal="2")
    _crear_inscripcion(db_session, distancia_id, dorsal="3")

    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/eliminar",
        json={"inscripcion_ids": [id1, id2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["eliminadas"] == 2
    assert db_session.query(Inscripcion).filter_by(distancia_id=distancia_id).count() == 1


def test_editar_corredor_de_otra_distancia_devuelve_404(cliente, db_session) -> None:
    token = _login_admin(cliente)
    _, distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    _, otra_distancia_id = _crear_evento_y_distancia(cliente, db_session, token)
    inscripcion_id = _crear_inscripcion(db_session, distancia_id)

    respuesta = cliente.put(
        f"/distancias/{otra_distancia_id}/corredores/{inscripcion_id}",
        json={"dorsal": "50"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 404
