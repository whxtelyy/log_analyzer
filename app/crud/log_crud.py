from app.config import AsyncSession
from app.models.log_models import LogShema, UserRegister
from app.schemas.log_schemas import LogDB, User
from sqlalchemy import select, func, delete
from datetime import datetime
import json
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password(password: str) -> str:
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
    logger.debug(f"В {new_log.timestamp} был создан новый лог с уровнем {new_log.level}")
    return new_log

async def get_logs_filtered(
        session: AsyncSession,
        level: str|None = None,
        service: str|None = None,
        start_time: datetime|None = None,
        end_time:  datetime|None = None,
        limit: int = 100,
        offset: int = 0
):

    count_query = select(func.count(LogDB.id))
    query = select(LogDB)

    if level is not None:
        count_query = count_query.where(LogDB.level == level)
        query = query.where(LogDB.level == level)
    if service is not None:
        count_query = count_query.where(LogDB.service == service)
        query = query.where(LogDB.service == service)
    if start_time is not None:
        count_query = count_query.where(LogDB.timestamp >= start_time)
        query = query.where(LogDB.timestamp >= start_time)
    if end_time is not None:
        count_query = count_query.where(LogDB.timestamp <= end_time)
        query = query.where(LogDB.timestamp <= end_time)

    total_result = await session.execute(count_query)
    total = total_result.scalar()

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    logs = result.scalars().all()

    logger.info(
        f"Передано {len(logs)} логов (всего по фильтру: {total}). "
        f"Фильтры: level={level}, service={service}, "
        f"start={start_time.isoformat() if start_time else 'None'}, "
        f"end={end_time.isoformat() if end_time else 'None'}, "
        f"limit={limit}, offset={offset}"
    )

    return logs, total

async def get_logs_stats(
        session: AsyncSession,
        start_time: datetime|None = None,
        end_time: datetime|None = None,
        service: str|None = None,
        group_by: str|None = None,
):
    query = select()
    query = query.add_columns(func.count().label("count"))

    filters = []
    if start_time:
        filters.append(LogDB.timestamp >= start_time)
    if end_time:
        filters.append(LogDB.timestamp <= end_time)
    if service:
        filters.append(LogDB.service == service)
    if filters:
        query = query.where(*filters)

    if group_by == "hour":
        time_interval = func.strftime("%Y-%m-%dT%H:00:00Z", LogDB.timestamp)
        query = query.add_columns(time_interval.label("time_interval"))
        query = query.group_by(time_interval)
    elif group_by == "day":
        time_interval = func.strftime("%Y-%m-%dT00:00Z", LogDB.timestamp)
        query = query.add_columns(time_interval.label("time_interval"))
        query = query.group_by(time_interval)
    elif group_by == "level":
        query = query.add_columns(LogDB.level)
        query = query.group_by(LogDB.level)
    elif group_by == "service":
        query = query.add_columns(LogDB.service)
        query = query.group_by(LogDB.service)

    result = await session.execute(query)
    rows = result.fetchall()

    stats = []
    for row in rows:
        entry = {"count": row.count}

        if group_by == 'hour' or group_by == 'day':
            entry["time_interval"] = row.time_interval
        elif group_by == 'level':
            entry["level"] = row.level
        elif group_by == 'service':
            entry["service"] = row.service

        stats.append(entry)

    return stats

async def create_user(session: AsyncSession, user_data: UserRegister):
    hashed_password = await hash_password(user_data.password)
    new_user = User(username=user_data.username, password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.info(f"Новый пользователь {new_user.username} был успешно создан")
    return new_user

async def get_user_by_username(session: AsyncSession, username: str):
    sel = select(User).where(User.username == username)
    result = await session.execute(sel)
    user = result.scalars().first()
    if user:
        logger.debug(f"Пользователь '{username}' был успешно найден (id: {user.id})")
    else:
        logger.debug(f"Пользователь '{username}' не найден в базе данных")
    return user

async def get_user_by_id(session: AsyncSession, user_id:int):
    sel = select(User).where(User.id == user_id)
    result = await session.execute(sel)
    user = result.scalars().first()
    if user:
        logger.debug(f"Пользователь {user_id} был успешно найден")
    else:
        logger.debug(f"Пользователь {user_id} не найден в базе данных")
    return user

async def delete_old_logs(session: AsyncSession, before: datetime):
    sel = delete(LogDB).where(LogDB.timestamp < before)

    result = await session.execute(sel)
    await session.commit()

    deleted_count = result.rowcount
    logger.info(f"Удалено {deleted_count} логов, созданных до {before.isoformat()}")
    return deleted_count
