import random
from aiogram import types
from database.models import UserLoteryBillets
import sqlalchemy as sa
from aiogram import Bot
from shared.bonus.bonus_giver import BonusGiver
from shared.bonus.promo_giver import PromoManager
from sqlalchemy.ext.asyncio import AsyncSession
from configs.bonus_config import BonusConfig
from configs import config


class Lotery:
    def __init__(self, config: BonusConfig):
        self.config = config

    @staticmethod
    async def give_billets(user_id: int, count: int, session: AsyncSession):
        result = await session.execute(sa.select(UserLoteryBillets).filter_by(user_id=user_id))
        user_lottery = result.scalar_one_or_none()

        if user_lottery:
            # Если запись существует, обновите её
            user_lottery.billets += count
        else:
            # Если записи нет, создайте новую
            user_lottery = UserLoteryBillets(user_id=user_id, billets=count)
            session.add(user_lottery)

        await session.commit()
        return True

    @staticmethod
    async def get_billets(user_id: int, session: AsyncSession):
        res = await session.execute(sa.select(UserLoteryBillets.billets).where(UserLoteryBillets.user_id == user_id))
        billets = res.scalar_one_or_none()
        return billets

    async def get_prize(self, user: types.User, session: AsyncSession, bot: Bot, logger):
        print('Получаем приз')
        billets = await self.get_billets(user_id=user.id, session=session)
        if billets <= 0:
            await bot.send_message(user.id, "😭 У вас нет билетов лотереи. Пополните баланс, чтобы получить их.")
            return
        await session.execute(sa.update(UserLoteryBillets).values(billets=UserLoteryBillets.billets-1,
                                                                  used_billets=UserLoteryBillets.used_billets+1)
                              .where(UserLoteryBillets.user_id == user.id))
        await session.commit()
        prize = self.random_prize()
        await self.attach_prize(user=user, prize=prize, session=session, bot=bot, logger=logger)

    async def attach_prize(self, user: types.User, prize: dict, session: AsyncSession, bot: Bot, logger):
        prize_info = self.config.PRIZE_CONFIG[prize]
        prize_type = prize_info['type']
        if prize_type == 'balance':
            amount = prize_info['amount']
            await BonusGiver(giver="lotery").give_balance_bonus(user_id=user.id, amount=amount, session=session)
            await bot.send_message(user.id, f'⭐️ Вы выиграли {amount}₽ на баланс')

        elif prize_type == 'package':
            days = prize_info['days']
            packet_id = prize_info['id']
            await BonusGiver(giver="lotery").give_packet_bonus(user_id=user.id, packet_id=packet_id, session=session)
            await bot.send_message(user.id,
                                   f'⭐️ Вы выиграли {prize} на {days} дней. Пакет начнет действовать с завтрашнего дня.')

        elif prize_type == 'balance_topup_percent':
            promo_id = prize_info.get('id')
            await PromoManager(giver="lotery").give_promo(user_id=user.id, promo_id=promo_id, session=session)
            await bot.send_message(user.id, f'⭐️ Вы выиграли {prize}, бонус будет применен при следующем пополнении.')

        elif prize_type == 'package_purchase_percent':
            promo_id = prize_info.get("id")
            await PromoManager(giver="lotery").give_promo(user_id=user.id, promo_id=promo_id, session=session)
            await bot.send_message(user.id, f'⭐️ Вы выиграли {prize}, свяжитесь с администратором - {config.admin_url}.')

        else:
            await bot.send_message(user.id, f'⭐️ Вы выиграли {prize}, свяжитесь с администратором - {config.admin_url}.')

        logger.info(f"Выиграл в лотерее - {prize}", extra={"user_id": user.id,
                                                           "username": user.username,
                                                           "action": "bonus"})

    def random_prize(self):
        weighted_items = [item for item, weight in self.config.PRIZE_WEIGHTS.items() for _ in range(weight)]
        return random.choice(weighted_items)
