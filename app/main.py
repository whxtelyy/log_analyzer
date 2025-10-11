from fastapi import FastAPI
from app.api import logs
from app.config import init_db
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.utils.logger import setup_logger
import logging

setup_logger()
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Началась инициализация базы данных")
    await init_db()
    logger.info("База данных успешно инициализирована")
    yield

    logger.info("Приложение завершает работу")

app = FastAPI(title="Log Analyzer", lifespan=lifespan)
app.include_router(logs.router)

logger.info("Приложение Log Analyzer запущено и готово принимать запросы")