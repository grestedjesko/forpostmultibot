import sqlalchemy as sa
from database.models import Packets, UserPromotion, Promotion
from database.models.promotion import PromotionType
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.prices import Prices, OneTimePacket
from shared.bonus.promo_giver import UserPacketPromotionInfo
from pydantic import BaseModel
from typing import Optional

one_time_price_id = 1


class PacketPrice(BaseModel):
    name: str
    price: int
    discount: Optional[int]


class PriceList:
    @staticmethod
    async def get_packet_price_by_id(session: AsyncSession, packet_id: int, user_promotion: UserPacketPromotionInfo):
        query = (sa.select(Packets.name, Prices.price)
                 .join(Prices, Packets.id == Prices.id)
                 .filter(Packets.id == packet_id))
        result = await session.execute(query)
        result = result.fetchone()
        packet_name, price = result
        if user_promotion:
            price = int(price * (1 - user_promotion.value / 100))
            discount = user_promotion.value
        else:
            discount = 0

        packet_price = PacketPrice(name=packet_name, price=price, discount=discount)
        return packet_price

    @staticmethod
    async def get_packets_price(session: AsyncSession, user_promotion):
        query = sa.select(Packets, Prices.price).join(Prices, Packets.id == Prices.id)
        result = await session.execute(query)
        prices = []
        for packet, price in result.fetchall():
            if user_promotion and (packet.id in user_promotion.packet_ids):
                packet.price = int(price * (1 - user_promotion.value / 100))
                packet.discount = user_promotion.value
            else:
                packet.price = price
                packet.discount = None

            prices.append(packet)

        return prices

    @staticmethod
    async def get_onetime_price(session: AsyncSession) -> list[OneTimePacket]:
        query = sa.select(Prices.price).where(Prices.id == one_time_price_id)
        result = await session.execute(query)

        price = result.scalar_one_or_none()
        return [OneTimePacket(one_time_price_id, 'Поштучное размещение', price)]

    @staticmethod
    async def get(session: AsyncSession, user_promotion = None):
        onetime_price = await PriceList.get_onetime_price(session=session)
        packet_prices = await PriceList.get_packets_price(session=session, user_promotion=user_promotion)

        result = onetime_price + packet_prices
        return result