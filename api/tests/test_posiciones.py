import uuid
from datetime import UTC, datetime, timedelta

from app.models import (
    Corredor,
    Distancia,
    Inscripcion,
    PosicionActual,
    PosicionHistorico,
    TokenDispositivo,
)
from app.security.passwords import hash_password
from app.security.rate_limit import limitador_ingesta, limitador_login
from app.security.tokens import generar_token_dispositivo, hash_token_dispositivo


def _login_admin(cliente) -> str:
    limitador_login.registrar_exito("panel:admin@example.com")
    respuesta = cliente.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin1234"}
    )
    return respuesta.json()["access_token"]


def _crear_evento_en_directo(cliente, db_session, token: str) -> tuple[int, int]:
    codigo = f"POS-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento posiciones", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    evento_id = creado.json()["id"]
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.commit()

    for estado in ("publicado", "preparacion", "en_directo"):
        cliente.post(
            f"/eventos/{evento_id}/estado",
            json={"estado": estado},
            headers={"Authorization": f"Bearer {token}"},
        )
    return evento_id, distancia.id


def _crear_inscripcion_con_token(
    db_session, distancia_id: int, dorsal: str = "1"
) -> tuple[int, str]:
    email = f"pos-{uuid.uuid4().hex[:8]}@example.com"
    corredor = Corredor(
        nombre="Runner", apellidos="Test", email=email, password_hash=hash_password("clave12345")
    )
    db_session.add(corredor)
    db_session.flush()

    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia_id, dorsal=dorsal)
    db_session.add(inscripcion)
    db_session.flush()

    token_plano = generar_token_dispositivo()
    db_session.add(
        TokenDispositivo(
            inscripcion_id=inscripcion.id, token_hash=hash_token_dispositivo(token_plano)
        )
    )
    db_session.commit()
    return inscripcion.id, token_plano


def _punto(minutos_atras: float = 0, **overrides) -> dict:
    ts = datetime.now(UTC) - timedelta(minutes=minutos_atras)
    base = {
        "timestamp_dispositivo": ts.isoformat(),
        "latitud": 40.0,
        "longitud": -3.5,
        "precision_m": 5.0,
        "velocidad_kmh": 12.0,
        "bateria_pct": 80,
    }
    base.update(overrides)
    return base


