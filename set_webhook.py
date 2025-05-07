import asyncio
from aiogram import Bot
from database.base import async_session_factory
from database.models import ForpostBotList
import sqlalchemy as sa


async def setup_all_webhooks():
    async with async_session_factory() as session:
        bots = (await session.execute(
            sa.select(ForpostBotList)
        )).scalars().all()

        for bot in bots:
            if bot.token == '0':
                continue
            print(bot.token)
            telegram_bot = Bot(token=bot.token)
            url = f"https://0b9zu7-185-103-24-123.ru.tuna.am/webhook/{bot.id}"
            await telegram_bot.set_webhook(url)
            await telegram_bot.session.close()
            print(f"Webhook set for bot {bot.name} -> {url}")


if __name__ == "__main__":
    asyncio.run(setup_all_webhooks())
