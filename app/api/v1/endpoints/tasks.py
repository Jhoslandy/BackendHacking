from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import (
    es_superadmin,
    exigir_acceso_proyecto,
    exigir_admin_proyecto,
    usuario_administra_proyecto,
    usuario_tiene_acceso_proyecto,
)
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.associations import proyecto_miembros
from app.models.board import Columna
from app.models.movement_request import SolicitudTareaMovimiento
from app.models.task import Tarea
from app.models.user import Usuario
from app.schemas.task import (
    AsignarUsuariosRequest,
    SolicitudMovimientoCreate,
    SolicitudMovimientoResponse,
    TareaCreate,
    TareaResponse,
    TareaUpdate,
)

router = APIRouter()


def obtener_columna_o_404(db: Session, columna_id: int) -> Columna:
    columna = db.query(Columna).filter(Columna.id == columna_id).first()
    if not columna:
        raise HTTPException(status_code=404, detail="Columna no encontrada")
    return columna


def obtener_tarea_o_404(db: Session, tarea_id: int) -> Tarea:
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea


def proyecto_de_columna(columna: Columna) -> int:
    return columna.tablero.proyecto_id


def proyecto_de_tarea(tarea: Tarea) -> int:
    return tarea.columna.tablero.proyecto_id


def usuarios_son_miembros(db: Session, proyecto_id: int, usuarios_ids: list[int]) -> bool:
    if not usuarios_ids:
        return True

    encontrados = (
        db.execute(
            proyecto_miembros.select().where(
                proyecto_miembros.c.proyecto_id == proyecto_id,
                proyecto_miembros.c.usuario_id.in_(usuarios_ids),
            )
        )
        .mappings()
        .all()
    )
    return len(encontrados) == len(set(usuarios_ids))


def asignar_usuarios_a_tarea(db: Session, tarea: Tarea, proyecto_id: int, usuarios_ids: list[int]) -> None:
    if not usuarios_son_miembros(db, proyecto_id, usuarios_ids):
        raise HTTPException(status_code=400, detail="Solo se pueden asignar miembros del proyecto")
    tarea.asignados = db.query(Usuario).filter(Usuario.id.in_(usuarios_ids)).all() if usuarios_ids else []


def siguiente_columna(db: Session, columna: Columna) -> Columna | None:
    return (
        db.query(Columna)
        .filter(Columna.tablero_id == columna.tablero_id, Columna.orden > columna.orden)
        .order_by(Columna.orden)
        .first()
    )


def obtener_solicitud_o_404(db: Session, solicitud_id: int) -> SolicitudTareaMovimiento:
    solicitud = (
        db.query(SolicitudTareaMovimiento)
        .filter(SolicitudTareaMovimiento.id == solicitud_id)
        .first()
    )
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud


def serializar_solicitud(solicitud: SolicitudTareaMovimiento, puede_resolver: bool = False) -> dict:
    return {
        "id": solicitud.id,
        "proyecto_id": proyecto_de_tarea(solicitud.tarea),
        "tarea_id": solicitud.tarea_id,
        "tarea_titulo": solicitud.tarea.titulo,
        "solicitante_id": solicitud.solicitante_id,
        "solicitante_nombre": solicitud.solicitante.nombre,
        "columna_origen_id": solicitud.columna_origen_id,
        "columna_origen_nombre": solicitud.columna_origen.nombre,
        "columna_destino_id": solicitud.columna_destino_id,
        "columna_destino_nombre": solicitud.columna_destino.nombre,
        "estado": solicitud.estado,
        "puede_resolver": puede_resolver,
        "mensaje": solicitud.mensaje,
        "creado_en": solicitud.creado_en,
        "resuelto_en": solicitud.resuelto_en,
    }


def exigir_admin_de_solicitud(
    db: Session,
    solicitud: SolicitudTareaMovimiento,
    usuario: Usuario,
) -> int:
    proyecto_id = proyecto_de_tarea(solicitud.tarea)
    if not usuario_administra_proyecto(db, proyecto_id, usuario):
        raise HTTPException(status_code=403, detail="Solo el administrador del proyecto puede resolver la solicitud")
    return proyecto_id


@router.post("/tareas", response_model=TareaResponse)
def crear_tarea(
    tarea: TareaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    columna = obtener_columna_o_404(db, tarea.columna_id)
    proyecto_id = proyecto_de_columna(columna)
    exigir_admin_proyecto(db, proyecto_id, usuario)

    nueva_tarea = Tarea(
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        fecha_vencimiento=tarea.fecha_vencimiento,
        columna_id=tarea.columna_id,
        creador_id=usuario.id,
    )
    asignar_usuarios_a_tarea(db, nueva_tarea, proyecto_id, tarea.asignados_ids)

    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea


@router.get("/tareas", response_model=list[TareaResponse])
def listar_tareas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Tarea]:
    if es_superadmin(usuario):
        return db.query(Tarea).all()

    tareas = db.query(Tarea).all()
    return [tarea for tarea in tareas if usuario_tiene_acceso_proyecto(db, proyecto_de_tarea(tarea), usuario)]


@router.get("/tareas/{tarea_id}", response_model=TareaResponse)
def obtener_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    tarea = obtener_tarea_o_404(db, tarea_id)
    exigir_acceso_proyecto(db, proyecto_de_tarea(tarea), usuario)
    return tarea


