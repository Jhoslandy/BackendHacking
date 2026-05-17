from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import crear_token_debil, obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.user import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UsuarioCreate, UsuarioExpuesto

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UsuarioExpuesto)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    # Vulnerabilidad intencional: password en texto plano y rol_id aceptado desde el body.
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


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or usuario.password_hash != datos.password:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    token = crear_token_debil(usuario)
    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioExpuesto)
def obtener_perfil(usuario: Usuario = Depends(obtener_usuario_actual_debil)) -> Usuario:
    return usuario