def test_ingesta_basica_devuelve_202_y_actualiza_posicion_actual(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 202
    assert respuesta.json()["procesados"] == 1

    actual = db_session.get(PosicionActual, inscripcion_id)
    assert actual is not None
    assert float(actual.latitud) == 40.0

    historico = db_session.query(PosicionHistorico).filter_by(inscripcion_id=inscripcion_id).all()
    assert len(historico) == 1
    assert historico[0].origen == "directo"
    assert historico[0].sospechoso is False


def test_ingesta_fuera_de_en_directo_devuelve_409(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    codigo = f"BORRADOR-{uuid.uuid4().hex[:6]}"
    creado = cliente.post(
        "/eventos",
        json={"nombre": "Evento borrador", "codigo_acceso": codigo, "fecha": "2026-09-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    evento_id = creado.json()["id"]
    distancia = Distancia(evento_id=evento_id, nombre="10K")
    db_session.add(distancia)
    db_session.commit()
    _, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia.id)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "evento_no_en_directo"


def test_ingesta_con_evento_distinto_al_del_token_devuelve_403(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    _, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    otro_evento_id = evento_id + 999999
    respuesta = cliente.post(
        f"/eventos/{otro_evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "evento_no_corresponde"


def test_lote_mayor_de_500_puntos_devuelve_413(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    _, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    lote = [_punto(minutos_atras=i / 60) for i in range(501)]
    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=lote,
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 413
    assert respuesta.json()["error"]["code"] == "lote_demasiado_grande"


def test_rate_limit_1_peticion_cada_5_segundos(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)
    limitador_ingesta._ultima.pop(f"dispositivo:{inscripcion_id}", None)

    cabeceras = {"Authorization": f"Bearer {token_dispositivo}"}
    primera = cliente.post(f"/eventos/{evento_id}/posiciones", json=[_punto()], headers=cabeceras)
    assert primera.status_code == 202

    segunda = cliente.post(f"/eventos/{evento_id}/posiciones", json=[_punto()], headers=cabeceras)
    assert segunda.status_code == 429
    assert segunda.json()["error"]["code"] == "demasiadas_peticiones"


def test_lote_desordenado_no_retrocede_posicion_actual(cliente, db_session) -> None:
    """EA-007: dentro de un mismo lote, solo el punto más reciente actualiza la posición actual."""
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    lote_desordenado = [
        _punto(minutos_atras=5, latitud=10.0),
        _punto(minutos_atras=1, latitud=30.0),  # el más reciente del lote
        _punto(minutos_atras=8, latitud=5.0),
    ]
    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=lote_desordenado,
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 202
    assert respuesta.json()["procesados"] == 3

    actual = db_session.get(PosicionActual, inscripcion_id)
    assert float(actual.latitud) == 30.0

    historico = db_session.query(PosicionHistorico).filter_by(inscripcion_id=inscripcion_id).all()
    assert len(historico) == 3


def test_lote_sincronizado_completo_en_historico_solo_ultimo_en_actual(cliente, db_session) -> None:
    """EA-005: tras recuperar conexión, el lote entero va al histórico y solo el
    punto más reciente actualiza posiciones_actuales."""
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)
    cabeceras = {"Authorization": f"Bearer {token_dispositivo}"}

    primer_envio = cliente.post(
        f"/eventos/{evento_id}/posiciones", json=[_punto(minutos_atras=20)], headers=cabeceras
    )
    assert primer_envio.status_code == 202

    limitador_ingesta._ultima.pop(f"dispositivo:{inscripcion_id}", None)

    lote_sincronizado = [_punto(minutos_atras=m) for m in (15, 12, 9, 6, 3)]
    segundo_envio = cliente.post(
        f"/eventos/{evento_id}/posiciones", json=lote_sincronizado, headers=cabeceras
    )
    assert segundo_envio.status_code == 202
    assert segundo_envio.json()["procesados"] == 5

    historico = db_session.query(PosicionHistorico).filter_by(inscripcion_id=inscripcion_id).all()
    assert len(historico) == 6  # 1 del primer envío + 5 del lote sincronizado
    assert all(p.origen == "sincronizado" for p in historico)

    actual = db_session.get(PosicionActual, inscripcion_id)
    # El punto más reciente del lote sincronizado es el de "3 minutos atrás".
    esperado = datetime.fromisoformat(lote_sincronizado[-1]["timestamp_dispositivo"])
    assert actual.timestamp_dispositivo == esperado


def test_punto_con_desviacion_excesiva_se_marca_sospechoso(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto(minutos_atras=15)],  # 900s > 600s umbral sospechoso
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 202

    historico = db_session.query(PosicionHistorico).filter_by(inscripcion_id=inscripcion_id).one()
    assert historico.sospechoso is True
    assert historico.origen == "sincronizado"


def test_punto_en_el_futuro_lejano_se_marca_sospechoso(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto(minutos_atras=-5)],  # 5 min en el futuro > 120s margen
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 202

    historico = db_session.query(PosicionHistorico).filter_by(inscripcion_id=inscripcion_id).one()
    assert historico.sospechoso is True


def test_token_dispositivo_revocado_no_autentica(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    fila = (
        db_session.query(TokenDispositivo).filter_by(inscripcion_id=inscripcion_id).one()
    )
    fila.revocado_en = datetime.now(UTC)
    db_session.commit()

    respuesta = cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "token_invalido"


def test_lectura_publica_no_requiere_autenticacion(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(
        db_session, distancia_id, dorsal="7"
    )

    cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )

    respuesta = cliente.get(f"/eventos/{evento_id}/distancias/{distancia_id}/posiciones")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["dorsal"] == "7"
    assert cuerpo[0]["estado"] == "transmitiendo"


def test_sin_senal_genera_incidencia_y_se_resuelve_al_recuperar(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    # umbral_sin_senal_seg por defecto = 180s; simulamos una última posición muy antigua.
    ahora = datetime.now(UTC)
    db_session.add(
        PosicionActual(
            inscripcion_id=inscripcion_id,
            timestamp_dispositivo=ahora - timedelta(seconds=600),
            timestamp_recepcion=ahora - timedelta(seconds=600),
            latitud=40.0,
            longitud=-3.5,
        )
    )
    db_session.commit()

    respuesta = cliente.get(f"/eventos/{evento_id}/distancias/{distancia_id}/posiciones")
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["estado"] == "sin_senal"

    from app.models import Incidencia

    incidencia = (
        db_session.query(Incidencia)
        .filter_by(inscripcion_id=inscripcion_id, tipo="sin_senal")
        .one()
    )
    assert incidencia.resuelto_en is None

    limitador_ingesta._ultima.pop(f"dispositivo:{inscripcion_id}", None)
    cliente.post(
        f"/eventos/{evento_id}/posiciones",
        json=[_punto()],
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )

    db_session.refresh(incidencia)
    assert incidencia.resuelto_en is not None


def test_estado_inscripcion_requiere_token_propio(cliente, db_session) -> None:
    admin_token = _login_admin(cliente)
    evento_id, distancia_id = _crear_evento_en_directo(cliente, db_session, admin_token)
    inscripcion_id, token_dispositivo = _crear_inscripcion_con_token(db_session, distancia_id)

    respuesta = cliente.get(
        f"/inscripciones/{inscripcion_id}/estado",
        headers={"Authorization": f"Bearer {token_dispositivo}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado_evento"] == "en_directo"

    otra_id, otro_token = _crear_inscripcion_con_token(db_session, distancia_id, dorsal="99")
    cruzada = cliente.get(
        f"/inscripciones/{inscripcion_id}/estado",
        headers={"Authorization": f"Bearer {otro_token}"},
    )
    assert cruzada.status_code == 403
