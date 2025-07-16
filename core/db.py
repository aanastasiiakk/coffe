from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings

engine = create_async_engine( settings.db_settings.sqlalchemy_database_url, echo=settings.db_settings.db_echo)


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

