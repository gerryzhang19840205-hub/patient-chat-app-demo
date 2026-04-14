import logging

from fastapi import FastAPI

from app.config import get_settings
from app.api.messages import router as messages_router
from app.services.conversation_store import init_db

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    description="Minimal FastAPI scaffold for the interview assignment.",
    version=settings.app_version,
)

init_db(settings.database_path)

app.include_router(messages_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"message": "Fasikl Patient Message Assistant API"}
