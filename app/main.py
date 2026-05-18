from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # IMPORTACIÓN NUEVA

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# --- INICIO CONFIGURACIÓN CORS ---
# Esto permite que tu frontend en Render o en localhost se conecte sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En un entorno real se pone la URL exacta del frontend, aquí ponemos "*" para evitar problemas en la demo.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- FIN CONFIGURACIÓN CORS ---

app.include_router(api_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": settings.APP_NAME}