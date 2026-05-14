from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de conexión a PostgreSQL
# Formato: postgresql://usuario:contraseña@localhost:5432/nombre_bd
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123456@localhost:5432/bd_web"

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