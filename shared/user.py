from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from database.models import User, UserActivity, Prices, UserPackets, Packets
from aiogram import types
from database.models.recommended_designers import RecommendedDesigners
from datetime import datetime
from sqlalchemy import func
from zoneinfo import ZoneInfo


class UserManager:
    @staticmethod
    async def register(user: types.User, session: AsyncSession):
        """Регистрация пользователя"""
        bot_id = session.info["bot_id"]
        query = sa.insert(User).values(bot_id=bot_id, telegram_user_id=user.id, first_name=user.first_name, last_name=user.last_name, username=user.username)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def authenticate(user: types.User, session: AsyncSession):
        """Авторизация пользователя"""
        bot_id = session.info["bot_id"]
        query = sa.select(User).where(User.telegram_user_id == user.id, User.bot_id == bot_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return True
        else:
            return False

    @staticmethod
    async def update_activity(user_id: int, session: AsyncSession):
        """Обновление активности"""
        bot_id = session.info["bot_id"]
        today = func.current_date()

        # Проверяем, есть ли запись для данного пользователя и текущей даты
        stmt = sa.select(UserActivity).where(UserActivity.user_id == user_id, UserActivity.date == today, UserActivity.bot_id == bot_id)
        result = await session.execute(stmt)
        activity = result.scalars().first()

        if activity:
            # Если запись существует, увеличиваем счетчик и обновляем время активности
            activity.count_activities += 1
            activity.Last_Activity_Time = func.now()
        else:
            # Если записи нет, создаем новую
            activity = UserActivity(bot_id=bot_id, user_id=user_id, date=today, count_activities=1, last_activity_time=func.now())
            session.add(activity)

        await session.commit()

    @staticmethod
    async def get_posting_ability(user_id: int, session: AsyncSession):
        """Получить информацию о возможности размещения объявления одним запросом."""
        bot_id = session.info["bot_id"]
        now = datetime.now()

        price_stmt = sa.select(Prices.price).where(
            sa.and_(
                Prices.id == 1,
                Prices.bot_id == bot_id
            )
        ).limit(1).scalar_subquery()

        stmt = sa.select(
            User.balance >= price_stmt,
            UserPackets.id.isnot(None),
        ).outerjoin(
            UserPackets, sa.and_(
                User.telegram_user_id == UserPackets.user_id,
                UserPackets.bot_id == bot_id,
                UserPackets.activated_at <= now,
                UserPackets.ending_at > now
            )
        ).outerjoin(
            Packets, sa.and_(
                UserPackets.type == Packets.id,
                Packets.bot_id == bot_id
            )
        ).where(
            sa.and_(
                User.telegram_user_id == user_id,
                User.bot_id == bot_id
            )
        )

        result = await session.execute(stmt)
        return result.first()


    @staticmethod
    async def check_recommended_status(user_id: int, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.select(sa.exists().where(RecommendedDesigners.user_id == user_id,
                                           RecommendedDesigners.ending_at >= datetime.now(),
                                           RecommendedDesigners.bot_id == bot_id))
        result = await session.execute(stmt)
        return result.scalar()


class BalanceManager:
    @staticmethod
    async def get_balance(user_id: int, session: AsyncSession):
        """Получение баланса пользователя"""
        bot_id = session.info["bot_id"]
        query = sa.select(User.balance).where(User.telegram_user_id == user_id, User.bot_id == bot_id)
        result = await session.execute(query)
        balance = result.scalar_one_or_none()
        return balance

    @staticmethod
    async def deposit(amount: float, user_id: int, session: AsyncSession):
        """Пополнение баланса пользователя"""
        bot_id = session.info["bot_id"]
        query = sa.update(User).values(balance=User.balance + amount).where(User.telegram_user_id == user_id,
                                                                            User.bot_id == bot_id)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def deduct(user_id: int, amount: float, session: AsyncSession, logger):
        """Списание с баланса пользователя"""
        bot_id = session.info["bot_id"]
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")

        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        new_balance = balance - amount
        if new_balance < 0:
            return False

        stmt = sa.update(User).where(User.telegram_user_id == user_id, User.bot_id == bot_id).values(balance=new_balance)
        try:
            await session.execute(stmt)
            await session.commit()

            logger.info(f"Списано {amount} с баланса",
                        extra={'user_id': user_id,
                               'action': 'balance_deduct'})

            return True
        except Exception as e:
            logger.info(f"{e}", extra={'user_id': user_id,
                                       'action': 'error'})
            return False