from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UsuarioExpuesto


class TableroCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    propietario_id: int


class TableroUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    propietario_id: int | None = None


class ColumnaCreate(BaseModel):
    nombre: str
    tablero_id: int
    orden: int = 0


class ColumnaUpdate(BaseModel):
    nombre: str | None = None
    tablero_id: int | None = None
    orden: int | None = None


class ColumnaResponse(BaseModel):
    id: int
    nombre: str
    tablero_id: int
    orden: int

    model_config = ConfigDict(from_attributes=True)


class TableroResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    propietario_id: int
    creado_en: datetime
    propietario: UsuarioExpuesto | None = None
    columnas: list[ColumnaResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
