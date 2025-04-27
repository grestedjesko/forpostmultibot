from sqlalchemy import ForeignKeyConstraint, TIMESTAMP, Boolean, Integer, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from database.base import Base
import uuid


class UserPromotion(Base):
    __tablename__ = "user_promotion"

    id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reward_id: Mapped[int] = mapped_column(Integer, nullable=False)

    assigned_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    ending_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id']
        ),
        ForeignKeyConstraint(
            ['bot_id', 'reward_id'],
            ['promotion.bot_id', 'promotion.id']
        ),
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id']
        ),
    )

    user = relationship("User", back_populates="promotion", overlaps="user_promotion")
    promotion = relationship("Promotion", back_populates="user_promotion", overlaps="promotion,user")
    payment_history = relationship("PaymentHistory", back_populates="user_promotion")
    bot = relationship("ForpostBotList", back_populates="user_promotion", overlaps="promotion,promotion,user,user_promotion")
