from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.schemas.log_schemas import Base

ASYNC_DATABASE_URL = "sqlite+aiosqlite:///test.db"

SYNC_DATABASE_URL = "sqlite:///test.db"

engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session