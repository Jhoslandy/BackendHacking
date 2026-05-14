from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import engine, get_db
import app.models as models
import app.schemas as schemas

# Esto crea las tablas en la base de datos si no existen 
# (Aunque ya las creaste en PgAdmin, es una buena práctica dejarlo)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Vulnerable - Grupo Kali-Entes",
    description="API para demostración de Ethical Hacking con Postman y Burp Suite"
)

# --- RUTAS DE USUARIOS ---

@app.post("/api/usuarios", response_model=schemas.UsuarioResponse)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Verificamos si el correo ya existe
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Creamos el objeto del modelo (Por ahora guardamos la contraseña en texto plano para agilizar las pruebas)
    nuevo_usuario = models.Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=usuario.password, 
        rol_id=usuario.rol_id
    )
    
    # Guardamos en la base de datos
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario) # Actualiza el objeto con el ID generado por PostgreSQL
    
    return nuevo_usuario

@app.get("/api/usuarios", response_model=list[schemas.UsuarioResponse])
def obtener_usuarios(db: Session = Depends(get_db)):
    # Obtiene todos los usuarios de la base de datos
    usuarios = db.query(models.Usuario).all()
    return usuarios

@app.put("/api/usuarios/{usuario_id}", response_model=schemas.UsuarioResponse)
def actualizar_usuario(usuario_id: int, datos_actualizacion: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    # 1. Buscamos al usuario en la base de datos
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Convertimos los datos recibidos a un diccionario (ignorando los nulos)
    datos_dict = datos_actualizacion.model_dump(exclude_unset=True)
    
    # --- INICIO DE VULNERABILIDAD: MASS ASSIGNMENT ---
    # Iteramos sobre todos los campos enviados y los sobreescribimos en la BD.
    # Un backend seguro filtraría campos críticos como 'rol_id', pero nosotros
    # confiamos ciegamente en lo que envía el usuario.
    for key, value in datos_dict.items():
        setattr(db_usuario, key, value)
    # --- FIN DE VULNERABILIDAD ---

    # 3. Guardamos los cambios
    db.commit()
    db.refresh(db_usuario)
    
    return db_usuario

# --- RUTAS DE TAREAS (TABLEROS KANBAN) ---

@app.post("/api/tareas", response_model=schemas.TareaResponse)
def crear_tarea(tarea: schemas.TareaCreate, db: Session = Depends(get_db)):
    # NOTA: Para no hacer el tutorial eterno creando Tableros y Columnas primero, 
    # insertaremos la tarea directamente confiando en el columna_id que mande el usuario.
    nueva_tarea = models.Tarea(
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        columna_id=tarea.columna_id,
        creador_id=tarea.creador_id
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea

@app.get("/api/tareas", response_model=list[schemas.TareaResponse])
def listar_tareas(db: Session = Depends(get_db)):
    return db.query(models.Tarea).all()

# --- INICIO DE VULNERABILIDAD: BOLA / IDOR ---
@app.delete("/api/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int, 
    x_user_id: int = Header(None, description="Simula el ID del usuario logueado en el Token"), 
    db: Session = Depends(get_db)
):
    # 1. Buscamos la tarea SOLO por el ID enviado en la URL
    tarea = db.query(models.Tarea).filter(models.Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # VULNERABILIDAD BOLA/IDOR:
    # Un backend seguro haría esto:
    # if tarea.creador_id != x_user_id and usuario_rol != "Admin":
    #     raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta tarea")
    #
    # PERO NOSOTROS NO VALIDAMOS NADA. Confiamos ciegamente.

    # 2. Borramos la tarea directamente
    db.delete(tarea)
    db.commit()
    
    return {"status": "success", "mensaje": f"La tarea {tarea_id} fue eliminada exitosamente"}
# --- FIN DE VULNERABILIDAD ---