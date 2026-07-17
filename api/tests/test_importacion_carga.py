import io
import uuid

from openpyxl import Workbook

from app.models import Distancia
from app.security.rate_limit import limitador_login


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_distancia(cliente, db_session, token: str) -> int:
    codigo = f"MASIVO-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento masivo", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    distancia = Distancia(evento_id=creado.json()["id"], nombre="10K")
    db_session.add(distancia)
    db_session.commit()
    return distancia.id


def _generar_800_filas_con_errores(sufijo: str) -> tuple[bytes, int]:
    """800 filas: la mayoría válidas, con 3 errores a propósito (EA-011, plan S3)."""
    filas = []
    for i in range(1, 801):
        filas.append(
            [f"masivo{i:04d}-{sufijo}@example.com", f"Nombre{i}", "Apellido", 5000 + i, None]
        )

    # 1) dorsal duplicado dentro del mismo Excel (fila 20 repite el dorsal de la fila 10).
    filas[19][3] = filas[9][3]
    # 2) fila sin dorsal.
    filas[50][3] = None
    # 3) fila sin email.
    filas[100][0] = None

    libro = Workbook()
    hoja = libro.active
    hoja.append(["email", "nombre", "apellidos", "dorsal", "club"])
    for fila in filas:
        hoja.append(fila)
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue(), 3  # 3 filas con error a propósito


def test_importacion_800_filas_con_errores_y_reimportacion_idempotente(cliente, db_session) -> None:
    token = _login_admin(cliente)
    distancia_id = _crear_distancia(cliente, db_session, token)
    sufijo = uuid.uuid4().hex[:8]
    archivo, errores_esperados = _generar_800_filas_con_errores(sufijo)

    primera = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("masivo.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert primera.status_code == 201
    cuerpo = primera.json()
    assert cuerpo["total_filas"] == 800
    assert cuerpo["errores"] == errores_esperados
    assert cuerpo["creados"] == 800 - errores_esperados
    assert cuerpo["actualizados"] == 0
    assert cuerpo["sin_cambios"] == 0

    segunda = cliente.post(
        f"/distancias/{distancia_id}/corredores/importar",
        files={"archivo": ("masivo.xlsx", archivo, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    cuerpo2 = segunda.json()
    assert cuerpo2["creados"] == 0
    assert cuerpo2["sin_cambios"] == 800 - errores_esperados
    assert cuerpo2["errores"] == errores_esperados

    from app.models import Inscripcion

    total_inscripciones = (
        db_session.query(Inscripcion).filter_by(distancia_id=distancia_id).count()
    )
    assert total_inscripciones == 800 - errores_esperados
