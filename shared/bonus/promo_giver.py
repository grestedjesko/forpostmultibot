from sqlalchemy.orm import Session, joinedload
from database.models import Promotion, UserPromotion
from database.models.promotion import PromotionType
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class PromoGiver:
    def __init__(self, giver: str):
        self.giver = giver

    async def give_promo(self, user_id: int, promo_type: PromotionType, value: int, session: AsyncSession):
        stmt = sa.select(Promotion).where(Promotion.type == promo_type, Promotion.value == value, Promotion.source == self.giver)
        result = await session.execute(stmt)
        promotion = result.scalars().first()

        if not promotion:
            return

        # Проверяем, есть ли конфликтующие промо-акции
        existing_promos = await self._get_user_promos(user_id=user_id, session=session)
        for promo in existing_promos:
            if self._is_conflicting(promo.promotion.type, promo_type):
                promo.is_active = False
                session.add(promo)

        new_promo = UserPromotion(user_id=user_id, reward_id=promotion.id, is_active=True, is_used=False)
        session.add(new_promo)
        await session.commit()

    async def give_deposit_percent_bonus(self, user_id: int, percent: int, session: AsyncSession):
        """Выдаёт бонус за пополнение (например, +10% к пополнению)"""
        await self.give_promo(user_id=user_id,
                              promo_type=PromotionType.BALANCE_TOPUP_PERCENT,
                              value=percent,
                              session=session)

    async def give_packet_purchase_percent_bonus(self, user_id: int, percent: int, session: AsyncSession):
        await self.give_promo(user_id=user_id,
                              promo_type=PromotionType.PACKAGE_PURCHASE_PERCENT,
                              value=percent,
                              session=session)

    async def _get_user_promos(self, user_id: int, session: AsyncSession):
        """Получает активные промо-акции пользователя"""
        result = await session.execute(
            sa.select(UserPromotion).filter(
                UserPromotion.user_id == user_id,
                UserPromotion.is_active == True,
                UserPromotion.is_used == False
            )
        )
        return result.scalars().all()

    @staticmethod
    def _is_conflicting(existing: PromotionType, new: PromotionType) -> bool:
        """Проверяет, конфликтуют ли типы промо-акций"""
        balance_promos = {PromotionType.BALANCE_TOPUP_PERCENT, PromotionType.BALANCE_TOPUP_FIXED}
        package_promos = {PromotionType.PACKAGE_PURCHASE_PERCENT, PromotionType.PACKAGE_PURCHASE_FIXED, PromotionType.BONUS_PLACEMENTS}

        return ({existing, new} <= balance_promos) or ({existing, new} <= package_promos)