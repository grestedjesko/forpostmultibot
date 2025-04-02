from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncSession


# Данные для подключения к MySQL
DATABASE_URL = "mysql+aiomysql://j31863890_fpn:j3rBwqS1@mysql.a62e45e70f29.hosting.myjino.ru/j31863890_fpn"

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика сессий

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass
