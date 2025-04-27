# middlewares/config_loader.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.future import select
from database.models import ForpostBotConfigs
import json


class ConfigLoaderMiddleware(BaseMiddleware):
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def __call__(self, handler, event: TelegramObject, data: dict):
        session = data.get("session")

        stmt = select(ForpostBotConfigs).where(ForpostBotConfigs.bot_id == self.bot_id)
        result = await session.execute(stmt)
        configs = result.scalars().all()

        config_dict = {}
        for item in configs:
            raw_value = item.config_value
            if not raw_value:  # None или пустая строка
                print(f"[!] Пустое значение для ключа: {item.config_name}")
                continue
            try:
                config_dict[item.config_name] = json.loads(raw_value)
            except json.JSONDecodeError as e:
                print(f"[!] Ошибка парсинга JSON у '{item.config_name}': {e}")
        data["bot_config"] = config_dict

        session.info["bot_id"] = self.bot_id

        return await handler(event, data)
