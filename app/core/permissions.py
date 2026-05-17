from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.constants import ROL_SUPERADMIN, SUBROL_ADMIN_PROYECTO
from app.models.associations import proyecto_miembros
from app.models.project import Proyecto
from app.models.user import Usuario


def es_superadmin(usuario: Usuario) -> bool:
    return usuario.rol is not None and usuario.rol.nombre == ROL_SUPERADMIN


def obtener_subrol_proyecto(db: Session, proyecto_id: int, usuario_id: int) -> str | None:
    row = (
        db.execute(
            proyecto_miembros.select().where(
                proyecto_miembros.c.proyecto_id == proyecto_id,
                proyecto_miembros.c.usuario_id == usuario_id,
            )
        )
        .mappings()
        .first()
    )
    return row["subrol"] if row else None


def usuario_tiene_acceso_proyecto(db: Session, proyecto_id: int, usuario: Usuario) -> bool:
    return es_superadmin(usuario) or obtener_subrol_proyecto(db, proyecto_id, usuario.id) is not None


def usuario_administra_proyecto(db: Session, proyecto_id: int, usuario: Usuario) -> bool:
    return es_superadmin(usuario) or obtener_subrol_proyecto(db, proyecto_id, usuario.id) == SUBROL_ADMIN_PROYECTO


def obtener_proyecto_o_404(db: Session, proyecto_id: int) -> Proyecto:
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


def exigir_acceso_proyecto(db: Session, proyecto_id: int, usuario: Usuario) -> Proyecto:
    proyecto = obtener_proyecto_o_404(db, proyecto_id)
    if not usuario_tiene_acceso_proyecto(db, proyecto_id, usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a este proyecto")
    return proyecto


def exigir_admin_proyecto(db: Session, proyecto_id: int, usuario: Usuario) -> Proyecto:
    proyecto = obtener_proyecto_o_404(db, proyecto_id)
    if not usuario_administra_proyecto(db, proyecto_id, usuario):
        raise HTTPException(status_code=403, detail="No puedes administrar este proyecto")
    return proyecto
