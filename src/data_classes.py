from dataclasses import dataclass
from aiogram import Bot

@dataclass
class BotWrapper:
    id: int
    bot: Bot

    async def close(self):
        await self.bot.session.close()