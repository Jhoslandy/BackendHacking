from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.constants import ROL_USUARIO_COMUN
from app.core.security import crear_token_debil, obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.user import Rol, Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/auth")


def obtener_rol_usuario_comun(db: Session) -> Rol:
    rol = db.query(Rol).filter(Rol.nombre == ROL_USUARIO_COMUN).first()
    if not rol:
        raise HTTPException(status_code=500, detail="Rol Usuario_Comun no configurado")
    return rol


@router.post("/register", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    rol_usuario = obtener_rol_usuario_comun(db)
    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=usuario.password,
        rol_id=rol_usuario.id,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or usuario.password_hash != datos.password:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    token = crear_token_debil(usuario)
    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil(usuario: Usuario = Depends(obtener_usuario_actual_debil)) -> Usuario:
    return usuario
