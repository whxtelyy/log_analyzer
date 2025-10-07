from app.config import AsyncSession
from app.models.log_models import LogShema
from app.schemas.log_schemas import LogDB
from sqlalchemy import select
import json

async def create_log(session: AsyncSession, log_schema: LogShema):
    new_log = LogDB(timestamp=log_schema.timestamp, level=log_schema.level,
                    service = log_schema.service , message=log_schema.message,
                    metadata_json=json.dumps(log_schema.metadata) if log_schema.metadata else None)

    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)
    return new_log

async def get_logs(session: AsyncSession):
    sel = select(LogDB)
    result = await session.execute(sel)
    logs = result.scalars().all()
    return logs

async def get_logs_filtered(session: AsyncSession, level:str|None = None):
    sel = select(LogDB)
    if level is not None:
        sel = sel.where(LogDB.level == level)
    result = await session.execute(sel)
    return result.scalars().all()
