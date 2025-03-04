from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from sqlalchemy import func
from database.models import User, UserActivity
from aiogram import types
from database.models.prices import OneTimePacket
from database.models.user_packets import UserPackets
from datetime import datetime
from database.models.packets import Packets
from datetime import timedelta
from sqlalchemy.exc import NoResultFound


class UserManager:
    def __init__(self):
        pass

    async def register_user(self, user: types.User, session: AsyncSession):
        """Регистрация пользователя"""
        query = sa.insert(User).values(
            telegram_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        await session.execute(query)
        await session.commit()

    async def authenticate_user(self, user: types.User, session: AsyncSession):
        """Авторизация пользователя"""
        query = sa.select(User).where(User.telegram_user_id == user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return True
        else:
            return False

    async def update_activity(self, user_id: int, session: AsyncSession):
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

    async def fetch_balance(self, user_id: int, session: AsyncSession):
        """Получение баланса пользователя"""
        query = sa.select(User.balance).where(User.telegram_user_id == user_id)
        result = await session.execute(query)
        balance = result.scalar_one_or_none()
        return balance

    async def deposit_funds(self, amount: float, user_id: int, session: AsyncSession):
        """Пополнение баланса пользователя"""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        query = sa.update(User).values(balance=User.balance+amount).where(User.telegram_user_id == user_id)
        await session.execute(query)
        await session.commit()

    async def withdraw_funds(self, user_id: int, amount: float, session: AsyncSession):
        """Списание с баланса пользователя"""
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")

        balance = await self.fetch_balance(user_id=user_id, session=session)
        new_balance = balance - amount

        if new_balance < 0:
            return False

        stmt = sa.update(User).where(User.telegram_user_id == user_id).values(balance=new_balance)
        try:
            await session.execute(stmt)
            return True
        except:
            return False

    async def has_active_packet(self, user_id: int, session: AsyncSession):
        """Проверка, есть ли у пользователя активный пакет"""

        stmt = sa.select(UserPackets).where(
            UserPackets.user_id == user_id,
            UserPackets.ending_at > datetime.utcnow()
        )
        return await session.scalar(stmt) is not None

    def assign_packet(self, user_id: int, packet_type: int, price: int, session: AsyncSession):
        # Получаем информацию о пакете
        packet = session.query(Packets).filter_by(id=packet_type).first()
        if not packet:
            raise ValueError("Указанный пакет не найден")

        now = datetime.utcnow()
        try:
            # Проверяем, есть ли уже активный пакет у пользователя
            user_packet = session.query(UserPackets).filter_by(user_id=user_id, type=packet_type).one()
            # Обновляем срок окончания
            user_packet.ending_at += timedelta(days=packet.period)
            user_packet.all_posts += packet.count_per_day * packet.period
            session.commit()
            return "Пакет продлен"
        except NoResultFound:
            # Создаём новую запись, если её нет
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
            session.commit()
            return "Пакет выдан"

    async def refresh_limits(self, user_id: int, session: AsyncSession):
        count_per_day = UserPacket.get_count_per_day(user_id=user_id)

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



class UserPacket:
    def __init__(self):
        pass

    async def assign(self, user_id: int):
        """Выдача пакета пользователю"""
        pass

    async def revoke(self, user_id: int):
        """Окончание срока действия пакета для пользователя"""
        pass

    @staticmethod
    async def get_count_per_day(user_id: int, session: AsyncSession):
        stmt = sa.select(Packets.count_per_day).join(UserPackets, Packets.id == UserPackets.type).where(UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()