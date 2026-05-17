from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table
from sqlalchemy.sql import func

from app.db.base import Base

usuario_tarea = Table(
    "usuario_tarea",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("tarea_id", Integer, ForeignKey("tareas.id", ondelete="CASCADE"), primary_key=True),
    Column("asignado_en", DateTime(timezone=True), server_default=func.now()),
)
