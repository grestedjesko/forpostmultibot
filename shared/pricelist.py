import sqlalchemy as sa
from database.models.packets import Packets
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.prices import Prices, OneTimePacket

one_time_price_id = 1


class PriceList:
    async def get_packet_price_by_id(self, session: AsyncSession, packet_id: int):
        query = (sa.select(Packets.name, Prices.price)
                .join(Prices, Packets.id == Prices.id)
                .filter(Packets.id == packet_id))

        result = await session.execute(query)
        result = result.fetchone()  # Получаем одну запись, так как ищем по id

        if result:
            return result
        else:
            return None

    async def get_packets_price(self, session: AsyncSession):
        query = sa.select(Packets, Prices.price).join(Prices, Packets.id == Prices.id)
        result = await session.execute(query)

        prices = []
        for packet, price in result.fetchall():
            packet.price = price  # Добавляем атрибут price вручную
            prices.append(packet)

        return prices

    async def get_onetime_price(self, session: AsyncSession) -> list[OneTimePacket]:
        query = sa.select(Prices.price).where(Prices.id == one_time_price_id)
        result = await session.execute(query)

        price = result.scalar_one_or_none()
        return [OneTimePacket(one_time_price_id, 'Поштучное размещение', price)]

    async def get(self, session: AsyncSession):
        onetime_price = await self.get_onetime_price(session=session)
        packet_prices = await self.get_packets_price(session=session)

        result = onetime_price + packet_prices
        return result