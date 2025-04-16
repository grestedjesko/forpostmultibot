import datetime
import asyncio
import sqlalchemy as sa

from configs import config
from database.models.shcedule import Schedule
from database.models.user_packets import UserPackets
from shared.post.post import AutoPost
from shared.user_packet import PacketManager
from database.base import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from configs.config import BOT_TOKEN
from src.keyboards import Keyboard


bot = Bot(token=BOT_TOKEN)


class PacketPoller:
    @staticmethod
    async def start_polling():
        print('post polling started')
        while True:
            try:
                async with async_session_factory() as session:
                    if datetime.datetime.now().strftime('%H:%M') == '18:39':
                        await PacketPoller.refresh_limits(session=session)

                    await PacketPoller.auto_posting(session=session)
                await asyncio.sleep(60)
            except Exception as e:
                print(e)

    @staticmethod
    async def refresh_limits(session: AsyncSession):
        r = await session.execute(sa.select(UserPackets))
        user_packets = r.scalars().all()
        for packet in user_packets:
            if packet.ending_at <= datetime.datetime.now() or (packet.all_posts == 0 and packet.today_posts == 0):
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

            await bot.send_message(config.admin_chat_id, f'Лимит {packet.user_id} обновлен')

    @staticmethod
    async def auto_posting(session: AsyncSession):
        current_time = datetime.datetime.now()

        stmt = sa.select(Schedule).where(Schedule.completed == 0, Schedule.time <= current_time)
        r = await session.execute(stmt)
        schedule = r.scalars().all()
        print(schedule)
        for post in schedule:
            auto_post = await AutoPost.from_db(auto_post_id=post.scheduled_post_id,
                                               session=session)

            await auto_post.post(bot=bot, session=session)

            await session.execute(sa.update(Schedule).values(completed=1).where(Schedule.id == post.id))
            await session.commit()


if __name__ == "__main__":
    packet_poller = PacketPoller()
    poller_task = asyncio.create_task(packet_poller.start_polling())