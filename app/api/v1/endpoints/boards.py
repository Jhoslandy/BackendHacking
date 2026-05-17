from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.board import Columna, Tablero
from app.models.user import Usuario
from app.schemas.board import (
    ColumnaCreate,
    ColumnaResponse,
    ColumnaUpdate,
    TableroCreate,
    TableroResponse,
    TableroUpdate,
)

router = APIRouter()


@router.post("/tableros", response_model=TableroResponse)
def crear_tablero(
    tablero: TableroCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    # Vulnerabilidad intencional: se ignora usuario.id y se acepta propietario_id del body.
    _ = usuario
    nuevo_tablero = Tablero(**tablero.model_dump())
    db.add(nuevo_tablero)
    db.commit()
    db.refresh(nuevo_tablero)
    return nuevo_tablero


@router.get("/tableros", response_model=list[TableroResponse])
def listar_tableros(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Tablero]:
    # Vulnerabilidad intencional: cualquier usuario autenticado ve todos los tableros.
    _ = usuario
    return db.query(Tablero).all()


@router.get("/tableros/{tablero_id}", response_model=TableroResponse)
def obtener_tablero(
    tablero_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    _ = usuario
    tablero = db.query(Tablero).filter(Tablero.id == tablero_id).first()
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    return tablero


@router.put("/tableros/{tablero_id}", response_model=TableroResponse)
def actualizar_tablero(
    tablero_id: int,
    datos: TableroUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    _ = usuario
    tablero = db.query(Tablero).filter(Tablero.id == tablero_id).first()
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")

    # Vulnerabilidad intencional: permite cambiar propietario_id por asignacion masiva.
    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(tablero, key, value)

    db.commit()
    db.refresh(tablero)
    return tablero


@router.post("/columnas", response_model=ColumnaResponse)
def crear_columna(
    columna: ColumnaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Columna:
    _ = usuario
    nueva_columna = Columna(**columna.model_dump())
    db.add(nueva_columna)
    db.commit()
    db.refresh(nueva_columna)
    return nueva_columna


@router.get("/tableros/{tablero_id}/columnas", response_model=list[ColumnaResponse])
def listar_columnas(
    tablero_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Columna]:
    _ = usuario
    return db.query(Columna).filter(Columna.tablero_id == tablero_id).all()


@router.put("/columnas/{columna_id}", response_model=ColumnaResponse)
def actualizar_columna(
    columna_id: int,
    datos: ColumnaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Columna:
    _ = usuario
    columna = db.query(Columna).filter(Columna.id == columna_id).first()
    if not columna:
        raise HTTPException(status_code=404, detail="Columna no encontrada")

    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(columna, key, value)

    db.commit()
    db.refresh(columna)
    return columna
