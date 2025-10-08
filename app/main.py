from fastapi import FastAPI
from app.api import logs
from app.config import init_db
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Log Analyzer", lifespan=lifespan)

app.include_router(logs.router)