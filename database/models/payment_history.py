from sqlalchemy import (
    BigInteger, String, DECIMAL, TIMESTAMP, func, Integer, ForeignKeyConstraint, BINARY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
import uuid


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gate_payment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    packet_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payment_message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    amount: Mapped[float] = mapped_column(DECIMAL(8, 2), nullable=False)
    discount_promo_id: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    user = relationship("User", back_populates="payment_history")
    user_promotion = relationship("UserPromotion", back_populates="payment_history")
    bot = relationship("ForpostBotList", back_populates="payment_history", overlaps="user, payment_history")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['discount_promo_id'],
            ['user_promotion.id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
