import asyncio
import datetime
import logging
from dataclasses import dataclass
import sqlalchemy as sa
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from configs.funnel_config import FunnelConfig
from database.base import async_session_factory
from database.models import (
    ForpostBotList,
    FunnelUserAction,
    FunnelScheduledMessage,
    UserFunnelStatus,
)
from shared.bonus.promo_manager import PromoManager
from aiogram.types import InlineKeyboardMarkup


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BotWrapper:
    id: int
    bot: Bot

    async def close(self):
        await self.bot.session.close()



class BotManager:
    @staticmethod
    async def get_all_bots() -> list[BotWrapper]:
        async with async_session_factory() as session:
            bots = (await session.execute(sa.select(ForpostBotList))).scalars().all()
            answer = []
            for bot in bots:
                try:
                    telegram_bot = Bot(token=bot.token)
                    answer.append(BotWrapper(id=bot.id, bot=telegram_bot))
                except Exception as e:
                    print(e)
            return answer


class FunnelManager:
    @staticmethod
    async def process(bot_wrapper: BotWrapper):
        async with async_session_factory() as session:
            session.info["bot_id"] = bot_wrapper.id
            now = datetime.datetime.now()
            config = FunnelConfig.funnels

            await FunnelManager._deactivate_funnels(session, config)
            await FunnelManager._activate_funnels(now, session, config)
            await FunnelManager._process_messages(now, session, config, bot_wrapper.bot)

    @staticmethod
    async def _deactivate_funnels(session, config):
        bot_id = session.info["bot_id"]
        stmt = sa.select(UserFunnelStatus).where(UserFunnelStatus.active == True, UserFunnelStatus.bot_id == bot_id)
        active_funnels = (await session.execute(stmt)).scalars().all()

        for funnel in active_funnels:
            cancel_conditions = config.get(funnel.funnel_id, {}).get("cancel_conditions", [])
            stmt = sa.select(FunnelUserAction).where(
                FunnelUserAction.user_id == funnel.user_id,
                FunnelUserAction.timestamp >= funnel.activated_at,
                FunnelUserAction.action.in_(cancel_conditions),
                FunnelUserAction.bot_id == bot_id
            )
            if (await session.execute(stmt)).scalars().first():
                funnel.active = False
                await session.execute(
                    sa.update(FunnelScheduledMessage)
                    .where(FunnelScheduledMessage.funnel_base_id == funnel.id,
                           FunnelScheduledMessage.bot_id == bot_id)
                    .values(active=False)
                )
        await session.commit()

    @staticmethod
    async def _activate_funnels(now, session, config):
        print('activating')
        bot_id = session.info["bot_id"]
        for funnel_id, funnel_cfg in config.items():
            trigger = funnel_cfg.get("trigger", {})
            trigger_type = trigger.get("condition")
            trigger_details = trigger.get("details")

            stmt = sa.select(FunnelUserAction).where(
                FunnelUserAction.action == trigger_type,
                FunnelUserAction.used == False,
                FunnelUserAction.bot_id == bot_id
            )
            if trigger_details:
                stmt = stmt.where(FunnelUserAction.details.in_(trigger_details.split(',')))

            user_actions = (await session.execute(stmt)).scalars().all()

            for action in user_actions:
                print(action)
                cancel_stmt = sa.select(FunnelUserAction).where(
                    FunnelUserAction.user_id == action.user_id,
                    FunnelUserAction.timestamp > action.timestamp,
                    FunnelUserAction.action.in_(funnel_cfg.get("cancel_conditions", [])),
                    FunnelUserAction.bot_id == bot_id
                )
                if (await session.execute(cancel_stmt)).scalars().first():
                    print('canceled')
                    continue

                user_funnel = await session.execute(sa.select(UserFunnelStatus).where(
                    UserFunnelStatus.user_id == action.user_id,
                    UserFunnelStatus.funnel_id == funnel_id,
                    UserFunnelStatus.bot_id == bot_id
                ))
                existing = user_funnel.scalars().first()
                if existing and (existing.active or existing.ended and not funnel_cfg.get("infinity")):
                    print('already sended')
                    continue

                if existing and funnel_cfg.get("infinity"):
                    existing.active = True
                    existing.ended = False
                    FunnelManager._schedule_messages(existing.id, funnel_cfg, now, session)
                    continue

                action.used = True
                new_funnel = UserFunnelStatus(
                    bot_id=bot_id,
                    user_id=action.user_id,
                    funnel_id=funnel_id,
                    details=action.details,
                    status=funnel_cfg.get("start_step")
                )
                session.add(new_funnel)
                await session.flush()
                FunnelManager._schedule_messages(new_funnel.id, funnel_cfg, now, session)
        await session.commit()

    @staticmethod
    def _schedule_messages(funnel_id, funnel_cfg, now, session):
        bot_id = session.info["bot_id"]
        send_time = now
        for msg_id, message in funnel_cfg["messages"].items():
            send_time += message.get("delay")
            session.add(FunnelScheduledMessage(
                bot_id=bot_id,
                funnel_base_id=funnel_id,
                message_id=msg_id,
                text=message["text"],
                send_time=send_time,
                active=True
            ))

    @staticmethod
    async def _process_messages(now, session, config, bot: Bot):
        bot_id = session.info["bot_id"]
        stmt = sa.select(FunnelScheduledMessage).where(
            FunnelScheduledMessage.active == True,
            FunnelScheduledMessage.sent == False,
            FunnelScheduledMessage.send_time <= now,
            FunnelScheduledMessage.bot_id == bot_id
        )
        messages = (await session.execute(stmt)).scalars().all()

        for msg in messages:
            funnel = await session.get(UserFunnelStatus, msg.funnel_base_id)
            if not funnel or not funnel.active:
                continue

            funnel_cfg = config.get(funnel.funnel_id, {})
            message_cfg = funnel_cfg.get("messages", {}).get(msg.message_id, {})
            if not message_cfg:
                continue

            if msg.message_id != funnel.status:
                continue

            action = message_cfg.get("action")
            if action:
                await PromoManager().give_promo(
                    user_id=funnel.user_id, promo_id=action, session=session, giver='funnel'
                )

            keyboard_cfg = message_cfg.get("keyboard")
            if keyboard_cfg:
                for row in keyboard_cfg:
                    for btn in row:
                        if btn.url and "%s" in btn.url:
                            btn.url = btn.url % funnel.details
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_cfg)
            else:
                reply_markup = None

            try:
                await bot.send_message(funnel.user_id, msg.text, reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Failed to send message to {funnel.user_id}: {e}")

            msg.sent = True
            next_step = message_cfg.get("next_step")
            if next_step:
                funnel.status = next_step
            else:
                funnel.ended = True
                await session.execute(
                    sa.update(FunnelScheduledMessage)
                    .where(FunnelScheduledMessage.funnel_base_id == funnel.id, FunnelScheduledMessage.bot_id == bot_id)
                    .values(active=False)
                )

        await session.commit()


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_funnels, CronTrigger(minute="*"))
    scheduler.start()

    await run_funnels()

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


async def run_funnels():
    bots = await BotManager.get_all_bots()
    for bot_wrapper in bots:
        try:
            await FunnelManager.process(bot_wrapper)
        except Exception as e:
            logger.exception(f"Error in funnel processing for bot {bot_wrapper.id}: {e}")
        finally:
            await bot_wrapper.close()


if __name__ == "__main__":
    asyncio.run(main())

