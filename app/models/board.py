from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Tablero(Base):
    __tablename__ = "tableros"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    propietario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    propietario = relationship("Usuario", back_populates="tableros")
    columnas = relationship("Columna", back_populates="tablero", cascade="all, delete-orphan")


class Columna(Base):
    __tablename__ = "columnas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    tablero_id = Column(Integer, ForeignKey("tableros.id", ondelete="CASCADE"), nullable=False)
    orden = Column(Integer, default=0)

    tablero = relationship("Tablero", back_populates="columnas")
    tareas = relationship("Tarea", back_populates="columna", cascade="all, delete-orphan")
