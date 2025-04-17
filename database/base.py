from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncSession

# Данные для подключения к MySQL
DATABASE_URL = "mysql+aiomysql://j98603797_fp:U6bsdxhmsrG@mysql.bc9753bc1538.hosting.myjino.ru/j98603797_fp"

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL,
                             echo=False,
                             pool_pre_ping=True,  # добавьте это
                             pool_recycle=3600,  # пересоздавать соединения раз в час (рекомендуется)
                             connect_args={"init_command": "SET time_zone = '+03:00'"}
                             )

# Фабрика сессий

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass
