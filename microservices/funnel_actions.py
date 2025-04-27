import datetime
import sqlalchemy as sa
from database.models import FunnelUserAction, UserFunnelStatus, FunnelScheduledMessage
from database.models.funnel_user_actions import FunnelUserActionsType
from configs.funnel_config import FunnelConfig
import asyncio
from database.base import async_session_factory
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from configs.config import BOT_TOKEN
from aiogram.types import InlineKeyboardMarkup
from shared.bonus.promo_manager import PromoManager
import logging
from zoneinfo import ZoneInfo


bot = Bot(token=BOT_TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FunnelActions:
    @staticmethod
    async def save(user_id: int, action: str, session: AsyncSession, details: str | None = None):
        bot_id = session.info["bot_id"]
        action = FunnelUserAction(bot_id=bot_id, user_id=user_id, action=action, details=details)
        session.add(action)
        await session.commit()

    async def deactivate_canceled_funnels(self, session, funnels_config):
        stmt = sa.select(UserFunnelStatus).where(UserFunnelStatus.active == True)
        res = await session.execute(stmt)
        active_funnels = res.scalars().all()
        for active_funnel in active_funnels:
            logger.info(f"Проверяем активную воронку {active_funnel.id}")
            cancel_conditions = funnels_config.get(active_funnel.funnel_id).get("cancel_conditions")

            res = await session.execute(sa.select(FunnelUserAction)
                                        .where(FunnelUserAction.action.in_(cancel_conditions),
                                               FunnelUserAction.user_id == active_funnel.user_id,
                                               FunnelUserAction.timestamp >= active_funnel.activated_at))
            cancel_actions = res.scalars().all()
            if any(cancel_actions):
                logger.info(f"Нашли cancel_trigger, отменяем воронку")
                active_funnel.active = False
                await session.execute(sa.update(FunnelScheduledMessage)
                                      .values(active=False)
                                      .where(FunnelScheduledMessage.funnel_base_id == active_funnel.id)
                                      )
        await session.commit()

    async def activate_funnels_by_trigger(self, now, session):
        logger.info("Активация воронок по триггеру")
        funnels_config = FunnelConfig.funnels
        for funnel_id, funnel_config in funnels_config.items():
            logger.info(f"Ищем триггеры на воронку {funnel_id}")
            trigger = funnel_config.get('trigger')
            trigger_condition = trigger.get('condition')
            trigger_details = trigger.get('details')

            cancel_conditions = funnel_config.get('cancel_conditions')
            messages_config = funnel_config.get('messages')
            infinity = funnel_config.get('infinity')

            if trigger_condition == FunnelUserActionsType.PACKET_PURCHASED and trigger_details:
                ids = trigger_details.split(',')
                stmt = sa.select(FunnelUserAction).where(
                    FunnelUserAction.action == trigger_condition,
                    FunnelUserAction.used == False,
                    FunnelUserAction.details.in_(ids)
                ).order_by(FunnelUserAction.timestamp)
                res = await session.execute(stmt)
                user_actions = res.scalars().all()
            elif trigger_condition == FunnelUserActionsType.POSTED and trigger_details:
                fua = FunnelUserAction
                # Оконная функция: считаем сколько POSTED у пользователя (used = False)
                count_over_user = sa.func.count().over(
                    partition_by=fua.user_id
                ).label("action_count")
                # Оконная функция: номер строки по убыванию времени
                row_number_over_time = sa.func.row_number().over(
                    partition_by=fua.user_id,
                    order_by=sa.desc(fua.timestamp)
                ).label("rn")
                stmt = (
                    sa.select(fua, count_over_user, row_number_over_time)
                    .where(
                        fua.action == FunnelUserActionsType.POSTED,
                        fua.used == False
                    )
                ).subquery()
                # Выбираем только те, где у пользователя ровно 5 действий и это последнее
                final_stmt = sa.select(stmt).where(
                    stmt.c.action_count == int(trigger_details),
                    stmt.c.rn == 1
                )
                results = await session.execute(final_stmt)
                user_actions = results.mappings().all()

            else:
                stmt = sa.select(FunnelUserAction).where(FunnelUserAction.action == trigger_condition,
                                                         FunnelUserAction.used == False)
                res = await session.execute(stmt)
                user_actions = res.scalars().all()

            if not user_actions:
                continue

            logger.info(f"Нашел триггеры {user_actions}")

            for user_action in user_actions:
                stmt = (sa.select(FunnelUserAction)
                        .where(FunnelUserAction.user_id == user_action.user_id,
                               FunnelUserAction.action.in_(cancel_conditions),
                               FunnelUserAction.timestamp > user_action.timestamp))
                cancel_action = (await session.execute(stmt)).scalars().all()
                if any(cancel_action):
                    logger.info(f"Нашел кансел триггер после триггера, пропускаем")
                    continue

                stmt = sa.select(UserFunnelStatus).where(UserFunnelStatus.user_id == user_action.user_id,
                                                         UserFunnelStatus.funnel_id == funnel_id)
                funnel = (await session.execute(stmt)).scalars().first()
                if funnel:
                    logger.info("Нашли в истории воронку для этого пользователя")
                    if (funnel.ended and not infinity) or funnel.active:
                        logger.info("Воронка закончена или активна, пропускаем")
                        continue
                    if (not funnel.active and not funnel.ended) or (infinity and not funnel.active):
                        logger.info("Воронка не активна и не закончена или бесконечная")
                        funnel.active = True
                        funnel.ended = True
                        stmt = ((sa.select(FunnelScheduledMessage))
                                .where(FunnelScheduledMessage.funnel_base_id == funnel.id))
                        scheduled_messages = (await session.execute(stmt)).scalars().all()
                        send_time = now
                        for scheduled_message in scheduled_messages:
                            message_config = messages_config.get(scheduled_message.message_id)
                            if scheduled_message.sent:
                                continue
                            send_time += message_config.get('delay')
                            scheduled_message.active = True
                            scheduled_message.send_time = send_time
                        logger.info("Обновили сообщения воронок")
                    continue

                user_action.used = True
                stmt = UserFunnelStatus(user_id=user_action.user_id,
                                        funnel_id=funnel_id,
                                        details=user_action.details,
                                        status=funnel_config.get('start_step'))
                session.add(stmt)
                await session.flush()  # Получаем ID до коммита
                funnel_base_id = stmt.id  # Теперь ID доступен

                send_time = now
                for message_id, message in funnel_config.get('messages').items():
                    message_delay = message.get('delay')
                    send_time = send_time + message_delay
                    message_text = message.get('text')
                    session.add(FunnelScheduledMessage(
                        funnel_base_id=funnel_base_id,
                        message_id=message_id,
                        text=message_text,
                        send_time=send_time
                    ))
                logger.info(f"Создали новую воронку {funnel_base_id}")
            await session.commit()

    async def process_messages(self, now, session, funnels_config):
        stmt = sa.select(FunnelScheduledMessage).where(FunnelScheduledMessage.active == True,
                                                       FunnelScheduledMessage.sent == False,
                                                       FunnelScheduledMessage.send_time <= now)
        res = await session.execute(stmt)
        scheduled_messages = res.scalars().all()

        logger.info(f"Получили запланированные сообщения {scheduled_messages}")
        for scheduled_message in scheduled_messages:
            funnel_id = scheduled_message.funnel_base_id

            stmt = sa.select(UserFunnelStatus).where(UserFunnelStatus.id == funnel_id,
                                                     UserFunnelStatus.active == True,
                                                     UserFunnelStatus.ended == False)
            funnel = (await session.execute(stmt)).scalar_one_or_none()
            if not funnel:
                continue

            if scheduled_message.message_id != funnel.status:
                logger.info(f"Статус обрабатываемого сообщения не равен шагу воронки, пропускаем")
                continue

            message_config = funnels_config.get(funnel.funnel_id).get("messages").get(scheduled_message.message_id)
            action = message_config.get('action')
            print(action)
            if action:
                logger.info(f"Выдаем пользователю {funnel.user_id} скидку {action}")
                await PromoManager().give_promo(user_id=funnel.user_id, promo_id=action, session=session, giver='funnel')

            keyboard = message_config.get('keyboard')
            if keyboard:
                for row in keyboard:
                    for btn in row:
                        if btn.url and "%s" in btn.url:
                            btn.url = btn.url % funnel.details

                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
            try:
                await bot.send_message(funnel.user_id, scheduled_message.text, reply_markup=keyboard)
                logger.info(f"Отправили сообщение {funnel.user_id} ")
            except Exception as e:
                print(e)
            scheduled_message.sent = True
            next_step = message_config.get('next_step')
            if next_step:
                funnel.status = next_step
                logger.info(f"Воронка {funnel.id} {funnel.user_id}  переведена на следующий этап")
            else:
                funnel.ended = True
                await session.execute(sa.update(FunnelScheduledMessage)
                                      .values(active=False)
                                      .where(FunnelScheduledMessage.funnel_base_id == funnel.id))
                logger.info(f"Следующего этапа нет, воронка {funnel.id} завершена")
        await session.commit()

    async def polling(self, session):
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        funnels_config = FunnelConfig.funnels
        await self.deactivate_canceled_funnels(session=session, funnels_config=funnels_config)
        await self.activate_funnels_by_trigger(now=now, session=session)
        await self.process_messages(now=now, session=session, funnels_config=funnels_config)


async def start_polling():
    funnel_actions = FunnelActions()
    while True:
        async with async_session_factory() as session:
            await funnel_actions.polling(session=session)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(start_polling())
