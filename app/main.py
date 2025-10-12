import logging
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import logs
from app.config import init_db
from app.utils.logger import setup_logger

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)