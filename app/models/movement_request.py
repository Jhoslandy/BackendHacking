from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SolicitudTareaMovimiento(Base):
    __tablename__ = "solicitudes_tarea_movimiento"

    id = Column(Integer, primary_key=True, index=True)
    tarea_id = Column(Integer, ForeignKey("tareas.id", ondelete="CASCADE"), nullable=False)
    solicitante_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    columna_origen_id = Column(Integer, ForeignKey("columnas.id", ondelete="CASCADE"), nullable=False)
    columna_destino_id = Column(Integer, ForeignKey("columnas.id", ondelete="CASCADE"), nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente")
    mensaje = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    resuelto_en = Column(DateTime(timezone=True))

    tarea = relationship("Tarea", back_populates="solicitudes_movimiento")
    solicitante = relationship("Usuario", back_populates="solicitudes_movimiento")
    columna_origen = relationship("Columna", foreign_keys=[columna_origen_id])
    columna_destino = relationship("Columna", foreign_keys=[columna_destino_id])
