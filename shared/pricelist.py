import sqlalchemy as sa
from database.models import Packets
from database.models.promotion import PromotionType
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.prices import Prices, OneTimePacket
from shared.bonus.promo_manager import UserPromotionInfo
from pydantic import BaseModel
from typing import Optional

one_time_price_id = 1


class PacketPrice(BaseModel):
    id: int
    name: str
    short_name: str
    price: int
    discount: Optional[str]


class PriceList:
    @staticmethod
    async def get_new_packet_price(packet_id, packet_promotion, price, packet_name, short_name):
        discount = None
        if packet_promotion and packet_id in packet_promotion.packet_ids:
            if packet_promotion.type == PromotionType.PACKAGE_PURCHASE_PERCENT:
                price = int(price * (1 - packet_promotion.value / 100))
                discount = f"-{packet_promotion.value}%"
            elif packet_promotion.type == PromotionType.PACKAGE_PURCHASE_FIXED:
                price = int(price - packet_promotion.value)
                discount = f"-{packet_promotion.value}₽"

        packet_price = PacketPrice(id=packet_id, name=packet_name, short_name=short_name, price=price, discount=discount)
        return packet_price

    @staticmethod
    async def get_packet_price_by_id(session: AsyncSession, packet_id: int, packet_promotion: UserPromotionInfo | None = None):
        bot_id = session.info["bot_id"]
        query = (
            sa.select(Packets.name, Packets.short_name, Prices.price)
            .join(Prices, sa.and_(
                Packets.id == Prices.id,
                Prices.bot_id == bot_id  # bot_id у цен
            ))
            .filter(
                sa.and_(
                    Packets.id == packet_id,
                    Packets.bot_id == bot_id  # bot_id у пакетов
                )
            )
        )
        result = await session.execute(query)
        result = result.fetchone()
        packet_name, packet_short_name, price = result
        packet_price = await PriceList.get_new_packet_price(packet_id=packet_id,
                                                            packet_promotion=packet_promotion,
                                                            price=price,
                                                            packet_name=packet_name,
                                                            short_name=packet_short_name)
        return packet_price

    @staticmethod
    async def get_packets_price(session: AsyncSession, packet_promotion):
        bot_id = session.info["bot_id"]
        query = (
            sa.select(Packets, Prices.price)
            .join(Prices, sa.and_(
                Packets.id == Prices.id,
                Prices.bot_id == bot_id  # bot_id у цен
            ))
            .where(
                Packets.bot_id == bot_id  # bot_id у пакетов
            )
        )

        result = await session.execute(query)
        prices = []
        for packet, price in result.fetchall():
            packet_price = await PriceList.get_new_packet_price(packet_id=packet.id,
                                                                packet_promotion=packet_promotion,
                                                                price=price,
                                                                packet_name=packet.name,
                                                                short_name=packet.short_name)
            prices.append(packet_price)
        return prices

    @staticmethod
    async def get_onetime_price(session: AsyncSession) -> list[OneTimePacket]:
        bot_id = session.info["bot_id"]
        query = sa.select(Prices.price).where(Prices.id == one_time_price_id, Prices.bot_id == bot_id)
        result = await session.execute(query)

        price = result.scalar_one_or_none()
        return [OneTimePacket(one_time_price_id, 'Поштучное размещение', price)]

    @staticmethod
    async def get(session: AsyncSession, packet_promotion=None):
        onetime_price = await PriceList.get_onetime_price(session=session)
        packet_prices = await PriceList.get_packets_price(session=session, packet_promotion=packet_promotion)
        result = onetime_price + packet_prices
        return result