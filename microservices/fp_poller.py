import asyncio
import datetime
import logging
import sqlalchemy as sa
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from configs import config
from database.base import async_session_factory
from database.models import ForpostBotList, AutoPosts
from database.models.schedule import Schedule
from database.models.user_packets import UserPackets
from shared.bot_config import BotConfig
from shared.post.post import AutoPost
from shared.user_packet import PacketManager
from src.keyboards import Keyboard
from crypto.encrypt_token import decrypt_token
from src.data_classes import BotWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotManager:
    @staticmethod
    async def get_all_bots() -> list[BotWrapper]:
        async with async_session_factory() as session:
            bots = (await session.execute(sa.select(ForpostBotList))).scalars().all()
            answer = []
            for bot in bots:
                if not bot.token:
                    continue

                try:
                    token = decrypt_token(bot.token)
                    telegram_bot = Bot(token=token)
                    answer.append(BotWrapper(id=bot.id, bot=telegram_bot))
                except Exception as e:
                    print(e)
            return answer


class PostScheduler:
    @staticmethod
    async def process_posts():
        bots = await BotManager.get_all_bots()
        print(bots)
        for bot_wrapper in bots:
            try:
                await PostScheduler._post_for_bot(bot_wrapper)
            except Exception as e:
                logger.exception(f"Posting failed for bot {bot_wrapper.id}: {e}")
            finally:
                await bot_wrapper.close()  # Закрываем сессию

    @staticmethod
    async def _post_for_bot(bot_wrapper: BotWrapper):
        async with async_session_factory() as session:
            session.info["bot_id"] = bot_wrapper.id
            bot_config = await BotConfig.load(bot_id=bot_wrapper.id, session=session)
            now = datetime.datetime.now()

            stmt = sa.select(Schedule).where(
                Schedule.completed == 0,
                Schedule.time <= now,
                Schedule.bot_id == bot_wrapper.id
            )
            result = await session.execute(stmt)
            schedules = result.scalars().all()

            for post in schedules:
                has_active_packet = await PacketManager.has_active_packet(user_id=post.user_id, session=session)
                if not has_active_packet:
                    continue
                auto_post = await AutoPost.from_db(auto_post_id=post.scheduled_post_id,
                                                   session=session,
                                                   bot_config=bot_config)
                await auto_post.post(bot=bot_wrapper.bot, session=session)
                await session.execute(sa.update(Schedule).values(completed=1).where(Schedule.id == post.id))
            await session.commit()


class LimitManager:
    @staticmethod
    async def refresh_limits():
        bots = await BotManager.get_all_bots()
        for bot_wrapper in bots:
            try:
                print(bot_wrapper)
                await LimitManager._refresh_for_bot(bot_wrapper)
            except Exception as e:
                logger.exception(f"Limit refresh failed for bot {bot_wrapper.id}: {e}")
            finally:
                await bot_wrapper.close()  # Закрываем сессию

    @staticmethod
    async def _refresh_for_bot(bot_wrapper: BotWrapper):
        async with async_session_factory() as session:
            session.info["bot_id"] = bot_wrapper.id
            result = await session.execute(sa.select(UserPackets).where(UserPackets.bot_id == bot_wrapper.id))
            packets = result.scalars().all()
            now = datetime.datetime.now()

            for packet in packets:
                ending_at = packet.ending_at

                if ending_at <= now or (packet.all_posts == 0 and packet.today_posts == 0):
                    await PacketManager.revoke_packet(packet, session=session)
                    await bot_wrapper.bot.send_message(packet.user_id,
                                                       config.end_packet_text,
                                                       reply_markup=Keyboard.buy_packet_keyboard())
                    continue
                count_per_day = await PacketManager.get_count_per_day(user_id=packet.user_id, session=session)
                new_today_limit = min(packet.all_posts, count_per_day)
                new_all_limit = max(0, packet.all_posts - new_today_limit)

                await session.execute(
                    sa.update(UserPackets)
                    .values(today_posts=new_today_limit, all_posts=new_all_limit)
                    .where(UserPackets.id == packet.id)
                )

                auto_post_id = (await session.execute(
                    sa.select(AutoPosts.id).where(AutoPosts.activated == True,
                                                  AutoPosts.user_id == packet.user_id,
                                                  AutoPosts.bot_id == bot_wrapper.id)
                )).scalar_one_or_none()

                if auto_post_id:
                    await session.execute(
                        sa.update(Schedule).values(completed=0).where(Schedule.scheduled_post_id == auto_post_id)
                    )

            await session.commit()


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(PostScheduler.process_posts, CronTrigger(minute="*"))
    scheduler.add_job(LimitManager.refresh_limits, CronTrigger(hour=23, minute=59))
    scheduler.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(main())