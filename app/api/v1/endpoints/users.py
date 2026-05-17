from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import es_superadmin
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.core.constants import ROL_USUARIO_COMUN
from app.models.user import Rol, Usuario
from app.schemas.user import UsuarioCreate, UsuarioResponse, UsuarioUpdate

router = APIRouter()


def obtener_usuario_o_404(db: Session, usuario_id: int) -> Usuario:
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


def rol_por_defecto(db: Session) -> Rol:
    rol = db.query(Rol).filter(Rol.nombre == ROL_USUARIO_COMUN).first()
    if not rol:
        raise HTTPException(status_code=500, detail="Rol Usuario_Comun no configurado")
    return rol


@router.post("/usuarios", response_model=UsuarioResponse)
def crear_usuario(
    datos_usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Usuario:
    if not es_superadmin(usuario):
        raise HTTPException(status_code=403, detail="Solo el SuperAdministrador puede crear usuarios")

    usuario_existente = db.query(Usuario).filter(Usuario.email == datos_usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    nuevo_usuario = Usuario(
        nombre=datos_usuario.nombre,
        email=datos_usuario.email,
        password_hash=datos_usuario.password,
        rol_id=datos_usuario.rol_id or rol_por_defecto(db).id,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


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

    db_usuario = obtener_usuario_o_404(db, usuario_id)
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

    db_usuario = obtener_usuario_o_404(db, usuario_id)

    datos_dict = datos_actualizacion.model_dump(exclude_unset=True)
    if "password" in datos_dict:
        datos_dict["password_hash"] = datos_dict.pop("password")

    for key, value in datos_dict.items():
        setattr(db_usuario, key, value)

    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> dict[str, str]:
    if not es_superadmin(usuario):
        raise HTTPException(status_code=403, detail="Solo el SuperAdministrador puede eliminar usuarios")
    if usuario.id == usuario_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta activa")

    db_usuario = obtener_usuario_o_404(db, usuario_id)
    db.delete(db_usuario)
    db.commit()
    return {"status": "success", "mensaje": f"Usuario {usuario_id} eliminado"}
