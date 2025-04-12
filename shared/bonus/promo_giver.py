from sqlalchemy.orm import Session, joinedload
from database.models import Promotion, UserPromotion
from database.models.promotion import PromotionType
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pydantic import BaseModel
from typing import List


class UserPacketPromotionInfo(BaseModel):
    id: int
    value: int
    packet_ids: List[int]
    ending_at: datetime


class PromoManager:
    @staticmethod
    async def set_promo_used(user_promo_id: int, session: AsyncSession):
        query = (sa.update(UserPromotion).values(used_at=datetime.now(),
                                                 is_active=False,
                                                 is_used=True)
                 .where(UserPromotion.id == user_promo_id))
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def get_user_promotion(user_id: int, session: AsyncSession):
        query = (
            sa.select(UserPromotion.id, Promotion.value, Promotion.packet_ids, UserPromotion.ending_at)
            .join(UserPromotion, Promotion.id == UserPromotion.reward_id)
            .where(UserPromotion.user_id == user_id,
                   UserPromotion.is_used == False,
                   UserPromotion.is_active == True,
                   UserPromotion.ending_at > datetime.now(),
                   Promotion.type == PromotionType.PACKAGE_PURCHASE_PERCENT)
            )
        result = await session.execute(query)
        data = result.first()
        if data:
            return UserPacketPromotionInfo(id=data[0],
                                           value=data[2],
                                           packet_ids=data[3],
                                           ending_at=data[4])
        return None


    @staticmethod
    async def give_promo(user_id: int, promo_id: int, giver: str, session: AsyncSession):
        stmt = sa.select(Promotion).where(Promotion.id == promo_id, Promotion.source == giver)
        result = await session.execute(stmt)
        promotion = result.scalars().first()

        if not promotion:
            return

        # Проверяем, есть ли конфликтующие промо-акции
        existing_promos = await PromoManager._get_user_promos(user_id=user_id, session=session)
        for promo in existing_promos:
            if PromoManager._is_conflicting(promo.promotion.type, promotion.type):
                promo.is_active = False
                session.add(promo)

        new_promo = UserPromotion(user_id=user_id, reward_id=promotion.id, is_active=True, is_used=False)
        session.add(new_promo)
        await session.commit()

    @staticmethod
    async def _get_user_promos(user_id: int, session: AsyncSession):
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
        package_promos = {PromotionType.PACKAGE_PURCHASE_PERCENT,
                          PromotionType.PACKAGE_PURCHASE_FIXED,
                          PromotionType.BONUS_PLACEMENTS}

        return ({existing, new} <= balance_promos) or ({existing, new} <= package_promos)