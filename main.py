import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import message_handlers, command_handlers, callback_handlers
from middlewares.database_middleware import DbSessionMiddleware
from middlewares.auth_user import RegistrationMiddleware
from middlewares.album_middleware import AlbumMiddleware
from handlers import topup_handlers
from handlers import post_handlers


# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Устанавливаем middleware для работы с БД
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(RegistrationMiddleware())
    dp.message.middleware(AlbumMiddleware())

    # Подключение роутеров
    dp.include_router(message_handlers.message_router)
    dp.include_router(command_handlers.command_router)
    dp.include_router(callback_handlers.router)
    dp.include_router(topup_handlers.router)
    dp.include_router(post_handlers.router)

    # Удаляем старый вебхук и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
