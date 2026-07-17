from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dominio.estados_evento import transicion_valida
from app.errores import ErrorAPI
from app.models import Corredor, Distancia, Evento, Inscripcion, TokenDispositivo, Usuario
from app.schemas.eventos import CambioEstadoEntrada, EventoActualizar, EventoCrear, EventoSalida
from app.schemas.unirse import UnirseSalida
from app.security.dependencies import obtener_corredor_actual, requiere_admin, requiere_panel
from app.security.tokens import generar_token_dispositivo, hash_token_dispositivo
from app.servicios.auditoria import registrar_auditoria
from app.servicios.backups import disparar_backup_en_segundo_plano, registrar_solicitud_backup
from app.servicios.tokens_dispositivo import revocar_tokens_dispositivo_evento

# Unirse a un evento está permitido en estos estados (spec v10 Anexo B §5).
_ESTADOS_PERMITEN_UNIRSE = ("publicado", "preparacion", "en_directo")

router = APIRouter(prefix="/eventos", tags=["eventos"])


def _obtener_evento_o_404(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise ErrorAPI(404, "no_encontrado", "Evento no encontrado.")
    return evento


@router.get("", response_model=list[EventoSalida])
def listar_eventos(
    db: Session = Depends(get_db), _: Usuario = Depends(requiere_panel)
) -> list[Evento]:
    return db.query(Evento).order_by(Evento.id).all()


@router.post("", response_model=EventoSalida, status_code=201)
def crear_evento(
    datos: EventoCrear, db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_admin)
) -> Evento:
    existente = db.query(Evento).filter_by(codigo_acceso=datos.codigo_acceso).one_or_none()
    if existente is not None:
        raise ErrorAPI(409, "codigo_duplicado", "Ya existe un evento con ese código de acceso.")

    evento = Evento(
        nombre=datos.nombre,
        codigo_acceso=datos.codigo_acceso,
        fecha=datos.fecha,
        creado_por=usuario.id,
    )
    db.add(evento)
    db.flush()
    registrar_auditoria(db, usuario.id, "evento_creado", "evento", str(evento.id))
    db.commit()
    db.refresh(evento)
    return evento


@router.get("/activo", response_model=EventoSalida)
def obtener_evento_activo(db: Session = Depends(get_db)) -> Evento:
    """Descubrimiento del evento a mostrar por la web pública (LAN, sin auth,
    igual criterio que las demás lecturas públicas — Anexo B §6): el más
    reciente que no esté en Borrador ni Archivado (SUP-002: un único evento
    activo por PC). Debe declararse ANTES de `/{evento_id}` para que "activo"
    no se intente interpretar como un id.
    """
    evento = (
        db.query(Evento)
        .filter(Evento.estado.notin_(["borrador", "archivado"]))
        .order_by(Evento.id.desc())
        .first()
    )
    if evento is None:
        raise ErrorAPI(404, "sin_evento_activo", "No hay ningún evento publicado actualmente.")
    return evento


@router.get("/{evento_id}", response_model=EventoSalida)
def obtener_evento(
    evento_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requiere_panel)
) -> Evento:
    return _obtener_evento_o_404(db, evento_id)


