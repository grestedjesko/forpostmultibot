# middlewares/config_loader.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from shared.bot_config import BotConfig


class ConfigLoaderMiddleware(BaseMiddleware):
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def __call__(self, handler, event: TelegramObject, data: dict):
        session = data.get("session")
        data["bot_config"] = await BotConfig.load(bot_id=self.bot_id, session=session)
        session.info["bot_id"] = self.bot_id
        return await handler(event, data)