@router.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(
    tarea_id: int,
    datos: TareaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    tarea = obtener_tarea_o_404(db, tarea_id)
    proyecto_id = proyecto_de_tarea(tarea)
    exigir_admin_proyecto(db, proyecto_id, usuario)

    datos_dict = datos.model_dump(exclude_unset=True)
    if "columna_id" in datos_dict:
        nueva_columna = obtener_columna_o_404(db, datos_dict["columna_id"])
        if proyecto_de_columna(nueva_columna) != proyecto_id:
            raise HTTPException(status_code=400, detail="La columna no pertenece al proyecto de la tarea")

    for key, value in datos_dict.items():
        setattr(tarea, key, value)

    db.commit()
    db.refresh(tarea)
    return tarea


@router.post("/tareas/{tarea_id}/asignados", response_model=TareaResponse)
def asignar_usuarios(
    tarea_id: int,
    datos: AsignarUsuariosRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    tarea = obtener_tarea_o_404(db, tarea_id)
    proyecto_id = proyecto_de_tarea(tarea)
    exigir_admin_proyecto(db, proyecto_id, usuario)
    asignar_usuarios_a_tarea(db, tarea, proyecto_id, datos.usuarios_ids)
    db.commit()
    db.refresh(tarea)
    return tarea


@router.delete("/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict[str, str]:
    tarea = obtener_tarea_o_404(db, tarea_id)
    exigir_admin_proyecto(db, proyecto_de_tarea(tarea), usuario)

    db.delete(tarea)
    db.commit()
    return {"status": "success", "mensaje": f"La tarea {tarea_id} fue eliminada exitosamente"}


@router.post("/tareas/{tarea_id}/solicitudes-movimiento", response_model=SolicitudMovimientoResponse)
def solicitar_movimiento_tarea(
    tarea_id: int,
    datos: SolicitudMovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict:
    tarea = obtener_tarea_o_404(db, tarea_id)
    proyecto_id = proyecto_de_tarea(tarea)
    exigir_acceso_proyecto(db, proyecto_id, usuario)

    if usuario.id not in {asignado.id for asignado in tarea.asignados}:
        raise HTTPException(status_code=403, detail="Solo un usuario asignado puede solicitar avance")

    destino = siguiente_columna(db, tarea.columna)
    if not destino:
        raise HTTPException(status_code=400, detail="La tarea ya esta en la ultima columna")

    pendiente = (
        db.query(SolicitudTareaMovimiento)
        .filter(
            SolicitudTareaMovimiento.tarea_id == tarea.id,
            SolicitudTareaMovimiento.estado == "pendiente",
        )
        .first()
    )
    if pendiente:
        raise HTTPException(status_code=400, detail="La tarea ya tiene una solicitud pendiente")

    solicitud = SolicitudTareaMovimiento(
        tarea_id=tarea.id,
        solicitante_id=usuario.id,
        columna_origen_id=tarea.columna_id,
        columna_destino_id=destino.id,
        mensaje=datos.mensaje,
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return serializar_solicitud(solicitud)


@router.get("/solicitudes-movimiento", response_model=list[SolicitudMovimientoResponse])
def listar_solicitudes_movimiento(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[dict]:
    solicitudes = db.query(SolicitudTareaMovimiento).order_by(SolicitudTareaMovimiento.creado_en.desc()).all()
    if es_superadmin(usuario):
        return [serializar_solicitud(solicitud, puede_resolver=True) for solicitud in solicitudes]

    visibles = []
    for solicitud in solicitudes:
        proyecto_id = proyecto_de_tarea(solicitud.tarea)
        puede_resolver = usuario_administra_proyecto(db, proyecto_id, usuario)
        if solicitud.solicitante_id == usuario.id or puede_resolver:
            visibles.append(solicitud)
    return [
        serializar_solicitud(
            solicitud,
            puede_resolver=usuario_administra_proyecto(db, proyecto_de_tarea(solicitud.tarea), usuario),
        )
        for solicitud in visibles
    ]


@router.post("/solicitudes-movimiento/{solicitud_id}/aprobar", response_model=SolicitudMovimientoResponse)
def aprobar_solicitud_movimiento(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict:
    solicitud = obtener_solicitud_o_404(db, solicitud_id)
    exigir_admin_de_solicitud(db, solicitud, usuario)
    if solicitud.estado != "pendiente":
        raise HTTPException(status_code=400, detail="La solicitud ya fue resuelta")

    solicitud.tarea.columna_id = solicitud.columna_destino_id
    solicitud.estado = "aprobada"
    solicitud.resuelto_en = datetime.now(timezone.utc)
    db.commit()
    db.refresh(solicitud)
    return serializar_solicitud(solicitud, puede_resolver=True)


@router.post("/solicitudes-movimiento/{solicitud_id}/rechazar", response_model=SolicitudMovimientoResponse)
def rechazar_solicitud_movimiento(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict:
    solicitud = obtener_solicitud_o_404(db, solicitud_id)
    exigir_admin_de_solicitud(db, solicitud, usuario)
    if solicitud.estado != "pendiente":
        raise HTTPException(status_code=400, detail="La solicitud ya fue resuelta")

    solicitud.estado = "rechazada"
    solicitud.resuelto_en = datetime.now(timezone.utc)
    db.commit()
    db.refresh(solicitud)
    return serializar_solicitud(solicitud, puede_resolver=True)
