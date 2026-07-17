from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.almacenamiento import ruta_storage, url_publica
from app.database import get_db
from app.errores import ErrorAPI
from app.models import Evento, Noticia, Patrocinador, Usuario
from app.schemas.contenido import (
    NoticiaActualizar,
    NoticiaCrear,
    NoticiaSalida,
    PatrocinadorActualizar,
    PatrocinadorCrear,
    PatrocinadorSalida,
)
from app.schemas.eventos import EventoSalida
from app.security.dependencies import requiere_admin
from app.servicios.auditoria import registrar_auditoria
from app.servicios.imagenes import validar_y_leer_imagen

router = APIRouter(tags=["contenido"])


def _obtener_evento_o_404(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise ErrorAPI(404, "no_encontrado", "Evento no encontrado.")
    return evento


def _obtener_patrocinador_o_404(db: Session, patrocinador_id: int) -> Patrocinador:
    patrocinador = db.get(Patrocinador, patrocinador_id)
    if patrocinador is None:
        raise ErrorAPI(404, "no_encontrado", "Patrocinador no encontrado.")
    return patrocinador


def _obtener_noticia_o_404(db: Session, noticia_id: int) -> Noticia:
    noticia = db.get(Noticia, noticia_id)
    if noticia is None:
        raise ErrorAPI(404, "no_encontrado", "Noticia no encontrada.")
    return noticia


# --- Patrocinadores: lectura LAN abierta, escritura Admin (Anexo B §4) ---


@router.get("/eventos/{evento_id}/patrocinadores", response_model=list[PatrocinadorSalida])
def listar_patrocinadores(evento_id: int, db: Session = Depends(get_db)) -> list[Patrocinador]:
    _obtener_evento_o_404(db, evento_id)
    return (
        db.query(Patrocinador)
        .filter_by(evento_id=evento_id)
        .order_by(Patrocinador.orden, Patrocinador.id)
        .all()
    )


@router.post(
    "/eventos/{evento_id}/patrocinadores", response_model=PatrocinadorSalida, status_code=201
)
def crear_patrocinador(
    evento_id: int,
    datos: PatrocinadorCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Patrocinador:
    _obtener_evento_o_404(db, evento_id)
    patrocinador = Patrocinador(evento_id=evento_id, **datos.model_dump())
    db.add(patrocinador)
    db.flush()
    registrar_auditoria(
        db, usuario.id, "patrocinador_creado", "patrocinador", str(patrocinador.id)
    )
    db.commit()
    db.refresh(patrocinador)
    return patrocinador


@router.put("/patrocinadores/{patrocinador_id}", response_model=PatrocinadorSalida)
def actualizar_patrocinador(
    patrocinador_id: int,
    datos: PatrocinadorActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Patrocinador:
    patrocinador = _obtener_patrocinador_o_404(db, patrocinador_id)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(patrocinador, campo, valor)
    registrar_auditoria(
        db,
        usuario.id,
        "patrocinador_actualizado",
        "patrocinador",
        str(patrocinador.id),
        detalle=datos.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(patrocinador)
    return patrocinador


@router.delete("/patrocinadores/{patrocinador_id}", status_code=204)
def eliminar_patrocinador(
    patrocinador_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> None:
    patrocinador = _obtener_patrocinador_o_404(db, patrocinador_id)
    registrar_auditoria(
        db, usuario.id, "patrocinador_eliminado", "patrocinador", str(patrocinador.id)
    )
    db.delete(patrocinador)
    db.commit()


# --- Noticias: lectura LAN abierta, escritura Admin (Anexo B §4) ---


@router.get("/eventos/{evento_id}/noticias", response_model=list[NoticiaSalida])
def listar_noticias(evento_id: int, db: Session = Depends(get_db)) -> list[Noticia]:
    _obtener_evento_o_404(db, evento_id)
    return (
        db.query(Noticia).filter_by(evento_id=evento_id).order_by(Noticia.publicado_en.desc()).all()
    )


@router.post("/eventos/{evento_id}/noticias", response_model=NoticiaSalida, status_code=201)
def crear_noticia(
    evento_id: int,
    datos: NoticiaCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Noticia:
    _obtener_evento_o_404(db, evento_id)
    noticia = Noticia(evento_id=evento_id, **datos.model_dump())
    db.add(noticia)
    db.flush()
    registrar_auditoria(db, usuario.id, "noticia_creada", "noticia", str(noticia.id))
    db.commit()
    db.refresh(noticia)
    return noticia


@router.put("/noticias/{noticia_id}", response_model=NoticiaSalida)
def actualizar_noticia(
    noticia_id: int,
    datos: NoticiaActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Noticia:
    noticia = _obtener_noticia_o_404(db, noticia_id)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(noticia, campo, valor)
    registrar_auditoria(
        db,
        usuario.id,
        "noticia_actualizada",
        "noticia",
        str(noticia.id),
        detalle=datos.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(noticia)
    return noticia


@router.delete("/noticias/{noticia_id}", status_code=204)
def eliminar_noticia(
    noticia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> None:
    noticia = _obtener_noticia_o_404(db, noticia_id)
    registrar_auditoria(db, usuario.id, "noticia_eliminada", "noticia", str(noticia.id))
    db.delete(noticia)
    db.commit()


# --- Cartel (RF-003): imagen propia del evento; se guarda en eventos.cartel_url ---


@router.post("/eventos/{evento_id}/cartel", response_model=EventoSalida)
def subir_cartel(
    evento_id: int,
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Evento:
    evento = _obtener_evento_o_404(db, evento_id)
    contenido = archivo.file.read()
    imagen = validar_y_leer_imagen(contenido)

    extension = "jpg" if imagen.format == "JPEG" else "png"
    destino = ruta_storage("carteles", f"{evento_id}.{extension}")
    destino.write_bytes(contenido)

    evento.cartel_url = url_publica("carteles", f"{evento_id}.{extension}")
    registrar_auditoria(db, usuario.id, "cartel_subido", "evento", str(evento_id))
    db.commit()
    db.refresh(evento)
    return evento


@router.delete("/eventos/{evento_id}/cartel", response_model=EventoSalida)
def eliminar_cartel(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Evento:
    evento = _obtener_evento_o_404(db, evento_id)
    if evento.cartel_url:
        # cartel_url es "/media/carteles/<archivo>"; el prefijo "/media/" lo
        # añade url_publica() y no forma parte de la ruta real en disco.
        relativo = evento.cartel_url.removeprefix("/media/")
        ruta_storage(*relativo.split("/")).unlink(missing_ok=True)
        evento.cartel_url = None
        registrar_auditoria(db, usuario.id, "cartel_eliminado", "evento", str(evento_id))
        db.commit()
        db.refresh(evento)
    return evento
