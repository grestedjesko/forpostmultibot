from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from database.models import ArchivePackets, AutoPosts, UserPackets, Packets
from datetime import datetime
from datetime import timedelta
import math
from microservices.funnel_actions import FunnelActions
from database.models.funnel_user_actions import FunnelUserActionsType
from zoneinfo import ZoneInfo


class AssignedPacketInfo:
    def __init__(self, activated_at, packet_name, ending_at, user_packet_id):
        self.activated_at = activated_at
        self.packet_name = packet_name
        self.ending_at = ending_at
        self.user_packet_id = user_packet_id


class PacketManager:
    @staticmethod
    async def get_packet_ending_date(user_id: int, session: AsyncSession):
        result = await session.execute(
            sa.select(UserPackets.ending_at)
            .where(UserPackets.user_id == user_id,
                   UserPackets.activated_at < datetime.now(ZoneInfo("Europe/Moscow")))
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
                .where(UserPackets.user_id == user_id))
        await session.execute(stmt)
        await session.commit()
        return True

    @staticmethod
    async def get_user_packet(user_id: int, session: AsyncSession):
        """Получить пакет пользователя с дополнительными полями"""
        stmt = (
            sa.select(UserPackets, Packets.name, Packets.count_per_day)
            .join(Packets, UserPackets.type == Packets.id)
            .where(UserPackets.user_id == user_id, UserPackets.ending_at > datetime.now(ZoneInfo("Europe/Moscow")))
        )
        result = await session.execute(stmt)
        return result.first()  # Вернет кортеж (UserPackets, name, count_per_day)

    @staticmethod
    async def has_active_packet(user_id: int, session: AsyncSession):
        """Проверка, есть ли у пользователя активный пакет"""

        stmt = sa.select(UserPackets).where(
            UserPackets.user_id == user_id,
            UserPackets.ending_at > datetime.now(ZoneInfo("Europe/Moscow")),
            UserPackets.activated_at <= datetime.now(ZoneInfo("Europe/Moscow"))
        )
        return await session.scalar(stmt) is not None

    @staticmethod
    async def get_packet_by_id(packet_type: int, session: AsyncSession):
        stmt = sa.select(Packets).filter_by(id=packet_type)
        result = await session.execute(stmt)
        packet = result.scalars().first()
        return packet

    @staticmethod
    async def assign_packet(user_id: int, packet_type: int, price: float, session: AsyncSession):
        packet = await PacketManager.get_packet_by_id(packet_type=packet_type, session=session)
        if not packet:
            raise ValueError("Указанный пакет не найден")
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        next_activation = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        user_packet = await PacketManager.get_user_packet(user_id=user_id, session=session)
        if not user_packet:
            user_packet = UserPackets(
                user_id=user_id,
                type=packet_type,
                activated_at=next_activation,
                ending_at=next_activation + timedelta(
                    days=math.ceil(packet.count_per_day * packet.period / packet.count_per_day)
                ),
                price=price,
                today_posts=packet.count_per_day,
                used_posts=0,
                all_posts=packet.count_per_day * (packet.period-1),
            )
            session.add(user_packet)
        else:
            user_packet = user_packet[0]
            new_limit_per_day = packet.count_per_day
            additional_posts = packet.count_per_day * packet.period
            user_packet.type = packet_type
            user_packet.price += price
            await PacketManager.extend_packet(user_packet=user_packet,
                                              new_limit_per_day=new_limit_per_day,
                                              additional_posts=additional_posts)
        await session.commit()

        ending_at = datetime.strftime(user_packet.ending_at, '%d.%m.%Y')
        return AssignedPacketInfo(activated_at=user_packet.activated_at,
                                  packet_name=packet.name,
                                  ending_at=ending_at,
                                  user_packet_id=user_packet.id)

    @staticmethod
    async def activate_packet(packet_id: int, session: AsyncSession):
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        stmt = (sa.select(UserPackets, Packets.name, Packets.count_per_day)
                .join(Packets, UserPackets.type == Packets.id)
                .where(UserPackets.id == packet_id))
        result = await session.execute(stmt)
        result = result.first()
        user_packet, packet_name, count_per_day = result
        if not user_packet or user_packet.activated_at <= now:  # Уже активирован или отсутствует
            return False
        user_packet.activated_at = now
        days_to_add = math.ceil((user_packet.all_posts + user_packet.today_posts) / count_per_day)
        user_packet.ending_at = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(days=days_to_add)

        await session.commit()
        result = {'name': packet_name,
                  'ending_at': user_packet.ending_at}
        return result

    @staticmethod
    async def pause_packet(packet_id: int, session: AsyncSession):
        stmt = (sa.select(UserPackets, Packets.name, Packets.count_per_day)
                .join(Packets, UserPackets.type == Packets.id)
                .where(UserPackets.id == packet_id))
        result = await session.execute(stmt)
        row = result.first()
        if not row:
            return False
        user_packet, packet_name, count_per_day = row
        user_packet.activated_at = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(days=3)
        user_packet.ending_at += timedelta(days=3)
        await session.commit()
        return datetime.strftime(user_packet.activated_at, '%d.%m')

    @staticmethod
    async def count_duration(post_count, count_per_day):
        return math.ceil(post_count / count_per_day)

    @staticmethod
    async def extend_packet(user_packet, additional_posts, new_limit_per_day):
        """Продлевает пакет, но не активирует его, если он еще не активирован."""
        user_packet.all_posts += additional_posts

        days_to_add = math.ceil(user_packet.all_posts / new_limit_per_day)
        user_packet.ending_at = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(days=days_to_add)

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
    async def revoke_packet(packet: UserPackets, session: AsyncSession):
        """Окончание срока действия пакета для пользователя"""
        await session.execute(sa.insert(ArchivePackets).values(id=packet.id,
                                                               user_id=packet.user_id,
                                                               activated_at=packet.activated_at,
                                                               ended_at=packet.ending_at,
                                                               price=packet.price))
        await session.execute(sa.delete(UserPackets).where(UserPackets.id == packet.id))
        await session.execute(sa.delete(AutoPosts).where(AutoPosts.user_id == packet.user_id))
        await session.commit()

        await FunnelActions.save(user_id=packet.user_id, action=FunnelUserActionsType.PACKET_ENDED, session=session)

    @staticmethod
    async def get_count_per_day(user_id: int, session: AsyncSession):
        stmt = sa.select(Packets.count_per_day).join(UserPackets, Packets.id == UserPackets.type).where(
            UserPackets.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
