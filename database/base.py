from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_HOST = os.getenv("DATABASE_HOST")

# Данные для подключения к MySQL
DATABASE_URL = f"mysql+aiomysql://{DATABASE_USER}:{DATABASE_PASSWORD}@/{DATABASE_NAME}"

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

