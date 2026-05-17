from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RolResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol_id: int | None = None


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol_id: int
    creado_en: datetime
    rol: RolResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    rol_id: int | None = None
