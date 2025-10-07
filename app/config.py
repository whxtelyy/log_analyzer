from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.schemas.log_schemas import Base


DATABASE_URL = 'sqlite+aiosqlite:///test.db'

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session() as session:
        yield session
