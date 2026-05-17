from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UsuarioResponse


class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: str | None = None

    model_config = ConfigDict(extra="allow")


class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    creador_id: int | None = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class MiembroProyectoCreate(BaseModel):
    usuario_id: int
    subrol: str = Field(default="miembro", pattern="^(administrador_proyecto|miembro)$")


class MiembroProyectoResponse(BaseModel):
    usuario: UsuarioResponse
    subrol: str
