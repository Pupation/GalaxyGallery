from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from main import config

engine = create_async_engine(config.db.sql)

db = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=engine)

async def get_sqldb() -> AsyncSession:
    async with db() as session:
        yield session