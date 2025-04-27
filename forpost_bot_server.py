# main.py
import asyncio
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from database.base import async_session_factory
from middlewares.database_middleware import DbSessionMiddleware
from middlewares.chat_middleware import ChatMiddleWare
from middlewares.callback_logging import CallbackLoggingMiddleware
from middlewares.auth_user import RegistrationMiddleware
from middlewares.global_error_middleware import GlobalErrorMiddleware
from middlewares.album_middleware import AlbumMiddleware
from database.models import ForpostBotList, ForpostBotConfigs
from middlewares.config_loader import ConfigLoaderMiddleware
from middlewares.get_logger_middleware import LoggerMiddleware
from handlers.admin_handlers import create_admin_router
from handlers.callback_handlers import create_callback_router
from handlers.command_handlers import create_command_router
from handlers.deposit_handlers import create_deposit_router
from handlers.message_handlers import create_message_router
from handlers.post_handlers import create_post_router


from handlers import (message_handlers,
                      command_handlers,
                      callback_handlers,
                      admin_handlers,
                      deposit_handlers,
                      post_handlers)

app = FastAPI()
bots_pool = {}  # bot_id -> (Bot, Dispatcher)


async def load_bot_and_dispatcher(bot_id: int):
    async with async_session_factory() as session:
        bot_data = await session.get(ForpostBotList, bot_id)
        if not bot_data:
            raise HTTPException(status_code=404, detail="Bot not found")
        print(bot_data.token)
        bot = Bot(token=bot_data.token)
        dp = Dispatcher()

        # Подключение middleware с конфигами
        dp.update.middleware(DbSessionMiddleware())
        dp.update.middleware(ConfigLoaderMiddleware(bot_id=bot_id))
        dp.update.middleware(LoggerMiddleware())

        # Устанавливаем middleware
        #dp.update.middleware(GlobalErrorMiddleware())
        dp.message.middleware(ChatMiddleWare())
        dp.update.middleware(RegistrationMiddleware())
        dp.message.middleware(AlbumMiddleware())
        dp.callback_query.middleware(CallbackLoggingMiddleware())

        # Подключение роутеров
        dp.include_router(message_handlers.create_message_router())
        dp.include_router(command_handlers.create_command_router())
        dp.include_router(callback_handlers.create_callback_router())
        dp.include_router(deposit_handlers.create_deposit_router())
        dp.include_router(post_handlers.create_post_router())
        dp.include_router(admin_handlers.create_admin_router())

        bots_pool[bot_id] = (bot, dp)
        return bot, dp


@app.post("/webhook/{bot_id}")
async def webhook_handler(bot_id: int, request: Request):
    body = await request.body()
    update = Update.model_validate_json(body)
    print(bots_pool)
    if bot_id not in bots_pool:
        await load_bot_and_dispatcher(bot_id)
    bot, dp = bots_pool[bot_id]
    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        print('sosi')
    return {"ok": True}


