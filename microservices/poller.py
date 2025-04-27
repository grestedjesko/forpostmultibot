import datetime
import asyncio
import sqlalchemy as sa

from configs import config
from database.models.schedule import Schedule
from database.models.user_packets import UserPackets
from shared.post.post import AutoPost
from shared.user_packet import PacketManager
from database.base import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from configs.config import BOT_TOKEN
from src.keyboards import Keyboard
from zoneinfo import ZoneInfo
from database.models import AutoPosts
from shared.bot_config import BotConfig

bot = Bot(token=BOT_TOKEN)


class PacketPoller:
    @staticmethod
    async def start_polling():
        print('post polling started')
        while True:
            try:
                async with async_session_factory() as session:
                    if datetime.datetime.now(ZoneInfo("Europe/Moscow")).strftime('%H:%M') == '23:59':
                        await PacketPoller.refresh_limits(session=session)

                    await PacketPoller.auto_posting(session=session)
                await asyncio.sleep(60)
            except Exception as e:
                print(e)

    @staticmethod
    async def refresh_limits(session: AsyncSession):
        print('Обновление лимитов')
        r = await session.execute(sa.select(UserPackets))
        user_packets = r.scalars().all()
        for packet in user_packets:
            ending_at = packet.ending_at

            if ending_at.tzinfo is None:
                ending_at = ending_at.replace(tzinfo=ZoneInfo("Europe/Moscow"))

            if ending_at <= datetime.datetime.now(ZoneInfo("Europe/Moscow")) or (packet.all_posts == 0 and
                                                                                 packet.today_posts == 0):
                await PacketManager.revoke_packet(packet, session=session)
                await bot.send_message(packet.user_id, config.end_packet_text,
                                       reply_markup=Keyboard.buy_packet_keyboard())
                continue

            count_per_day = await PacketManager.get_count_per_day(user_id=packet.user_id, session=session)

            if packet.all_posts >= count_per_day:
                new_today_limit = count_per_day
                new_all_limit = packet.all_posts - new_today_limit
            else:
                new_today_limit = packet.all_posts
                new_all_limit = 0

            await session.execute(sa.update(UserPackets)
                                  .values(today_posts=new_today_limit, all_posts=new_all_limit)
                                  .where(UserPackets.id == packet.id))
            await session.commit()

            stmt = sa.select(AutoPosts.id).where(AutoPosts.activated == True,
                                                 AutoPosts.user_id == packet.user_id)
            auto_post_id = (await session.execute(stmt)).scalar_one_or_none()

            await session.execute(sa.update(Schedule).values(completed=0)
                                  .where(Schedule.scheduled_post_id == auto_post_id))

            await bot.send_message(config.admin_chat_id, f'Лимит {packet.user_id} обновлен')

    @staticmethod
    async def auto_posting(session: AsyncSession):
        current_time = datetime.datetime.now(ZoneInfo("Europe/Moscow"))

        stmt = sa.select(Schedule).where(Schedule.completed == 0, Schedule.time <= current_time)
        r = await session.execute(stmt)
        schedule = r.scalars().all()

        for post in schedule:
            bot_config = BotConfig.load(post.bot_id, session=session)

            auto_post = await AutoPost.from_db(auto_post_id=post.scheduled_post_id,
                                               session=session,
                                               bot_config=bot_config)

            await auto_post.post(bot=bot, session=session)

            await session.execute(sa.update(Schedule).values(completed=1).where(Schedule.id == post.id))
            await session.commit()


if __name__ == "__main__":
    packet_poller = PacketPoller()
    poller_task = asyncio.run(packet_poller.start_polling())