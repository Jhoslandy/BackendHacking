from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RolResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol_id: int | None = None


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioResponse(UsuarioBase):
    id: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioExpuesto(UsuarioResponse):
    password_hash: str
    rol: RolResponse | None = None


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    password_hash: str | None = None
    rol_id: int | None = None
