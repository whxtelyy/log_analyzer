import logging
import os
import time

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_db
from app.crud.log_crud import get_user_by_id

logger = logging.getLogger(__name__)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.error("SECRET_KEY не задан в .env файле")
    raise ValueError("SECRET_KEY не задан в .env файле")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(user_id: int, username: str, expires_delta: int = 3600) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_delta,
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    logger.info(f"Сгенерирован токен для пользователя {username} (id: {user_id})")
    return encoded_jwt


async def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        logger.debug("Токен успешно декодирован")
        return payload

    except ExpiredSignatureError:
        logger.error("Срок действия токена истёк")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        logger.error("Недействительный токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
):
    payload = await decode_access_token(token)

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        logger.error(f"user_id в токене не является целым числом")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(session, user_id)
    if user is None:
        logger.error(f"Пользователь с ID {user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Аутентифицирован пользователь: {user.username} (ID: {user_id})")
    return user