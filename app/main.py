from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# --- CORRECCIÓN DE CORS ---
# Definimos exactamente quién puede conectarse
origins = [
    "http://localhost:5173",  # Tu frontend local (Vite)
    "https://kanban-kali-entes.onrender.com",  # Tu futuro frontend en Render
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Usamos la lista en lugar de "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- FIN CORRECCIÓN ---

app.include_router(api_router)

@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": settings.APP_NAME}