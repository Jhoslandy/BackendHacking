from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UsuarioResponse


class TareaBase(BaseModel):
    titulo: str
    descripcion: str | None = None
    columna_id: int
    fecha_vencimiento: datetime | None = None


class TareaCreate(TareaBase):
    asignados_ids: list[int] = Field(default_factory=list)


class TareaUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    fecha_vencimiento: datetime | None = None
    columna_id: int | None = None


class TareaResponse(TareaBase):
    id: int
    creador_id: int | None
    proyecto_id: int | None = None
    creado_en: datetime
    creador: UsuarioResponse | None = None
    asignados: list[UsuarioResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AsignarUsuariosRequest(BaseModel):
    usuarios_ids: list[int]


class SolicitudMovimientoCreate(BaseModel):
    mensaje: str | None = None


class SolicitudMovimientoResponse(BaseModel):
    id: int
    proyecto_id: int | None = None
    tarea_id: int
    tarea_titulo: str
    solicitante_id: int
    solicitante_nombre: str
    columna_origen_id: int
    columna_origen_nombre: str
    columna_destino_id: int
    columna_destino_nombre: str
    estado: str
    puede_resolver: bool = False
    mensaje: str | None = None
    creado_en: datetime
    resuelto_en: datetime | None = None
