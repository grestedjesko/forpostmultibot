import asyncio
from aiogram import Bot
from database.base import async_session_factory
from database.models import ForpostBotList
import sqlalchemy as sa
from crypto.encrypt_token import decrypt_token

async def setup_all_webhooks():
    async with async_session_factory() as session:
        bots = (await session.execute(
            sa.select(ForpostBotList).where(ForpostBotList.id == 1)
        )).scalars().all()

        for bot in bots:
            if bot.token == '0':
                continue
            decrypted_token = decrypt_token(bot.token)
            telegram_bot = Bot(token="5131133862:AAHW1ZTZ4ExQxk84MXkdcBS_dQdu_UD9pJE")
            url = f"https://api2.forpost.me/webhook/{bot.id}"
            await telegram_bot.set_webhook(url)
            await telegram_bot.session.close()
            print(f"Webhook set for bot {bot.name} -> {url}")


if __name__ == "__main__":
    asyncio.run(setup_all_webhooks())
