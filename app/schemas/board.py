from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TableroCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class TableroUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None


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
    proyecto_id: int
    creado_en: datetime
    columnas: list[ColumnaResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
