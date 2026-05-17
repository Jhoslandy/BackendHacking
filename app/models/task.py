from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.associations import usuario_tarea


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha_vencimiento = Column(DateTime(timezone=True))
    columna_id = Column(Integer, ForeignKey("columnas.id", ondelete="CASCADE"), nullable=False)
    creador_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    columna = relationship("Columna", back_populates="tareas")
    creador = relationship("Usuario", back_populates="tareas_creadas")
    asignados = relationship("Usuario", secondary=usuario_tarea, back_populates="tareas_asignadas")
    solicitudes_movimiento = relationship(
        "SolicitudTareaMovimiento",
        back_populates="tarea",
        cascade="all, delete-orphan",
    )

    @property
    def proyecto_id(self) -> int | None:
        return self.columna.tablero.proyecto_id if self.columna and self.columna.tablero else None
