from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log_models import LogShema
from app.config import get_db
from app.crud.log_crud import get_logs_filtered, create_log

router = APIRouter()

@router.get("/logs")
async def get_log(level: str|None = None, session: AsyncSession = Depends(get_db)):
    return await get_logs_filtered(session, level=level)

@router.post("/add_log")
async def add_log(log: LogShema, session: AsyncSession = Depends(get_db)):
    save_log = await create_log(session, log)
    return {"status": "Лог добавлен", "id": save_log.id}
