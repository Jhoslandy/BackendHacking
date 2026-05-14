from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Tabla intermedia N:M para asignar usuarios a tareas
usuario_tarea = Table(
    'usuario_tarea',
    Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id', ondelete="CASCADE"), primary_key=True),
    Column('tarea_id', Integer, ForeignKey('tareas.id', ondelete="CASCADE"), primary_key=True),
    Column('asignado_en', DateTime(timezone=True), server_default=func.now())
)

class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    # Relación: Un rol puede tener muchos usuarios
    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    tableros = relationship("Tablero", back_populates="propietario")
    tareas_creadas = relationship("Tarea", back_populates="creador")
    # Relación N:M con Tareas
    tareas_asignadas = relationship("Tarea", secondary=usuario_tarea, back_populates="asignados")


class Tablero(Base):
    __tablename__ = "tableros"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    propietario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    propietario = relationship("Usuario", back_populates="tableros")
    columnas = relationship("Columna", back_populates="tablero", cascade="all, delete-orphan")


class Columna(Base):
    __tablename__ = "columnas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    tablero_id = Column(Integer, ForeignKey("tableros.id", ondelete="CASCADE"), nullable=False)
    orden = Column(Integer, default=0)

    # Relaciones
    tablero = relationship("Tablero", back_populates="columnas")
    tareas = relationship("Tarea", back_populates="columna", cascade="all, delete-orphan")


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha_vencimiento = Column(DateTime(timezone=True))
    columna_id = Column(Integer, ForeignKey("columnas.id", ondelete="CASCADE"), nullable=False)
    creador_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    columna = relationship("Columna", back_populates="tareas")
    creador = relationship("Usuario", back_populates="tareas_creadas")
    # Relación N:M con Usuarios
    asignados = relationship("Usuario", secondary=usuario_tarea, back_populates="tareas_asignadas")