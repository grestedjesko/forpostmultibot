import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import message_handlers, command_handlers, callback_handlers
from middlewares.database_middleware import DbSessionMiddleware
from middlewares.callback_logging import CallbackLoggingMiddleware
from middlewares.auth_user import RegistrationMiddleware
from middlewares.global_error_middleware import GlobalErrorMiddleware
from middlewares.album_middleware import AlbumMiddleware
from handlers import topup_handlers
from handlers import admin_handlers
from handlers import post_handlers
from poller import PacketPoller
from services.logs.logging_config import setup_logging
from config import  chat_map


# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def bot_main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    logger = setup_logging(bot, chat_map)
    dp["logger"] = logger

    # Устанавливаем middleware
    dp.update.middleware(GlobalErrorMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(RegistrationMiddleware())
    dp.message.middleware(AlbumMiddleware())
    dp.callback_query.middleware(CallbackLoggingMiddleware())

    # Подключение роутеров
    dp.include_router(message_handlers.message_router)
    dp.include_router(command_handlers.command_router)
    dp.include_router(callback_handlers.router)
    dp.include_router(topup_handlers.router)
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
    """Функция для запуска бота и PacketPoller параллельно"""
    # Запускаем PacketPoller как фоновую задачу
    packet_poller = PacketPoller()
    poller_task = asyncio.create_task(packet_poller.start_polling())

    try:
        await bot_main()  # Запускаем бота
    finally:
        # Корректно отменяем PacketPoller
        poller_task.cancel()
        print('task canceled')
        try:
            await poller_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    print('123')
    try:
        asyncio.run(start_services())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot and PacketPoller stopped.")
