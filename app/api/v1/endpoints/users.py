from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.user import Usuario
from app.schemas.user import UsuarioCreate, UsuarioExpuesto, UsuarioUpdate

router = APIRouter()


@router.post("/usuarios", response_model=UsuarioExpuesto)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=usuario.password,
        rol_id=usuario.rol_id,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/usuarios", response_model=list[UsuarioExpuesto])
def obtener_usuarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Usuario]:
    # Vulnerabilidad intencional: expone todos los usuarios y sus password_hash.
    _ = usuario
    return db.query(Usuario).all()


@router.get("/usuarios/{usuario_id}", response_model=UsuarioExpuesto)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Usuario:
    _ = usuario
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


@router.put("/usuarios/{usuario_id}", response_model=UsuarioExpuesto)
def actualizar_usuario(
    usuario_id: int,
    datos_actualizacion: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Usuario:
    _ = usuario
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    datos_dict = datos_actualizacion.model_dump(exclude_unset=True)
    if "password" in datos_dict:
        datos_dict["password_hash"] = datos_dict.pop("password")

    # Vulnerabilidad intencional: mass assignment sobre campos sensibles.
    for key, value in datos_dict.items():
        setattr(db_usuario, key, value)

    db.commit()
    db.refresh(db_usuario)
    return db_usuario
