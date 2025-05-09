from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from shared.logs.logging_config import setup_logging


class LoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data["bot"]
        session = data["session"]

        bot_config = data.get("bot_config", {})
        admin_id = bot_config.admin_ids
        admin_id = admin_id[0]

        logs_chat_id = bot_config.chat_map
        logger = setup_logging(bot, logs_chat_id)
        data["logger"] = logger

        return await handler(event, data)
