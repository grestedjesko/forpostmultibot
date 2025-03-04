from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from sqlalchemy import func
from database.models import User, UserActivity
from aiogram import types
from database.models.user_packets import UserPackets
from datetime import datetime, UTC
from database.models.packets import Packets
from datetime import timedelta
from sqlalchemy.exc import NoResultFound


class UserManager:
    @staticmethod
    async def register(user: types.User, session: AsyncSession):
        """Регистрация пользователя"""
        query = sa.insert(User).values(
            telegram_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def authenticate(user: types.User, session: AsyncSession):
        """Авторизация пользователя"""
        query = sa.select(User).where(User.telegram_user_id == user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return True
        else:
            return False

    @staticmethod
    async def update_activity(user_id: int, session: AsyncSession):
        """Обновление активности"""

        today = func.current_date()

        # Проверяем, есть ли запись для данного пользователя и текущей даты
        stmt = sa.select(UserActivity).where(UserActivity.user_id == user_id, UserActivity.date == today)
        result = await session.execute(stmt)
        activity = result.scalars().first()

        if activity:
            # Если запись существует, увеличиваем счетчик и обновляем время активности
            activity.count_activities += 1
            activity.Last_Activity_Time = func.now()
        else:
            # Если записи нет, создаем новую
            activity = UserActivity(user_id=user_id, date=today, count_activities=1, last_activity_time=func.now())
            session.add(activity)

        await session.commit()


class BalanceManager:
    @staticmethod
    async def get_balance(user_id: int, session: AsyncSession):
        """Получение баланса пользователя"""
        query = sa.select(User.balance).where(User.telegram_user_id == user_id)
        result = await session.execute(query)
        balance = result.scalar_one_or_none()
        return balance

    @staticmethod
    async def deposit(amount: float, user_id: int, session: AsyncSession):
        """Пополнение баланса пользователя"""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        query = sa.update(User).values(balance=User.balance + amount).where(User.telegram_user_id == user_id)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def deduct(user_id: int, amount: float, session: AsyncSession):
        """Списание с баланса пользователя"""
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")

        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        new_balance = balance - amount

        if new_balance < 0:
            return False

        stmt = sa.update(User).where(User.telegram_user_id == user_id).values(balance=new_balance)
        try:
            await session.execute(stmt)
            return True
        except:
            return False


class PacketManager:
    @staticmethod
    async def get_limit(user_id: int, session: AsyncSession):
        """Получение лимитов пользователя"""
        stmt = sa.select(UserPackets.today_posts, UserPackets.all_posts).where(UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        today_limit = result.first()
        return today_limit

    @staticmethod
    async def get_today_limit(user_id: int, session: AsyncSession):
        """Получение лимитов пользователя"""
        stmt = sa.select(UserPackets.today_posts).where(UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        today_limit = result.first()
        return today_limit

    @staticmethod
    async def deduct_today_limit(user_id: int, session: AsyncSession):
        """Обновление текущего лимита"""
        stmt = sa.update(UserPackets).values(today_posts=UserPackets.today_posts-1).where(UserPackets.user_id==user_id)
        result = await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def has_active_packet(user_id: int, session: AsyncSession):
        """Проверка, есть ли у пользователя активный пакет"""

        stmt = sa.select(UserPackets).where(
            UserPackets.user_id == user_id,
            UserPackets.ending_at > datetime.now()
        )
        return await session.scalar(stmt) is not None

    @staticmethod
    async def assign_packet(user_id: int, packet_type: int, price: int, session: AsyncSession):
        stmt = sa.select(Packets).filter_by(id=packet_type)
        result = await session.execute(stmt)
        packet = result.scalars().first()

        if not packet:
            raise ValueError("Указанный пакет не найден")

        now = datetime.now()

        try:
            stmt = sa.select(UserPackets).filter_by(user_id=user_id, type=packet_type)
            result = await session.execute(stmt)
            user_packet = result.scalars().one()

            user_packet.ending_at += timedelta(days=packet.period)
            user_packet.all_posts += packet.count_per_day * packet.period

        except NoResultFound:
            user_packet = UserPackets(
                user_id=user_id,
                status=True,
                type=packet_type,
                activated_at=now,
                ending_at=now + timedelta(days=packet.period),
                price=price,
                today_posts=0,
                used_posts=0,
                all_posts=packet.count_per_day * packet.period,
                active=True
            )
            session.add(user_packet)
        await session.commit()
        return "Пакет продлен" if 'user_packet' in locals() else "Пакет выдан"

    @staticmethod
    async def refresh_limits(user_id: int, session: AsyncSession):
        count_per_day = await PacketManager.get_count_per_day(user_id=user_id, session=session)

        stmt = sa.select(UserPackets.all_posts).where(UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        all_limit = result.scalar_one_or_none()

        if all_limit == 0:
            print('Пакет завершен')
            return

        if all_limit < count_per_day:
            today_limit = all_limit
            all_limit = 0
        else:
            today_limit = count_per_day
            all_limit = all_limit - today_limit

        stmt = sa.update(UserPackets).values(all_posts=all_limit, today_posts=today_limit)
        await session.execute(stmt)
        await session.commit()

    async def revoke_packet(self):
        """Окончание срока действия пакета для пользователя"""
        pass

    @staticmethod
    async def get_count_per_day(user_id: int, session: AsyncSession):
        stmt = sa.select(Packets.count_per_day).join(UserPackets, Packets.id == UserPackets.type).where(
            UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


