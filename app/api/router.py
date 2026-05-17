from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.boards import router as boards_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(users_router, tags=["Usuarios"])
api_router.include_router(boards_router, tags=["Kanban"])
api_router.include_router(tasks_router, tags=["Tareas"])
