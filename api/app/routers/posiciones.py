from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dominio.estado_transmision import calcular_estado_transmision
from app.errores import ErrorAPI
from app.models import Distancia, Inscripcion, PosicionActual, PosicionHistorico
from app.schemas.posiciones import (
    IngestaSalida,
    InscripcionEstadoSalida,
    PosicionPublica,
    PuntoPosicionEntrada,
)
from app.security.dependencies import obtener_inscripcion_por_token_dispositivo
from app.security.rate_limit import limitador_ingesta
from app.servicios.incidencias import resolver_si_recupera_senal, sincronizar_incidencias_sin_senal

router = APIRouter(tags=["posiciones"])

# Reglas de ingesta (decisión clarify 2026-07-16, spec v10 Anexo B §5).
MAX_PUNTOS_POR_LOTE = 500
UMBRAL_DIRECTO_SEG = 10
UMBRAL_SOSPECHOSO_SEG = 600
MARGEN_FUTURO_SEG = 120


def _con_zona_horaria(ts: datetime) -> datetime:
    return ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)


@router.post("/eventos/{evento_id}/posiciones", response_model=IngestaSalida, status_code=202)
def ingerir_posiciones(
    evento_id: int,
    puntos: list[PuntoPosicionEntrada],
    db: Session = Depends(get_db),
    inscripcion: Inscripcion = Depends(obtener_inscripcion_por_token_dispositivo),
) -> IngestaSalida:
    # La identidad del token manda sobre la URL (anti-suplantación): se comprueba
    # antes que cualquier otra cosa, incluido el rate limit.
    if inscripcion.distancia.evento_id != evento_id:
        raise ErrorAPI(
            403, "evento_no_corresponde", "El token de dispositivo no pertenece a este evento."
        )

    if not limitador_ingesta.permitir(f"dispositivo:{inscripcion.id}"):
        raise ErrorAPI(
            429, "demasiadas_peticiones", "Máximo una petición cada 5 s por dispositivo."
        )

    evento = inscripcion.distancia.evento
    if evento.estado != "en_directo":
        raise ErrorAPI(409, "evento_no_en_directo", "El evento no está En directo.")

    if len(puntos) > MAX_PUNTOS_POR_LOTE:
        raise ErrorAPI(
            413,
            "lote_demasiado_grande",
            f"Máximo {MAX_PUNTOS_POR_LOTE} puntos por petición; divide el envío.",
        )

    if not puntos:
        return IngestaSalida(procesados=0)

    ahora = datetime.now(UTC)
    punto_mas_reciente: PuntoPosicionEntrada | None = None
    timestamp_mas_reciente: datetime | None = None

    for punto in puntos:
        ts_dispositivo = _con_zona_horaria(punto.timestamp_dispositivo)
        desviacion_seg = (ahora - ts_dispositivo).total_seconds()
        origen = "directo" if desviacion_seg <= UMBRAL_DIRECTO_SEG else "sincronizado"
        sospechoso = abs(desviacion_seg) > UMBRAL_SOSPECHOSO_SEG or (
            -desviacion_seg > MARGEN_FUTURO_SEG
        )

        db.add(
            PosicionHistorico(
                inscripcion_id=inscripcion.id,
                timestamp_dispositivo=ts_dispositivo,
                timestamp_recepcion=ahora,
                latitud=punto.latitud,
                longitud=punto.longitud,
                precision_m=punto.precision_m,
                velocidad_kmh=punto.velocidad_kmh,
                bateria_pct=punto.bateria_pct,
                origen=origen,
                sospechoso=sospechoso,
            )
        )

        if timestamp_mas_reciente is None or ts_dispositivo > timestamp_mas_reciente:
            timestamp_mas_reciente = ts_dispositivo
            punto_mas_reciente = punto

    # UPSERT condicionado: solo si el punto más reciente del lote es posterior al
    # almacenado (EA-007: un lote desordenado nunca retrocede la posición actual).
    actual = db.get(PosicionActual, inscripcion.id)
    if punto_mas_reciente is not None and timestamp_mas_reciente is not None:
        debe_actualizar = actual is None or timestamp_mas_reciente > actual.timestamp_dispositivo
        if debe_actualizar:
            if actual is None:
                actual = PosicionActual(inscripcion_id=inscripcion.id)
                db.add(actual)
            actual.timestamp_dispositivo = timestamp_mas_reciente
            actual.timestamp_recepcion = ahora
            actual.latitud = punto_mas_reciente.latitud
            actual.longitud = punto_mas_reciente.longitud
            actual.precision_m = punto_mas_reciente.precision_m
            actual.velocidad_kmh = punto_mas_reciente.velocidad_kmh
            actual.bateria_pct = punto_mas_reciente.bateria_pct

    resolver_si_recupera_senal(db, inscripcion.id)

    db.commit()
    return IngestaSalida(procesados=len(puntos))


