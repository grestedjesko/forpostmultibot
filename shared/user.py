from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import sqlalchemy as sa
from database.models import User, UserActivity, ArchivePackets, AutoPosts, Prices
from aiogram import types
from database.models.user_packets import UserPackets
from database.models.recommended_designers import RecommendedDesigners
from datetime import datetime
from database.models.packets import Packets
from datetime import timedelta
import math
import config
from src.keyboards import Keyboard
from sqlalchemy import func


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

    @staticmethod
    async def get_posting_ability(user_id: int, session: AsyncSession):
        """Получить информацию о возможности размещения объявления одним запросом."""
        price_stmt = sa.select(Prices.price).where(Prices.id==2).limit(1).scalar_subquery()

        stmt = sa.select(
            User.balance >= price_stmt,  # Достаточно ли баланса
            UserPackets.id.isnot(None),  # Есть ли активный пакет
        ).outerjoin(
            UserPackets, sa.and_(
                User.telegram_user_id == UserPackets.user_id,
                UserPackets.activated_at <= datetime.now(),
                UserPackets.ending_at > datetime.now()
            )
        ).outerjoin(
            Packets, UserPackets.type == Packets.id
        ).where(User.telegram_user_id == user_id)

        result = await session.execute(stmt)
        return result.first()  # Вернет (has_balance, has_active_packet)

    @staticmethod
    async def check_recommended_status(user_id: int, session: AsyncSession):
        stmt = sa.select(sa.exists().where(RecommendedDesigners.user_id == user_id, RecommendedDesigners.ending_at>=datetime.now()))
        result = await session.execute(stmt)
        return result.scalar()


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
    async def get_packet_ending_date(user_id: int, session: AsyncSession):
        result = await session.execute(
            sa.select(UserPackets.ending_at)
            .where(UserPackets.user_id == user_id,
            UserPackets.activated_at < datetime.now())
        )
        return result.first()

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
        today_limit = result.scalar()
        return today_limit

    @staticmethod
    async def deduct_today_limit(user_id: int, session: AsyncSession):
        """Обновление текущего лимита"""
        stmt = (sa.update(UserPackets)
                .values(today_posts=UserPackets.today_posts - 1, used_posts=UserPackets.used_posts + 1)
                .where(UserPackets.user_id == user_id)
        )
        result = await session.execute(stmt)
        await session.commit()
        return True

    @staticmethod
    async def get_user_packet(user_id: int, session: AsyncSession):
        """Получить пакет пользователя с дополнительными полями"""
        stmt = (
            sa.select(UserPackets, Packets.name, Packets.count_per_day)
            .join(Packets, UserPackets.type == Packets.id)
            .where(UserPackets.user_id == user_id, UserPackets.ending_at > datetime.now())
        )
        result = await session.execute(stmt)
        return result.first()  # Вернет кортеж (UserPackets, name, count_per_day)

    @staticmethod
    async def has_active_packet(user_id: int, session: AsyncSession):
        """Проверка, есть ли у пользователя активный пакет"""

        stmt = sa.select(UserPackets).where(
            UserPackets.user_id == user_id,
            UserPackets.ending_at > datetime.now(),
            UserPackets.activated_at <= datetime.now()
        )
        return await session.scalar(stmt) is not None

    @staticmethod
    async def assign_packet(user_id: int, packet_type: int, price: float, session: AsyncSession, bot: Bot):
        stmt = sa.select(Packets).filter_by(id=packet_type)
        result = await session.execute(stmt)
        packet = result.scalars().first()

        if not packet:
            raise ValueError("Указанный пакет не найден")

        now = datetime.now()
        next_activation = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Получаем текущий активный или неактивный пакет пользователя
        stmt = sa.select(UserPackets).filter_by(user_id=user_id).where(UserPackets.ending_at >= now)
        result = await session.execute(stmt)
        user_packet = result.scalars().one_or_none()

        if not user_packet:
            # Если пакета нет, создаем новый с активацией на следующий день в 00:00
            user_packet = UserPackets(
                user_id=user_id,
                type=packet_type,
                activated_at=next_activation,  # Устанавливаем на следующий день в 00:00
                ending_at=next_activation + timedelta(
                    days=math.ceil(packet.count_per_day * packet.period / packet.count_per_day)
                ),
                price=price,
                today_posts=0,
                used_posts=0,
                all_posts=packet.count_per_day * packet.period,
            )
            session.add(user_packet)
        else:
            # Если у пользователя уже есть пакет, продлеваем его
            await PacketManager._extend_packet(user_packet, packet)

        await session.commit()

        ending_at = datetime.strftime(user_packet.ending_at, '%d.%m.%Y')

        print(user_packet.activated_at)
        if user_packet.activated_at > now:
            txt = config.success_bought_packet % (packet.name, ending_at)
            await bot.send_message(chat_id=user_id,
                                   text=txt,
                                   parse_mode='html',
                                   reply_markup=Keyboard.activate_packet(packet_id= user_packet.id))

        else:
            txt = config.success_prolonged_packet % (packet.name, ending_at)
            await bot.send_message(chat_id=user_id,
                                   text=txt,
                                   parse_mode='html',
                                   reply_markup=Keyboard.create_auto())


    @staticmethod
    async def activate_packet(packet_id: int, session: AsyncSession):
        now = datetime.now()

        stmt = sa.select(UserPackets).filter_by(id=packet_id)
        result = await session.execute(stmt)
        user_packet = result.scalars().one_or_none()

        if not user_packet or user_packet.activated_at <= now:  # Уже активирован или отсутствует
            return False

        stmt = sa.select(Packets).filter_by(id=user_packet.type)
        result = await session.execute(stmt)
        packet = result.scalars().first()

        if not packet:
            return False

            # Активируем пакет (но не пересчитываем лимиты, так как они уже были учтены)
        user_packet.activated_at = now
        user_packet.today_posts = packet.count_per_day
        user_packet.all_posts -= packet.count_per_day  # Уменьшаем доступные посты на текущий день
        user_packet.ending_at -= timedelta(days=1)

        await session.commit()
        result = {'name': packet.name,
                  'ending_at': user_packet.ending_at}
        return result

    @staticmethod
    async def _extend_packet(user_packet, packet):
        """Продлевает пакет, но не активирует его, если он еще не активирован."""
        new_limit_per_day = packet.count_per_day
        additional_posts = packet.count_per_day * packet.period

        # Увеличиваем общее количество объявлений
        user_packet.all_posts += additional_posts

        # Пересчитываем дату окончания (но не трогаем `activated_at`)
        days_to_add = math.ceil(user_packet.all_posts / new_limit_per_day)
        user_packet.ending_at = datetime.now() + timedelta(days=days_to_add)


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

    @staticmethod
    async def revoke_packet(user_id: int, session: AsyncSession):
        """Окончание срока действия пакета для пользователя"""
        res = await session.execute(sa.select(UserPackets).where(UserPackets.user_id==user_id))
        user_packet = res.scalar()

        stmt = sa.insert(ArchivePackets).values(id=user_packet.id,
                                                user_id=user_packet.user_id,
                                                activated_at=user_packet.activated_at,
                                                ended_at=user_packet.ending_at,
                                                price=user_packet.price)

        await session.execute(stmt)

        stmt2 = sa.delete(UserPackets).where(UserPackets.id == user_packet.id)
        stmt3 = sa.delete(AutoPosts).where(AutoPosts.user_id == user_packet.user_id)
        await session.execute(stmt2)
        await session.execute(stmt3)
        await session.commit()

    @staticmethod
    async def get_count_per_day(user_id: int, session: AsyncSession):
        stmt = sa.select(Packets.count_per_day).join(UserPackets, Packets.id == UserPackets.type).where(
            UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
