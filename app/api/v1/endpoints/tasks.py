from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.task import Tarea
from app.models.user import Usuario
from app.schemas.task import AsignarUsuariosRequest, TareaCreate, TareaResponse, TareaUpdate

router = APIRouter()


@router.post("/tareas", response_model=TareaResponse)
def crear_tarea(
    tarea: TareaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    _ = usuario
    datos = tarea.model_dump(exclude={"asignados_ids"})
    nueva_tarea = Tarea(
        **datos,
    )
    if tarea.asignados_ids:
        nueva_tarea.asignados = db.query(Usuario).filter(Usuario.id.in_(tarea.asignados_ids)).all()

    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea


@router.get("/tareas", response_model=list[TareaResponse])
def listar_tareas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Tarea]:
    _ = usuario
    return db.query(Tarea).all()


@router.get("/tareas/{tarea_id}", response_model=TareaResponse)
def obtener_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    _ = usuario
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea


@router.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(
    tarea_id: int,
    datos: TareaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tarea:
    _ = usuario
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Vulnerabilidad intencional: permite cambiar creador_id y columna_id.
    for key, value in datos.model_dump(exclude_unset=True).items():
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
    _ = usuario
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Vulnerabilidad intencional: cualquier usuario asigna a cualquiera a cualquier tarea.
    tarea.asignados = db.query(Usuario).filter(Usuario.id.in_(datos.usuarios_ids)).all()
    db.commit()
    db.refresh(tarea)
    return tarea


@router.delete("/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int,
    x_user_id: int | None = Header(
        default=None,
        description="Simula el ID del usuario logueado en el Token",
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict[str, str]:
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Vulnerabilidad intencional: se ignora usuario y x_user_id.
    _ = usuario
    _ = x_user_id

    db.delete(tarea)
    db.commit()
    return {
        "status": "success",
        "mensaje": f"La tarea {tarea_id} fue eliminada exitosamente",
    }
