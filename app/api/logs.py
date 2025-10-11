from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log_models import LogShema, UserLogin, UserRegister
from app.config import get_db
from app.crud.log_crud import (get_logs_filtered, create_log, create_user, get_user_by_username,
                               verify_password_hash, get_logs_stats, delete_old_logs)
from app.core.security import create_access_token, get_current_user
from app.schemas.log_schemas import User
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/logs")
async def get_log(
        level: str|None = None,
        start_time: str|None = None,
        end_time: str|None = None,
        service : str|None = None,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    start_date = None
    end_date = None

    try:
        if start_time:
            date = start_time.replace("Z", "+00:00")
            start_date = datetime.fromisoformat(date)
        if end_time:
            date = end_time.replace("Z", "+00:00")
            end_date = datetime.fromisoformat(date)
    except ValueError:
        logger.error("Использован неверный формат даты в /logs")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты. Используйте ISO 8601 (например, '2025-05-14T12:00:00Z')."
        )

    logger.debug(f"Пользователь {current_user.username} запрашивает логи")
    db_logs, total = await get_logs_filtered(
        session,
        level=level,
        service=service,
        start_time=start_date,
        end_time=end_date,
        limit=limit,
        offset=offset
    )

    logs = []
    for log in db_logs:
        metadata = None
        if log.metadata_json:
            try:
                metadata = json.loads(log.metadata_json)
            except json.JSONDecodeError:
                logger.warning(f"Некорректный JSON в логе ID={log.id}: {log.metadata_json!r}")
                metadata = None
        logs.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() + "Z",
            "level": log.level,
            "service": log.service,
            "message": log.message,
            "metadata": metadata
        })

    logger.info(f"Пользователь {current_user.username} получил {len(logs)} записей (всего по фильтру: {total})")
    return {"logs": logs, "total": total}

@router.get("/stats")
async def get_stats(
        session: AsyncSession = Depends(get_db),
        start_time: str|None = None,
        end_time: str|None = None,
        service: str|None = None,
        group_by: str|None = Query(None,  regex="^(hour|day|level|service)$"),
        current_user: User = Depends(get_current_user)
):
    logger.debug(f"Пользователь '{current_user.username}' запрашивает статистику (group_by={group_by})")

    start_date = None
    end_date = None

    try:
        if start_time:
            date = start_time.replace("Z", "+00:00")
            start_date = datetime.fromisoformat(date)
        if end_time:
            date = end_time.replace("Z", "+00:00")
            end_date = datetime.fromisoformat(date)
    except ValueError:
        logger.error("Использован неверный формат даты в /stats")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты. Используйте ISO 8601."
        )

    try:
        stats = await get_logs_stats(
            session,
            start_time=start_date,
            end_time=end_date,
            service=service,
            group_by=group_by,
        )
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты. Используйте ISO 8601."
        )
    logger.info(f"Статистика получена: {len(stats)} групп")
    return {"stats": stats}

@router.post("/add_log")
async def add_log(log: LogShema, session: AsyncSession = Depends(get_db)):
    save_log = await create_log(session, log)
    logger.debug(f"Лог успешно добавлен. 'id лога': {save_log.id}")
    return {"status": "Лог добавлен", "id": save_log.id}

@router.post("/auth/register")
async def register_user(log: UserRegister, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(session, log.username)
    if user:
        logger.warning(f"Попытка регистрации существующего пользователя: {log.username}")
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    save_user = await create_user(session, log)
    logger.info(f"Пользователь {log.username} успешно зарегистрирован")
    return {"status": "Пользователь зарегистрирован", "id": save_user.id}

@router.post("/auth/login")
async def login_user(log: UserLogin, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(session, log.username)
    if not user:
        logger.warning(f"Попытка входа несуществующего пользователя: {log.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not await verify_password_hash(log.password, user.password):
        logger.warning(f"Неверный пароль для пользователя: {log.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id, username=user.username)
    logger.debug(f"Сгенерирован токен для пользователя: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/logs")
async def delete_logs(
        before: str,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.username != "admin":
        logger.warning(f"Пользователь '{current_user.username}' попытался удалить логи без прав")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может удалять логи"
        )

    try:
        if before.endswith("Z"):
            date_str = before.replace("Z", "+00:00")
        else:
            date_str = before
        before_date = datetime.fromisoformat(date_str)
    except ValueError:
        logger.error(f"Неверный формат даты 'before': {before}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты 'before'. Используйте ISO 8601 (например, '2025-05-14T00:00:00Z')."
        )
    logger.debug(f"Администратор {current_user.username} запрашивает удаление логов до {before}")

    deleted_count = await delete_old_logs(session, before_date)

    logger.info(f"Удалено {deleted_count} логов по запросу администратора {current_user.username}")
    return {"deleted": deleted_count}
