from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import es_superadmin
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.user import Usuario
from app.schemas.user import UsuarioResponse, UsuarioUpdate

router = APIRouter()


@router.get("/usuarios", response_model=list[UsuarioResponse])
def obtener_usuarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Usuario]:
    if es_superadmin(usuario):
        return db.query(Usuario).all()

    return db.query(Usuario).filter(Usuario.id != usuario.id).all()


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Usuario:
    if not es_superadmin(usuario) and usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="No puedes consultar este usuario")

    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    datos_actualizacion: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Usuario:
    if not es_superadmin(usuario) and usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="No puedes actualizar este usuario")

    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    datos_dict = datos_actualizacion.model_dump(exclude_unset=True)
    if "password" in datos_dict:
        datos_dict["password_hash"] = datos_dict.pop("password")

    for key, value in datos_dict.items():
        setattr(db_usuario, key, value)

    db.commit()
    db.refresh(db_usuario)
    return db_usuario
