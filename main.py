import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.auth.router import router as app_router
from app.logger import setup_logging
from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)
    logger.info("Starting up Ecommerce API")
    yield
    logger.info("Shutting down Ecommerce API")


app = FastAPI(lifespan=lifespan)

app.include_router(app_router)
