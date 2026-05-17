from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

app.include_router(api_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": settings.APP_NAME}
