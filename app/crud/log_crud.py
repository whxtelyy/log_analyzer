from app.config import AsyncSession
from app.models.log_models import LogShema, UserRegister
from app.schemas.log_schemas import LogDB, User
from sqlalchemy import select
import json
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

async def verify_password_hash(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

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

async def create_user(session: AsyncSession, user_data: UserRegister):
    hashed_password = await hash_password_hash(user_data.password)
    new_user = User(username=user_data.username, password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def get_user_by_username(session: AsyncSession, username):
    sel = select(User).where(User.username == username)
    result = await session.execute(sel)
    return result.scalars().first()

async def get_user_by_id(session: AsyncSession, user_id:int):
    sel = select(User).where(User.id == user_id)
    result = await session.execute(sel)
    return result.scalars().first()