@router.put("/{evento_id}", response_model=EventoSalida)
def actualizar_evento(
    evento_id: int,
    datos: EventoActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Evento:
    evento = _obtener_evento_o_404(db, evento_id)

    if datos.codigo_acceso is not None and datos.codigo_acceso != evento.codigo_acceso:
        colision = (
            db.query(Evento)
            .filter(Evento.codigo_acceso == datos.codigo_acceso, Evento.id != evento_id)
            .one_or_none()
        )
        if colision is not None:
            raise ErrorAPI(
                409, "codigo_duplicado", "Ya existe un evento con ese código de acceso."
            )

    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(evento, campo, valor)
    registrar_auditoria(
        db,
        usuario.id,
        "evento_actualizado",
        "evento",
        str(evento.id),
        # mode="json" (no el `cambios` de arriba): `fecha` es un `date` de Python,
        # no serializable a JSON sin más — al guardarlo tal cual en el JSONB de
        # auditoría, psycopg lanzaba un 500 en cualquier guardado que tocara la
        # fecha (bug real reportado: "al guardar no se guarda o tarda mucho").
        detalle=datos.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(evento)
    return evento


@router.post("/{evento_id}/duplicar", response_model=EventoSalida, status_code=201)
def duplicar_evento(
    evento_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_admin)
) -> Evento:
    original = _obtener_evento_o_404(db, evento_id)
    copia = Evento(
        nombre=f"{original.nombre} (copia)",
        codigo_acceso=f"{original.codigo_acceso}-COPIA-{original.id}",
        fecha=original.fecha,
        creado_por=usuario.id,
        intervalo_gps_parado_seg=original.intervalo_gps_parado_seg,
        intervalo_gps_movimiento_seg=original.intervalo_gps_movimiento_seg,
        umbral_sin_senal_seg=original.umbral_sin_senal_seg,
        colores_config=original.colores_config,
        info_visible_config=original.info_visible_config,
    )
    db.add(copia)
    db.flush()
    registrar_auditoria(
        db,
        usuario.id,
        "evento_duplicado",
        "evento",
        str(copia.id),
        detalle={"origen_id": original.id},
    )
    db.commit()
    db.refresh(copia)
    return copia


@router.post("/{evento_id}/estado", response_model=EventoSalida)
def cambiar_estado_evento(
    evento_id: int,
    datos: CambioEstadoEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Evento:
    evento = _obtener_evento_o_404(db, evento_id)
    if not transicion_valida(evento.estado, datos.estado):
        raise ErrorAPI(
            409,
            "transicion_invalida",
            f"No se puede pasar de '{evento.estado}' a '{datos.estado}'.",
        )

    estado_anterior = evento.estado
    evento.estado = datos.estado
    # Cualquier cambio de estado (manual o automático) invalida una salida
    # programada pendiente: evita que una hora ya pasada dispare el paso a En
    # directo por sorpresa si el evento vuelve más tarde a Preparación.
    evento.hora_programada_directo = None

    if datos.estado == "finalizado":
        revocar_tokens_dispositivo_evento(db, evento.id)
        registrar_solicitud_backup(db, usuario.id, evento.id, motivo="transicion_a_finalizado")

    registrar_auditoria(
        db,
        usuario.id,
        "evento_cambio_estado",
        "evento",
        str(evento.id),
        detalle={"desde": estado_anterior, "hasta": datos.estado},
    )
    db.commit()

    if datos.estado == "finalizado":
        # Después del commit: el dump debe ver ya el estado Finalizado confirmado.
        disparar_backup_en_segundo_plano(usuario.id, evento.id)

    db.refresh(evento)
    return evento


@router.post("/codigo/{codigo_acceso}/unirse", response_model=UnirseSalida)
def unirse_a_evento(
    codigo_acceso: str,
    db: Session = Depends(get_db),
    corredor: Corredor = Depends(obtener_corredor_actual),
) -> UnirseSalida:
    evento = db.query(Evento).filter_by(codigo_acceso=codigo_acceso).one_or_none()
    if evento is None:
        raise ErrorAPI(404, "no_encontrado", "No existe ningún evento con ese código.")
    if evento.estado not in _ESTADOS_PERMITEN_UNIRSE:
        raise ErrorAPI(
            409,
            "estado_no_permite_union",
            f"El evento está en estado '{evento.estado}' y no admite nuevas uniones.",
        )

    inscripcion = (
        db.query(Inscripcion)
        .join(Distancia)
        .filter(Distancia.evento_id == evento.id, Inscripcion.corredor_id == corredor.id)
        .order_by(Inscripcion.id)
        .first()
    )
    if inscripcion is None:
        raise ErrorAPI(
            404,
            "sin_inscripcion",
            "No se ha encontrado tu inscripción; contacta con el organizador.",
        )

    # Un solo token de dispositivo activo por inscripción (SUP-008): unirse desde un
    # segundo dispositivo revoca el anterior.
    ahora = datetime.now(UTC)
    db.query(TokenDispositivo).filter(
        TokenDispositivo.inscripcion_id == inscripcion.id, TokenDispositivo.revocado_en.is_(None)
    ).update({TokenDispositivo.revocado_en: ahora}, synchronize_session=False)

    token_plano = generar_token_dispositivo()
    db.add(
        TokenDispositivo(
            inscripcion_id=inscripcion.id, token_hash=hash_token_dispositivo(token_plano)
        )
    )
    db.commit()

    return UnirseSalida(
        evento_id=evento.id,
        inscripcion_id=inscripcion.id,
        distancia_id=inscripcion.distancia_id,
        distancia_nombre=inscripcion.distancia.nombre,
        dorsal=inscripcion.dorsal,
        token_dispositivo=token_plano,
        evento_estado=evento.estado,
    )
