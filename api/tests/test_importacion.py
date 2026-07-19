import io
import uuid

from openpyxl import Workbook

from app.models import Distancia, Evento
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento_con_distancia(cliente, db_session, token: str) -> int:
    codigo = f"IMP-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento import", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.commit()
    return distancia.id


def _excel_bytes(filas: list[tuple]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.append(["email", "nombre", "apellidos", "dorsal", "club"])
    for fila in filas:
        hoja.append(list(fila))
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def _excel_bytes_con_columnas(columnas: list[str], filas: list[tuple]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.append(columnas)
    for fila in filas:
        hoja.append(list(fila))
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def test_importacion_crea_corredores_e_inscripciones(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    sufijo = uuid.uuid4().hex[:8]
    filas = [
        (f"a-{sufijo}@example.com", "Ana", "Gómez", 101, "Club A"),
        (f"b-{sufijo}@example.com", "Bea", "López", 102, None),
    ]
    archivo = _excel_bytes(filas)

    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={
            "archivo": (
                "corredores.xlsx",
                archivo,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["creados"] == 2
    assert cuerpo["errores"] == 0
    assert all(f["estado"] == "creado" for f in cuerpo["filas"])


def test_reimportar_mismo_excel_es_idempotente(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    sufijo = uuid.uuid4().hex[:8]
    archivo = _excel_bytes([(f"c-{sufijo}@example.com", "Carla", "Ruiz", 201, None)])

    primer = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("c.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert primer.json()["creados"] == 1

    segundo = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("c.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    cuerpo = segundo.json()
    assert cuerpo["creados"] == 0
    assert cuerpo["sin_cambios"] == 1
    assert cuerpo["errores"] == 0


def test_dorsal_duplicado_en_el_mismo_excel_se_reporta_como_error(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    sufijo = uuid.uuid4().hex[:8]
    archivo = _excel_bytes(
        [
            (f"d1-{sufijo}@example.com", "Uno", "Test", 301, None),
            (f"d2-{sufijo}@example.com", "Dos", "Test", 301, None),
        ]
    )

    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("d.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    cuerpo = respuesta.json()
    assert cuerpo["creados"] == 1
    assert cuerpo["errores"] == 1
    filas_error = [f for f in cuerpo["filas"] if f["estado"] == "error"]
    assert len(filas_error) == 1
    assert "dorsal" in filas_error[0]["motivo"].lower()


def test_importacion_con_fila_incompleta_se_reporta_como_error(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    archivo = _excel_bytes([("sin-dorsal@example.com", "Sin", "Dorsal", None, None)])
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("e.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    cuerpo = respuesta.json()
    assert cuerpo["errores"] == 1
    assert cuerpo["creados"] == 0


def test_importacion_vincula_corredor_existente_sin_modificar_perfil(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)
    evento_id = db_session.get(Distancia, distancia_id).evento_id
    assert db_session.get(Evento, evento_id) is not None

    email = f"existente-{uuid.uuid4().hex[:8]}@example.com"
    registro = cliente.post(
        "/auth/corredores/registro",
        json={
            "nombre": "Nombre original",
            "apellidos": "Apellido original",
            "email": email,
            "password": "clave12345",
        },
    )
    assert registro.status_code == 201

    archivo = _excel_bytes([(email, "Nombre del excel", "Apellido del excel", 401, None)])
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("f.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.json()["creados"] == 1

    from app.models import Corredor

    corredor = db_session.query(Corredor).filter_by(email=email).one()
    assert corredor.nombre == "Nombre original"


def test_importacion_solo_con_telefono_crea_cuenta_pre_importada(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    telefono = f"6{uuid.uuid4().int % 10**8:08d}"
    archivo = _excel_bytes_con_columnas(
        ["telefono", "nombre", "apellidos", "dorsal", "club"],
        [(telefono, "Solo", "Telefono", 501, None)],
    )
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("g.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    cuerpo = respuesta.json()
    assert cuerpo["creados"] == 1
    assert cuerpo["errores"] == 0

    from app.models import Corredor

    corredor = db_session.query(Corredor).filter_by(telefono=telefono).one()
    assert corredor.email is None
    assert corredor.password_hash is None


def test_importacion_sin_columna_email_ni_telefono_da_error_de_columnas(
    cliente, db_session
) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    archivo = _excel_bytes_con_columnas(
        ["nombre", "apellidos", "dorsal"], [("Sin", "Identidad", 601)]
    )
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("h.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "columnas_faltantes"


def test_importacion_matching_por_telefono_cuando_email_no_coincide(
    cliente, db_session
) -> None:
    """Fila con email distinto al ya registrado pero mismo teléfono: se enlaza
    con la cuenta existente en vez de crear un corredor duplicado (decisión
    2026-07-19: email/teléfono alternativos para el matching)."""
    token = _login_admin(cliente)
    distancia_id = _crear_evento_con_distancia(cliente, db_session, token)

    from app.models import Corredor

    telefono = f"6{uuid.uuid4().int % 10**8:08d}"
    email_original = f"orig-{uuid.uuid4().hex[:8]}@example.com"
    corredor_previo = Corredor(
        nombre="Previo", apellidos="Previo", email=email_original, telefono=telefono
    )
    db_session.add(corredor_previo)
    db_session.commit()

    email_nuevo_en_excel = f"distinto-{uuid.uuid4().hex[:8]}@example.com"
    archivo = _excel_bytes_con_columnas(
        ["email", "telefono", "nombre", "apellidos", "dorsal"],
        [(email_nuevo_en_excel, telefono, "Previo", "Previo", 701)],
    )
    respuesta = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("i.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.json()["errores"] == 0
    assert respuesta.json()["creados"] == 1

    corredores_con_telefono = (
        db_session.query(Corredor).filter_by(telefono=telefono).all()
    )
    assert len(corredores_con_telefono) == 1  # no se duplicó
    inscripciones = corredores_con_telefono[0].inscripciones
    assert len(inscripciones) == 1
    assert inscripciones[0].dorsal == "701"
