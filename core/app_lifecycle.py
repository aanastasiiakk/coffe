import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.db import engine
from core.config import settings
from models.Base import Base


@asynccontextmanager
async def lifespan(app: FastAPI): #?
    try:
        conn = await asyncpg.connect(settings.db_settings.asyncpg_database_url)
        await conn.close()
        print("Подключение успешно!")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        raise RuntimeError("Не удалось подключиться")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) #DeclarativeBase

    yield
    await engine.dispose()
