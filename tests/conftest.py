import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

from app.config import get_db
from app.crud.log_crud import hash_password
from app.main import app
from app.schemas.log_schemas import Base
from app.schemas.log_schemas import User as DBUser

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    testing_session_local = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with testing_session_local() as session:
        await session.execute(text("DELETE FROM log"))
        await session.execute(text("DELETE FROM user"))
        await session.commit()
        yield session
        await session.execute(text("DELETE FROM log"))
        await session.execute(text("DELETE FROM user"))
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session):
    hashed_password = await hash_password("adminpass123")
    user = DBUser(username="admin", password=hashed_password)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
