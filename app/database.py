import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cargamos las variables del archivo .env al entorno de Python
load_dotenv()

# Obtenemos la URL de la base de datos de las variables de entorno
# Si no la encuentra, podemos poner un valor por defecto o dejar que falle
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("¡La variable DATABASE_URL no está configurada en el archivo .env!")

# Crear el motor de la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Crear una clase "fábrica" de sesiones para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para que nuestros futuros modelos hereden de ella
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos en nuestras rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()