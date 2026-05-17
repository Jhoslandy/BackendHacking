from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.constants import COLUMNAS_FIJAS
from app.core.permissions import es_superadmin, exigir_acceso_proyecto, exigir_admin_proyecto
from app.core.security import obtener_usuario_actual_debil
from app.db.deps import get_db
from app.models.associations import proyecto_miembros
from app.models.board import Columna, Tablero
from app.models.user import Usuario
from app.schemas.board import ColumnaResponse, TableroCreate, TableroResponse, TableroUpdate

router = APIRouter()


def obtener_tablero_o_404(db: Session, tablero_id: int) -> Tablero:
    tablero = db.query(Tablero).filter(Tablero.id == tablero_id).first()
    if not tablero:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    return tablero


def crear_columnas_fijas(db: Session, tablero_id: int) -> None:
    for nombre, orden in COLUMNAS_FIJAS:
        db.add(Columna(nombre=nombre, orden=orden, tablero_id=tablero_id))


@router.post("/proyectos/{proyecto_id}/tableros", response_model=TableroResponse)
def crear_tablero(
    proyecto_id: int,
    datos: TableroCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    exigir_admin_proyecto(db, proyecto_id, usuario)
    tablero = Tablero(nombre=datos.nombre, descripcion=datos.descripcion, proyecto_id=proyecto_id)
    db.add(tablero)
    db.flush()
    crear_columnas_fijas(db, tablero.id)
    db.commit()
    db.refresh(tablero)
    return tablero


@router.get("/proyectos/{proyecto_id}/tableros", response_model=list[TableroResponse])
def listar_tableros_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Tablero]:
    exigir_acceso_proyecto(db, proyecto_id, usuario)
    return db.query(Tablero).filter(Tablero.proyecto_id == proyecto_id).all()


@router.get("/tableros", response_model=list[TableroResponse])
def listar_tableros(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Tablero]:
    if es_superadmin(usuario):
        return db.query(Tablero).all()

    return (
        db.query(Tablero)
        .join(proyecto_miembros, proyecto_miembros.c.proyecto_id == Tablero.proyecto_id)
        .filter(proyecto_miembros.c.usuario_id == usuario.id)
        .all()
    )


@router.get("/tableros/{tablero_id}", response_model=TableroResponse)
def obtener_tablero(
    tablero_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    tablero = obtener_tablero_o_404(db, tablero_id)
    exigir_acceso_proyecto(db, tablero.proyecto_id, usuario)
    return tablero


@router.put("/tableros/{tablero_id}", response_model=TableroResponse)
def actualizar_tablero(
    tablero_id: int,
    datos: TableroUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> Tablero:
    tablero = obtener_tablero_o_404(db, tablero_id)
    exigir_admin_proyecto(db, tablero.proyecto_id, usuario)

    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(tablero, key, value)

    db.commit()
    db.refresh(tablero)
    return tablero


@router.get("/tableros/{tablero_id}/columnas", response_model=list[ColumnaResponse])
def listar_columnas(
    tablero_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual_debil),
) -> list[Columna]:
    tablero = obtener_tablero_o_404(db, tablero_id)
    exigir_acceso_proyecto(db, tablero.proyecto_id, usuario)
    return db.query(Columna).filter(Columna.tablero_id == tablero_id).order_by(Columna.orden).all()
