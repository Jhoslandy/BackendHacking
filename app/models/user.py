from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.associations import proyecto_miembros, usuario_tarea


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    rol = relationship("Rol", back_populates="usuarios")
    proyectos_creados = relationship("Proyecto", back_populates="creador")
    proyectos = relationship("Proyecto", secondary=proyecto_miembros, back_populates="miembros")
    tareas_creadas = relationship("Tarea", back_populates="creador")
    tareas_asignadas = relationship("Tarea", secondary=usuario_tarea, back_populates="asignados")
    solicitudes_movimiento = relationship("SolicitudTareaMovimiento", back_populates="solicitante")
