from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log_models import LogShema, UserLogin, UserRegister
from app.config import get_db
from app.crud.log_crud import get_logs_filtered, create_log, create_user, get_user_by_username, verify_password_hash
from app.core.security import create_access_token, get_current_user
from app.schemas.log_schemas import User

router = APIRouter()

@router.get("/logs")
async def get_log(level: str|None = None, session: AsyncSession = Depends(get_db),
                  current_user: User = Depends(get_current_user)
):
    print(f"Пользователь {current_user.username} запрашивает логи")
    return await get_logs_filtered(session, level=level)

@router.post("/add_log")
async def add_log(log: LogShema, session: AsyncSession = Depends(get_db)):
    save_log = await create_log(session, log)
    return {"status": "Лог добавлен", "id": save_log.id}

@router.post("/auth/register")
async def register_user(log: UserRegister, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(session, log.username)
    if user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    save_user = await create_user(session, log)
    print(f"Регистрация пользователя: {log.username}")
    return {"status": "Пользователь зарегистрирован", "id": save_user.id}

@router.post("/auth/login")
async def login_user(log: UserLogin, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(session, log.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not await verify_password_hash(log.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id, username=user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }