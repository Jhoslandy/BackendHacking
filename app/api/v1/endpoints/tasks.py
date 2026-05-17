from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import (
    es_superadmin,
    exigir_acceso_proyecto,
    exigir_admin_proyecto,
    usuario_tiene_acceso_proyecto,
)
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.associations import proyecto_miembros
from app.models.board import Columna
from app.models.task import Tarea
from app.models.user import Usuario
from app.schemas.task import AsignarUsuariosRequest, TareaCreate, TareaResponse, TareaUpdate

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
