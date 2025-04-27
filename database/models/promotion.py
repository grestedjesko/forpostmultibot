from sqlalchemy import TIMESTAMP, Float, Enum, String, JSON, Integer, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from database.base import Base
import uuid
import json


class PromotionType(str, PyEnum):
    BALANCE_TOPUP_PERCENT = "balance_topup_percent"
    BALANCE_TOPUP_FIXED = "balance_topup_fixed"
    PACKAGE_PURCHASE_PERCENT = "package_purchase_percent"
    PACKAGE_PURCHASE_FIXED = "package_purchase_fixed"
    BONUS_PLACEMENTS = "bonus_placements"


class Promotion(Base):
    __tablename__ = "promotion"

    id: Mapped[str] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[PromotionType] = mapped_column(Enum(PromotionType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    source: Mapped[str] = mapped_column(String(20))  # например: "funnel", "lottery"
    packet_ids: Mapped[json] = mapped_column(JSON, nullable=False, default="[]")

    user_promotion = relationship("UserPromotion", back_populates="promotion", overlaps="promotion,user")
    bot = relationship("ForpostBotList", back_populates="promotion")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )


