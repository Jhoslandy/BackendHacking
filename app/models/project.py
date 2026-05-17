from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.associations import proyecto_miembros


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    creador_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    creador = relationship("Usuario", back_populates="proyectos_creados")
    miembros = relationship("Usuario", secondary=proyecto_miembros, back_populates="proyectos")
    tableros = relationship("Tablero", back_populates="proyecto", cascade="all, delete-orphan")
