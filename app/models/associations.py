from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.sql import func

from app.db.base import Base

usuario_tarea = Table(
    "usuario_tarea",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("tarea_id", Integer, ForeignKey("tareas.id", ondelete="CASCADE"), primary_key=True),
    Column("asignado_en", DateTime(timezone=True), server_default=func.now()),
)

proyecto_miembros = Table(
    "proyecto_miembros",
    Base.metadata,
    Column("proyecto_id", Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True),
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("subrol", String(50), nullable=False),
    Column("agregado_en", DateTime(timezone=True), server_default=func.now()),
)
