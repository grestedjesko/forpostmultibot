from sqlalchemy import ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from database.base import Base


class UserPromotion(Base):
    __tablename__ = "user_promotion"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_user_id"), nullable=False)
    reward_id: Mapped[int] = mapped_column(ForeignKey("promotion.id"), nullable=False)

    assigned_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    ending_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="promotion")
    promotion = relationship("Promotion", back_populates="user_promotion")
    payment_history = relationship("PaymentHistory", back_populates="user_promotion")
