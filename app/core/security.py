from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.deps import get_db
from app.models.user import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


def _parse_expiration(value: str) -> timedelta:
    unit = value[-1].lower()
    amount = int(value[:-1])

    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)

    return timedelta(days=7)


def crear_token_debil(usuario: Usuario) -> str:
    settings = get_settings()
    expires_delta = _parse_expiration(settings.JWT_EXPIRES_IN)
    payload: dict[str, Any] = {
        "sub": str(usuario.id),
        "user_id": usuario.id,
        "email": usuario.email,
        "rol_id": usuario.rol_id,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def obtener_usuario_actual_debil(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )

    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    # Vulnerabilidad intencional: se confia en el user_id del token.
    usuario = db.query(Usuario).filter(Usuario.id == payload.get("user_id")).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return usuario