@router.get(
    "/eventos/{evento_id}/distancias/{distancia_id}/posiciones",
    response_model=list[PosicionPublica],
)
def listar_posiciones_publicas(
    evento_id: int, distancia_id: int, db: Session = Depends(get_db)
) -> list[PosicionPublica]:
    """Lectura pública LAN (Anexo B §6): sin autenticación, sondeada cada 3-5 s."""
    distancia = db.get(Distancia, distancia_id)
    if distancia is None or distancia.evento_id != evento_id:
        raise ErrorAPI(404, "no_encontrado", "Distancia no encontrada para este evento.")
    evento = distancia.evento

    # Sin carga adiestrada, `.posicion_actual`/`.corredor` en el bucle de abajo
    # dispararían 2 consultas por inscripción (N+1): a 800 corredores eso son
    # ~1600 queries extra por sondeo y, bajo la escritura concurrente de una
    # carrera real, deja el endpoint (sondeado cada 3-5 s) en varios segundos
    # de latencia — hallado en el ensayo general a escala con el simulador.
    inscripciones = (
        db.query(Inscripcion)
        .filter(Inscripcion.distancia_id == distancia_id)
        .options(selectinload(Inscripcion.posicion_actual), selectinload(Inscripcion.corredor))
        .all()
    )

    sincronizar_incidencias_sin_senal(db, evento_id, inscripciones, evento.umbral_sin_senal_seg)
    db.commit()

    resultado = []
    for inscripcion in inscripciones:
        actual = inscripcion.posicion_actual
        corredor = inscripcion.corredor
        estado = calcular_estado_transmision(
            actual.timestamp_dispositivo if actual else None, evento.umbral_sin_senal_seg
        )
        resultado.append(
            PosicionPublica(
                inscripcion_id=inscripcion.id,
                dorsal=inscripcion.dorsal,
                nombre=corredor.nombre,
                apellidos=corredor.apellidos,
                club=corredor.club,
                foto_url=corredor.foto_url,
                latitud=float(actual.latitud) if actual else None,
                longitud=float(actual.longitud) if actual else None,
                timestamp_dispositivo=actual.timestamp_dispositivo if actual else None,
                estado=estado,
            )
        )
    return resultado


@router.get("/inscripciones/{inscripcion_id}/estado", response_model=InscripcionEstadoSalida)
def obtener_estado_inscripcion(
    inscripcion_id: int,
    db: Session = Depends(get_db),
    inscripcion_token: Inscripcion = Depends(obtener_inscripcion_por_token_dispositivo),
) -> InscripcionEstadoSalida:
    if inscripcion_token.id != inscripcion_id:
        raise ErrorAPI(403, "prohibido", "El token no corresponde a esta inscripción.")

    inscripcion = inscripcion_token
    evento = inscripcion.distancia.evento
    actual = inscripcion.posicion_actual

    sincronizar_incidencias_sin_senal(db, evento.id, [inscripcion], evento.umbral_sin_senal_seg)
    db.commit()

    estado_transmision = calcular_estado_transmision(
        actual.timestamp_dispositivo if actual else None, evento.umbral_sin_senal_seg
    )

    return InscripcionEstadoSalida(
        dorsal=inscripcion.dorsal,
        distancia_nombre=inscripcion.distancia.nombre,
        estado_transmision=estado_transmision,
        latitud=float(actual.latitud) if actual else None,
        longitud=float(actual.longitud) if actual else None,
        timestamp_dispositivo=actual.timestamp_dispositivo if actual else None,
        timestamp_recepcion=actual.timestamp_recepcion if actual else None,
        bateria_pct=actual.bateria_pct if actual else None,
        estado_evento=evento.estado,
    )
