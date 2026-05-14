from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Esquema base con los datos comunes
class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol_id: int

# Esquema para CUANDO CREAMOS el usuario (requiere la contraseña)
class UsuarioCreate(UsuarioBase):
    password: str

# Esquema para la RESPUESTA de la API (lo que ve el frontend/Postman)
class UsuarioResponse(UsuarioBase):
    id: int
    creado_en: datetime

    # Esta configuración permite que Pydantic lea los modelos de SQLAlchemy
    class Config:
        from_attributes = True

# NUEVO: Esquema para ACTUALIZAR (hace que todos los campos sean opcionales)
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    rol_id: Optional[int] = None  # ¡ESTE ES EL PROBLEMA! Permitimos que el cliente envíe esto.

# Añade esto al final de schemas.py

class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    columna_id: int

class TareaCreate(TareaBase):
    creador_id: int  # Quien crea la tarea

class TareaResponse(TareaBase):
    id: int
    creador_id: int
    creado_en: datetime

    class Config:
        from_attributes = True