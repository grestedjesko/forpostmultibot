import asyncio
import logging
from aiogram import Bot, Dispatcher

import configs.config
from configs.config import BOT_TOKEN
from handlers import message_handlers, command_handlers, callback_handlers
from middlewares.database_middleware import DbSessionMiddleware
from middlewares.chat_middleware import ChatMiddleWare
from middlewares.callback_logging import CallbackLoggingMiddleware
from middlewares.auth_user import RegistrationMiddleware
from middlewares.global_error_middleware import GlobalErrorMiddleware
from middlewares.album_middleware import AlbumMiddleware
from handlers import deposit_handlers
from handlers import admin_handlers
from handlers.post import post_handlers
from database.base import Base, engine
from shared.stats import send_stats
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from shared.logs.logging_config import setup_logging
from configs.config import chat_map
from zoneinfo import ZoneInfo


async def scheduled_send_stats(bot):
    from datetime import datetime
    await send_stats(datetime.now().date(), bot)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def bot_main(bot):
    dp = Dispatcher()

    logger = setup_logging(bot, chat_map, configs.config.admin_chat_id)
    dp["logger"] = logger

    # Устанавливаем middleware
    dp.update.middleware(GlobalErrorMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.message.middleware(ChatMiddleWare())
    dp.update.middleware(RegistrationMiddleware())
    dp.message.middleware(AlbumMiddleware())
    dp.callback_query.middleware(CallbackLoggingMiddleware())

    # Подключение роутеров
    dp.include_router(message_handlers.message_router)
    dp.include_router(command_handlers.command_router)
    dp.include_router(callback_handlers.router)
    dp.include_router(deposit_handlers.router)
    dp.include_router(post_handlers.router)
    dp.include_router(admin_handlers.admin_router)

    # Удаляем старый вебхук
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Shutting down bot...")
        await bot.session.close()
        logging.info("Bot stopped.")


async def start_services():
    bot = Bot(token=BOT_TOKEN)
    await create_tables()

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_send_stats,
        trigger=CronTrigger(hour=23, minute=59),  # каждый день в 10:00
        args=[bot],
        name="Daily Stats Sender"
    )
    scheduler.start()

    await bot_main(bot)  # Запускаем бота


if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot and PacketPoller stopped.")

