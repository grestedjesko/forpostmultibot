from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user_bonus_history import UserBonusHistory
from shared.user import BalanceManager
from shared.user_packet import PacketManager
import sqlalchemy as sa
from database.models import User


class BonusGiver:
    def __init__(self, giver: str):
        self.giver = giver

    async def give_balance_bonus(self, user_id: int, amount: int, session: AsyncSession):
        """Выдаёт бонус на баланс"""
        print(user_id)
        await BalanceManager.deposit(amount=amount, user_id=user_id, session=session)
        await self._save_bonus(session, amount=amount, packet_id=None, session=session)

    async def give_packet_bonus(self, user_id: int, packet_id: int, session: AsyncSession):
        """Выдаёт бонус-пакет"""
        assigned_packet = await PacketManager.assign_packet(
            user_id=user_id,
            packet_type=packet_id,
            price=0,
            session=session
        )
        await self._save_bonus(user_id=user_id, amount=None, packet_id=packet_id, session=session)
        return assigned_packet

    async def _save_bonus(self, user_id: int, amount: int | None, packet_id: int | None, session: AsyncSession):
        """Сохраняет бонус в истории (только для баланса и пакетов)"""
        print(f"Attempting to find user with ID: {user_id}")
        user = await session.execute(sa.select(User).filter_by(telegram_user_id=user_id))
        user = user.scalars().first()

        if user:
            print(f"User with ID {user_id} found.")
            bonus = UserBonusHistory(user_id=user_id, packet_type=packet_id, amount=amount, giver=self.giver)
            session.add(bonus)
            await session.commit()
        else:
            print(f"User with ID {user_id} not found.")