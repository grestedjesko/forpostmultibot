from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from shared.logs.logging_config import setup_logging


class LoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data["bot"]
        session = data["session"]

        bot_config = data.get("bot_config", {})
        admin_id = bot_config.get('admin_id')
        chat_map = bot_config.get("chat_map", {})

        logs_chat_id = chat_map.get("logs_chat_id")
        logger = setup_logging(bot, logs_chat_id, admin_id)
        data["logger"] = logger

        return await handler(event, data)
