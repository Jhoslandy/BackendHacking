from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core.constants import ROL_USUARIO_COMUN, SUBROL_ADMIN_PROYECTO
from app.core.permissions import (
    es_superadmin,
    exigir_acceso_proyecto,
    exigir_admin_proyecto,
)
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.associations import proyecto_miembros
from app.models.project import Proyecto
from app.models.user import Usuario
from app.schemas.project import (
    MiembroProyectoCreate,
    MiembroProyectoResponse,
    ProyectoCreate,
    ProyectoResponse,
)

router = APIRouter(prefix="/proyectos")


@router.post("", response_model=ProyectoResponse)
def crear_proyecto(
    datos: ProyectoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Proyecto:
    proyecto = Proyecto(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        creador_id=usuario.id,
    )
    db.add(proyecto)
    db.flush()
    db.execute(
        insert(proyecto_miembros).values(
            proyecto_id=proyecto.id,
            usuario_id=usuario.id,
            subrol=SUBROL_ADMIN_PROYECTO,
        )
    )
    db.commit()
    db.refresh(proyecto)
    return proyecto


@router.get("", response_model=list[ProyectoResponse])
def listar_proyectos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Proyecto]:
    if es_superadmin(usuario):
        return db.query(Proyecto).all()

    return (
        db.query(Proyecto)
        .join(proyecto_miembros, proyecto_miembros.c.proyecto_id == Proyecto.id)
        .filter(proyecto_miembros.c.usuario_id == usuario.id)
        .all()
    )


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Proyecto:
    return exigir_acceso_proyecto(db, proyecto_id, usuario)


@router.get("/{proyecto_id}/miembros", response_model=list[MiembroProyectoResponse])
def listar_miembros(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[dict]:
    exigir_acceso_proyecto(db, proyecto_id, usuario)
    rows = (
        db.query(Usuario, proyecto_miembros.c.subrol)
        .join(proyecto_miembros, proyecto_miembros.c.usuario_id == Usuario.id)
        .filter(proyecto_miembros.c.proyecto_id == proyecto_id)
        .all()
    )
    return [{"usuario": usuario_row, "subrol": subrol} for usuario_row, subrol in rows]


@router.post("/{proyecto_id}/miembros", response_model=MiembroProyectoResponse)
def agregar_miembro(
    proyecto_id: int,
    datos: MiembroProyectoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict:
    exigir_admin_proyecto(db, proyecto_id, usuario)

    nuevo_miembro = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not nuevo_miembro:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if nuevo_miembro.rol is None or nuevo_miembro.rol.nombre != ROL_USUARIO_COMUN:
        raise HTTPException(status_code=400, detail="Solo se pueden agregar usuarios comunes")

    existe = (
        db.execute(
            proyecto_miembros.select().where(
                proyecto_miembros.c.proyecto_id == proyecto_id,
                proyecto_miembros.c.usuario_id == datos.usuario_id,
            )
        )
        .mappings()
        .first()
    )
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya pertenece al proyecto")

    db.execute(
        insert(proyecto_miembros).values(
            proyecto_id=proyecto_id,
            usuario_id=datos.usuario_id,
            subrol=datos.subrol,
        )
    )
    db.commit()
    return {"usuario": nuevo_miembro, "subrol": datos.subrol}
